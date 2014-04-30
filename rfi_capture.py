#!/usr/bin/env python

import time
import numpy as np
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
SNAPSHOT_BLOCK_SIZE =4*4*(2**22) 
SAMPLE_FREQUENCY = 800.0e6
RESAMPLE_FACTOR = 5.0
#ANTENNA_SPACING_METRES = 4.32 #this is the beam length
ANTENNA_SPACING_METRES = 3.53


def plot_initial_signal(signal0):
    # remove DC offset
    #signal0 = signal0 - np.mean(signal0)
    #signal1 = signal1 - np.mean(signal1)
    # get time axis of full signal. Multiply end time by 1e6 to get units of microseconds
    signal_axis = np.linspace(0, (SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY) * 1e6, SNAPSHOT_BLOCK_SIZE, endpoint=False)

    # get the FFT of the signal
    #fft_signal0 = np.fft.rfft(signal0)
    #fft_axis = np.linspace(0, (SAMPLE_FREQUENCY/2.0)/1e6, len(fft_signal0), endpoint=False)
    # create and link the axes
    fig = plt.figure()
    ax_signal0 = fig.add_subplot(111)
    #ax_signal1 = fig.add_subplot(122, sharex=ax_signal0, sharey=ax_signal0)
    #ax_fft_signal0 = fig.add_subplot(223)
    #ax_fft_signal0_phase = fig.add_subplot(224, sharex=ax_fft_signal0)
    # TODO: lable the axes
    # add the plots
    ax_signal0.plot(signal_axis, signal0, "r,")
    #ax_signal1.plot(signal_axis, signal1, ".-")
    #ax_fft_signal0.plot(fft_axis, numpy.abs(fft_signal0))
    #ax_fft_signal0_phase.plot(fft_axis, numpy.angle(fft_signal0))
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plt.show()

def get_triggered_snapshot():
    # arm the snapshot blocks
    fpga.snapshot_arm("dram_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
    fpga.snapshot_arm("bram_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
    # enable the triger gate
    fpga.write_int("trig_gate", 1)
    logging.info("trigger gate enabeled. waiting for capture event")
    #TODO: Logic to actually detect trigger event!
    #bram_data = fpga.snapshot_get("bram_snap", wait_period=-1, arm=False)["data"]
    #logging.info("bram read")
    #2^11 DRAM entries, each containing 4 ADC snapshot, each snapshot containing 4 samples
    dram_data = fpga.read_dram(SNAPSHOT_BLOCK_SIZE)
    logging.info("dram read")
    fpga.write_int("trig_gate", 0)

    logging.info("captured. unpacking data")
    #signal0 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE ) + "b", (dram_data))
    signal0 = np.frombuffer(dram_data, dtype=np.int8)

    #signal1 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE) + "b", (bram_data))
    b,a = scipy.signal.butter(10, 37.0e6/(800.0e6/2), btype="highpass") 
    #signal0 = scipy.signal.filtfilt(b,a,signal0)
    #signal1 = scipy.signal.filtfilt(b,a,signal1)

    plot_initial_signal(signal0)
    #now plot the signal
    return signal0


def log_to_file(signal0):
    shutil.copyfile("/tmp/sig0",  results_directory + "/adc_dumps/" + timestamp + "-signal0")
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

#ENTRY POINT
global_config = json.load(open(config_file))

# connect to FPGA and program
logging.info("starting programming and configuring")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147, timeout=40)
time.sleep(1)
#fpga.progdev("jgowans_snapshot_no_fft_2014_Apr_17_1307.bof")
time.sleep(1)
fpga.write_int("trig_level", 1)
get_triggered_snapshot()
new_trigger = int(raw_input("What value should the trigger be?:  "))
fpga.write_int("trig_level", new_trigger)
time.sleep(1)
raw_input("Ready to continue when you are... ")

while True:
    signal0 = get_triggered_snapshot()
    print("and the amplitude was: {:d}".format(int(max(signal0))))
    timestamp = time.strftime("%y-%m-%d-%H-%M-%S")
    user_response = raw_input("Use this signal [y], ignore it [n], or adjust the trigger level [a]:  ")
    #user_response =  'n'
    if user_response == "a":
        print "Trigger is currently {:d}".format(fpga.read_int("trig_level"))
        new_trigger = int(raw_input("What value should the trigger be?:  "))
        fpga.write_int("trig_level", new_trigger)
    if  user_response == "y":
        user_response = raw_input("Should this vecor be logged to file? [y/n]  ")
        if user_response == "y":
            log_to_file(signal0) #this should also log the PNG!
    plt.close('all')
