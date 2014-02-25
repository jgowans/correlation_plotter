#!/usr/bin/env python

import numpy
import matplotlib.pyplot as plt
import threading
import corr
import struct
import time

SAMPLE_FREQUENCY = 800.0e6
ANTENNA_SPACING_METRES = 10.0
SPEED_OF_LIGHT = 299792458.0

sample_delay_max = int(ANTENNA_SPACING_METRES * SAMPLE_FREQUENCY / SPEED_OF_LIGHT)
print "this set up means a maximum samples delay of " + str(sample_delay_max)

# the following lines create test signals. These should be replaced with pulls from the Roach
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147)
fpga.progdev("jgowans-power_calculator_2014_Feb_23_1521.bof")
fpga.write_int("trig_level", 10)
time.sleep(0.1)
# arm the snapshot blocks
fpga.snapshot_arm("adc0_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
fpga.snapshot_arm("adc1_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)a
# enable the triger gate
fpga.write_int("trig_gate", 1)
adc0_data = fpga.snapshot_get("adc0_snap", wait_period=-1, arm=False)["data"]
adc1_data = fpga.snapshot_get("adc1_snap", wait_period=-1, arm=False)["data"]

signal1 = struct.unpack("8192b", (adc0_data))
signal2 = struct.unpack("8192b", (adc1_data))

correlation = numpy.correlate(signal1, signal2, "full")

index_of_max_value = correlation.argmax()
samples_delay = len(signal1) - index_of_max_value - 1
print "antenna 2 is delayed from antenna 1 by " + str(samples_delay) + " samples"
time_delay = (1.0/SAMPLE_FREQUENCY) * samples_delay
#print "this means a time delay of " + str(time_delay)
delay_max = ANTENNA_SPACING_METRES / SPEED_OF_LIGHT
print "delay max: " + str(delay_max) + "  time_delay: " + str(time_delay)
#angle = numpy.arcsin(time_delay / delay_max)
#print "this means an angle of arrival of " + str(round(angle, 3)) + " radians or " + str(round(numpy.degrees(angle), 3)) + " degrees"

fig = plt.figure
plt.subplot(311)
plt.plot(signal1)
plt.ylabel("signal1")
plt.subplot(312)
plt.plot(signal2)
plt.ylabel("signal2")
plt.subplot(313)
plt.plot(correlation)
plt.ylabel("correlation")
plt.show()

