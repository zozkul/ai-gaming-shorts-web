from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import os
import shutil
from typing import Optional

from routes import router as process_router

app = FastAPI(title="AI Gaming Shorts API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
BASE_GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "games")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "AI Gaming Shorts API is running"}

@app.get("/api/games")
def get_games():
    """List all available games in the directory structure"""
    games = []
    if os.path.exists(BASE_GAMES_DIR):
        for item in os.listdir(BASE_GAMES_DIR):
            if os.path.isdir(os.path.join(BASE_GAMES_DIR, item)):
                games.append(item)
    return {"games": games}

@app.post("/api/upload/{game_name}")
async def upload_video(game_name: str, file: UploadFile = File(...)):
    """Upload a raw gameplay video (streamed in chunks to avoid blocking)."""
    game_dir = os.path.join(BASE_GAMES_DIR, game_name, "raw")
    os.makedirs(game_dir, exist_ok=True)

    file_path = os.path.join(game_dir, file.filename)

    # If the file already exists with the same name, skip re-uploading
    if os.path.exists(file_path):
        return {"status": "success", "filename": file.filename, "skipped": True}

    def _write():
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

    # Run blocking file I/O in a thread pool so the event loop stays free
    await run_in_threadpool(_write)

    return {"status": "success", "filename": file.filename}

# Connect the processing routes
app.include_router(process_router)
