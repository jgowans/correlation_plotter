#!/usr/bin/env python

import os, time
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

results_directory = os.getenv('HOME') + "/rfi_capture_results/"
SAMPLE_FREQUENCY = 3600.0 # MHz and us
ADC_SCALE_VALUE = 707.94

# algorithm:
# open a .npy file (or do the disk buffer thing)

filename = raw_input("what file should be open? [most recent]  ")
if filename == "": # default to the most recent file
    filename = "/tmp/rfi_signal.npy"
else:
    filename = results_directory + filename
signal = np.load(filename)
decimation_factor = int(len(signal)/2**20) + 1
print "decimation factor: " + str(decimation_factor)
if decimation_factor >= 2 :
    signal_decimated = scipy.signal.decimate(signal, decimation_factor, n=1, ftype="fir")
else:
    signal_decimated = signal
print "len : " + str(len(signal_decimated))
axis = np.linspace(0, decimation_factor * len(signal_decimated)/SAMPLE_FREQUENCY, len(signal_decimated), endpoint=False)
plt.plot(axis, signal_decimated, "b.")
plt.show()
# plot the signal decimated by a paramamter (defualt: 1)

# ask the user to input a subplot time
start_time = float(raw_input("At what time (microseconds) does the signal start?  "))
end_time = float(raw_input("At what time (microseconds) does the signal end?   "))
start_sample = int( start_time * SAMPLE_FREQUENCY )
end_sample = int( end_time * SAMPLE_FREQUENCY )

subsignal = signal[start_sample:end_sample]
subsignal_axis = np.linspace(start_time, end_time, len(subsignal), endpoint=False)
spectrum = np.fft.rfft(subsignal)
spectrum_axis = np.linspace(0, SAMPLE_FREQUENCY/2, len(spectrum), endpoint=False)

plt.subplot(211)
plt.plot(subsignal_axis, subsignal)
plt.subplot(212)
plt.plot(spectrum_axis, 10*np.log10( np.abs(spectrum) / (ADC_SCALE_VALUE*len(spectrum) )))
plt.show()

# plot the subplot and the fft of the subplot
