from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import os
import sys
import json
import time
import threading

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import importlib.util

def import_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

extractor = import_script("extractor", os.path.join(parent_dir, "scripts", "1_extract_viral_clips.py"))
prompter = import_script("prompter", os.path.join(parent_dir, "scripts", "2_generate_veo3_prompts.py"))
shorts_creator = import_script("shorts_creator", os.path.join(parent_dir, "scripts", "3_create_final_shorts.py"))
voiceover = import_script("voiceover", os.path.join(parent_dir, "scripts", "voiceover_clip.py"))

router = APIRouter(prefix="/api/process", tags=["Processing"])

# ── Status helpers ───────────────────────────────────────────────────────────

PIPELINE_STAGES = [
    {"id": "upload",     "label": "Video uploaded"},
    {"id": "extracting", "label": "Extracting viral clips"},
    {"id": "prompts",    "label": "Generating AI prompts"},
    {"id": "combining",  "label": "Combining clips"},
    {"id": "done",       "label": "Pipeline complete"},
]

def status_path(game_name: str) -> str:
    return os.path.join(parent_dir, "games", game_name, "status.json")

def write_status(game_name: str, stage: str, message: str, progress: int = 0, error: str = None):
    path = status_path(game_name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "stage": stage,
        "message": message,
        "progress": progress,
        "updated_at": time.time(),
    }
    if error:
        payload["error"] = error
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)

# ── Heartbeat ─────────────────────────────────────────────────────────────────

HEARTBEAT_MESSAGES = [
    (12, "Extracting frames from video…"),
    (18, "Sending frames to GPT-4o Vision — this takes 3-8 min…"),
    (22, "GPT-4o analyzing gameplay moments…"),
    (26, "Still analyzing — AI is reviewing all frames…"),
    (30, "Almost done with AI analysis…"),
    (34, "Waiting for GPT-4o response…"),
    (38, "GPT-4o response processing…"),
]

def _heartbeat(game_name: str, stop_event: threading.Event):
    """Slowly increment progress while a long AI call is in flight."""
    for progress, message in HEARTBEAT_MESSAGES:
        if stop_event.wait(timeout=30):   # wait 30s between steps, exit early if set
            return
        if not stop_event.is_set():
            write_status(game_name, "extracting", message, progress)

# ── Background task wrappers ──────────────────────────────────────────────────

def run_extraction(game_name: str, video_filename: str, max_clips: int):
    orig_cwd = os.getcwd()
    stop_event = threading.Event()
    hb = threading.Thread(target=_heartbeat, args=(game_name, stop_event), daemon=True)
    try:
        os.chdir(parent_dir)
        write_status(game_name, "extracting", f"Starting extraction of {max_clips} clips…", 10)
        hb.start()
        result = extractor.process_game_video(game_name, video_filename, max_clips)
        stop_event.set()
        hb.join()
        if result:
            write_status(game_name, "done", f"Extracted {len(result)} clips!", 100)
        else:
            write_status(game_name, "error", "Extraction returned no clips — check video path and API keys", 0,
                         error="process_game_video returned None. Video may not exist or OpenAI key missing.")
    except Exception as e:
        stop_event.set()
        write_status(game_name, "error", "Extraction failed", 0, error=str(e))
    finally:
        os.chdir(orig_cwd)

def run_full_pipeline(game_name: str, config: dict):
    orig_cwd = os.getcwd()
    stop_event = threading.Event()
    hb = threading.Thread(target=_heartbeat, args=(game_name, stop_event), daemon=True)
    try:
        os.chdir(parent_dir)
        write_status(game_name, "extracting", f"Starting extraction of {config['max_clips']} clips…", 10)
        hb.start()
        result = extractor.process_game_video(game_name, config["video_filename"], config["max_clips"])
        stop_event.set()
        hb.join()

        if not result:
            write_status(game_name, "error", "Extraction returned no clips", 0,
                         error="process_game_video returned None. Check video path and OPENAI_API_KEY.")
            return

        write_status(game_name, "extracting", f"{len(result)} clips extracted, cutting with FFmpeg…", 45)

        presenter_mode = config.get("presenter_mode", "voiceover")

        if presenter_mode == "ai_presenter":
            write_status(game_name, "prompts", "Generating Veo3 AI presenter prompts…", 60)
            prompter.process_clips(game_name)
            write_status(game_name, "prompts", "Prompts generated", 75)
            write_status(game_name, "done", f"Pipeline complete! {len(result)} clips in games/{game_name}/clips/", 100)

        else:  # voiceover (default)
            write_status(game_name, "combining", f"Generating AI commentary + ElevenLabs voiceover for {len(result)} clips…", 50)
            voice_settings = config.get("voice_settings")
            # voice_settings may be a dict (from model_dump) — pass as-is
            voiceover.process_voiceover(
                game_name,
                text_input=config.get("commentary_text") if config.get("commentary_mode") == "manual" else None,
                voice=config.get("voice_id", "y8mBjGEqtMV3PO41kDm0"),
                platforms=config.get("platforms", ["tiktok"]),
                voice_settings=voice_settings,
            )
            write_status(game_name, "done", f"Pipeline complete! {len(result)} voiceover shorts in games/{game_name}/output/", 100)
    except Exception as e:
        stop_event.set()
        write_status(game_name, "error", "Pipeline failed", 0, error=str(e))
    finally:
        os.chdir(orig_cwd)

# ── Models ───────────────────────────────────────────────────────────────────

class VoiceSettings(BaseModel):
    stability: float = 0.5
    similarity_boost: float = 0.5
    style: float = 0.5
    speed: float = 1.1
    use_speaker_boost: bool = True

class ProcessConfig(BaseModel):
    video_filename: str
    max_clips: int = 5
    platforms: List[str] = ["tiktok"]
    presenter_mode: str = "ai_presenter"
    commentary_mode: Optional[str] = "auto"
    commentary_text: Optional[str] = None
    voice_id: Optional[str] = "y8mBjGEqtMV3PO41kDm0"
    voice_settings: Optional[VoiceSettings] = None

# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/start/{game_name}")
async def start_pipeline(game_name: str, config: ProcessConfig, background_tasks: BackgroundTasks):
    """Start the full processing pipeline."""
    video_path = os.path.join(parent_dir, "games", game_name, "raw", config.video_filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video not found: {video_path}")

    game_dir = os.path.join(parent_dir, "games", game_name)
    os.makedirs(game_dir, exist_ok=True)

    session = config.model_dump()
    with open(os.path.join(game_dir, "session_config.json"), "w") as f:
        json.dump(session, f, indent=2)

    write_status(game_name, "extracting", "Pipeline started, preparing…", 5)
    background_tasks.add_task(run_full_pipeline, game_name, session)

    return {
        "status": "processing",
        "message": f"Pipeline started: {config.max_clips} clips, mode={config.presenter_mode}",
        "game": game_name,
    }

@router.get("/status/{game_name}")
async def get_status(game_name: str):
    """Return the current processing status for a project."""
    path = status_path(game_name)

    if not os.path.exists(path):
        # Check if there's a session config (project exists but not started)
        config_path = os.path.join(parent_dir, "games", game_name, "session_config.json")
        if os.path.exists(config_path):
            return {"stage": "idle", "message": "Project exists, not started yet", "progress": 0}
        raise HTTPException(status_code=404, detail="Project not found")

    with open(path) as f:
        data = json.load(f)

    # Attach stage metadata for the frontend
    data["stages"] = PIPELINE_STAGES
    return data

@router.get("/list")
async def list_projects():
    """List all known projects and their statuses."""
    games_dir = os.path.join(parent_dir, "games")
    if not os.path.exists(games_dir):
        return {"projects": []}

    projects = []
    for name in os.listdir(games_dir):
        game_path = os.path.join(games_dir, name)
        if not os.path.isdir(game_path):
            continue

        status = {"stage": "idle", "message": "No activity", "progress": 0}
        sp = os.path.join(game_path, "status.json")
        if os.path.exists(sp):
            with open(sp) as f:
                status = json.load(f)

        config = {}
        cp = os.path.join(game_path, "session_config.json")
        if os.path.exists(cp):
            with open(cp) as f:
                config = json.load(f)

        projects.append({"name": name, "status": status, "config": config})

    return {"projects": projects}

@router.post("/extract/{game_name}")
async def start_extraction(game_name: str, video_filename: str, background_tasks: BackgroundTasks, max_clips: int = 5):
    video_path = os.path.join(parent_dir, "games", game_name, "raw", video_filename)
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail=f"Video not found: {video_path}")

    write_status(game_name, "extracting", "Starting clip extraction…", 5)
    background_tasks.add_task(run_extraction, game_name, video_filename, max_clips)

    return {"status": "processing", "message": f"Extracting {max_clips} clips from {video_filename}", "game": game_name}

@router.post("/generate-prompts/{game_name}")
async def generate_prompts(game_name: str, background_tasks: BackgroundTasks):
    metadata_file = os.path.join(parent_dir, "games", game_name, "clips", "clips_metadata.json")
    if not os.path.exists(metadata_file):
        raise HTTPException(status_code=404, detail="No clips metadata found. Run extraction first.")
    background_tasks.add_task(prompter.process_clips, game_name)
    return {"status": "processing", "message": f"Generating Veo3 prompts for {game_name}"}

@router.post("/create-shorts/{game_name}")
async def create_shorts(game_name: str, background_tasks: BackgroundTasks):
    prompts_file = os.path.join(parent_dir, "games", game_name, "clips", "veo3_prompts.json")
    if not os.path.exists(prompts_file):
        raise HTTPException(status_code=404, detail="No prompts file found. Run generation first.")
    background_tasks.add_task(shorts_creator.create_all_shorts, game_name)
    return {"status": "processing", "message": f"Assembling final shorts for {game_name}"}
