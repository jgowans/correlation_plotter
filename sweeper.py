#!/usr/bin/env python

import numpy as np
from directionFinder_backend import correlator, scpi
import logging
import time

logging.basicConfig()
logger = logging.getLogger('sweeper')
logger.setLevel(logging.INFO)
logger.debug("Test debug")

CHAN_A = 0
CHAN_B = 1
FSTART = 50e6
FSTOP = 399e6
STEPS = 1024*3

COMB = (CHAN_A, CHAN_B)
myCorrelator = correlator.Correlator(logger = logger.getChild('correlator'))
myCorrelator.set_accumulation_len(40000)
myCorrelator.re_sync()
siggen = scpi.SCPI(host='localhost')
assert(siggen.testConnect())

data = []

for frequency in np.linspace(FSTART, FSTOP, STEPS):
    siggen.setFrequency(frequency)
    time.sleep(1)
    myCorrelator.fetch_combinations([COMB])
    strongest = myCorrelator.frequency_correlations[COMB].strongest_frequency()
    if( (strongest < frequency - 400e3) or (strongest > frequency + 400e3) ):
        raise Exception("Too far out!")
    phase = myCorrelator.frequency_correlations[COMB].phase_at_freq(strongest)
    logger.info("Freq: {f},  phase: {ph}".format(f = frequency/1e6, ph = phase))
    data.append([frequency, phase])

data = np.array(data)  # convert to numpy array
np.savetxt("/home/jgowans/Documents/phases.txt")
plt.plot(np.take(data, 0, 1), np.take(data, 1, 1))
