#!/usr/bin/env python

'''
#TODO: write doc string
'''

import numpy as np
from snapshot import Snapshot

class Correlation:
    def __init__(self, combination, fpga):
        '''
        combination -- what antennas is this the correlation of? Eg: (0, 0)
        '''
        self.combination = combination
        self.fpga = fpga
        snap_name = "snap_{a}x{b}".format(a = combination[0], b = combination[1])
        # big endian 4 byte signed ints in snapblock which should be converted to complex numbers
        self.snapshot = Snapshot(fpga, snap_name, dtype='>i4', cvalue=True)
        # TODO: adjust autos to be power (real valued only)

    def signal(self):
        return self.snapshot.signal

    def fetch_signal(self, force=False):
        self.snapshot.fetch_signal(force)

    def arm(self):
        self.snapshot.arm()
