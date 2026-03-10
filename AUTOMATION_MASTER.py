#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

BOLD = '\033[1m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
END = '\033[0m'

def print_header(text):
    print(f"\n{BOLD}{BLUE}{'='*60}{END}")
    print(f"{BOLD}{BLUE}{text}{END}")
    print(f"{BOLD}{BLUE}{'='*60}{END}\n")

def print_success(text): print(f"{GREEN}✅ {text}{END}")
def print_error(text): print(f"{RED}❌ {text}{END}")
def print_info(text): print(f"{BLUE}ℹ️  {text}{END}")
def print_warning(text): print(f"{YELLOW}⚠️  {text}{END}")

def run_script(script_name, game_name):
    script_path = f"scripts/{script_name}"
    if not os.path.exists(script_path):
        print_error(f"Script not found: {script_path}")
        return False
    print_info(f"Running: {script_name}")
    result = subprocess.run(["python3", script_path, game_name], cwd=os.getcwd())
    if result.returncode == 0:
        print_success(f"Completed: {script_name}")
        return True
    else:
        print_error(f"Failed: {script_name}")
        return False

def check_raw_videos(game_name):
    raw_dir = f"games/{game_name}/raw"
    if not os.path.exists(raw_dir):
        print_error(f"Raw directory not found: {raw_dir}")
        return False
    video_extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.m4v']
    videos = []
    for ext in video_extensions:
        videos.extend(list(Path(raw_dir).glob(ext)))
    if not videos:
        print_error(f"No video files found in: {raw_dir}")
        print_info("Add .mp4 or .mov gameplay video to this folder")
        return False
    print_success(f"Found raw video: {videos[0].name}")
    return True

def check_assets(game_name):
    assets_dir = f"games/{game_name}/assets"
    missing = []
    if not os.path.exists(f"{assets_dir}/end.mp4"):
        missing.append("end.mp4")
    if not os.path.exists(f"{assets_dir}/background_music.m4a"):
        missing.append("background_music.m4a")
    if missing:
        print_warning(f"Missing assets: {', '.join(missing)}")
        return False
    print_success("All assets found")
    return True

def mode_extract(game_name, max_clips=5):
    """Step 1: Extract viral clips from raw gameplay video"""
    print_header("STEP 1: EXTRACT VIRAL CLIPS")

    raw_dir = f"games/{game_name}/raw"
    if not os.path.exists(raw_dir):
        print_error(f"Raw directory not found: {raw_dir}")
        return False

    video_extensions = ["*.mp4", "*.mov", "*.avi", "*.mkv", "*.m4v"]
    videos = []
    for ext in video_extensions:
        videos.extend(list(Path(raw_dir).glob(ext)))

    if not videos:
        print_error(f"No video files found in: {raw_dir}")
        print_info(f"Add your gameplay video to: {raw_dir}/")
        return False

    video_filename = videos[0].name
    print_success(f"Found raw video: {video_filename}")
    print_info(f"Extracting 12-13 second viral moments using GPT-4o Vision...")

    script_path = "scripts/1_extract_viral_clips.py"
    if not os.path.exists(script_path):
        print_error(f"Script not found: {script_path}")
        return False

    import subprocess
    cmd = ["python3", script_path, game_name, video_filename, str(max_clips)]
    print_info(f"Running: python3 1_extract_viral_clips.py {game_name} {video_filename}")

    try:
        subprocess.run(cmd, check=True)
        print_success("Clip extraction completed!")
        return True
    except subprocess.CalledProcessError:
        print_error("Clip extraction failed!")
        return False

def mode_prompts(game_name):
    print_header("STEP 2: GENERATE INFLUENCER VIDEOS (VEO3 AUTO)")
    print_info("Generating prompts AND videos automatically with Veo3 API...")
    return run_script("2_generate_veo3_prompts.py", game_name)

def mode_combine(game_name):
    print_header("STEP 3: COMBINE GAMEPLAY + INFLUENCER")
    print_info("Creating platform-specific shorts...")
    return run_script("3_create_final_shorts.py", game_name)

def mode_images(game_name):
    print_header("STEP 4: GENERATE VIRAL IMAGES")
    print_info("Creating promotional images with DALL-E 3...")
    return run_script("4_generate_viral_images.py", game_name)

def mode_finalize(game_name):
    print_header("STEP 5: FINALIZE")
    if not check_assets(game_name):
        print_error("Missing assets!")
        print_info(f"Add to: games/{game_name}/assets/")
        print_info("  - end.mp4")
        print_info("  - background_music.m4a")
        return False
    print_info("Adding viral subtitles, end screen, and music...")
    return run_script("add_viral_subtitles.py", game_name)

def mode_upload(game_name):
    print_header("STEP 6: UPLOAD")
    output_dir = f"games/{game_name}/output_final"
    if not os.path.exists(output_dir):
        print_error("No final videos found! Run finalize first.")
        return False
    videos = list(Path(output_dir).glob("*.mp4"))
    print_success(f"{len(videos)} video(s) ready for upload")
    print(f"\n{YELLOW}📁 Videos: {output_dir}/{END}")
    print(f"{YELLOW}Upload to: TikTok, YouTube Shorts, Instagram{END}\n")
    return True

def mode_full(game_name):
    """Full pipeline"""
    print_header("FULL AUTOMATION PIPELINE")

    # 1) Clip sayisi
    print(f"{BOLD}Kac viral clip olusturmak istiyorsun? (1-10){END}")
    while True:
        try:
            max_clips = int(input("Clip sayisi: ").strip())
            if 1 <= max_clips <= 10:
                break
            print_warning("1-10 arasi gir")
        except ValueError:
            print_warning("Gecerli sayi gir")
    print_success(f"{max_clips} clip uretilecek")

    # 2) Platform secimi
    print(f"\n{BOLD}Hangi platformlar icin video olusturulsun?{END}")
    print("  1) TikTok")
    print("  2) YouTube Shorts")
    print("  3) Instagram Reels")
    print("  4) Instagram Story")
    print("  Ornek: 1  -> sadece TikTok")
    print("  Ornek: 1,2 -> TikTok + YouTube")
    print("  Ornek: all -> hepsi\n")
    platform_map = {
        "1": "tiktok",
        "2": "youtube",
        "3": "instagram_reels",
        "4": "instagram_story"
    }
    platform_labels = {
        "tiktok": "TikTok",
        "youtube": "YouTube Shorts",
        "instagram_reels": "Instagram Reels",
        "instagram_story": "Instagram Story"
    }
    while True:
        sel = input("Secim: ").strip().lower()
        if sel == "all":
            selected_platforms = list(platform_map.values())
            break
        try:
            nums = [s.strip() for s in sel.split(",")]
            selected_platforms = [platform_map[n] for n in nums if n in platform_map]
            if selected_platforms:
                break
            print_warning("Gecersiz secim")
        except Exception:
            print_warning("Tekrar dene")
    labels = [platform_labels[p] for p in selected_platforms]
    print_success(f"Secilen: {', '.join(labels)}")

    # Config kaydet
    import json
    os.makedirs(f"games/{game_name}", exist_ok=True)
    with open(f"games/{game_name}/session_config.json", "w") as f:
        json.dump({"max_clips": max_clips, "platforms": selected_platforms}, f, indent=2)

    # 3) Presenter modu
    print(f"\n{BOLD}Presenter modunu sec:{END}")
    print("  1) AI Presenter - Veo3 ile influencer videosu")
    print("  2) Voiceover    - Metin -> TTS ses + altyazi\n")
    while True:
        choice = input("Secim (1/2): ").strip()
        if choice in ["1", "2"]:
            break
        print_warning("1 veya 2 gir")

    # Extract
    if not mode_extract(game_name, max_clips=max_clips):
        return False

    if choice == "1":
        print_header("AI PRESENTER MODE")
        if not mode_prompts(game_name):
            return False
        if not os.path.exists("scripts/auto_veo3.py"):
            print_error("auto_veo3.py bulunamadi!")
            return False
        try:
            subprocess.run(["python3", "scripts/auto_veo3.py", game_name], check=True)
        except subprocess.CalledProcessError:
            print_error("Veo3 uretimi basarisiz!")
            return False
        if not mode_combine(game_name):
            return False
    else:
        print_header("VOICEOVER MODE")
        print("Yorum metni:")
        print("  1) Manuel gir")
        print("  2) Otomatik (GPT-4o)\n")
        while True:
            tc = input("Secim (1/2): ").strip()
            if tc in ["1", "2"]:
                break
        text_input = None
        if tc == "1":
            text_input = input("Yorumu gir: ").strip() or None

        print("\nSes tonu:")
        print("\nSes tonu (ElevenLabs eleven_v3):")
        print("  1) Kendi sesin - y8mBjGEqtMV3PO41kDm0 (onerilen)")
        print("  2) Adam        - pNInz4obpvDQR2KxHPt2  - Guclu erkek")
        print("  3) Rachel      - 21m00Tcm4TlvDq8ikWAM  - Dost canlisi kadin")
        print("  4) Domi        - AZnzlk1XvdvUeBnXmlld  - Enerjik kadin")
        print("  5) Antoni      - ErXwobaYiN019PkySvjV  - Akici erkek")
        print("  6) Manuel gir  - Kendi voice ID'ni gir\n")
        voice_map = {
            "1": "y8mBjGEqtMV3PO41kDm0",
            "2": "pNInz4obpvDQR2KxHPt2",
            "3": "21m00Tcm4TlvDq8ikWAM",
            "4": "AZnzlk1XvdvUeBnXmlld",
            "5": "ErXwobaYiN019PkySvjV",
        }
        voice_sel = input("Ses (1-6, default=1): ").strip()
        if voice_sel == "6":
            voice = input("Voice ID gir: ").strip()
        else:
            voice = voice_map.get(voice_sel, "y8mBjGEqtMV3PO41kDm0")
        print("Secilen ses ID: " + voice)

        print("\nSes ayarlari:")
        print("  1) Varsayilan kullan  (stability=0.5 | similarity=0.5 | style=0.5 | speed=1.1 | boost=true)")
        print("  2) Ozellestirilmis   - Kendim girerim\n")

        settings_choice = input("  Secim (1/2, default=1): ").strip()

        if settings_choice == "2":
            def _get_float(prompt, default, lo, hi):
                while True:
                    val = input(f"  {prompt} [{default}]: ").strip()
                    if val == "": return default
                    try:
                        v = float(val)
                        if lo <= v <= hi: return v
                        print(f"    {lo}-{hi} arasi olmali")
                    except ValueError:
                        print("    Gecerli sayi gir")

            stability  = _get_float("stability   (0.0-1.0)", 0.5,  0.0, 1.0)
            similarity = _get_float("similarity  (0.0-1.0)", 0.5,  0.0, 1.0)
            style      = _get_float("style       (0.0-1.0)", 0.5,  0.0, 1.0)
            speed      = _get_float("speed       (0.7-1.2)", 1.1,  0.7, 1.2)
            boost_raw  = input(f"  boost (true/false) [true]: ").strip().lower()
            speaker_boost = boost_raw != "false"
        else:
            stability     = 0.5
            similarity    = 0.5
            style         = 0.5
            speed         = 1.1
            speaker_boost = True

        voice_settings = {
            "stability": stability,
            "similarity_boost": similarity,
            "style": style,
            "use_speaker_boost": speaker_boost,
            "speed": speed
        }
        print(f"Ayarlar: stability={stability} | similarity={similarity} | style={style} | speed={speed} | boost={speaker_boost}")
        print(f"Ayarlar: stability={stability} | similarity={similarity} | style={style} | speed={speed} | boost={speaker_boost}")
        print_success(f"Ses: {voice}")

        import importlib.util
        spec = importlib.util.spec_from_file_location("voiceover_clip", "scripts/voiceover_clip.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not mod.process_voiceover(game_name, text_input=text_input, voice=voice, platforms=selected_platforms, voice_settings=voice_settings):
            return False

    if not mode_images(game_name):
        print_warning("Gorsel uretimi basarisiz, devam ediliyor...")
    if not mode_finalize(game_name):
        return False
    mode_upload(game_name)
    print_header("PIPELINE TAMAMLANDI!")
    return True


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 AUTOMATION_MASTER.py <game_name> <mode>")
        print("Modes: extract, prompts, combine, images, finalize, upload, full")
        sys.exit(1)

    game_name = sys.argv[1]
    mode = sys.argv[2].lower()

    os.makedirs(f"games/{game_name}/raw", exist_ok=True)
    os.makedirs(f"games/{game_name}/clips", exist_ok=True)
    os.makedirs(f"games/{game_name}/output", exist_ok=True)
    os.makedirs(f"games/{game_name}/output_final", exist_ok=True)
    os.makedirs(f"games/{game_name}/assets", exist_ok=True)
    os.makedirs(f"games/{game_name}/images", exist_ok=True)

    print_header("AI GAMING SHORTS")
    print_info(f"Game: {game_name}")
    print_info(f"Mode: {mode}")

    modes = {
        'extract': mode_extract,
        'prompts': mode_prompts,
        'combine': mode_combine,
        'images': mode_images,
        'finalize': mode_finalize,
        'upload': mode_upload,
        'full': mode_full
    }

    if mode not in modes:
        print_error(f"Invalid mode: {mode}")
        print_info(f"Valid modes: {', '.join(modes.keys())}")
        sys.exit(1)

    success = modes[mode](game_name)

    if success:
        print_header("SUCCESS!")
    else:
        print_header("FAILED")
        sys.exit(1)

if __name__ == '__main__':
    main()
