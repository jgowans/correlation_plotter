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
    correlator.set_impulse_filter_len(100)
    correlator.set_impulse_setpoint(1000)
    correlator.re_sync()
    correlator.impulse_arm()

    while True:
        logger.info("Impulse level: {}".format(correlator.get_current_impulse_level()))
        correlator.impulse_fetch()
        time.sleep(1)
