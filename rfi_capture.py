#!/usr/bin/env python

import time, logging, os, shutil
import numpy as np
import matplotlib.pyplot as plt
import corr

logging.basicConfig(level=logging.INFO, format="%(asctime)s:" + logging.BASIC_FORMAT)
results_directory = os.getenv('HOME') + "/rfi_capture_results/"
SNAPSHOT_BLOCK_SIZE =4*4*(2**23)/128 
SAMPLE_FREQUENCY = 3600.0e6 


def plot_signal(signal):
    signal_axis = np.linspace(0, (len(signal)/SAMPLE_FREQUENCY) * 1e6, len(signal), endpoint=False)
    fig = plt.figure()
    ax_signal0 = fig.add_subplot(111)
    ax_signal0.plot(signal_axis, signal, ",")
    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plt.show()

def get_triggered_snapshot(read_full_dram=False):
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
    length_to_read = 16*((2*(2**14)) + fpga.read_int("pulse_length")) 
    # ensure we don't try to read more than the maximum number of camptured samples
    length_to_read = min(length_to_read, SNAPSHOT_BLOCK_SIZE)
    if read_full_dram == True:
        length_to_read = SNAPSHOT_BLOCK_SIZE
    dram_data = fpga.read_dram(length_to_read)
    logging.info("dram read. unpacking data")
    signal = np.frombuffer(dram_data, dtype=np.int8)
    logging.info("unpack complete")
    return signal

def log_to_file(signal):
    if raw_input("log signal to disk? [y/n]:  ") == "n":
        return
    timestamp = time.strftime("%y-%m-%d-%H-%M-%S")
    np.save("/tmp/rfi_signal", signal)
    shutil.copyfile("/tmp/rfi_signal.npy",  results_directory + timestamp + ".npy")
    logging.info("signal in both /tmp and results directory")

#ENTRY POINT
# connect to FPGA and program
logging.info("connecting to FPGA")
fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147, timeout=80)
# initial read of current data
fpga.write_int("trig_level", 0)
if raw_input("look at untriggered data? [y/n]  ") == "y":
    signal = get_triggered_snapshot(read_full_dram=True)
    print "largest value in the signal = " + str(max( abs(max(signal)), abs(min(signal))))
    plot_signal(signal)
    log_to_file(signal)
fpga.write_int("trig_level", 3)
while True:
    signal = get_triggered_snapshot()
    logging.info("got one! of length " + str(fpga.read_int("pulse_length")))
    plt.close('all')
    if raw_input("look at signal? [y/n]  ") == "y":
        plot_signal(signal)
    log_to_file(signal)
    print "Trigger is currently {:d}".format(fpga.read_int("trig_level"))
    new_trigger = raw_input("What value should the trigger be?:  ")
    try:
        fpga.write_int("trig_level", int(new_trigger))
    except:
        pass

