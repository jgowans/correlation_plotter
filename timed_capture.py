#!/usr/bin/env python

import argparse
import corr
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time

parser = argparse.ArgumentParser(description = 'Generate output clock and capture ADC data on clock edges with delay')
parser.add_argument('--calibrate', action='store_true')
parser.add_argument('--plot_time', action='store_true')
parser.add_argument('--plot_freq', action='store_true')
parser.add_argument('--force_snap_trigger', action='store_true')
parser.add_argument('--pos_delay_ms', default=0, type=float)
parser.add_argument('--neg_delay_ms', default=0, type=float)
parser.add_argument('--period_ms', default=1000, type=float)
parser.add_argument('--host', default='192.168.14.30', type=str)
parser.add_argument('--samples', default=2**20, type=int)
parser.add_argument('--capture_dir', default='/tmp/', type=str)

args = parser.parse_args()

if args.calibrate == True:
    execfile('set_iad_calibration_values.py')

fpga = corr.katcp_wrapper.FpgaClient(args.host)
time.sleep(0.1)
clock_speed = int(fpga.est_brd_clk()) * 10**6
print('got clk speed of: {cs}'.format(cs = clock_speed))

period_samples = int((args.period_ms / 10**3) / (1.0/clock_speed))
print('for period of {t} ms, setting {s} samples'.format(t = args.period_ms, s = period_samples))
fpga.write_int('period', period_samples)

pos_delay_samples = int((args.pos_delay_ms / 10**3)/(1.0/clock_speed))
print('for positive edge delay time of {t} ms, setting {s} samples'.format(t = args.pos_delay_ms, s = pos_delay_samples))
fpga.write_int('pos_delay', pos_delay_samples)

neg_delay_samples = int((args.neg_delay_ms / 10**3)/(1.0/clock_speed))
print('for negative edge delay time of {t} ms, setting {s} samples'.format(t = args.neg_delay_ms, s = neg_delay_samples))
fpga.write_int('neg_delay', neg_delay_samples)

while True:
    fpga.write_int('reset_triggered_latch', 1)
    time.sleep(0.01)
    fpga.write_int('reset_triggered_latch', 0)
    fpga.snapshot_arm('snapshot', man_trig=args.force_snap_trigger, man_valid=False, offset=-1, circular_capture=False)
    while (fpga.read_uint('triggered_latch') == 0) and (args.force_snap_trigger == False):
        pass
    fpga.write_int('led_1_control', 0)
    edge = 'pos' if fpga.read_uint('gpioa_0_status') else 'neg'
    snap_time = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S_%f')
    print('got edge: {e} at time: {t}'.format(e = edge, t = snap_time))
    time.sleep(0.01)
    raw = fpga.read_dram(args.samples)
    signal = np.frombuffer(raw, dtype=np.int8)
    file_name = '{d}/{t}_{e}'.format(d = args.capture_dir, t = snap_time, e = edge)
    with open(file_name, 'w') as f:
        f.write(signal)
    if args.plot_time == True:
        delay = args.pos_delay_ms if edge == 'pos' else args.neg_delay_ms
        edge_full = 'POSITIVE' if edge == 'pos' else 'NEGATIVE'
        title = 'Time domain of {e} edge with a delay of {t} ms'.format(e = edge_full, t = delay)
        time_axis = np.linspace(delay, delay + len(signal)/1600000, len(signal)) # work in milliseconds
        plt.plot(signal)
        plt.title(title)
        plt.show()
    if args.plot_freq == True:
        signal_fft = np.fft.rfft(signal)
        fft_axis = np.linspace(0, 1600/2, len(signal_fft), endpoint=False)
        plt.plot(fft_axis, np.abs(signal_fft))
        plt.show()
    fpga.write_int('led_1_control', 1)

