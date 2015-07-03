import logging

class DirectionFinder:
    def __init__(self, correlator, array, frequency, logger=logging.getLogger(__name__)):
        """ Takes data from a correlator and compares it to the expected output
        of the antenna array to figure out where the signal at the correlator 
        is coming from

        frequency -- the frequency bin to DF in Hz
        correlator -- instance of Correlator
        array -- instance of AntennaArray

        """
        self.logger = logger
        self.correlator = correlator
        self.array = array
        self.set_frequency(frequency)
        self.generate_manifold()

    def set_frequency(self, frequency):
        # assert that frequency is valid as per correlator specs here
        self._frequency = frequency

    def generate_manifold(self):
        self.manifold = None  # TODO: actually generate a manifold here from array
        # TODO: later, run this through a Calibration class which applies offsets
        # to the phase values such that the simulated phase mirrors the actual phase
        # differences. 

    def self.direction_find(self):
        pass
        # get data from correlator (sit in loop until data available)
        # iterate through manifold and find nearest point
