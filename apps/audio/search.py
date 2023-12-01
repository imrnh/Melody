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
        upper_frequency = 23_000
        frequency_bits = 10

        for idx, (time, freq) in enumerate(constellation_map):
            for other_time, other_freq in constellation_map[idx: idx + 100]:
                diff = other_time - time
                if diff <= 1 or diff > 10:  # only tuples with time difference greater than 1 or less than 11 will be allowed
                    continue

                freq_binned = freq / upper_frequency * (2 ** frequency_bits)
                other_freq_binned = other_freq / upper_frequency * (2 ** frequency_bits)

                freq_hash = (int(freq_binned) | (int(other_freq_binned) << 10) | (int(diff) << 20))
                hashes[freq_hash] = (time, song_id)
        return hashes

    def load_database(self):
        self.database = pickle.load(open(self.database_file, 'rb'))
        self.song_name_index = pickle.load(open(self.song_index_file, "rb"))

    def transform_audio(self, audio_path, song_id):
        sr, audio_content = read(audio_path)

        constellation_map = self.create_constellation(audio_content, sr)
        hashes = self.create_hashes(constellation_map, song_id=song_id)

        return hashes

    def recognize(self, file_name: str):
        self.load_database()
        Fs, audio_input = read(f"{self.root_path}/{file_name}")

        constellation = self.create_constellation(audio_input, Fs)
        hashes = self.create_hashes(constellation, None)

        matches_per_song = {}
        for freq_hash, (sample_time, _) in hashes.items():
            if freq_hash in self.database:
                matching_occurrences = self.database[freq_hash]
                for source_time, song_id in matching_occurrences:
                    if song_id not in matches_per_song:
                        matches_per_song[song_id] = 0
                    matches_per_song[song_id] += 1

        song_ids = []
        for song_id, num_matches in list(
                sorted(matches_per_song.items(), key=lambda x: x[1], reverse=True)
        )[:4]:
            song_ids.append(song_id)

        return song_ids

