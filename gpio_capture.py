#!/usr/bin/env python

import argparse
import corr
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time

parser = argparse.ArgumentParser(description = 'Capture transients from GPIO triggered ROACH')
parser.add_argument('--calibrate', default=False, type=bool)
parser.add_argument('--plot_time', default=False, type=bool)
parser.add_argument('--plot_freq', default=False, type=bool)
parser.add_argument('--force_trigger', default=False, type=bool)
parser.add_argument('--pos_time_us', default=0, type=float)
parser.add_argument('--neg_time_us', default=0, type=float)
parser.add_argument('--host', default='192.168.14.30', type=str)
parser.add_argument('--samples', default=2**20, type=int)
parser.add_argument('--trig_level', default=20, type=int)
parser.add_argument('--capture_dir', default='/tmp/', type=str)

args = parser.parse_args()

if args.calibrate == True:
    execfile('set_iad_calibration_values.py')

fpga = corr.katcp_wrapper.FpgaClient(args.host)
time.sleep(0.1)
clock_speed = int(fpga.est_brd_clk())
print('got clk speed of: {cs}'.format(cs = clock_speed))

pos_edge_samples = int((args.pos_time_us / 10**6)/(1.0/clock_speed))
print('for pos edge time of {t} us, setting {s} samples'.format(t = args.pos_time_us, s = pos_edge_samples))
fpga.write_int('pos_edge_time', pos_edge_samples)

neg_edge_samples = int((args.neg_time_us / 10**6)/(1.0/clock_speed))
print('for neg edge time of {t} us, setting {s} samples'.format(t = args.neg_time_us, s = neg_edge_samples))
fpga.write_int('neg_edge_time', neg_edge_samples)

fpga.write_int('trig_level', args.trig_level)
fpga.write_int('force_trigger_arm', args.force_trigger)

while True:
    fpga.snapshot_arm('snapshot', man_trig=args.force_trigger, man_valid=False, offset=-1, circular_capture=False)
    while fpga.read_int('triggered_latch') == 0:
        pass
    edge = 'pos' if fpga.read_uint('gpioa_state_snap') else 'neg'
    snap_time = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
    print('got edge: {e} at time: {t}'.format(e = edge, t = snap_time))
    time.sleep(0.1)
    raw = fpga.read_dram(args.samples)
    signal = np.frombuffer(raw, dtype=np.int8)
    x0 = signal[0:len(signal)+1:2]
    x1 = signal[1:len(signal)+1:2]
    x0 = x0 - np.mean(x0)
    x1 = x1 - np.mean(x1)
    signal = []
    for idx, val in enumerate(x0):
        signal.append(val)
        signal.append(x1[idx])
    file_name = '{d}/{t}_{e}'.format(d = args.capture_dir, t = snap_time, e = edge)
    with open(file_name, 'w') as f:
        f.write(signal)
    if args.plot_time == True:
        plt.plot(signal)
        plt.show()
    if args.plot_freq == True:
        signal_fft = np.fft.rfft(signal)
        fft_axis = np.linspace(0, 1600/2, len(signal_fft), endpoint=False)
        plt.plot(fft_axis, np.abs(signal_fft))
        plt.show()

