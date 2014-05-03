#!/usr/bin/env python

import os, time
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal

results_directory = os.getenv('HOME') + "/rfi_capture_results/"

# algorithm:
# open a .npy file (or do the disk buffer thing)

filename = raw_input("what file should be open? [most recent]  ")
if filename == "": # default to the most recent file
    filename = "/tmp/rfi_signal.npy"
else:
    filename = results_directory + filename

# get the annotation here
data = np.load(filename)
axis = np.linspace(0, len(data), len(data), endpoint=False)
t0 = time.time()
data_decimated = scipy.signal.decimate(data, 30)
print time.time() - t0
axis_decimated = np.linspace(0, len(data), len(data_decimated), endpoint=False)
#plt.plot(axis, data, "b.-")
plt.plot(axis_decimated, data_decimated, "r.-")
plt.show()
# plot the signal decimated by a paramamter (defualt: 1)
# ask the user to input a subplot time
# plot the subplot and the fft of the subplot
