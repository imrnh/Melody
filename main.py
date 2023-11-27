import os
from fastapi import FastAPI, UploadFile, Response
from services.search import FingerprintPipeline
from services.crawler import crawl_songs
from services.to_wav import m4a_to_wav
from humming.routes import router

api = FastAPI()


api.include_router(router) 

@api.get("/crawle")
async def perform_crawling():
    try:
        crawl_msg = crawl_songs()
        return {"msg": f"Succesfully crawled {crawl_msg} songs"}
    except Exception as e:
        return {"msg": f"Something went wrong {e}"}


@api.post("/uploadfile/")
async def upload_file(file: UploadFile):
    try:
        if file.filename:
            filePath = os.path.join("assets/torec/", file.filename)
            with open(filePath, "wb") as f:
                f.write(file.file.read())

            #convert the song into wav with single channel.
            m4a_to_wav(file.filename)

            fingerprint_obj = FingerprintPipeline()
            songs = fingerprint_obj.recognize(file.filename + ".wav")

            print("@@ Songs: ", songs)

            return {
                "songs": songs
            }

    except Exception as e:
        print("ERROR: ---- ", e)
    return {"message": "No file received"}
