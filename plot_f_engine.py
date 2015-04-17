#!/usr/bin/env python

# Note: all frequencies in MHz, all times in us

import corr
import numpy as np
import itertools
import matplotlib.pyplot as plt
import time
from operator import add

def snaps():
    return ['ch0_00_re', 'ch0_00_im', 'ch0_01_re', 'ch0_01_im']

def arm_snaps():
    for snap in snaps():
        fpga.snapshot_arm(snap)

def get_snap(snap):
    raw = fpga.snapshot_get(snap, arm=False)['data']
    unpacked = np.frombuffer(raw, dtype=np.int32)
    return unpacked

def re_sync():
    fpga.write_int('sync_gen_sync', 0)
    fpga.write_int('sync_gen_sync', 1)
    fpga.write_int('sync_gen_sync', 0)

def get_sync_time():
    re_sync()
    fpga.write_int('sync_gen_latch_reset', 0)
    while fpga.read_uint('sync_gen_latch') == 0:
        pass
    t0 = time.time()
    fpga.write_int('sync_gen_latch_reset', 1)
    fpga.write_int('sync_gen_latch_reset', 0)
    while fpga.read_uint('sync_gen_latch') == 0:
        pass
    delta_t = time.time() - t0
    print("sync time: {t}".format(t=delta_t))
    return delta_t

def get_acc_time():
    fpga.write_int('new_acc_latch_reset', 0)
    while fpga.read_uint('new_acc_latch') == 0:
        pass
    t0 = time.time()
    fpga.write_int('new_acc_latch_reset', 1)
    fpga.write_int('new_acc_latch_reset', 0)
    while fpga.read_uint('new_acc_latch') == 0:
        pass
    delta_t = time.time() - t0
    print("accumulation time: {t}".format(t=delta_t))
    return delta_t

def plot_power():
    raw = fpga.snapshot_get('ch0_snap1')['data']
    unpacked = np.frombuffer(raw, np.dtype('>i4'))
    fft_ax = np.linspace(0, 400, len(unpacked))
    plt.plot(fft_ax, unpacked)
    plt.show()

def plot_cross():
    raw = fpga.snapshot_get('ch0_snap')['data']
    unpacked = np.frombuffer(raw, np.dtype('>i4')) # big endian 4 byte ints
    re = unpacked[1::2]
    im = unpacked[0::2]
    assert(len(re) == len(im))
    fft = []
    for i in range(0, len(re)):
        fft.append(re[i] + (1j * im[i]))
    fft_ax = np.linspace(0, 400, len(fft))
    fig = plt.figure()
    ax_fft_mag = fig.add_subplot(211)
    ax_fft_phase = fig.add_subplot(212, sharex=ax_fft_mag)
    ax_fft_mag.plot(fft_ax, np.abs(fft))
    ax_fft_phase.plot(fft_ax, np.angle(fft, deg=True))
    plt.show()

class FFTData:
    def __init__(self, signal, fs, f_min, f_max):
        self.signal = signal
        self.fs = fs
        self.axis = np.linspace(0, fs, len(signal), endpoint=False)

    def find_peak(self, f_min, f_max):
        '''
        Finds the peak frequency and amplitude in a given range.
        Returns (f, amp)
        '''
        pass


fpga = corr.katcp_wrapper.FpgaClient('localhost')
time.sleep(0.1)

fpga.write_int('acc_len', 4096)
#fpga.write_int('acc_len', 65536)
#fpga.write_int('acc_len', 128)
fpga.write_int('fft_shift', 2**12 - 1)
time.sleep(1)
fpga.write_int('acc_rst', 1)
fpga.write_int('acc_rst', 0)
#re_sync()
#get_acc_time()
re_sync()
time.sleep(1)

while True:
#    plot_power()
    plot_cross()
