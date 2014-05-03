#!/usr/bin/env python

import time, logging, os, shutil
import numpy as np
import matplotlib.pyplot as plt
import corr

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
results_directory = os.getenv('HOME') + "/rfi_capture_results/"
SNAPSHOT_BLOCK_SIZE =4*4*(2**22) 
SAMPLE_FREQUENCY = 3600.0e6 # microseconds and megahertz


def plot_initial_signal(signal0):
    signal_axis = np.linspace(0, (len(signal0)/SAMPLE_FREQUENCY) * 1e6, len(signal0), endpoint=False)
    fig = plt.figure()
    ax_signal0 = fig.add_subplot(111)
    ax_signal0.plot(signal_axis, signal0, ",")
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plt.show()

def get_triggered_snapshot():
    # arm the snapshot blocks
    fpga.snapshot_arm("dram_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
    fpga.write_int("trig_arm", 0)
    fpga.write_int("trig_arm", 1) # present a rising edge
    logging.info("trigger gate enabeled. waiting for capture event")
    while fpga.read_int("triggered") == 0:
        time.sleep(0.1)
    time.sleep(0.1)
    fpga.write_int("trig_arm", 0)
    logging.info("got trigger. now dumping dram")
    # length = padding of 2^15 "clock cycles" each side of the pulse, where each clock cycle is 16 samples.
    # the padding takes about 1 second to read out. Worth it, I think!! :-)
    length_to_read = 16*((2*(2**15)) + fpga.read_int("pulse_length")) 
    # ensure we don't try to read more than the maximum number of camptured samples
    length_to_read = min(length_to_read, SNAPSHOT_BLOCK_SIZE) 
    length_to_read = SNAPSHOT_BLOCK_SIZE
    dram_data = fpga.read_dram(length_to_read)
    logging.info("dram read. unpacking data")
    signal0 = np.frombuffer(dram_data, dtype=np.int8)
    plot_initial_signal(signal0)
    return signal0

def log_to_file(signal0, timestamp):
    if raw_input("log signal to disk? [y/n]:  ") == "n":
        return
    #annotation = raw_input("annotate this signal please: ")
    #np.save("/tmp/rfi_signal", {"annotation": annotation, "data": signal0})
    np.save("/tmp/rfi_signal", signal0)
    shutil.copyfile("/tmp/rfi_signal.npy",  results_directory + timestamp + ".npy")
    logging.info("signal in both /tmp and results directory")

#ENTRY POINT
# connect to FPGA and program
logging.info("starting programming and configuring")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147, timeout=120)
#fpga.progdev("jgowans_snapshot_no_fft_2014_Apr_17_1307.bof")
time.sleep(1)
fpga.write_int("trig_level", 10)
signal0 = get_triggered_snapshot()
timestamp = time.strftime("%y-%m-%d-%H-%M-%S")
log_to_file(signal0, timestamp)
while True:
    fpga.write_int("trig_arm", 0)
    fpga.write_int("trig_arm", 1) # assert a rising edge
    while fpga.read_int("triggered") == 0:
        pass
    logging.info("got one! of length " + str(fpga.read_int("pulse_length")))
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
