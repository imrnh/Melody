from fastapi import FastAPI, UploadFile, Response
from apps.audio.routes import router as audio_router
from apps.lyrics.routes import router as lyrics_router


api = FastAPI()

api.include_router(audio_router, prefix="/audio")
api.include_router(lyrics_router, prefix="/lyrics")