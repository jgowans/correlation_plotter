#!/usr/bin/env python

import argparse
import logging
from colorlog import ColoredFormatter
import time
import os
import csv
import geo
import datetime
import pytz
import dateutil.parser
import numpy as np
from directionFinder_backend.antenna_array import AntennaArray
from directionFinder_backend.direction_finder import DirectionFinder
from directionFinder_backend.correlator import Correlator
from directionFinder_backend.correlation import Correlation
import itertools

class FakeCorrelation(Correlation):
    def __init__(self, fpga, comb, f_start, f_stop, logger, signal):
        self.logger = logger
        self.f_start = f_start
        snap_name = "snap_{a}x{b}".format(a=comb[0], b=comb[1])
        self.f_start = np.uint64(f_start)
        self.f_stop = np.uint64(f_stop)
        self.calibration_phase_offsets = None
        self.calibration_cable_length_offsets = None
        self.signal = signal
        self.frequency_bins = np.linspace(
            start = self.f_start,
            stop = self.f_stop,
            num = len(self.signal),
            endpoint = False)

class FakeCorrelator(Correlator):
    def __init__(self, ip_addr='192.168.14.30', num_channels=4, fs=800e6, logger=logging.getLogger(__name__), signals = None):
        self.logger = logger
        self.num_channels = num_channels
        self.fs = np.float64(fs)
        self.cross_combinations = list(itertools.combinations(range(num_channels), 2))
        self.auto_combinations = [(0, 0)]
        self.frequency_correlations = {}
        for comb in (self.cross_combinations):
            self.frequency_correlations[comb] = FakeCorrelation(fpga = None,
                                                            comb = comb,
                                                            f_start = 0,
                                                            f_stop = fs/2,
                                                            logger = self.logger.getChild("{a}x{b}".format(a = comb[0], b = comb[1])),
                                                            signal = signals[comb])
        self.time_domain_calibration_values = None
        self.time_domain_calibration_cable_values = None

                                                  

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

    parser = argparse.ArgumentParser(description = "Run RMS error simulations")
    parser.add_argument('--d', type=str)
    parser.add_argument('--f_start', default=220e6, type=float)
    parser.add_argument('--f_stop', default=261e6, type=float)
    parser.add_argument('--array_geometry_file', default=None)
    args = parser.parse_args()

    directory = args.d

    contents = os.listdir(directory)
    contents.sort()
    for timestamp_str in contents:
        try:
            timestamp = float(timestamp_str)
        except ValueError:
            continue
        correlations = {}
        num_channels = 4
        cross_combinations = list(itertools.combinations(range(num_channels), 2))
        for comb in cross_combinations:
            filename = "{a}x{b}.npy".format(a = comb[0], b = comb[1])
            with open("{d}/{t}/{f}".format(d = directory, t = timestamp, f = filename)) as f:
                signal = np.load(f)
                correlations[comb] = signal
        correlator = FakeCorrelator(signals = correlations)
        correlator.add_cable_length_calibrations('/home/jgowans/workspace/directionFinder_backend/config/cable_length_calibration_actual_array.json')
        correlator.add_frequency_bin_calibrations('/home/jgowans/workspace/directionFinder_backend/config/frequency_domain_calibration_through_chain.json')
        correlator.apply_frequency_domain_calibrations()

        array = AntennaArray.mk_from_config(args.array_geometry_file)

        df = DirectionFinder(correlator, array, args.f_start, logger.getChild('df'))

        df.df_strongest_signal(args.f_start, args.f_stop, directory, t = timestamp)
