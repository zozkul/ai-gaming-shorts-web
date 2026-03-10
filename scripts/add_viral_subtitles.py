#!/usr/bin/env python3
"""
Add VIRAL subtitles with proper audio transcription
- Transcribe influencer audio with Whisper
- Word-by-word pop-up animations
- Add end screen with gameplay audio
- Add background music from audio library
"""

import os
import sys
import json
import subprocess
import random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Asset paths - will be set based on game directory
END_VIDEO = None
BACKGROUND_MUSIC = None

def get_duration(video_path):
    """Get video duration"""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not result.stdout.strip():
        print(f"   ⚠️  Warning: Could not get duration for {video_path}")
        print(f"   stdout: '{result.stdout}'")
        print(f"   stderr: '{result.stderr}'")
        return 0.0

    return float(result.stdout.strip())

def extract_audio(video_path, output_audio):
    """Extract audio from video"""
    cmd = [
        'ffmpeg', '-y',
        '-i', video_path,
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        output_audio
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def transcribe_influencer_audio(video_path, influencer_start, influencer_end):
    """Transcribe influencer audio segment using Whisper"""

    # Extract influencer audio segment
    temp_audio = "/tmp/influencer_audio.wav"

    cmd = [
        'ffmpeg', '-y',
        '-ss', str(influencer_start),
        '-i', video_path,
        '-t', str(influencer_end - influencer_start),
        '-vn',
        '-acodec', 'pcm_s16le',
        '-ar', '16000',
        '-ac', '1',
        temp_audio
    ]
    subprocess.run(cmd, check=True, capture_output=True)

    # Transcribe with Whisper
    print(f"      🎤 Transcribing influencer audio...")
    with open(temp_audio, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )

    # Clean up
    os.remove(temp_audio)

    return transcript

def create_word_by_word_subtitles(transcript, influencer_start, clip_title):
    """Create word-by-word viral subtitles"""

    subtitles = []

    if not transcript.words:
        return {"subtitles": []}

    # BOTTOM: Gameplay title at start (before influencer)
    subtitles.append({
        "layer": "bottom",
        "text": clip_title.upper(),
        "start": 0.0,
        "end": influencer_start,
        "color": "yellow"
    })

    # TOP: Word-by-word influencer reactions
    for word_info in transcript.words:
        word = word_info.word.strip().upper()
        start = influencer_start + word_info.start
        end = influencer_start + word_info.end

        # Skip very short words
        if len(word) < 2:
            continue

        # Detect emotion words for color coding
        emotion_words = ['NO', 'WOW', 'INSANE', 'CRAZY', 'WHAT', 'OH', 'YES', 'BOOM']
        color = 'yellow' if any(e in word for e in emotion_words) else 'white'

        subtitles.append({
            "layer": "top",
            "text": word,
            "start": start,
            "end": end,
            "color": color
        })

    return {"subtitles": subtitles}

def create_viral_subtitle_filter(subtitles, video_duration):
    """Create FFmpeg drawtext filters with ULTRA VIRAL animations"""

    filters = []

    for sub in subtitles:
        text = sub['text'].upper()
        text = text.encode('ascii', 'ignore').decode('ascii').strip()

        if not text:
            continue

        start = sub['start']
        end = sub['end']
        duration = end - start
        layer = sub['layer']
        color = sub.get('color', 'white')

        # Escape for FFmpeg
        text = text.replace("'", "").replace(":", "").replace("!", "").replace("?", "")

        # VIRAL SETTINGS based on layer
        if layer == 'top':
            # INFLUENCER REACTIONS - MASSIVE, EXPLOSIVE TEXT
            y_pos = 500
            base_fontsize = 110  # MUCH BIGGER
            borderw = 12  # THICK BORDER
            shadowx = 5
            shadowy = 5
        else:
            # BOTTOM GAMEPLAY TITLE - STILL BIG BUT LOWER
            y_pos = 1550
            base_fontsize = 130
            borderw = 14
            shadowx = 6
            shadowy = 6

        # VIRAL COLOR SCHEME
        if color == 'yellow':
            # BRIGHT YELLOW for emotion words
            fontcolor = '#FFFF00'
            shadowcolor = '#FF6B00'  # Orange shadow
        else:
            # WHITE with colored shadow
            fontcolor = 'white'
            shadowcolor = '#0080FF'  # Blue shadow

        # Animation timings
        pop_time = 0.08  # Fast pop-in
        fade_out_time = 0.08

        # SHAKE/BOUNCE for emphasis (more intense for short words)
        shake_intensity = 6 if duration < 0.5 else 3
        bounce_expr = f"sin((t-{start})*20)*{shake_intensity}"

        # Position: centered with shake effect
        x_expr = f"(w-text_w)/2+{bounce_expr}"

        # Y position with drop effect (drops from above during pop-in)
        drop_offset = 30
        y_drop = (
            f"if(lt(t-{start},{pop_time}),"
            f"{y_pos}-{drop_offset}+(t-{start})/{pop_time}*{drop_offset},"
            f"{y_pos})"
        )

        # Alpha: fast fade in, hold, fast fade out
        alpha_expr = (
            f"if(lt(t-{start},{pop_time}),"
            f"(t-{start})/{pop_time},"  # Fade in
            f"if(gt(t,{end-fade_out_time}),"
            f"({end}-t)/{fade_out_time},"  # Fade out
            f"1.0)"  # Hold
            f")"
        )

        # LAYER 1: Shadow/Glow (behind main text)
        shadow_filter = (
            f"drawtext="
            f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            f"text='{text}':"
            f"fontsize={base_fontsize}:"
            f"fontcolor={shadowcolor}:"
            f"x='{x_expr}+{shadowx}':"
            f"y='{y_drop}+{shadowy}':"
            f"enable='between(t,{start},{end})':"
            f"alpha='({alpha_expr})*0.8'"
        )
        filters.append(shadow_filter)

        # LAYER 2: Main text with THICK black border
        main_filter = (
            f"drawtext="
            f"fontfile=/System/Library/Fonts/Supplemental/Impact.ttf:"
            f"text='{text}':"
            f"fontsize={base_fontsize}:"
            f"fontcolor={fontcolor}:"
            f"bordercolor=black:"
            f"borderw={borderw}:"
            f"x='{x_expr}':"
            f"y='{y_drop}':"
            f"enable='between(t,{start},{end})':"
            f"alpha='{alpha_expr}'"
        )
        filters.append(main_filter)

    return ','.join(filters) if filters else None

def add_end_screen_and_music(input_video, output_video, subtitles, clip_metadata, end_video_path, music_path):
    """Add subtitles, end screen, and background music"""

    duration = get_duration(input_video)
    end_duration = 5.0
    total_duration = duration + end_duration

    # Get random segment from background music
    music_duration = get_duration(music_path)
    music_start = random.uniform(0, max(0, music_duration - total_duration - 1))

    # Create subtitle filter
    subtitle_filter = create_viral_subtitle_filter(subtitles['subtitles'], duration)

    # Build filter_complex
    filter_parts = []

    # Video: Trim to exact duration, then concat with end screen
    filter_parts.append(
        f"[0:v]trim=duration={duration},"
        f"scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setsar=1,setpts=PTS-STARTPTS[main];"
        f"[1:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,setsar=1,setpts=PTS-STARTPTS[end];"
        f"[main][end]concat=n=2:v=1:a=0[vbase]"
    )

    # Add subtitles if available
    if subtitle_filter:
        # Apply subtitles to concatenated video
        filter_parts.append(f"[vbase]{subtitle_filter}[vout]")
        video_output = "[vout]"
    else:
        video_output = "[vbase]"

    # Audio: Trim gameplay to exact duration, pad for end screen, mix with music
    filter_parts.append(
        f"[0:a]atrim=duration={duration},"
        f"asetpts=PTS-STARTPTS,"
        f"apad=pad_dur={end_duration}[gameplay];"
        f"[2:a]atrim=start={music_start}:duration={total_duration},"
        f"volume=0.3[music];"
        f"[gameplay][music]amix=inputs=2:duration=first[aout]"
    )

    filter_complex = ';'.join(filter_parts)

    cmd = [
        'ffmpeg', '-y',
        '-i', input_video,
        '-i', end_video_path,
        '-i', music_path,
        '-filter_complex', filter_complex,
        '-map', video_output,
        '-map', '[aout]',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-r', '60',
        '-c:a', 'aac',
        '-b:a', '192k',
        output_video
    ]

    print(f"      🎬 Adding subtitles, end screen, and music...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"      ✅ Done!")
    except subprocess.CalledProcessError as e:
        print(f"      ❌ Failed!")
        print(f"      Error: {e.stderr[:500] if e.stderr else 'Unknown'}")
        raise

def process_game_shorts(game_name):
    """Add viral subtitles to all shorts"""

    global END_VIDEO, BACKGROUND_MUSIC

    clips_dir = f"games/{game_name}/clips"
    output_dir = f"games/{game_name}/output"
    final_dir = f"games/{game_name}/output_final"
    assets_dir = f"games/{game_name}/assets"

    metadata_file = f"{clips_dir}/clips_metadata.json"

    if not os.path.exists(metadata_file):
        print(f"❌ No clips metadata found")
        return

    # Check for assets
    os.makedirs(assets_dir, exist_ok=True)

    END_VIDEO = f"{assets_dir}/end.mp4"
    BACKGROUND_MUSIC = f"{assets_dir}/background_music.m4a"

    if not os.path.exists(END_VIDEO):
        print(f"❌ End video not found: {END_VIDEO}")
        print(f"   Please copy your end.mp4 to: {assets_dir}/")
        return

    if not os.path.exists(BACKGROUND_MUSIC):
        print(f"❌ Background music not found: {BACKGROUND_MUSIC}")
        print(f"   Please copy your audio file to: {assets_dir}/background_music.m4a")
        return

    os.makedirs(final_dir, exist_ok=True)

    print("=" * 60)
    print("🎬 VIRAL SUBTITLE GENERATOR V2")
    print("=" * 60)

    with open(metadata_file, 'r') as f:
        data = json.load(f)

    clips = data['clips']
    print(f"\n🎮 Game: {game_name}")
    print(f"📹 Total clips: {len(clips)}\n")

    import json as _json
    _config = f"games/{game_name}/session_config.json"
    if os.path.exists(_config):
        with open(_config) as _cf:
            platforms = _json.load(_cf).get("platforms", ["tiktok","youtube","instagram_reels","instagram_story"])
        print("   Platformlar: " + ", ".join(platforms))
    else:
        platforms = ['tiktok', 'youtube', 'instagram_reels', 'instagram_story']
    platform_specs = {
        'tiktok': {'start': 3.0, 'suffix': '_tiktok'},
        'youtube': {'start': 3.0, 'suffix': '_youtube'},
        'instagram_reels': {'start': 3.0, 'suffix': '_ig_reels'},
        'instagram_story': {'start': 2.0, 'suffix': '_ig_story'}
    }

    for i, clip in enumerate(clips, 1):
        clip_num = f"{i:02d}"
        viral_score = clip['viral_score']
        clip_title = clip['title']

        print(f"🎬 Clip {i}/{len(clips)}: {clip_title}")

        for platform in platforms:
            specs = platform_specs[platform]
            suffix = specs['suffix']
            influencer_start = specs['start']

            input_name = f"short_{clip_num}_{viral_score:.0f}{suffix}.mp4"
            input_path = f"{output_dir}/{input_name}"

            if not os.path.exists(input_path):
                print(f"   ⏭️  {platform}: Video not found")
                continue

            output_name = f"FINAL_{clip_num}_{viral_score:.0f}{suffix}.mp4"
            output_path = f"{final_dir}/{output_name}"

            print(f"   📱 {platform.upper()}:")

            # Get video duration
            duration = get_duration(input_path)

            # Calculate influencer segment (starts at influencer_start, lasts ~8s)
            influencer_end = min(influencer_start + 8.0, duration)

            # Transcribe influencer audio
            transcript = transcribe_influencer_audio(input_path, influencer_start, influencer_end)

            # Create word-by-word subtitles
            print(f"      📝 Creating viral subtitles...")
            subtitles = create_word_by_word_subtitles(transcript, influencer_start, clip_title)

            # Save subtitle data
            sub_json = f"{final_dir}/subtitles_{clip_num}_{platform}.json"
            with open(sub_json, 'w') as f:
                json.dump(subtitles, f, indent=2)

            # Add subtitles + end screen + music
            print(f"      🔍 Debug: END_VIDEO = {END_VIDEO}")
            print(f"      🔍 Debug: BACKGROUND_MUSIC = {BACKGROUND_MUSIC}")
            add_end_screen_and_music(input_path, output_path, subtitles, clip, END_VIDEO, BACKGROUND_MUSIC)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            final_duration = get_duration(output_path)
            print(f"      📊 {final_duration:.1f}s, {size_mb:.1f}MB\n")

        print()

    print("=" * 60)
    print(f"✅ SUCCESS! All final videos ready")
    print(f"📁 Output: {final_dir}/")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 add_viral_subtitles.py <game_name>")
        print("\nExample: python3 add_viral_subtitles.py monsterlab")
        sys.exit(1)

    game_name = sys.argv[1]
    process_game_shorts(game_name)