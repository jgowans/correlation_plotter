#!/usr/bin/env python

import time
import numpy as np
import matplotlib.pyplot as plt
from directionFinder_backend.snapshot import Snapshot
from directionFinder_backend.correlator import Correlator
import corr
import itertools
import logging
from colorlog import ColoredFormatter

axes =  [[], [], [], []]
lines = [[], [], [], []]
fig = plt.figure(1)

def create_figure(time, frequency, cross):
    # time domain signals
    axes[0].append(fig.add_subplot(4, 5, 1))
    axes[0].append(fig.add_subplot(4, 5, 2, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(fig.add_subplot(4, 5, 3, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(fig.add_subplot(4, 5, 4, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(None)
    axes[0][0].set_ylim([-130, 130])
    for idx in range(4):
        lines[0].append(axes[0][idx].plot(time[idx])[0])
    # single channel FFTs
    axes[1].append(fig.add_subplot(4, 5, 6))
    axes[1].append(fig.add_subplot(4, 5, 7, sharex=axes[1][0], sharey=axes[1][0]))
    axes[1].append(fig.add_subplot(4, 5, 8, sharex=axes[1][0], sharey=axes[1][0]))
    axes[1].append(fig.add_subplot(4, 5, 9, sharex=axes[1][0], sharey=axes[1][0]))
    axes[1].append(fig.add_subplot(4, 5, 10, sharex=axes[1][0]))
    for idx in range(4):
        fft = np.square((np.fft.rfft(time[idx])))
        fft[0] = 0 # focing DC bin to 0. naughty... this should be done with ADC cal
        fft = 10*np.log10(fft)
        fft_x = np.linspace(0, 400, fft.shape[0])
        lines[1].append(axes[1][idx].plot(fft_x, fft, marker='.')[0])
    #axes[1][0].set_ylim(bottom=0)
    fft_x = np.linspace(0, 400, frequency[0].shape[0])
    lines[1].append(axes[1][4].plot(fft_x, 10*np.log10(np.abs(frequency[0])), marker='.')[0])
    #axes[1][-1].set_ylim(bottom=0)
    # cross correlations
    axes[2].append(fig.add_subplot(4, 6, 13))
    axes[2].append(fig.add_subplot(4, 6, 14, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(4, 6, 15, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(4, 6, 16, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(4, 6, 17, sharex=axes[2][0], sharey=axes[2][0]))
    axes[2].append(fig.add_subplot(4, 6, 18, sharex=axes[2][0], sharey=axes[2][0]))
    cross_x = np.linspace(0, 400, cross[0].shape[0])
    baselines = list(itertools.combinations(range(4), 2))
    for idx in range(6):
        #to_plot = np.abs(cross[idx])
        #to_plot = 10*np.log10(cross[idx])
        a, b = baselines[idx]
        to_plot = np.angle(np.fft.rfft(time[a]) * np.conj(np.fft.rfft(time[b])))[0:-1]
        lines[2].append(
            axes[2][idx].plot(cross_x, to_plot)[0]
        )
    #axes[2][0].set_ylim(bottom=0)
    axes[3].append(fig.add_subplot(4, 6, 19, sharex=axes[2][0]))
    axes[3].append(fig.add_subplot(4, 6, 20, sharex=axes[2][0], sharey=axes[3][0]))
    axes[3].append(fig.add_subplot(4, 6, 21, sharex=axes[2][0], sharey=axes[3][0]))
    axes[3].append(fig.add_subplot(4, 6, 22, sharex=axes[2][0], sharey=axes[3][0]))
    axes[3].append(fig.add_subplot(4, 6, 23, sharex=axes[2][0], sharey=axes[3][0]))
    axes[3].append(fig.add_subplot(4, 6, 24, sharex=axes[2][0], sharey=axes[3][0]))
    for idx in range(6):
        lines[3].append(
            axes[3][idx].plot(cross_x, np.angle(cross[idx]))[0]
        )
#    axes[3][0].set_ylim(bottom=-0.05, top=0.05)
    fig.show()


def update_figure(time, frequency, cross):
    for idx in range(4):
        lines[0][idx].set_ydata(time[idx])
        fft = np.fft.rfft(time[idx])
        fft = np.abs( fft * np.conj(fft) ) # get autocorrelation
        fft[0] = 0  # focing DC bin to 0. naughty... this should be done with ADC cal
        fft = 10*np.log10(fft)
        lines[1][idx].set_ydata(fft)
    lines[1][4].set_ydata(10*np.log10((np.abs(frequency[0]))))
    baselines = list(itertools.combinations(range(4), 2))
    for idx in range(6):
        #to_plot = 10*np.log10((np.abs(cross[idx])))
        a, b = baselines[idx]
        to_plot = np.angle(np.fft.rfft(time[a]) * np.conj(np.fft.rfft(time[b])))[0:-1]
        lines[2][idx].set_ydata(to_plot)
        lines[3][idx].set_ydata(np.angle(cross[idx]))
    plt.pause(0.05)

if __name__ == '__main__':
    logger = logging.getLogger('main')
    handler = logging.StreamHandler()
    colored_formatter = ColoredFormatter("%(log_color)s%(asctime)s%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(colored_formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    correlator = Correlator(logger = logger.getChild('correlator'))
    correlator.set_shift_schedule(0b00000000000)
    correlator.set_accumulation_len(40000)
    correlator.re_sync()
    correlator.fetch_autos()
    correlator.fetch_time_domain_snapshot(force=True)
    #correlator.apply_cable_length_calibrations('/home/jgowans/workspace/directionFinder_backend/config/cable_length_calibration.json')
    #correlator.apply_frequency_bin_calibrations('/home/jgowans/workspace/directionFinder_backend/config/frequency_domain_calibration_direct_in_phase.json')
    created = False
    while True:
        time = []
        correlator.fetch_time_domain_snapshot(force=True)
        for antenna_idx in range(4):
            time.append(correlator.time_domain_signals[antenna_idx][0:2048])
        correlator.fetch_all()
        frequency = [(correlator.frequency_correlations[(0,0)].signal)]
        frequency[0][0] = 0  # focing DC bin to 0. naughty... this should be done with ADC cal
        f = correlator.frequency_correlations[(0,1)].strongest_frequency()
        #ph = correlator.correlations[(0,1)].phase_at_freq(f)
        #print("f: {f}   ;   ph: {ph}".format(f = f, ph = ph))
        cross = []
        cross_combinations = list(itertools.combinations(range(4), 2))
        for comb in cross_combinations:
            x = correlator.frequency_correlations[comb].signal
            x[0] = 0
            cross.append(x)
        if created == True:
            update_figure(time, frequency, cross)
        else:
            create_figure(time, frequency, cross)
            created = True
