#!/usr/bin/env python

import corr
import struct
import matplotlib.pyplot as plt
import numpy
import time

fpga = corr.katcp_wrapper.FpgaClient("localhost")
fpga.write_int("trig_level", 5)
fpga.write_int("trig_gate", 1)
fpga.snapshot_arm("adc0_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
time.sleep(1)
sig_raw = fpga.read_dram(4*4*(2**19)/(2*10))
sig = struct.unpack(str(len(sig_raw)) + "b", sig_raw)
sig0 = []
sig1 = []
#there are groups of eight bytes, where the first four belong to one ADC, and the next four belong to the next ADC
for i in range(len(sig)/8): 
    sig0.append(sig[(i*8)+0])
    sig0.append(sig[(i*8)+1])
    sig0.append(sig[(i*8)+2])
    sig0.append(sig[(i*8)+3])
ax_sig0 = numpy.linspace(0, len(sig0)/800.0, len(sig0), endpoint = False) #time axis with each sample being 1/fs
fft_sig0 = numpy.fft.rfft(sig0)
ax_fft = numpy.linspace(0, 400, len(fft_sig0), endpoint = False) #fft from 0 to 400 MHz
fig = plt.figure()
sig_ax = fig.add_subplot(211)
fft_ax = fig.add_subplot(212)
sig_ax.plot(ax_sig0, sig0)
fft_ax.plot(ax_fft, numpy.abs(fft_sig0))
plt.show()
