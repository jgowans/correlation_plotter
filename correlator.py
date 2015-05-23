#!/usr/bin/env python

'''
Interface to the ROACH.
'''
import logging
import corr
from correlation import Correlation
import itertools
import numpy as np
import time


class Correlator:
    def __init__(self, ip_addr='localhost', num_channels=4, fs=800e6, logger=logging.getLogger(__name__)):
        """The interface to a ROACH cross correlator

        Keyword arguments:
        ip_addr -- IP address (or hostname) of the ROACH. (default: localhost)
        num_channels -- antennas in the correlator. (default: 4)
        fs -- sample frequency of antennas. (default 800e6; 800 MHz)
        logger -- logger to use. (default: new default logger)
        """
        self.fpga = corr.katcp_wrapper.FpgaClient(ip_addr)
        time.sleep(0.1)
        self.num_channels = num_channels
        self.cross_combinations = list(itertools.combinations(range(num_channels), 2))  # [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        # only 0x0 has been implemented
        #self.auto_combinations = [(x, x) for x in range(num_channels)] # [(0, 0), (1, 1), (2, 2), (3, 3)]
        self.auto_combinations = [(0, 0)]
        self.logger = logger
        self.logger.info("My name is: {n}".format(n = __name__))

    def get_crosses(self):
        """Reads the snapshot blocks for all cross correlations and populates Correlation objects
        """
        self.crosses = self.get_combinations(self.cross_combinations)
        return self.crosses

    def get_autos(self):
        """Reads the snapshot blocks for all auto correlations and populates Correlation objects"""
        self.autos = self.get_combinations(self.auto_combinations)
        return self.autos

    def get_all(self):
        """Popules both cross correlations and auto correlations.
        Returns Correlation objects for crosses and autos
        """
        all_correlations = self.get_combinations(self.cross_combinations + self.auto_combinations)
        self.crosses = all_correlations[0:len(self.cross_combinations)]
        self.autos = all_correlations[-len(self.auto_combinations):]
        return all_correlations

    def get_combinations(self, combinations):
        """ Takes an array of X correlations and returns the Correlation objects
        """
        correlations = []
        self.block_trigger()
        for comb in combinations:
            self.arm_combination(comb)
        self.allow_trigger()
        for comb in combinations:
            correlations.append(Correlation(comb, self.get_vector_from_snap(comb)))
        return correlations

    def get_vector_from_snap(self, combination):
        """ Returns an array of complex numbers for the snap block associated with a particular combination
        """
        raw_data = self.fpga.snapshot_get(self.get_snap_name(combination), arm=False, wait_period=12)['data']
        raw_components = np.frombuffer(raw_data, dtype=np.dtype('>i4')) # big endian 4 byte ints
        # the imaginary component appears first.
        #TODO: VERIFY THIS!!
        #signal = [complex(raw_components[i+1], raw_components[i]) for i in range(0, len(raw_components), 2)]
        signal = [complex(raw_components[i], raw_components[i+1]) for i in range(0, len(raw_components), 2)]
        self.logger.debug("From snap: {c} a signal of length {l} was read".format(c = combination, l = len(signal)))
        return signal

    def arm_combination(self, combination):
        self.fpga.snapshot_arm(self.get_snap_name(combination))
        self.logger.debug("Armed snapshot combination: {c}".format(c = combination))

    def block_trigger(self):
        ctrl = self.fpga.read_uint('control')
        ctrl &= ~(1 << 1) # clear bit 1
        self.fpga.write_int('control', ctrl)
        self.logger.debug("Snap trigger blocked")

    def allow_trigger(self):
        ctrl = self.fpga.read_uint('control')
        ctrl |= (1 << 1) # set bit 1
        self.fpga.write_int('control', ctrl)
        self.logger.debug("Snap trigger allowed")

    def get_snap_name(self, combination):
        """Returns the name of the snapshot block for a particular cross combination (tuple)
        Eg: (1, 3) -> snap_1x3
        """
        return "snap_{a}x{b}".format(a = combination[0], b = combination[1])

    def set_accumulation_len(self, acc_len):
        """The number of vectors which should be accumulated before being snapped. 
        """
        self.fpga.write_int('acc_len', acc_len)
        self.logger.info("Accumulation length set to {l}".format(l = acc_len))
        self.re_sync()

    def set_shift_schedule(self, shift_schedule):
        """ Defines the FFT bit shift schedule
        """
        ctrl = self.fpga.read_uint('control')
        ctrl &= ~(0xFFF << 2)  # clear bit 2 -> bit 14
        shift_schedule &= (0xFFF) # ensure only 12 bits
        ctrl |= (shift_schedule << 2)
        self.fpga.write_int('control', ctrl)
        self.logger.info("FFT shift schedule set to {s}".format(s = shift_schedule))
        self.re_sync()

    def re_sync(self):
        ctrl  = self.fpga.read_uint('control')
        ctrl &= 0xFFFE  # clear bit 0
        self.fpga.write_int('control', ctrl)
        ctrl |= 0x1  # set bit 0
        self.fpga.write_int('control', ctrl)
        ctrl &= 0xFFFE  # clear bit 0
        self.fpga.write_int('control', ctrl)
        self.logger.info("Re-issed a sync pulse")
        time.sleep(0.1)

