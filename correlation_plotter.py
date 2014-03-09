#!/usr/bin/env python

import time
import numpy
import matplotlib.pyplot as plt
import threading
import corr
import struct
import scipy.signal
import scipy.constants
import logging
import os
import json

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
config_file = os.getenv('HOME') + "/correlation_plotter_config"
SNAPSHOT_BLOCK_SIZE = 131072
SAMPLE_FREQUENCY = 800.0e6
RESAMPLE_FACTOR = 10

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

def plot_initial_signals(signal0, signal1):
    # get time axis of full signal. Multiply end time by 1e6 to get units of microseconds
    signal_axis = numpy.linspace(0, (SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY) * 1e6, SNAPSHOT_BLOCK_SIZE, endpoint=False)

    # get the FFT of the signals
    fft_signal0_axis, fft_signal0 = get_fft_and_axis(signal0)
    fft_signal1_axis, fft_signal1 = get_fft_and_axis(signal1)
    # create and link the axes
    fig = plt.figure()
    ax_signal0 = fig.add_subplot(231)
    ax_fft_signal0 = fig.add_subplot(232)
    ax_fft_signal0_phase = fig.add_subplot(233, sharex=ax_fft_signal0)
    ax_signal1 = fig.add_subplot(234, sharex=ax_signal0, sharey=ax_signal0)
    ax_fft_signal1 = fig.add_subplot(235, sharex=ax_fft_signal0, sharey=ax_fft_signal0)
    ax_fft_signal1_phase = fig.add_subplot(236, sharex=ax_fft_signal0, sharey=ax_fft_signal0_phase)
    # TODO: lable the axes
    # add the plots
    ax_signal0.plot(signal_axis, signal0)
    ax_fft_signal0.plot(fft_signal0_axis, numpy.abs(fft_signal0))
    ax_fft_signal0_phase.plot(fft_signal0_axis, numpy.angle(fft_signal0))
    ax_signal1.plot(signal_axis, signal1)
    ax_fft_signal1.plot(fft_signal1_axis, numpy.abs(fft_signal1))
    ax_fft_signal1_phase.plot(fft_signal1_axis, numpy.angle(fft_signal1))
    fig.show()

def get_triggered_snapshot():
    # arm the snapshot blocks
    fpga.snapshot_arm("adc0_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
    fpga.snapshot_arm("adc1_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
    # enable the triger gate
    fpga.write_int("trig_gate", 1)
    logging.info("trigger gate enabeled. waiting for capture event")
    adc0_data = fpga.snapshot_get("adc0_snap", wait_period=-1, arm=False)["data"]
    adc1_data = fpga.snapshot_get("adc1_snap", wait_period=-1, arm=False)["data"]
    fpga.write_int("trig_gate", 0)

    logging.info("captured. unpacking data")
    signal0 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc0_data))
    signal1 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc1_data))
    # remove ADC offset
    signal0 = signal0 -  numpy.mean(signal0)
    signal1 = signal1 - numpy.mean(signal1)
    plot_initial_signals(signal0, signal1)
    #now plot the signals
    return signal0, signal1


def plot_correlation_and_get_angle(signal0, signal1):
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
    plt.show()

    index_of_max_value = correlation.argmax()
    samples_delay = len(upsampled_sub_signal0) - index_of_max_value - 1
    print "antenna 2 is delayed from antenna 1 by " + str(samples_delay) + " samples"
    time_delay = (1.0/(SAMPLE_FREQUENCY * RESAMPLE_FACTOR)) * samples_delay
    delay_max = ANTENNA_SPACING_METRES / SPEED_OF_LIGHT
    print "delay max: " + str(delay_max) + "  time_delay: " + str(time_delay)
    angle = numpy.arcsin(time_delay / delay_max)
    print "angle of arrival: " + str(round(angle, 3)) + " radians or " + str(round(numpy.degrees(angle), 3)) + " degrees"
    return angle

def verify_paramaters():
    print global_config["latitude"] + " N    " + global_config["longitude"] + " W"
    if raw_input("Are the above coordinates correct? ") != "y":
        exit()
    print global_config["antenna_angle"]
    if raw_input("Is the above angle correct? ") != "y":
        exit()


#ENTRY POINT
global_config = json.load(open(config_file))
#verify_paramaters()

# connect to FPGA and program
logging.info("starting programming and configuring")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147)
time.sleep(1)
fpga.progdev("jgowans_snapshot_no_fft_2014_Mar_09_1345.bof")
fpga.write_int("adc_delay", 4096) #max = 2^12 = 4096 which is about 20 us
time.sleep(1)
fpga.write_int("trig_level", 0)
signal0, signal1 = get_triggered_snapshot()
fpga.write_int("trig_level", 10)
time.sleep(1)
raw_input("Ready to continue when you are... ")

while True:
    signal0, signal1 = get_triggered_snapshot()
    user_response = raw_input("Use this signal [y], ignore it [n], or adjust the trigger level [a]:  ")
    if user_response == "a":
        new_trigger = int(raw_input("What value should the trigger be?:  "))
        fpga.write_int("trig_level", new_trigger)
    if  user_response == "y":
        angle = plot_correlation_and_get_angle(signal0, signal1)
        user_reponse = raw_input("Should this vecor be logged to file? [y/n]  ")
        if user_response == "y":
            log_to_file(angle) #this should also log the PNG!



# all of the above stuff should be put into methods. The algorithm should be as follows:
# you are at <coordinates>. confirm?
# run un-triggered dump.
# provide oportunity to set trigger level
# wait for trigger
# plot fft
# interested?
# correlation interval?
# plot correlation and output AOA.
# save and log?
# write coordinates and AOA to log file. save PNG to directory (name = time)
