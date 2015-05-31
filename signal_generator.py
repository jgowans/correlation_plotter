""" Attempts to simulate a system consisting of a tone being received by
multiple phase-shifted and amplitude scaled sensors with uncorrelated noise
at each
"""

import numpy as np

class SignalGenerator:
    def __init__(self, num_channels=4, tone_freq=0.2, snr=0.1,
                 phase_shift=np.zeros(4), amplitude_scale=np.ones(4)):
        """ Creates a signal generator instance
        
        Parameters:
        num_channels -- how many independant sensors should be simulated.
        tone_freq -- the frequency of the signal in the presence of noise.
                pi = nyquist. 2pi = alias for 0
        SNR -- signal to noise ratio in linear power terms
        phase_shift -- array of phase shifts to apply to each channel in radians
        amplitude_scale -- array of amplitude scalings to apply to each channel
            #TODO: Is this a voltage or power scale???
        """
        self.num_channels = num_channels
        self.tone_freq = tone_freq
        self.snr = snr
        self.phase_shift = phase_shift
        self.amplitude_scale = amplitude_scale
        assert(phase_shift.size == num_channels)
        assert(amplitude_scale.size == num_channels)

    def generate(self, samples):
        signals = np.ndarray((self.num_channels, samples))
        for channel in range(self.num_channels):
            signals[channel] = self.generate_tone(samples, channel)
            signals[channel] += self.generate_noise(samples)
        return signals

    def generate_tone(self, samples, channel):
        x = np.linspace(start = self.phase_shift[channel],
                        stop = self.phase_shift[channel] + (self.tone_freq * samples),
                        num = samples,
                        endpoint = True)
        return self.amplitude_scale[channel] * np.sin(x)


    def generate_noise(self, samples):
        variance = np.sqrt(samples*0.5/self.snr)
        #variance = np.sqrt(0.5/self.snr)
        return np.random.normal(0, variance, samples)
