import glob
from typing import List, Dict, Tuple
from tqdm import tqdm
import pickle
from scipy.io.wavfile import read

from .search import FingerprintPipeline

root_path = "assets/audio"
database_file = "database/database.pickle"
song_index_file = "database/song_index.pickle"


def crawl_songs():
    songs = glob.glob(f"{root_path}/*.wav")
    fingerprint_pipeline = FingerprintPipeline()

    song_name_index = {}
    database: Dict[int, List[Tuple[int, int]]] = {}

    for index, filename in enumerate(tqdm(sorted(songs))):
        # song_name_index[index] = filename.split("/")[-1]
        Fs, audio_input = read(filename)
        constellation = fingerprint_pipeline.create_constellation(audio_input, Fs)
        hashes = fingerprint_pipeline.create_hashes(constellation, index)

        # For each hash, append it to the list for this hash
        for hash, time_index_pair in hashes.items():
            if hash not in database:
                database[hash] = []
            database[hash].append(time_index_pair)
    with open(database_file, "wb") as db:
        pickle.dump(database, db, pickle.HIGHEST_PROTOCOL)
    with open(song_index_file, "wb") as songs:
        pickle.dump(song_name_index, songs, pickle.HIGHEST_PROTOCOL)

    return len(songs)
