#!/usr/bin/env python

import corr
import numpy as np
import itertools
import matplotlib.pyplot as plt
import time
from operator import add

def snaps():
    return ['ch0_00_re', 'ch0_00_im', 'ch0_01_re', 'ch0_01_im']

def arm_snaps():
    for snap in snaps():
        fpga.snapshot_arm(snap)

def get_snap(snap):
    raw = fpga.snapshot_get(snap, arm=False)['data']
    unpacked = np.frombuffer(raw, dtype=np.int32)
    return unpacked



fpga = corr.katcp_wrapper.FpgaClient('localhost')
time.sleep(0.1)

while True:
    arm_snaps()
    ch0_00 = map(add, get_snap('ch0_00_re'), 1j*get_snap('ch0_00_im'))
    print(ch0_00[0:10])
    ch0_01 = map(add, get_snap('ch0_01_re'), 1j*get_snap('ch0_01_im'))
    ch0_iter = itertools.chain.from_iterable(itertools.izip(ch0_00, ch0_01))
    plt.plot(np.abs(list(ch0_iter)))
    plt.show()
