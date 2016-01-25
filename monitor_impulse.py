#!/usr/bin/env python

import time
import numpy as np
import matplotlib.pyplot as plt
from directionFinder_backend.correlator import Correlator
import corr
import itertools
import logging
from colorlog import ColoredFormatter

if __name__ == '__main__':
    logger = logging.getLogger('main')
    handler = logging.StreamHandler()
    colored_formatter = ColoredFormatter("%(log_color)s%(asctime)s%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(colored_formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    correlator = Correlator(logger = logger.getChild('correlator'))
    time.sleep(1)
    correlator.set_impulse_filter_len(50)
    correlator.set_impulse_setpoint(3772)
    correlator.add_time_domain_calibration('/home/jgowans/workspace/directionFinder_backend/config/time_domain_calibration_long_sma_cables_only.json')
    correlator.add_cable_length_calibrations('/home/jgowans/workspace/directionFinder_backend/config/cable_length_calibration.json')
    correlator.re_sync()
    correlator.impulse_arm()

    fig = plt.figure()
    axes = [[], []]

    axes[0].append(fig.add_subplot(2, 4, 1))
    axes[0].append(fig.add_subplot(2, 4, 2, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(fig.add_subplot(2, 4, 3, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0].append(fig.add_subplot(2, 4, 4, sharex=axes[0][0], sharey=axes[0][0]))
    axes[0][0].set_ylim([-130, 130])

    axes[1].append(fig.add_subplot(2, 1, 2))


    while True:
        logger.info("Impulse level: {}".format(correlator.get_current_impulse_level()))
        if correlator.impulse_fetch() == True:
            for ax_idx in range(len(axes[0])):
                axes[0][ax_idx].cla()
                axes[0][ax_idx].plot(correlator.time_domain_axis * 1e6, correlator.time_domain_signals[ax_idx])
            correlator.do_time_domain_cross_correlation()
            axes[1][0].cla()
            for baseline in correlator.cross_combinations:
                axes[1][0].plot(
                    correlator.time_domain_correlations_times[baseline],
                    correlator.time_domain_correlations_values[baseline],
                    marker = '.')
            logger.info(correlator.time_domain_cross_correlations_peaks)
            logger.info(correlator.visibilities_from_time())
            plt.pause(0.05)
        time.sleep(0.5)
