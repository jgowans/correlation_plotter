import struct

class SnapReader:
    def __init__(self, fpga, snap_name, data_length):
        self.fpga = fpga
        self.snap_name = snap_name
        self.data_length = data_length
        
        devs = fpga.listdev()
        if '{}_dram'.format(snap_name) in devs:
            self.is_dram_snap = True
        elif '{}_bram'.format(snap_name) in devs:
            self.is_dram_snap = False
        else:
            raise Exception("Can\'t find bram or dram dev for snap: {}. Does the snap exist?".format(snap_name))

    def arm(self, force_trigger=False):
        self.fpga.snapshot_arm(self.snap_name, force_trigger=force_trigger)

    def force_trigger(self):
        fpga.snapshot_arm

    def read(self):
        if self.is_dram_snap:
            raw = fpga.read_dram(self.data_length)
            unpacked = struct.unpack('{}b'.format(len(raw)), sig_raw)
        else:
            raise Exception('Not yet implemented')
        return unpacked

    def arm_and_read(self):
        self.arm()
        return self.read()

    def force_trigger_and_read(self):


