#!/usr/bin/env python

import correlator
import matplotlib.pyplot as plt
import numpy as np
import time
import logging
import argparse

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser("Get data from correlator and plot it")
parser.add_argument('--acc_len', type=int)
args = parser.parse_args()

c = correlator.Correlator('localhost', 4, logger=logger.getChild('correlator'))
#c.set_shift_schedule(0b1110101101)
c.set_shift_schedule(4095)
c.set_accumulation_len(args.acc_len)
c.re_sync()
time.sleep(10)
to_plot = c.get_autos()[0].signal # 0x0
#to_plot = c.get_crosses()[0].signal # 0x1
print(to_plot)
plt.plot(np.abs(to_plot), marker='.')
plt.show()

