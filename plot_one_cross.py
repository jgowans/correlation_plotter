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
    correlator.fetch_crosses()

    to_plot = correlator.frequency_correlations[(0,1)].signal
    to_plot = np.abs(to_plot)
    to_plot[0] = 0
    to_plot = np.log10(to_plot)
    plt.plot(correlator.frequency_correlations[(0,1)].frequency_bins / 1e6,
             to_plot)
    plt.title("Spectrum of the 0x1 visibility")
    plt.xlabel("Frequency (MHz)")
    plt.ylabel("Power (arbitrary units) [log]")
    plt.show()
