""" Interface to the control register on the FPGA
Bits:
    0 - manual sync
    1 - snap gate
    2 - accumulation counter reset
    3:4 - adc select
    5:17 - fft shift schedule
"""

import logging

class ControlRegisters:
    def __init__(self, fpga, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.fpga = fpga
        self.value = 0
        self.write()

    def write(self):
        self.fpga.write_uint('control', value)

    def block_trigger(self):
        self.value &= ~(1 << 1)
        self.write()
        self.logger.debug("Blocking trigger. Control register: {value:#x}".format(value = self.value))

    def allow_trigger(self):
        self.value |= (1 << 1)
        self.write()
        self.logger.debug("Allowing trigger. Control register: {value:#x}".format(value = self.value))

    def pulse_sync(self):
        self.value &= ~(1 << 0)  # clear bit 0
        self.write()
        self.value |= (1 << 0)  # set bit 0
        self.write()
        self.value &= ~(1 << 0)  # clear bit 0
        self.write()
        self.logger.debug("Pulsed sync bit")

    def set_shift_schedule(self, schedule):
        self.value &= ~(0xFFF << 5)
        self.value |= (schedule << 5)
        self.write()
        self.logger.debug("Setting shift schedule to {ss:#x}. Control register: {value:#x}".format(
            ss = schedule, value = self.value))

    def reset_accumulation_counter(self):
        self.value &= ~(1 << 2)
        self.write()
        self.value |= (1 << 2)
        self.write()
        self.value &= ~(1 << 2)
        self.write()
        self.logger.debug("Accumulation counter reset bit pulsed")

    def select_adc(self, adc):
        """ Selects which ADC channel is connected to the time domain snap

        adc -- '0I', '0Q', '1I' or '1Q'
        """
        channel_to_mux = {
            '0I': 0b00
            '0Q': 0b01
            '1I': 0b10
            '1Q': 0b11
        }
        self.value &= ~(0b11 << 3)
        self.value |= (channel_to_mux[adc] << 3)
        self.write()
        self.logger.debug("ADC channel {c} selected. Control register: {value:#x}".format(
            c = adc, value = self.value)
