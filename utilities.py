import os, asyncpg, json, pickle
from decouple import config

DATABASE_URL = config('DATABASE_URL')


async def save_identification_history(uid: str, song_id: int):
    try:
        connection = await asyncpg.connect(DATABASE_URL)
        query = "insert into history (user_id, song_id) values ($1, $2);"
        connection.execute(query, uid, song_id)
        print(f"I'm saving for user : {uid} and song_id : {song_id}")
        return True, None
    except Exception as e:
        return False, e


async def load_identification_history(uid: str):
    connection = await asyncpg.connect(DATABASE_URL)
    query = "select * from history where user_id = $1;"
    result = connection.fetch(query, uid)
    return result
