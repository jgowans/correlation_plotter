#!/usr/bin/env python

import time
import numpy as np
import matplotlib.pyplot as plt
from directionFinder_backend.snapshot import Snapshot
from directionFinder_backend.control_register import ControlRegister
import corr

axes =  [[], [], [], []]
lines = [[], [], [], []]
fig = plt.figure(1)

def create_figure(signals):
    axes[0].append(fig.add_subplot(241))
    axes[1].append(fig.add_subplot(242))
    axes[2].append(fig.add_subplot(243))
    axes[3].append(fig.add_subplot(244))
    axes[0].append(fig.add_subplot(245))
    axes[1].append(fig.add_subplot(246))
    axes[2].append(fig.add_subplot(247))
    axes[3].append(fig.add_subplot(248))
    for idx in range(4):
        axes[idx][0].set_ylim([-130, 130])
    for idx in range(4):
        fft = np.abs(np.fft.rfft(signals[idx]))
        fft_x = np.linspace(0, 400, fft.shape[0])
        lines[idx].append(axes[idx][0].plot(signals[idx])[0])
        lines[idx].append(axes[idx][1].plot(fft_x, fft)[0])
    fig.show()


def update_figure(signals):
    for idx in range(4):
        lines[idx][0].set_ydata(signals[idx])
        fft = np.abs(np.fft.rfft(signals[idx]))
        lines[idx][1].set_ydata(fft)
    plt.pause(0.1)


if __name__ == '__main__':
    fpga = corr.katcp_wrapper.FpgaClient('localhost', 7147, timeout=5)
    time.sleep(1)
    print(fpga.est_brd_clk())
    control_register = ControlRegister(fpga)
    snapshot = Snapshot(fpga, 
                        'time_domain_snap',
                        dtype = np.int8,
                        cvalue = False)
    created = False
    while True:
        signals = []
        for antenna_idx in range(4):
            adcs = ['0I', '0Q', '1I', '1Q']
            control_register.select_adc(adcs[antenna_idx])
            snapshot.fetch_signal(force=True)
            signals.append(snapshot.signal[0:1024])
        if created == True:
            update_figure(signals)
        else:
            create_figure(signals)
            created = True



