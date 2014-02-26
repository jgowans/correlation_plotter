#!/usr/bin/env python

import time
import numpy
import matplotlib.pyplot as plt
import threading
import corr
import struct
from scipy import signal
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)

SAMPLE_FREQUENCY = 800.0e6
ANTENNA_SPACING_METRES = 5.0
SPEED_OF_LIGHT = 299792458.0
RESAMPLE_FACTOR = 10
SNAPSHOT_BLOCK_SIZE = 131072

# connect to FPGA and program
logging.info("starting programming and configuring")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147)
time.sleep(0.1)
fpga.progdev("jgowans_snapshot_grabber_2014_Feb_25_1514.bof")
fpga.write_int("trig_level", 20)
time.sleep(0.1)
# arm the snapshot blocks
fpga.snapshot_arm("adc0_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
fpga.snapshot_arm("adc1_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
# enable the triger gate
fpga.write_int("trig_gate", 1)
logging.info("trigger gate enabeled. waiting for capture event")
adc0_data = fpga.snapshot_get("adc0_snap", wait_period=-1, arm=False)["data"]
adc1_data = fpga.snapshot_get("adc1_snap", wait_period=-1, arm=False)["data"]

logging.info("captured. unpacking data")
signal1 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc0_data))
signal2 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc1_data))
#cater for ADC offset
signal1 = signal1 -  numpy.mean(signal1)
signal2 = signal2 - numpy.mean(signal2)
full_signal_time_axis = numpy.arange(0, SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY, 1/SAMPLE_FREQUENCY)
full_signal_time_axis = [i*1e6 for i in full_signal_time_axis] #convert the axis to microseconds
f, (ax1, ax2) = plt.subplots(2, 1, sharey=True, sharex=True)
ax1.plot(full_signal_time_axis, signal1)
ax2.plot(full_signal_time_axis, signal2)
plt.show()
time_to_correlate_from = float(raw_input("FROM when should the correlation consider data? (microseconds):  "))
time_to_correlate_to = float(raw_input("UNTIL when should the correlation consider data? (microseconds):  "))
start_sample = int( (time_to_correlate_from/1.0e6) * SAMPLE_FREQUENCY )
end_sample = int( (time_to_correlate_to/1.0e6) * SAMPLE_FREQUENCY )
subsample_length = end_sample - start_sample

#means
print numpy.mean(signal1)
print numpy.mean(signal2)

signal1_sub = signal1[start_sample:end_sample]
signal2_sub = signal2[start_sample:end_sample]
subsignal_time_axis = numpy.linspace(time_to_correlate_from, time_to_correlate_to, subsample_length*RESAMPLE_FACTOR, endpoint=False)
logging.info("unpack complete. resampling")
#signal_x_axis = [10*i for i in range(0, len(signal1))]
signal1_upsampled = signal.resample(signal1_sub, len(signal1_sub)*RESAMPLE_FACTOR)
signal2_upsampled = signal.resample(signal2_sub, len(signal2_sub)*RESAMPLE_FACTOR)
logging.info("correlating")
correlation = numpy.correlate(signal1_upsampled, signal2_upsampled, "full")
logging.info("correlation complete. starting FFT.")
signal1_fft = numpy.abs(numpy.fft.rfft(signal1))

index_of_max_value = correlation.argmax()
samples_delay = len(signal1_upsampled) - index_of_max_value - 1
print "antenna 2 is delayed from antenna 1 by " + str(samples_delay) + " samples"
time_delay = (1.0/(SAMPLE_FREQUENCY * RESAMPLE_FACTOR)) * samples_delay
delay_max = ANTENNA_SPACING_METRES / SPEED_OF_LIGHT
print "delay max: " + str(delay_max) + "  time_delay: " + str(time_delay)
angle = numpy.arcsin(time_delay / delay_max)
print "angle of arrival: " + str(round(angle, 3)) + " radians or " + str(round(numpy.degrees(angle), 3)) + " degrees"

# set up the graph
fig = plt.figure()
ax_sig1 = fig.add_subplot(321)
ax_sig2 = fig.add_subplot(323, sharex=ax_sig1, sharey=ax_sig1)
ax_sig1sub = fig.add_subplot(322)
ax_sig2sub = fig.add_subplot(324, sharex=ax_sig1sub, sharey=ax_sig1sub)
ax_correlation = fig.add_subplot(325)
ax_fft = fig.add_subplot(326)
# label the axis
ax_sig1.set_title("full ADC0 dump")
ax_sig2.set_title("full ADC1 dump")
ax_sig1sub.set_title("ADC0 subset for correlation")
ax_sig2sub.set_title("ADC1 subset for correlation")
ax_correlation.set_title("Cross correlation")
ax_fft.set_title("FFT of signal_1")
# add the graphs to the axis
ax_sig1.plot(full_signal_time_axis, signal1)
ax_sig2.plot(full_signal_time_axis, signal2)
ax_sig1sub.plot(subsignal_time_axis, signal1_upsampled)
ax_sig2sub.plot(subsignal_time_axis, signal2_upsampled)
ax_correlation.plot(correlation)
ax_fft.plot(signal1__fft)
plt.show()

