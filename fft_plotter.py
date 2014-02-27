#!/usr/bin/env python

import numpy
import matplotlib.pyplot as plt
import corr
import struct
from scipy import signal
import time

SAMPLE_FREQUENCY = 800e6
RESAMPLE_FACTOR = 10
#SNAPSHOT_BLOCK_SIZE = 131072
SNAPSHOT_BLOCK_SIZE = 8192

def get_raw_upsampled_and_fft(bof_name):
    fpga = corr.katcp_wrapper.FpgaClient("localhost", 7147)
    time.sleep(0.1)
    #fpga.progdev("jgowans_snapshot_grabber_2014_Feb_26_1800.bof") # wires from ADC to snapshot cross over
    fpga.progdev(bof_name) # wires from ADC to snapshot straight through
    fpga.write_int("trig_level", 10)
    time.sleep(0.1)

    #arm and capture
    fpga.snapshot_arm("adc0_snap", man_trig=False, man_valid=False, offset=-1, circular_capture=False)
    fpga.write_int("trig_gate", 1)
    adc0_data = fpga.snapshot_get("adc0_snap", wait_period=-1, arm=False)["data"][8192:8192+8192]

    #unpack and remove DC offset and calculate FFT
    signal1 = struct.unpack(str(SNAPSHOT_BLOCK_SIZE) + "b", (adc0_data))
    signal1 = signal1 -  numpy.mean(signal1)
    signal1_fft = numpy.abs(numpy.fft.rfft(signal1))

    #compute an unsampled version of the signal. Just for looking at
    signal1_upsampled = signal.resample(signal1, len(signal1)*RESAMPLE_FACTOR)

    # calculate axes for time signal
    ax_signal1 = numpy.linspace(0, 1e6*(SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY), len(signal1), endpoint=False)
    ax_signal1_upsampled = numpy.linspace(0, 1e6*(SNAPSHOT_BLOCK_SIZE/SAMPLE_FREQUENCY), len(signal1_upsampled), endpoint=False)

    #calculate axes for fft signals
    ax_signal1_fft = numpy.linspace(0, (SAMPLE_FREQUENCY/2)/1e6, len(signal1_fft), endpoint=False)

    # return vals
    to_return = {}
    to_return["signal1"] = signal1
    to_return["ax_signal1"] = ax_signal1
    to_return["signal1_upsampled"] = signal1_upsampled
    to_return["ax_signal1_upsampled"] = ax_signal1_upsampled
    to_return["signal1_fft"] = signal1_fft
    to_return["ax_signal1_fft"] = ax_signal1_fft
    return to_return

straight_wires = get_raw_upsampled_and_fft("jgowans_snapshot_grabber_2014_Feb_27_1324.bof")
time.sleep(2)
crossed_wires = get_raw_upsampled_and_fft("jgowans_snapshot_grabber_2014_Feb_26_1800.bof")

fig = plt.figure()
#plot straight
plt.subplot(221)
plt.plot(straight_wires["ax_signal1"], straight_wires["signal1"])
plt.plot(straight_wires["ax_signal1_upsampled"], straight_wires["signal1_upsampled"])
plt.subplot(223)
plt.plot(straight_wires["ax_signal1_fft"], straight_wires["signal1_fft"])

# plt crosed wires
plt.subplot(222)
plt.plot(crossed_wires["ax_signal1"], crossed_wires["signal1"])
plt.plot(crossed_wires["ax_signal1_upsampled"], crossed_wires["signal1_upsampled"])
plt.subplot(224)
plt.plot(crossed_wires["ax_signal1_fft"], crossed_wires["signal1_fft"])

plt.show()



