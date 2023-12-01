import pickle
import numpy as np
import matplotlib.pyplot as plt

from scipy import fft, signal
import scipy
from scipy.io.wavfile import read


class FingerprintPipeline:
    def __init__(self) -> None:
        self.root_path = "assets/torec"
        self.database_file = "database/database.pickle"
        self.song_index_file = "database/song_index.pickle"
        self.database = None
        self.song_name_index = None

    def create_constellation(self, audio, Fs):
        window_length_seconds = 0.5
        window_length_samples = int(window_length_seconds * Fs)
        window_length_samples += window_length_samples % 2
        num_peaks = 15

        amount_to_pad = (  # Pad the song to divide evenly into windows
            window_length_samples - audio.size % window_length_samples
        )
        song_input = np.pad(audio, (0, amount_to_pad))

        frequencies, times, stft = signal.stft(
            song_input,
            Fs,
            nperseg=window_length_samples,
            nfft=window_length_samples,
            return_onesided=True,
        )

        constellation_map = []

        for time_idx, window in enumerate(stft.T):
            spectrum = abs(window)
            peaks, props = signal.find_peaks(spectrum, prominence=0, distance=200)

            n_peaks = min(num_peaks, len(peaks))
            largest_peaks = np.argpartition(props["prominences"], -n_peaks)[-n_peaks:]
            for peak in peaks[largest_peaks]:
                frequency = frequencies[peak]
                constellation_map.append([time_idx, frequency])

        return constellation_map

    def create_hashes(self, constellation_map, song_id=None):
        hashes = {}
        # Use this for binning - 23_000 is slighlty higher than the maximum
        # frequency that can be stored in the .wav files, 22.05 kHz
        upper_frequency = 23_000
        frequency_bits = 10

        # Iterate the constellation
        for idx, (time, freq) in enumerate(constellation_map):
            # Iterate the next 100 pairs to produce the combinatorial hashes
            # When we produced the constellation before, it was sorted by time already
            # So this finds the next n points in time (though they might occur at the same time)
            for other_time, other_freq in constellation_map[idx : idx + 100]:
                diff = other_time - time
                # If the time difference between the pairs is too small or large
                # ignore this set of pairs
                if diff <= 1 or diff > 10:
                    continue

                # Place the frequencies (in Hz) into a 1024 bins
                freq_binned = freq / upper_frequency * (2**frequency_bits)
                other_freq_binned = other_freq / upper_frequency * (2**frequency_bits)

                # Produce a 32 bit hash
                # Use bit shifting to move the bits to the correct location
                hash = (
                    int(freq_binned)
                    | (int(other_freq_binned) << 10)
                    | (int(diff) << 20)
                )
                hashes[hash] = (time, song_id)
        return hashes
    

    def load_database(self):
        self.database = pickle.load(open(self.database_file, 'rb'))
        self.song_name_index = pickle.load(open(self.song_index_file, "rb"))


    def recognize(self, file_name: str):
        self.load_database()
        Fs, audio_input = read(f"{self.root_path}/{file_name}")

        constellation = self.create_constellation(audio_input, Fs)
        hashes = self.create_hashes(constellation, None)

        matches_per_song = {}
        for hash, (sample_time, _) in hashes.items():
            if hash in self.database:
                matching_occurences = self.database[hash]
                for source_time, song_id in matching_occurences:
                    if song_id not in matches_per_song:
                        matches_per_song[song_id] = 0
                    matches_per_song[song_id] += 1

        song_names = []
        for song_id, num_matches in list(
            sorted(matches_per_song.items(), key=lambda x: x[1], reverse=True)
        )[:4]:
            song_names.append(self.song_name_index[song_id])

        return song_names
