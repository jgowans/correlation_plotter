#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from directionFinder_backend.correlator import Correlator
import scipy.signal
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

if __name__ == '__main__':
    c = Correlator()
    c.fetch_time_domain_snapshot(force=True)

    time_domain_padding = 10
    fs = 800e6
    upsample_factor = 100 
    a_idx = 0 
    b_idx = 1 
    a = np.concatenate(
        (np.zeros(time_domain_padding),
         c.time_domain_signals[a_idx],
         np.zeros(time_domain_padding)))
    a_time = np.linspace(-(time_domain_padding/fs), 
                         (len(a)-time_domain_padding)/fs, 
                         len(a),
                         endpoint=False)
    b = c.time_domain_signals[b_idx]
    b_time = np.linspace(0,
                         len(b)/fs,
                         len(b),
                         endpoint=False)
    correlation = np.correlate(a, b, mode='valid')
    correlation_time = np.linspace(a_time[0] - b_time[0],
                                    a_time[-1] - b_time[-1],
                                    len(correlation),
                                    endpoint=True)
    correlation_upped, correlation_time_upped = scipy.signal.resample(
        correlation,
        len(correlation)*upsample_factor,
        t = correlation_time)
    # normalise
    correlation_upped /= max(correlation)
    correlation /= max(correlation)
    correlation_time *= 1e9
    correlation_time_upped *= 1e9
    fig = plt.figure()
    ax1 = fig.gca()
    ax1.plot(correlation_time_upped, correlation_upped, color='b', linewidth=2, label="Upsampled")
    ax1.plot(correlation_time, correlation, color='r', linewidth=2, marker='.', markersize=15, label="Raw")
    xy_before = (correlation_time[np.argmax(correlation)-1], correlation[np.argmax(correlation)-1])
    ax1.annotate('higher', xy=xy_before,
                xytext=(0.2, 0.4), textcoords='axes fraction',
                arrowprops=dict(facecolor='black', shrink=0.09, width=2),
                horizontalalignment='right', verticalalignment='top',)
    xy_after = (correlation_time[np.argmax(correlation)+1], correlation[np.argmax(correlation)+1])
    ax1.annotate('lower', xy=xy_after,
                xytext=(0.6, 0.3), textcoords='axes fraction',
                arrowprops=dict(facecolor='black', shrink=0.09, width=2),
                horizontalalignment='right', verticalalignment='top',)
    axins = zoomed_inset_axes(ax1, 9, loc=1)
    axins.plot(correlation_time_upped, correlation_upped, color='b', marker='.', linewidth=2, label="Upsampled")
    axins.plot(correlation_time, correlation, color='r', linewidth=2, marker='.', markersize=15, label="Raw")

    axins.set_xlim(-3.2, -2.2)
    axins.set_ylim(0.97, 1.05)
    axins.xaxis.set_ticks(np.arange(-3.4, -1.9, 0.4))
    #plt.xticks(visible=False)
    plt.yticks(visible=False)
    mark_inset(ax1, axins, loc1=2, loc2=3, fc='none', ec='0.5')

    ax1.set_title("Comparison of raw time domain cross correlation with upsampled version")
    ax1.set_xlabel("Time shift (ns)")
    ax1.set_ylabel("Cross correlation value (normalised)")
    ax1.legend(loc=2)

    plt.show()

