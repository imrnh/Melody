import os, asyncpg, json, pickle
from fastapi import APIRouter, UploadFile, Form
from pydantic import BaseModel
from .search import FingerprintPipeline
from .to_wav import m4a_to_wav
from .downloader import MusicDownloader
from decouple import config
from typing import List, Dict, Tuple
from utilities import save_identification_history, load_identification_history

router = APIRouter()

DATABASE_URL = config("DATABASE_URL")


@router.get("/crawle")
async def perform_crawling():
    try:
        # crawl_msg = crawl_songs()
        # return {"msg": f"Succesfully crawled {crawl_msg} songs"}
        """
        TODO:
            - iterate over music table in db for all song with audio_hash_available as false.
            - for every song, download the video and convert it into hashes.
            - push hashes to db along with song id
            - for that song in music table, tick the audio_hash_available field to true.
            - repeat 2-4 till the end of cursor.
        """

        database_file = "database/database.pickle"

        # Get all music id and url that doesn't have audio_hash_available
        connection = await asyncpg.connect(DATABASE_URL)
        query_all_music_without_audio_hash = "select id, playback_url as url from music where audio_hash_available=false;"
        r_response = await connection.fetch(query_all_music_without_audio_hash)

        # Iterate over all music, download the video and convert it into hashes.
        music_downloader_obj = MusicDownloader()
        list_of_hash_pairs: Dict[int, List[Tuple[int, int]]] = {}

        # save current db before removing all items.
        with open("../database/database.pickle", "rb") as db:
            curr_database = pickle.load(db)
            list_of_hash_pairs = curr_database

        # build db for other songs.
        for r_music in r_response:
            print("Working with id: ", r_music["id"])
            output_wav_file = music_downloader_obj.download_and_convert(r_music["url"])

            fingerprint_obj = FingerprintPipeline()
            audio_hashes = fingerprint_obj.transform_audio(
                output_wav_file, r_music["id"]
            )

            for ad_hash, time_index_pair in audio_hashes.items():
                if ad_hash not in list_of_hash_pairs:
                    list_of_hash_pairs[ad_hash] = []
                list_of_hash_pairs[ad_hash].append(time_index_pair)

            # make the hash available as true.
            query_update_audio_hash_available = (
                "update music set audio_hash_available=true where id = $1;"
            )
            await connection.execute(query_update_audio_hash_available, r_music["id"])

        with open(database_file, "wb") as db:
            pickle.dump(list_of_hash_pairs, db, pickle.HIGHEST_PROTOCOL)
            print("Database operation performed for song ", r_music["id"])

            # for hash_point, song_info_list in list_of_hash_pairs.items():
            #     query_to_add_hash = "INSERT INTO music_hash (hash, info, music_id) VALUES ($1, $2, $3);"
            #     await connection.execute(query_to_add_hash, hash_point, json.dumps(song_info_list), r_music['id'])
            #
            # print(f"Hashing and database operation for song id: {r_music['id']} done")
            # # Then tick this song's audio_hash_available to true.
            # query_update_audio_hash_available = "update music set audio_hash_available=true where id = $1;"
            # await connection.execute(query_update_audio_hash_available, r_music['id'])

        return {"status": 200, "songs_modified": r_response}

    except Exception as e:
        return {"msg": f"Something went wrong {e}"}


@router.post("/identify/")
async def upload_file(file: UploadFile, user_id: str = Form(...)):
    try:
        if file.filename:
            filePath = os.path.join("assets/torec/", file.filename)
            with open(filePath, "wb") as f:
                f.write(file.file.read())

            # convert the song into wav with single channel.
            m4a_to_wav(file.filename)

            fingerprint_obj = FingerprintPipeline()
            song_ids = fingerprint_obj.recognize(file.filename + ".wav")

            hs_status, err = await save_identification_history(
                user_id, song_ids[0]
            )
            if hs_status:
                # get song info
                songs = []

                conn = await asyncpg.connect(DATABASE_URL)

                for song_id in song_ids:
                    _qry = "SELECT m.id,  m.mname, m.artist_id, m.playback_url, m.cover_image, a.artist_name FROM music m INNER JOIN artist a ON m.artist_id = a.id WHERE m.id = $1;"
                    res = await conn.fetch(_qry, song_id)
                    songs.append(res[0])

                return {"songs": songs}
            else:
                raise err

    except Exception as e:
        print("Exception: ", e)
    return {"message": "No file received"}



class ViewHistoryModel(BaseModel):
    user_id : str

@router.post("/view_history/")
async def view_history(vhm: ViewHistoryModel):
    conn = await asyncpg.connect(DATABASE_URL)

    _qry = "select song_id from history where  user_id = $1;"
    resulting_music_ids = await conn.fetch(_qry, vhm.user_id)

    songs = []
    for song_rec in resulting_music_ids:
        _qry = "SELECT m.id,  m.mname, m.artist_id, m.playback_url, m.cover_image, a.artist_name FROM music m INNER JOIN artist a ON m.artist_id = a.id WHERE m.id = $1;"
        res = await conn.fetch(_qry, song_rec['song_id'])
        songs.append(res[0])
    print("REtunred: ", songs)
    return {"songs": songs}
