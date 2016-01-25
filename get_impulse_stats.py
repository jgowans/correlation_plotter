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
    # setup root logger. Shouldn't be used much but will catch unexpected messages
    colored_formatter = ColoredFormatter("%(log_color)s%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    handler = logging.StreamHandler()
    handler.setFormatter(colored_formatter)
    handler.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    logger = logging.getLogger('main')
    logger.propagate = False
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    correlator = Correlator(logger = logger.getChild('correlator'))
    time.sleep(1)
    correlator.set_impulse_filter_len(100)
    correlator.set_impulse_setpoint(100)
    correlator.add_time_domain_calibration('/home/jgowans/workspace/directionFinder_backend/bin/time_domain_calibration.json')
    correlator.re_sync()
    correlator.impulse_arm()

    impulse_levels = []

    for _ in range(1000):
        impulse_levels.append(
            correlator.get_current_impulse_level())
        #time.sleep(0.01)

    logger.info("Mean: {}".format(np.mean(impulse_levels)))
    logger.info("Std dev: {}".format(np.std(impulse_levels)))
    logger.info("Max: {}".format(np.max(impulse_levels)))
