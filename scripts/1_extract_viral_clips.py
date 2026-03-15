#!/usr/bin/env python3
"""
Script 1: Extract Viral Clips from Long Gameplay
Analyzes long gameplay videos and extracts viral moments
"""

import os
import sys
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv
import subprocess

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_video_duration(video_path):
    """Get video duration in seconds"""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_frames(video_path, num_frames=10):
    """Extract frames from video for analysis using FFmpeg (memory efficient)."""
    import tempfile, shutil

    # Get duration via ffprobe
    probe = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True
    )
    duration = float(probe.stdout.strip())

    frames = []
    timestamps = []
    tmpdir = tempfile.mkdtemp()

    try:
        # Extract frames one-by-one via FFmpeg (no large video buffer in RAM)
        for i in range(num_frames):
            ts = duration * i / num_frames
            out_path = os.path.join(tmpdir, f"frame_{i}.jpg")
            subprocess.run(
                ['ffmpeg', '-y', '-ss', str(ts), '-i', video_path,
                 '-vframes', '1', '-q:v', '6', '-vf', 'scale=640:-1', out_path],
                capture_output=True
            )
            if os.path.exists(out_path):
                with open(out_path, 'rb') as f:
                    b64_frame = base64.b64encode(f.read()).decode('utf-8')
                frames.append(b64_frame)
                timestamps.append(ts)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

    return frames, timestamps, duration

def analyze_for_viral_moments(video_path, game_name, max_clips=5):
    """Use GPT-4o Vision to find viral moments"""
    print(f"\n🔍 Analyzing: {os.path.basename(video_path)}")
    print(f"🎮 Game: {game_name}")

    frames, timestamps, duration = extract_frames(video_path)
    print(f"⏱️  Duration: {duration:.1f}s")
    print(f"📸 Extracted {len(frames)} frames for analysis\n")

    # Build GPT-4o Vision request
    messages = [
        {
            "role": "system",
            "content": f"You are an expert at identifying viral gaming moments for {game_name}. Find the most exciting, shareable clips."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Analyze this {game_name} gameplay video ({duration:.0f} seconds).

TASK: Identify exactly {max_clips} VIRAL moments perfect for TikTok/Reels/Shorts (12-13 second clips).

CRITICAL: Clips MUST be 12-13 seconds! Include BUILD-UP + ACTION + REACTION for maximum engagement.

Look for COMPLETE story moments:
- Multi-kills: Show approach → kills → aftermath (12-13s)
- Clutch moments: Show setup → clutch action → victory (12-13s)
- Insane plays: Show aim → shot → reaction (12-13s)
- Funny moments: Show setup → punchline → laugh (12-13s)
- Close calls: Show danger → escape → relief (12-13s)
- Victory: Show final push → win → celebration (12-13s)

IMPORTANT: Each clip should tell a COMPLETE mini-story with:
- Opening (2-3s): Set the scene, build anticipation
- Peak moment (5-7s): The main action/highlight
- Closing (2-3s): Reaction, aftermath, or payoff

Return JSON:
{{
  "clips": [
    {{
      "start_time": <seconds>,
      "end_time": <seconds>,
      "title": "compelling title (5-10 words)",
      "description": "full story arc of what happens",
      "viral_score": <1-10>,
      "tags": ["action", "clutch", "insane"],
      "peak_moment": <timestamp of best frame>,
      "emotion": "excited/shocked/hyped",
      "optimal_duration": <12-13 seconds>
    }}
  ]
}}

Order by viral_score (highest first). Each clip EXACTLY 12-13 seconds for complete storytelling!"""
                }
            ]
        }
    ]

    # Add frames
    for i, (frame, ts) in enumerate(zip(frames, timestamps)):
        messages[1]["content"].append({"type": "text", "text": f"\n[Frame {i+1} at {ts:.1f}s]"})
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{frame}",
                "detail": "low"
            }
        })

    print("🤖 Sending to GPT-4o Vision...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=2000,
        temperature=0.7
    )

    result = response.choices[0].message.content

    # Parse JSON
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].split("```")[0].strip()

    return json.loads(result)

def extract_clip(video_path, start_time, end_time, output_path):
    """Extract a clip from video"""
    # Use more robust settings: re-encode to avoid codec issues
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', video_path,
        '-t', str(end_time - start_time),
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '26',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-ar', '48000',
        '-ac', '2',
        '-movflags', '+faststart',
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=False, text=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed with code {e.returncode}")
        print(f"   Command: {' '.join(cmd)}")
        raise

def process_game_video(game_name, video_filename, max_clips=5):
    """Process a gameplay video"""
    base_dir = f"games/{game_name}"
    video_path = f"{base_dir}/raw/{video_filename}"

    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return

    os.makedirs(f"{base_dir}/clips", exist_ok=True)

    print("=" * 60)
    print("🎬 VIRAL CLIP EXTRACTOR")
    print("=" * 60)

    # Analyze video
    analysis = analyze_for_viral_moments(video_path, game_name, max_clips=max_clips)
    clips = analysis['clips']

    print(f"\n✅ Found {len(clips)} viral moments!\n")

    # Extract clips
    extracted_clips = []
    for i, clip in enumerate(clips, 1):
        viral_score = clip['viral_score']
        clip_name = f"clip_{i:02d}_{viral_score:.0f}_viral"
        clip_path = f"{base_dir}/clips/{clip_name}.mp4"

        print(f"🎬 Extracting clip {i}/{len(clips)}")
        print(f"   Title: {clip['title']}")
        print(f"   Time: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s ({clip['end_time']-clip['start_time']:.1f}s)")
        print(f"   Viral Score: {viral_score}/10")

        extract_clip(video_path, clip['start_time'], clip['end_time'], clip_path)

        clip['filename'] = f"{clip_name}.mp4"
        extracted_clips.append(clip)

        print(f"   ✅ Saved: {clip_name}.mp4\n")

    # Save all clip metadata
    metadata_path = f"{base_dir}/clips/clips_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({
            'source_video': video_filename,
            'game': game_name,
            'total_clips': len(extracted_clips),
            'clips': extracted_clips
        }, f, indent=2)

    print("=" * 60)
    print(f"✅ SUCCESS! Extracted {len(clips)} viral clips")
    print(f"📁 Clips: {base_dir}/clips/")
    print(f"📄 Metadata: {metadata_path}")
    print("=" * 60)

    return extracted_clips

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 1_extract_viral_clips.py <game_name> <video_filename>")
        print("\nExample: python3 1_extract_viral_clips.py valorant my_gameplay.mp4")
        print("\nAvailable games: valorant, fortnite, apex")
        sys.exit(1)

    game_name = sys.argv[1]
    video_filename = sys.argv[2]
    max_clips = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    process_game_video(game_name, video_filename, max_clips=max_clips)
