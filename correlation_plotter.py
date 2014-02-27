#!/usr/bin/env python

import time
import numpy
import matplotlib.pyplot as plt
import threading
import corr
import struct
from scipy.signal import resample
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)

SAMPLE_FREQUENCY = 800.0e6
ANTENNA_SPACING_METRES = 5.0
SPEED_OF_LIGHT = 299792458.0
RESAMPLE_FACTOR = 10
SNAPSHOT_BLOCK_SIZE = 131072

def get_fft_and_axis(signal, resample_factor=1):
    '''Note: the FFT returned is complex. The axis is in units MHz'''
    fft = numpy.fft.rfft(signal)
    fft_axis = numpy.linspace(0, (SAMPLE_FREQUENCY/2.0)/1e6, len(fft), endpoint=False)
    return fft_axis, fft

def get_upsampled_subsignal_and_axis(signal, start_sample, end_sample):
    '''Note: end_sample is not included'''
    subsignal = signal[start_sample:end_sample]
    upsampled_subsignal = resample(subsignal, len(subsignal)*RESAMPLE_FACTOR)
    start_time = (start_sample/SAMPLE_FREQUENCY) * 1e6
    end_time = (end_sample/SAMPLE_FREQUENCY) * 1e6
    upsampled_subsignal_axis = numpy.linspace(start_time, end_time, len(upsampled_subsignal), endpoint=False)
    return upsampled_subsignal_axis, upsampled_subsignal

def cross_correlate(signal0, signal1):
    correlation = numpy.correlate(signal0, signal1, "full")
    return correlation

# connect to FPGA and program
logging.info("starting programming and configuring")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147)
time.sleep(0.1)
fpga.progdev("jgowans_snapshot_grabber_2014_Feb_27_1324.bof")
fpga.write_int("trig_level", 1)
time.sleep(0.1)
# arm the snapshot blocks
fpga.snapshot_arm("adc0_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
fpga.snapshot_arm("adc1_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
# enable the triger gate
fpga.write_int("trig_gate", 5)
logging.info("trigger gate enabeled. waiting for capture event")
adc0_data = fpga.snapshot_get("adc0_snap", wait_period=-1, arm=False)["data"]
adc1_data = fpga.snapshot_get("adc1_snap", wait_period=-1, arm=False)["data"]

logging.info("captured. unpacking data")
signal0 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc0_data))
signal1 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc1_data))
# remove ADC offset
signal0 = signal0 -  numpy.mean(signal0)
signal1 = signal1 - numpy.mean(signal1)

# get time axis of full signal. Multiply end time by 1e6 to get units of microseconds
signal_axis = numpy.linspace(0, (SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY) * 1e6, SNAPSHOT_BLOCK_SIZE, endpoint=False)

# get the FFT of the signals
fft_signal0_axis, fft_signal0 = get_fft_and_axis(signal0)
fft_signal1_axis, fft_signal1 = get_fft_and_axis(signal1)

# create and link the axes
fig = plt.figure()
ax_signal0 = fig.add_subplot(221)
ax_fft_signal0 = fig.add_subplot(223)
ax_signal1 = fig.add_subplot(222, sharex=ax_signal0, sharey=ax_signal0)
ax_fft_signal1 = fig.add_subplot(224, sharex=ax_fft_signal0, sharey=ax_fft_signal0)
# lable the axes
# add the plots
ax_signal0.plot(signal_axis, signal0)
ax_fft_signal0.plot(fft_signal0_axis, numpy.abs(fft_signal0))
ax_signal1.plot(signal_axis, signal1)
ax_fft_signal1.plot(fft_signal1_axis, numpy.abs(fft_signal1))
fig.show()

# get user input regarding the interesting part of the signal
time_to_correlate_from = float(raw_input("FROM when should the correlation consider data? (microseconds):  "))
time_to_correlate_to = float(raw_input("UNTIL when should the correlation consider data? (microseconds):  "))
start_sample = int( (time_to_correlate_from/1.0e6) * SAMPLE_FREQUENCY )
end_sample = int( (time_to_correlate_to/1.0e6) * SAMPLE_FREQUENCY )

# upsample
upsampled_sub_signal0_axis, upsampled_sub_signal0 = get_upsampled_subsignal_and_axis(signal0, start_sample, end_sample)
upsampled_sub_signal1_axis, upsampled_sub_signal1 = get_upsampled_subsignal_and_axis(signal1, start_sample, end_sample)
# get FFT up subsignal
fft_upsampled_sub_signal0_axis, fft_upsampled_sub_signal0 = get_fft_and_axis(upsampled_sub_signal0)
fft_upsampled_sub_signal1_axis, fft_upsampled_sub_signal1 = get_fft_and_axis(upsampled_sub_signal0)
# get the correlation of the upsampled signals
correlation = cross_correlate(upsampled_sub_signal0, upsampled_sub_signal1)

#create the axes
# create and link the axes
fig = plt.figure()
ax_signal0 = fig.add_subplot(321)
ax_fft_signal0 = fig.add_subplot(323)
ax_signal1 = fig.add_subplot(322, sharex=ax_signal0, sharey=ax_signal0)
ax_fft_signal1 = fig.add_subplot(324, sharex=ax_fft_signal0, sharey=ax_fft_signal0)
ax_correlation = fig.add_subplot(313)
# lable the axes
# add the plots
ax_signal0.plot(upsampled_sub_signal0_axis, upsampled_sub_signal0)
ax_fft_signal0.plot(fft_upsampled_sub_signal0_axis, numpy.abs(fft_upsampled_sub_signal0))
ax_signal1.plot(upsampled_sub_signal1_axis, upsampled_sub_signal1)
ax_fft_signal1.plot(fft_upsampled_sub_signal1_axis, numpy.abs(fft_upsampled_sub_signal1))
ax_correlation.plot(correlation)

index_of_max_value = correlation.argmax()
samples_delay = len(upsampled_sub_signal0) - index_of_max_value - 1
print "antenna 2 is delayed from antenna 1 by " + str(samples_delay) + " samples"
time_delay = (1.0/(SAMPLE_FREQUENCY * RESAMPLE_FACTOR)) * samples_delay
delay_max = ANTENNA_SPACING_METRES / SPEED_OF_LIGHT
print "delay max: " + str(delay_max) + "  time_delay: " + str(time_delay)
angle = numpy.arcsin(time_delay / delay_max)
print "angle of arrival: " + str(round(angle, 3)) + " radians or " + str(round(numpy.degrees(angle), 3)) + " degrees"


plt.show()

