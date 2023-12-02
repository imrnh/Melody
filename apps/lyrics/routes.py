from fastapi import APIRouter
from pydantic import BaseModel
from decouple import config
from .text_processor import TextProcessor
import asyncpg
from utilities import save_identification_history, load_identification_history

router = APIRouter()

DATABASE_URL = config("DATABASE_URL")


class LyricsSearchSongMakerModel(BaseModel):
    title: str
    artist: int
    playback_url: str
    cover_img: str
    lyrics: str


class SearchTextModel(BaseModel):
    search_text: str
    user_id: str


def convert_to_unique_numer_list(input_list):
    unique_list = []
    seen = set()

    for num in input_list:
        if num not in seen:
            seen.add(num)
            unique_list.append(num)

    return unique_list


@router.post("/")
async def add_song_lyrics(lsm: LyricsSearchSongMakerModel):
    """
        1. split lyrics & init text processor
        2. Push music data to database.

    :param lsm:
    :return:
    """
    connection = await asyncpg.connect(DATABASE_URL)

    try:
        lyrics_lines = lsm.lyrics.split("\n")
        lyrics_lines = set(lyrics_lines)  # taking only unique lines.
        text_processor = TextProcessor()

        if len(lyrics_lines) <= 0:
            return {"msg": "Error with lyrics parsing"}

        query = "INSERT INTO music (mname, artist_id, playback_url, cover_image) VALUES ($1, $2, $3, $4) RETURNING id;"
        song_id = await connection.fetchval(
            query, lsm.title, lsm.artist, lsm.playback_url, lsm.cover_img
        )

        query_to_submit_lyrics = "INSERT INTO lyrics (music_id, lyrics_text) VALUES ($1, $2);"
        await connection.execute(query_to_submit_lyrics, song_id, lsm.lyrics)

        for line in lyrics_lines:
            hashes = text_processor.transform(line)
            all_window = list(hashes.keys())

            for window in all_window:
                for l_hash in hashes[window]:
                    query = "INSERT INTO lyrics_hash (l_hash, window_size, music_id) VALUES ($1, $2, $3);"
                    await connection.execute(query, l_hash, window, song_id)
        return {"t": lsm.title, "l": lsm.lyrics, "sid": song_id}
    except Exception as exception:
        print("Exception: ", exception)
        return {"msg": "error"}
    finally:
        await connection.close()


@router.post("/search")
async def search_lyrics(search_text_model: SearchTextModel):
    print("@\n\n\n\n@@@ User id: \t\t\t ", search_text_model.user_id)
    search_text = search_text_model.search_text
    search_texts = search_text.split(", ")  # comma seperated lines
    text_processor = TextProcessor()

    connection = await asyncpg.connect(DATABASE_URL)
    music_ids = {}  # temporary storage for music ids.
    for srch_text in search_texts:
        hashes = text_processor.transform(srch_text)
        all_window = list(hashes.keys())

        for window_key in all_window:
            music_ids[window_key] = []
            for hash_item in hashes[window_key]:
                query = "SELECT music_id FROM lyrics_hash WHERE l_hash=$1 and window_size=$2;"
                result = await connection.fetch(query, hash_item, window_key)
                music_ids[window_key].append(result)

    # fetching song info
    all_window_sizes = list(music_ids.keys())
    all_window_sizes.reverse()

    music_ids_in_order = []
    for k in all_window_sizes:
        for id_list in music_ids[k]:
            try:
                music_ids_in_order.append(id_list[0]["music_id"])
            except IndexError as ixerror:
                pass

    music_ids_in_order = convert_to_unique_numer_list(music_ids_in_order)

    hs_stat, err = await save_identification_history(
        search_text_model.user_id, music_ids_in_order[0]
    )

    all_song_info = []
    for mid in music_ids_in_order:
        query = "SELECT m.mname, m.artist_id, m.playback_url, m.cover_image, a.artist_name FROM music m INNER JOIN artist a ON m.artist_id = a.id WHERE m.id = $1;"
        song_search_result = await connection.fetch(query, mid)
        all_song_info.append(song_search_result[0])

    return {"songs": all_song_info}


@router.get("/get_lyrics")
async def get_song_lyrics(song_id : int):
    print("@@SONG ID \n\n",song_id)
    conn = await asyncpg.connect(DATABASE_URL)
    query = "select lyrics_text from lyrics where music_id = $1;"
    lyrics_res = await conn.fetch(query, song_id)

    if len(lyrics_res) > 0:
        ltext = lyrics_res[0]
        return {"lyrics": ltext}
    
    else:
        return {"lyrics": ""}
