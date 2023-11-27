from fastapi import APIRouter
import sqlite3 

router= APIRouter(prefix="/music")

@router.post("/add_lyrics")
def insert_song_data(song_name, youtube_url, artist, lyrics):
    # Connect to the SQLite database
    conn = sqlite3.connect('system.db')
    cursor = conn.cursor()

    # Insert data into the 'songs' table
    cursor.execute('''
        INSERT INTO songs (song_name, youtube_url, artist) VALUES (?, ?, ?)
    ''', (song_name, youtube_url, artist))

    # Get the song_id of the inserted record
    song_id = cursor.lastrowid

    # Insert lyrics into the 'lyrics' table
    for line in lyrics.split('\n'):
        cursor.execute('''
            INSERT INTO lyrics (song_id, lyrics) VALUES (?, ?)
        ''', (song_id, line))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    return {"string":"complete"}

# Example usage
# insert_song_data("Song Title", "https://www.youtube.com/song123", "Artist Name", "Lyrics line 1\nLyrics line 2\nLyrics line 3")
