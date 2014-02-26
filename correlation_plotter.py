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
fpga.write_int("trig_level", 10)
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
full_signal_time_axis = numpy.arange(0, SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY, 1/SAMPLE_FREQUENCY)
full_signal_time_axis = [i*1e6 for i in full_signal_time_axis] #convert the axis to microseconds
plt.subplot(211)
plt.plot(full_signal_time_axis, signal1)
plt.subplot(212)
plt.plot(full_signal_time_axis, signal2)
plt.show()
time_to_correlate_to = raw_input("Until when should the correlation consider data? microseconds)")
subsample_size = int( float(time_to_correlate_to)/1.0e6 * SAMPLE_FREQUENCY )

signal1_sub = signal1[0:subsample_size]
signal2_sub = signal2[0:subsample_size]
subsignal_time_axis = numpy.arange(0, subsample_size/SAMPLE_FREQUENCY, 1/(SAMPLE_FREQUENCY*RESAMPLE_FACTOR))
subsignal_time_axis = [i*1e6 for i in subsignal_time_axis] # convert the axis to microseconds
logging.info("unpack complete. resampling")
#signal_x_axis = [10*i for i in range(0, len(signal1))]
signal1_upsampled = signal.resample(signal1_sub, len(signal1_sub)*RESAMPLE_FACTOR)
signal2_upsampled = signal.resample(signal2_sub, len(signal2_sub)*RESAMPLE_FACTOR)
logging.info("correlating")
correlation = numpy.correlate(signal1_upsampled, signal2_upsampled, "full")
logging.info("correlation complete")

index_of_max_value = correlation.argmax()
samples_delay = len(signal1_upsampled) - index_of_max_value - 1
print "antenna 2 is delayed from antenna 1 by " + str(samples_delay) + " samples"
time_delay = (1.0/(SAMPLE_FREQUENCY * RESAMPLE_FACTOR)) * samples_delay
delay_max = ANTENNA_SPACING_METRES / SPEED_OF_LIGHT
print "delay max: " + str(delay_max) + "  time_delay: " + str(time_delay)
angle = numpy.arcsin(time_delay / delay_max)
print "angle of arrival: " + str(round(angle, 3)) + " radians or " + str(round(numpy.degrees(angle), 3)) + " degrees"

fig = plt.figure
plt.subplot(511)
plt.plot(full_signal_time_axis, signal1)
plt.subplot(512)
plt.plot(full_signal_time_axis, signal2)
plt.subplot(513)
#plt.plot(signal_x_axis, signal1, "r")
plt.plot(subsignal_time_axis, signal1_upsampled)
plt.ylabel("signal1")
plt.subplot(514)
#plt.plot(signal_x_axis, signal2, "r")
plt.plot(subsignal_time_axis, signal2_upsampled)
plt.ylabel("signal2")
plt.subplot(515)
plt.plot(correlation)
plt.ylabel("correlation")
plt.show()

