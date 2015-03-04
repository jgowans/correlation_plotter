#!/usr/bin/env python

import time, logging, os, shutil
import numpy as np
import matplotlib.pyplot as plt
import corr

SNAPSHOT_BLOCK_SIZE =8*(2**16)
SAMPLE_FREQUENCY = 1600.0 # MHz and us


def get_triggered_snapshot():
    # arm the snapshot blocks
    fpga.snapshot_arm("snap64", man_trig=True, man_valid=False, offset=-1, circular_capture=False)
    fpga.snapshot_arm("snapshot", man_trig=True, man_valid=False, offset=-1, circular_capture=False)
    time.sleep(0.1)
    # length = padding of 2^15 "clock cycles" each side of the pulse, where each clock cycle is 16 samples.
    # the padding takes about 1 second to read out. Worth it, I think!! :-)
    # ensure we don't try to read more than the maximum number of camptured samples
    length_to_read = SNAPSHOT_BLOCK_SIZE
    dram_data = fpga.read_dram(length_to_read)
    bram_data = fpga.snapshot_get('snap64', arm=False)['data']
    dram_signal = np.frombuffer(dram_data, dtype=np.int8)
    bram_signal = np.frombuffer(bram_data, dtype=np.int8)
    dram_fft = np.fft.rfft(dram_signal)
    bram_fft = np.fft.rfft(bram_signal)
    assert(len(bram_fft) == len(dram_fft))
    fft_axis = np.linspace(0, (SAMPLE_FREQUENCY/2.0), len(dram_fft), endpoint=False)
    fig = plt.figure()
    ax_fft_signal0 = fig.add_subplot(121)
    ax_fft_signal1 = fig.add_subplot(122, sharex=ax_fft_signal0, sharey=ax_fft_signal0)
    ax_fft_signal0.plot(fft_axis, (np.abs(dram_fft)))
    ax_fft_signal1.plot(fft_axis, (np.abs(bram_fft)))
#    ax_fft_signal0.plot((dram_signal[0:1000]))
#    ax_fft_signal1.plot((bram_signal[0:1000]))
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plt.show()

fpga = corr.katcp_wrapper.FpgaClient("localhost")

while True:
    get_triggered_snapshot()
