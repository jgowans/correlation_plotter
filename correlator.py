#!/usr/bin/env python

'''
Interface to the ROACH.
'''

import corr
from correlation import Correlation
import itertools

class Correlator:
    def __init__(self, ip_addr, num_channels):
        self.fpga = corr.katcp_wrapper.FpgaClient(ip_addr)
        self.num_channels = num_channels
        self.cross_combinations = list(itertools.combinations(range(num_channels), 2)) # [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        # only 0x0 has been implemented
        #self.auto_combinations = [(x, x) for x in range(num_channels)] # [(0, 0), (1, 1), (2, 2), (3, 3)]
        self.auto_combinations = [(0,0)]

    def get_crosses(self):
        """Reads the snapshot blocks for all cross correlations and populates Correlation objects
        """
        self.crosses = self.get_combinations(self.cross_combinations)
        return self.crosses

    def get_autos(self):
        """Reads the snapshot blocks for all auto correlations and populates Correlation objects"""
        self.autos = self.get_combinations(self.cross_combinations)
        return self.autos

    def get_all(self):
        all_correlations = self.get_combinations(self.cross_combinations + self.auto_combinations)
        self.crosses = all_correlations[0:len(self.cross_combinations)]
        self.autos = all_correlations[-len(self.auto_combinations):]
        return all_correlations

    def get_combinations(self, combinations):
        """ Takes an array of X correlations and returns the Correlation objects
        """
        correlations = []
        for comb in combinations:
            self.arm_combination(comb)
        self.arm_trigger()
        for comb in combinations:
            correlations.append(Correlation(comb, get_vector_for_combination(comb)))


    def get_vector_from_snap(self, combination):
        """ Returns an array of complex numbers for the snap block associated with a particular combination
        """
        raw_data = self.fgpa.snapshot_get(get_snap_name(combination), arm=False)['data']
        raw_components = np.frombuffer(raw_data, dtype=np.int32) 
        # the imaginary component appears first.
        signal = [complex(raw_components[i+1], raw_components[i]) for i in range(len(raw_components)/2)]
        return signal

    def arm_combination(self, combinations):
        for comb in combinations:
            snapshot_arm(get_snap_name(comb))

    
    def arm_crosses(self):

    def arm_trigger(self):
        self.fpga.write_int('snap_trig_reset', 0)
        self.fpga.write_int('snap_trig_reset', 1)
        self.fpga.write_int('snap_trig_reset', 0)

    def get_snap_name(self, combination):
        """Returns the name of the snapshot block for a particular cross combination (tuple)
        Eg: (1, 3) -> snap_1x3
        """
        return "snap_{a}x{b}".format(a = combination[0], b = combination[1])

    def set_accumulation_len(self, acc_len):
        """The number of vectors which should be accumulated before being snapped. 
        """
        assert(acc_len < 2**16) # only have a 16-bit register
        self.fpga.write_int('acc_len', acc_len)
        self.re_sync()

    def re_sync(self):
        self.fpga.write_int('manual_sync', 0)
        self.fpga.write_int('manual_sync', 1)
        self.fpga.write_int('manual_sync', 0)


