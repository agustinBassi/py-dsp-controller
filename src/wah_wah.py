import math

import numpy as numpy
from numpy import array as np_array


class WahWahFilter():

    # For limit the amplitude of wah wah signal for int16 wav file format
    MAX_INT16_VALUE = 32767

    def __init__(self, damping, min_f, max_f, wah_f):
        self.__damping = damping
        self.__min_f = min_f
        self.__max_f = max_f
        self.__wah_f = wah_f

    def __repr__(self):
        return ("{'damping': '%f', 'min_f': '%d','max_f': '%d','wah_f': '%d'}" %
                (self.__damping, self.__min_f, self.__max_f, self.__wah_f))

    def __str__(self):
        return (
            "WahWahFilter(damping = %f, min_f = %d, max_f = %d, wah_f = %d)" %
             (self.__damping, self.__min_f, self.__max_f, self.__wah_f))

    def _create_triangle_waveform(self, original_signal_lenght, fs):
        # establish signal period from fs and wah wah frecuency
        signal_period = fs/self.__wah_f
        # steps which triangle signal will do, considering the minummum
        # and max value that it has to reach. Also signal period is taken in account 
        # and finally it is multiplied by 2, because the signal will have to 
        # increase and decrease it's value in each signal period
        step = ((self.__max_f - self.__min_f)/signal_period) * 2
        # This is internal function that will create the signal, from the min value
        # to max value. It's a generator to make it memory efficient.
        def generator():
            index = 0
            # loop until to reach the lenght of original signal
            while index < original_signal_lenght:
                # each iteration start with an initial value
                signal_value = self.__min_f
                # create ascendent part of triangle
                while signal_value < self.__max_f:
                    signal_value += step
                    index += 1
                    yield signal_value
                # create desscendent part of triangle
                while signal_value > self.__min_f:
                    signal_value -= step
                    index += 1
                    yield signal_value

        # Call the generator of the function and create a list from it
        triangle_signal = list(generator())
        # Trim triangle signal to lenght of original signal
        triangle_signal = triangle_signal[:original_signal_lenght]
        # return triangle singla.
        return triangle_signal

    def apply_filter(self, original_signal, fs):
        # Create triangle signal
        cuttoff_frequencies = self._create_triangle_waveform(len(original_signal), fs)
        # equation coefficients
        f1 = 2 * math.sin((math.pi * cuttoff_frequencies[0])/fs)
        # size of band pass filter
        q1 = 2 * self.__damping
        # initialize filters arrays with zero values
        highpass = numpy.zeros(len(original_signal))
        bandpass = numpy.zeros(len(original_signal))
        lowpass = numpy.zeros(len(original_signal))
        # assign first values
        highpass[0] = original_signal[0]
        bandpass[0] = f1 * highpass[0]
        lowpass[0] = f1 * bandpass[0]
        # loop to reach the lenght of original signal
        for n in range (1, len(original_signal)):
            highpass[n] = original_signal[n] - lowpass[n-1] - (q1 * bandpass[n - 1])
            bandpass[n] = (f1 * highpass[n]) + bandpass[n - 1]
            lowpass[n] = (f1 * bandpass[n]) + lowpass[n - 1]
            # recalculate equation coefficients
            f1 = 2 * math.sin((math.pi * cuttoff_frequencies[n])/fs)
        # Obtain the max value of YB
        max_bandpass = numpy.amax(bandpass)
        # Establish a relation between max YB value and INT 16 max value
        normalized_relation = WahWahFilter.MAX_INT16_VALUE/max_bandpass
        # adapt wahwah signal to original signal amplitude
        normalized_bandpass = [int(x * normalized_relation) for x in bandpass]
        # create an np array to reproduce it then
        wahwah_signal = np_array(normalized_bandpass)
        
        return wahwah_signal


import os
import matplotlib.pyplot as plt
import scipy.signal as signal
from scipy.io import wavfile

def save_raw_to_wav(raw_data, wav_file, fs):
    print("\n==================================================\n")
    print("Converting raw data to wav file: %s" % wavfile)
    wavfile.write(wav_file, fs, raw_data.astype(numpy.dtype('i2')))
    print("\n==================================================\n")

def convert_wav_to_raw(wav_file):
    print("\n==================================================\n")
    data = None
    fs, data = wavfile.read(wav_file)
    print("Creating raw data from wav file: %s - FS: %d" % (wavfile, fs))
    print("\n==================================================\n")

    return fs, data

def play_audio(audio_file):
    print("\n==================================================\n")
    os.system("aplay %s" % audio_file)
    print("\n==================================================\n")

def plot_wahwah_triangle_wave(triangle_signal,
                        title="Triangle waveform",
                        label_x="Samples", label_y="Frecuency (Hz)",
                        ref_1="Response in frecuency", refs_location="best"):

    # plot signals to graphic
    plt.plot(triangle_signal)
    # set labels to axes
    plt.title(title)
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.legend([ref_1], loc=refs_location)
    # show figure
    plt.show()

def plot_wahwah_signals(original_signal, wahwah_signal,
                            title="Wahwah signal response",
                            label_x="Time", label_y="Amplitude",
                            ref_1="Original signal", ref_2="Wahwah signal",
                            refs_location="best"):

    # plot signals to graphic
    plt.plot(original_signal)
    plt.plot(wahwah_signal)
    # set legends to graph
    plt.title(title)
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.legend([ref_1, ref_2], loc=refs_location)
    # show figure
    plt.show()
    
def main():
    # Filter settings
    DAMPING = 0.05
    MIN_F = 300
    MAX_F = 4000
    WAH_F = 0.4
    # Program settings
    ORIGINAL_WAV = "/home/juan.bassi/personalProjects/dsp_controller/wavs/guitars.wav"
    WAHWAH_WAV = "/home/juan.bassi/personalProjects/dsp_controller/wavs/guitars_modified.wav"

    # WahWahFilter.play_audio(ORIGINAL_WAV)

    wahwah = WahWahFilter(DAMPING, MIN_F, MAX_F, WAH_F)

    fs, original_signal = convert_wav_to_raw(ORIGINAL_WAV)

    triangle_signal = wahwah._create_triangle_waveform(len(original_signal), fs)
    plot_wahwah_triangle_wave(triangle_signal)

    wahwah_signal = wahwah.apply_filter(original_signal, fs)

    plot_wahwah_signals(original_signal, wahwah_signal)

    save_raw_to_wav(wahwah_signal, WAHWAH_WAV, fs)

    play_audio(WAHWAH_WAV)
    

if __name__ == "__main__":
    main()