CREATE TABLE
  public.artist (id serial NOT NULL, artist_name text NULL);

ALTER TABLE
  public.artist
ADD
  CONSTRAINT artist_pkey PRIMARY KEY (id)



CREATE TABLE
  public.music (
    id serial NOT NULL,
    mname text NULL,
    artist_id integer NULL,
    playback_url text NULL,
    cover_image text NULL
  );

ALTER TABLE
  public.music
ADD
  CONSTRAINT music_pkey PRIMARY KEY (id)



CREATE TABLE music_hash (
    id SERIAL PRIMARY KEY,
    hash TEXT,
    info JSONB,
  	music_id INT REFERENCES music(id)
);



create table lyrics_hash(
  id serial primary key,
  l_hash TEXT,
  window_size INT,
  music_id INT REFERENCES music(id)
 );