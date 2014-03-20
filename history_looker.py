#!/usr/bin/env python

import struct
import matplotlib.pyplot as plt
import numpy
import scipy.signal
import sys

PREFIX = sys.argv[1]
DUMP_DIR = "/home/jgowans/correlation_plotter_results/adc_dumps/"

with open(DUMP_DIR + PREFIX + "-signal0") as f:
    sig0_raw = f.read()
with open(DUMP_DIR + PREFIX + "-signal1") as f:
    sig1_raw = f.read()
sig0 = struct.unpack(str(len(sig0_raw)) + "b", sig0_raw)
sig0 = scipy.signal.resample(sig0,len(sig0)*5)
sig1 = struct.unpack(str(len(sig1_raw)) + "b", sig1_raw)
sig1 = scipy.signal.resample(sig1, len(sig1)*5)
ax_sig0 = numpy.linspace(0, 2**17/800.0, len(sig0), endpoint = False)
fft_sig0 = numpy.fft.rfft(sig0)
fft_sig1 = numpy.fft.rfft(sig1)
ax_fft = numpy.linspace(0, 2000, len(fft_sig0), endpoint = False)

fig = plt.figure()
sig_ax = fig.add_subplot(211)
sig_ax.plot(sig0)
sig_ax.plot(sig1, "r")
fft_ax = fig.add_subplot(212)
fft_ax.plot(ax_fft, numpy.abs(fft_sig0))
fft_ax.plot(ax_fft, numpy.abs(fft_sig1), "r")
plt.show()
