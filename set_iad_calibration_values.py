#!/usr/bin/env python

import corr
import time

fpga = corr.katcp_wrapper.FpgaClient('localhost',7147)
time.sleep(0.1)

offset_vi = 135  
offset_vq = 148
corr.iadc.set_mode(fpga)
time.sleep(0.1)
corr.iadc.configure(fpga, 0, 'inter_I', 'new', 800)
corr.iadc.spi_write_register(fpga, 0, 2, (148 << 8) + 135)
corr.iadc.spi_write_register(fpga, 0, 0b001, (127 << 8) + 127)
corr.iadc.spi_write_register(fpga, 0, 3, 8)
corr.iadc.spi_write_register(fpga, 0, 0b100, (0b1000010000 << 6) + (0b010 << 3) + 0b010)
corr.iadc.spi_write_register(fpga, 0, 7, (0x18 << 6) + (4 << 3) + 4)
#roach.blindwrite('iadc_controller','%c%c%c%c'%(offset_vi,offset_vq,0x02,0x01),offset=0x4)


