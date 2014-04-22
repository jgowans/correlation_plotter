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
import shutil
import csv

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
config_file = os.getenv('HOME') + "/correlation_plotter_config"
results_directory = os.getenv('HOME') + "/correlation_plotter_results/"
SNAPSHOT_BLOCK_SIZE = 131072
SAMPLE_FREQUENCY = 900.0e6
RESAMPLE_FACTOR = 5.0
#ANTENNA_SPACING_METRES = 4.32 #this is the beam length
ANTENNA_SPACING_METRES = 3.53


def plot_initial_signals(signal0, signal1):
    # remove DC offset
    signal0 = signal0 - numpy.mean(signal0)
    signal1 = signal1 - numpy.mean(signal1)
    # get time axis of full signal. Multiply end time by 1e6 to get units of microseconds
    signal_axis = numpy.linspace(0, (SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY) * 1e6, SNAPSHOT_BLOCK_SIZE, endpoint=False)

    # get the FFT of the signals
    fft_signal0 = numpy.fft.rfft(signal0)
    fft_signal1 = numpy.fft.rfft(signal1)
    fft_axis = numpy.linspace(0, (SAMPLE_FREQUENCY/2.0)/1e6, len(fft_signal0), endpoint=False)
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
    ax_fft_signal0.plot(fft_axis, numpy.abs(fft_signal0))
    ax_fft_signal0_phase.plot(fft_axis, numpy.angle(fft_signal0))
    ax_signal1.plot(signal_axis, signal1) 
    ax_fft_signal1.plot(fft_axis, numpy.abs(fft_signal1))
    ax_fft_signal1_phase.plot(fft_axis, numpy.angle(fft_signal1))
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plt.show()

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
    with open("/tmp/sig0", "wb") as f:
        f.write(adc0_data)
    with open("/tmp/sig1", "wb") as f:
        f.write(adc1_data)


    logging.info("captured. unpacking data")
    signal0 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc0_data))
    signal1 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (adc1_data))
    b,a = scipy.signal.butter(10, 37.0e6/(800.0e6/2), btype="highpass") 
    #signal0 = scipy.signal.filtfilt(b,a,signal0)
    #signal1 = scipy.signal.filtfilt(b,a,signal1)

    # remove ADC offset
    plot_initial_signals(signal0, signal1)
    #now plot the signals
    return signal0, signal1


def plot_correlation_and_get_angle(signal0, signal1):
    # get user input regarding the interesting part of the signal
    time_to_correlate_from = float(raw_input("FROM when should the correlation consider data? (microseconds):  "))
    time_to_correlate_to = float(raw_input("UNTIL when should the correlation consider data? (microseconds):  "))
    start_sample = int( (time_to_correlate_from/1.0e6) * SAMPLE_FREQUENCY )
    end_sample = int( (time_to_correlate_to/1.0e6) * SAMPLE_FREQUENCY )
    
    sub_signal0 = signal0[start_sample:end_sample]
    sub_signal1 = signal1[start_sample:end_sample]
    # remove DC offset
    sub_signal0 = sub_signal0 - numpy.mean(sub_signal0)
    sub_signal1 = sub_signal1 - numpy.mean(sub_signal1)
    upsampled_sub_signal0 = scipy.signal.resample(sub_signal0, len(sub_signal0)*RESAMPLE_FACTOR)
    upsampled_sub_signal1 = scipy.signal.resample(sub_signal1, len(sub_signal1)*RESAMPLE_FACTOR)
    start_time = (start_sample/SAMPLE_FREQUENCY) * 1e6
    end_time = (end_sample/SAMPLE_FREQUENCY) * 1e6
    upsampled_sub_signal_axis = numpy.linspace(start_time, end_time, len(upsampled_sub_signal0), endpoint=False)

    # get FFT of  subsignal
    fft_sub_signal0 = numpy.fft.rfft(sub_signal0)
    fft_sub_signal1 = numpy.fft.rfft(sub_signal1)
    fft_sub_signal_axis = numpy.linspace(0, (SAMPLE_FREQUENCY/2.0)/1e6, len(fft_sub_signal0), endpoint=False)
    # get the correlation of the upsampled signals
    correlation = numpy.correlate(upsampled_sub_signal0, upsampled_sub_signal1, "full")

    index_of_max_value = correlation.argmax()
    samples_delay = len(upsampled_sub_signal0) - index_of_max_value - 1
    shifted_start_time = ((start_sample-(samples_delay/5.0))/SAMPLE_FREQUENCY) * 1e6
    shifted_end_time = ((end_sample-(samples_delay/5.0))/SAMPLE_FREQUENCY)*1e6
    upsampled_sub_signal_axis_shifted = numpy.linspace(shifted_start_time, shifted_end_time, len(upsampled_sub_signal1), endpoint=False)
    print "antenna 2 is delayed from antenna 1 by " + str(samples_delay) + " samples"
    time_delay = (1.0/(SAMPLE_FREQUENCY * RESAMPLE_FACTOR)) * samples_delay
    delay_max = ANTENNA_SPACING_METRES / scipy.constants.c
    print "delay max: " + str(delay_max) + "  time_delay: " + str(time_delay)
    angle = round(numpy.degrees(numpy.arccos(time_delay / delay_max)), 2)
    print "angle of arrival: " + str(angle) + " degrees"

    #create the axes
    # create and link the axes
    fig = plt.figure()
    ax_signal0 = fig.add_subplot(321)
    ax_fft_signal0 = fig.add_subplot(323)
    ax_signal1 = fig.add_subplot(322, sharex=ax_signal0, sharey=ax_signal0)
    ax_fft_signal1 = fig.add_subplot(324, sharex=ax_fft_signal0, sharey=ax_fft_signal0)
    ax_correlation = fig.add_subplot(325)
    ax_signals_on_top_of_each_other = fig.add_subplot(326)
    # lable the axes
    # add the plots
    ax_signal0.plot(upsampled_sub_signal_axis, upsampled_sub_signal0)
    ax_fft_signal0.plot(fft_sub_signal_axis, numpy.abs(fft_sub_signal0))
    ax_signal1.plot(upsampled_sub_signal_axis, upsampled_sub_signal1)
    ax_fft_signal1.plot(fft_sub_signal_axis, numpy.abs(fft_sub_signal1))
    ax_correlation.plot(correlation)
    ax_signals_on_top_of_each_other.plot(upsampled_sub_signal_axis, upsampled_sub_signal0)
    ax_signals_on_top_of_each_other.plot(upsampled_sub_signal_axis_shifted, upsampled_sub_signal1, "r")
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    fig.show()
    plt.savefig("/tmp/pyplot_dump.png")

    return angle

def log_to_file(signal0, signal1, angle):
    shutil.copyfile("/tmp/sig0",  results_directory + "/adc_dumps/" + timestamp + "-signal0")
    shutil.copyfile("/tmp/sig1",  results_directory + "/adc_dumps/" + timestamp + "-signal1")
    shutil.copyfile("/tmp/pyplot_dump.png", results_directory + "/pyplot_dumps/" + timestamp + ".png")
    # start building up summary string. format:
    # time, lat, long, antenna_angle, signal_angle_relative_to_antenna
    summary = []
    summary.append(timestamp)
    summary.append(global_config["latitude"])
    summary.append(global_config["longitude"])
    summary.append(global_config["antenna_angle_degrees"])
    summary.append(angle) #angle of arival 
    with open(results_directory + "summary.csv", "a") as summary_file:
        csv_writer = csv.writer(summary_file)
        csv_writer.writerow(summary)

def verify_paramaters():
    print "{:f} N   {:f} W".format(global_config["latitude"],  global_config["longitude"])
    if raw_input("Are the above coordinates correct? ") != "y":
        exit()
    print global_config["antenna_angle_degrees"]
    if raw_input("Is the above angle correct? ") != "y":
        exit()


#ENTRY POINT
global_config = json.load(open(config_file))
#verify_paramaters()

# connect to FPGA and program
logging.info("starting programming and configuring")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147)
time.sleep(1)
fpga.progdev("jgowans_snapshot_no_fft_2014_Apr_17_1307.bof")
#fpga.progdev("jgowans_snapshot_no_fft_2014_Mar_16_0748.bof")
fpga.write_int("trig_level", 1)
signal0, signal1 = get_triggered_snapshot()
fpga.write_int("trig_level", 10)
time.sleep(1)
raw_input("Ready to continue when you are... ")

while True:
    signal0, signal1 = get_triggered_snapshot()
    print("and the amplitude was: {:d}".format(int(max(signal0))))
    timestamp = time.strftime("%y-%m-%d-%H-%M-%S")
    user_response = raw_input("Use this signal [y], ignore it [n], or adjust the trigger level [a]:  ")
    #user_response =  'n'
    if user_response == "a":
        print "Trigger is currently {:d}".format(fpga.read_int("trig_level"))
        new_trigger = int(raw_input("What value should the trigger be?:  "))
        fpga.write_int("trig_level", new_trigger)
    if  user_response == "y":
        angle = plot_correlation_and_get_angle(signal0, signal1)
        user_response = raw_input("Should this vecor be logged to file? [y/n]  ")
        if user_response == "y":
            log_to_file(signal0, signal1, angle) #this should also log the PNG!
    plt.close('all')
