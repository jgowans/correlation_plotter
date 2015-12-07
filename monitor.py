#!/usr/bin/env python

import time
import numpy as np
import matplotlib.pyplot as plt
from directionFinder_backend.snapshot import Snapshot
from directionFinder_backend.correlator import Correlator
import corr

axes =  [[], [], []]
lines = [[], [], []]
fig = plt.figure(1)

def create_figure(time, frequency, cross):
    # time domain signals
    axes[0].append(fig.add_subplot(3, 5, 1))
    axes[0].append(fig.add_subplot(3, 5, 2, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(fig.add_subplot(3, 5, 3, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(fig.add_subplot(3, 5, 4, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(None)
    axes[0][0].set_ylim([-130, 130])
    for idx in range(4):
        lines[0].append(axes[0][idx].plot(time[idx])[0])
    # single channel FFTs
    axes[1].append(fig.add_subplot(3, 5, 6))
    axes[1].append(fig.add_subplot(3, 5, 7, sharex=axes[1][0], sharey=axes[1][0]))
    axes[1].append(fig.add_subplot(3, 5, 8, sharex=axes[1][0], sharey=axes[1][0]))
    axes[1].append(fig.add_subplot(3, 5, 9, sharex=axes[1][0], sharey=axes[1][0]))
    axes[1].append(fig.add_subplot(3, 5, 10))
    for idx in range(4):
        fft = np.abs(np.fft.rfft(time[idx]))
        fft_x = np.linspace(0, 400, fft.shape[0])
        lines[1].append(axes[1][idx].plot(fft_x, fft)[0])
    fft_x = np.linspace(0, 400, frequency[0].shape[0])
    lines[1].append(axes[1][4].plot(fft_x, frequency[0])[0])
    # cross correlations
    axes[2].append(fig.add_subplot(3, 6, 13))
    axes[2].append(fig.add_subplot(3, 6, 14, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(3, 6, 15, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(3, 6, 16, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(3, 6, 17, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(3, 6, 18, sharex=axes[2][0], sharey=axes[2][0]))
    for idx in range(4):
        pass
    fig.show()


def update_figure(time, frequency, cross):
    for idx in range(4):
        lines[0][idx].set_ydata(time[idx])
        fft = np.abs(np.fft.rfft(time[idx]))
        lines[1][idx].set_ydata(fft)
    lines[1][4].set_ydata(frequency[0])
    plt.pause(0.05)

if __name__ == '__main__':
    fpga = corr.katcp_wrapper.FpgaClient('localhost', 7147, timeout=5)
    time.sleep(1)
    print(fpga.est_brd_clk())
    correlator = Correlator()
    correlator.set_shift_schedule(0b1111101111)
    correlator.set_accumulation_len(400)
    correlator.re_sync()
    correlator.fetch_autos()
    snapshot = Snapshot(fpga, 
                        'time_domain_snap',
                        dtype = np.int8,
                        cvalue = False)
    created = False
    while True:
        time = []
        for antenna_idx in range(4):
            adcs = ['0I', '0Q', '1I', '1Q']
            correlator.control_register.select_adc(adcs[antenna_idx])
            snapshot.fetch_signal(force=True)
            time.append(snapshot.signal[0:1024])
        correlator.fetch_autos()
        frequency = [np.abs(correlator.correlations[(0,0)].snapshot.signal)]
        print(sum(np.square(np.abs(frequency[0])))/len(frequency[0]))
        if created == True:
            update_figure(time, frequency, None)
        else:
            create_figure(time, frequency, None)
            created = True
