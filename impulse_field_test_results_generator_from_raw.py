#!/usr/bin/env python

import argparse
import logging
from colorlog import ColoredFormatter
import time
import os
import csv
import datetime
import numpy as np
from directionFinder_backend.antenna_array import AntennaArray
from directionFinder_backend.direction_finder import DirectionFinder
from directionFinder_backend.correlator import Correlator
from directionFinder_backend.correlation import Correlation
import itertools
import matplotlib.pyplot as plt

class FakeCorrelation():
    def add_cable_length_calibration(self, length_a, velocity_factor_a, length_b, velocity_factor_b):
        pass

class FakeCorrelator(Correlator):
    def __init__(self, ip_addr='192.168.14.30', num_channels=4, fs=800e6, logger=logging.getLogger(__name__), signals = None):
        self.logger = logger
        self.num_channels = num_channels
        self.fs = np.float64(fs)
        self.cross_combinations = list(itertools.combinations(range(num_channels), 2))
        self.auto_combinations = [(0, 0)]
        self.time_domain_calibration_values = None
        self.time_domain_calibration_cable_values = None
        self.frequency_correlations = {}
        for a, b in self.cross_combinations:
            self.frequency_correlations[(a, b)] = FakeCorrelation()
        self.time_domain_signals = None
        self.upsample_factor = 100
        self.subsignal_length_max = 2**17
        self.time_domain_padding = 100

def notch_filter(signal, fs, start, stop):
    """ Sets bins from and including start throgh stop to 0
    """
    fft = np.fft.rfft(signal)
    axis = np.linspace(0, fs/2.0, len(fft))
    for idx, freq in enumerate(axis):
        if freq >= start and freq <= stop:
            fft[idx] = 0
    signal = np.fft.irfft(fft)
    return signal

def time_domain_filter(signal, filter_len, filter_level):
    signal_filtered = np.copy(signal)
    for centre_idx in range(len(signal)):
        accumulation = 0
        for offset in range(-int(round(filter_len/2.0)), int(round(filter_len/2))):
            idx = centre_idx + offset
            if idx >= 0 and idx < len(signal):
                accumulation += np.abs(signal[idx])
            else:
                accumulation += 0  # expcit: don't add anything
        if accumulation < filter_level * filter_len:
            signal_filtered[centre_idx] = 0
    return signal_filtered

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

    parser = argparse.ArgumentParser()
    parser.add_argument('--d', type=str)
    parser.add_argument('--f_start', default=200e6, type=float)
    parser.add_argument('--f_stop', default=300e6, type=float)
    parser.add_argument('--array_geometry_file', default=None)
    args = parser.parse_args()

    directory = args.d

    correlator = FakeCorrelator()
    correlator.add_cable_length_calibrations('/home/jgowans/workspace/directionFinder_backend/config/cable_length_calibration_actual_array.json')
    correlator.add_time_domain_calibration('/home/jgowans/workspace/directionFinder_backend/config/time_domain_calibration_through_rf_chain.json')
    fs = correlator.fs

    array = AntennaArray.mk_from_config(args.array_geometry_file)

    df = DirectionFinder(correlator, array, args.f_start, logger.getChild('df'))
    df.set_time()

    contents = os.listdir(directory)
    contents.sort()
    for timestamp_str in contents:
        try:
            timestamp = float(timestamp_str)
        except ValueError:
            continue
        #fig = plt.figure()
        correlator.time_domain_signals = None
        num_channels = 4
        for channel in range(num_channels):
            filename = "{c}.npy".format(c = channel)
            with open("{d}/{t}/{f}".format(d = directory, t = timestamp, f = filename)) as f:
                signal = np.load(f)
                #subplot_sig = fig.add_subplot(4, 2, (2*channel) + 1)
                #subplot_fft = fig.add_subplot(4, 2, (2*channel) + 2)
                #subplot_sig.plot(signal)
                #fft = np.abs(np.fft.rfft(signal))
                #subplot_fft.plot(np.linspace(0, 400, len(fft)), fft)
                signal = notch_filter(signal, fs, 0, args.f_start)
                signal = notch_filter(signal, fs, args.f_stop, 400e6)
                signal = time_domain_filter(signal, 10, 10)
                if correlator.time_domain_signals == None:
                    correlator.time_domain_signals = np.ndarray((num_channels, len(signal)))
                correlator.time_domain_signals[channel] = signal
                #subplot_sig.plot(signal)
                #fft = np.abs(np.fft.rfft(signal))
                #subplot_fft.plot(np.linspace(0, 400, len(fft)), fft)
            correlator.time_domain_axis = np.linspace(0,
                                            len(correlator.time_domain_signals[0])/fs,
                                            len(correlator.time_domain_signals[0]),
                                            endpoint = False)
        #plt.show()
        df.df_impulse(args.d, t = timestamp)
    exit()
