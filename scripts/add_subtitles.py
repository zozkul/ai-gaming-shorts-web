#!/usr/bin/env python3
"""
Add viral-style subtitles to gaming shorts
- Influencer reactions (top - emotional)
- Gameplay narration (bottom - story)
"""

import os
import sys
import json
import subprocess
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_duration(video_path):
    """Get video duration"""
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def generate_subtitles(clip_metadata, video_duration):
    """Generate subtitles using GPT-4o"""

    title = clip_metadata.get('title', '')
    description = clip_metadata.get('description', '')
    emotion = clip_metadata.get('emotion', 'excited')

    prompt = f"""Create viral TikTok/Reels subtitles for this {video_duration:.0f}s gaming clip.

CLIP INFO:
- Title: {title}
- Description: {description}
- Emotion: {emotion}
- Duration: {video_duration:.0f}s

RULES:
1. TWO LAYERS:
   - TOP (Influencer): Emotional reactions (2-3 words max)
   - BOTTOM (Gameplay): Story/action (4-6 words max)

2. NEVER repeat same content in both layers
   - TOP = emotion/reaction
   - BOTTOM = what's happening

3. DO NOT USE EMOJIS (they break the system)

4. Timing:
   - Short bursts: 0.8-1.5s each
   - Sync with action peaks
   - Leave 0.2s gaps between subtitles

EXAMPLES:

Example 1 (Clutch moment):
TOP: "NO WAY" (0.0-1.2s)
BOTTOM: "LAST PLAYER STANDING" (0.0-1.5s)
TOP: "BROOO" (2.0-3.0s)
BOTTOM: "INSANE HEADSHOT" (2.5-4.0s)

Example 2 (Multi-kill):
BOTTOM: "ENEMY SPOTTED" (0.0-1.0s)
TOP: "WAIT WAIT" (1.2-2.2s)
BOTTOM: "TRIPLE KILL INCOMING" (1.5-3.0s)
TOP: "YESSS" (3.2-4.5s)

Return JSON:
{{
  "subtitles": [
    {{
      "layer": "top",
      "text": "NO WAY",
      "start": 0.0,
      "end": 1.2
    }},
    {{
      "layer": "bottom",
      "text": "LAST PLAYER STANDING",
      "start": 0.0,
      "end": 1.5
    }}
  ]
}}

Create {int(video_duration * 1.2)} subtitle entries (mix of top and bottom)."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You create viral gaming subtitles. NO EMOJIS."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    result = response.choices[0].message.content

    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    elif "```" in result:
        result = result.split("```")[1].split("```")[0].strip()

    return json.loads(result)

def create_subtitle_filter(subtitles, video_duration):
    """Create FFmpeg drawtext filters for subtitles"""

    filters = []

    for sub in subtitles:
        # Clean text: remove emojis and special chars
        text = sub['text'].upper()
        # Remove emojis and special characters that break FFmpeg
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = text.strip()

        if not text:
            continue

        start = sub['start']
        end = sub['end']
        layer = sub['layer']

        # Escape special characters for FFmpeg
        text = text.replace("'", "\\'").replace(":", "\\:")

        # Position based on layer
        if layer == 'top':
            # Top layer - influencer reactions (chest level)
            y_pos = 450
            fontsize = 52
        else:
            # Bottom layer - gameplay story (safe zone)
            y_pos = 1550
            fontsize = 95

        # Calculate fade times
        fade_in_end = start + 0.15
        fade_out_start = end - 0.15

        # Standard subtitle
        filter_text = (
            f"drawtext=fontfile=/System/Library/Fonts/Supplemental/Arial\\ Bold.ttf:"
            f"text='{text}':"
            f"fontsize={fontsize}:"
            f"fontcolor=white:"
            f"bordercolor=black:"
            f"borderw=5:"
            f"x=(w-text_w)/2:"
            f"y={y_pos}:"
            f"enable='between(t\\,{start}\\,{end})':"
            f"alpha='if(lt(t\\,{fade_in_end})\\,(t-{start})/0.15\\,"
            f"if(lt(t\\,{fade_out_start})\\,1\\,({end}-t)/0.15))'"
        )
        filters.append(filter_text)

    return ','.join(filters)

def add_subtitles_to_video(input_video, output_video, subtitles):
    """Add subtitles to video using FFmpeg"""

    duration = get_duration(input_video)

    # Create subtitle filter
    subtitle_filter = create_subtitle_filter(subtitles['subtitles'], duration)

    if not subtitle_filter:
        print(f"   ⚠️  No valid subtitles generated")
        # Copy video without subtitles
        import shutil
        shutil.copy(input_video, output_video)
        return

    cmd = [
        'ffmpeg', '-y',
        '-i', input_video,
        '-vf', subtitle_filter,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_video
    ]

    print(f"   📝 Adding subtitles...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"   ✅ Subtitles added!")
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed to add subtitles")
        stderr = e.stderr.decode() if e.stderr else 'Unknown'
        print(f"   Error: {stderr[:500]}")
        raise

def process_game_shorts(game_name):
    """Add subtitles to all shorts for a game"""

    clips_dir = f"games/{game_name}/clips"
    output_dir = f"games/{game_name}/output"
    subtitled_dir = f"games/{game_name}/output_subtitled"

    metadata_file = f"{clips_dir}/clips_metadata.json"

    if not os.path.exists(metadata_file):
        print(f"❌ No clips metadata found")
        return

    os.makedirs(subtitled_dir, exist_ok=True)

    print("=" * 60)
    print("📝 SUBTITLE GENERATOR")
    print("=" * 60)

    # Load clip metadata
    with open(metadata_file, 'r') as f:
        data = json.load(f)

    clips = data['clips']
    print(f"\n🎮 Game: {game_name}")
    print(f"📹 Total clips: {len(clips)}\n")

    # Process each clip's shorts
    platforms = ['tiktok', 'youtube', 'instagram_reels', 'instagram_story']

    for i, clip in enumerate(clips, 1):
        clip_num = f"{i:02d}"
        viral_score = clip['viral_score']

        print(f"🎬 Clip {i}/{len(clips)}: {clip['title']}")

        for platform in platforms:
            # Find the video file
            platform_suffix = {
                'tiktok': '_tiktok',
                'youtube': '_youtube',
                'instagram_reels': '_ig_reels',
                'instagram_story': '_ig_story'
            }[platform]

            input_name = f"short_{clip_num}_{viral_score:.0f}{platform_suffix}.mp4"
            input_path = f"{output_dir}/{input_name}"

            if not os.path.exists(input_path):
                print(f"   ⏭️  {platform}: Video not found, skipping")
                continue

            output_name = f"short_{clip_num}_{viral_score:.0f}{platform_suffix}_SUBTITLED.mp4"
            output_path = f"{subtitled_dir}/{output_name}"

            print(f"   📱 {platform.upper()}: Processing...")

            # Get video duration
            duration = get_duration(input_path)

            # Generate subtitles
            print(f"      🤖 Generating subtitles...")
            subtitles = generate_subtitles(clip, duration)

            # Save subtitle metadata
            subtitle_json = f"{subtitled_dir}/subtitles_{clip_num}_{platform}.json"
            with open(subtitle_json, 'w') as f:
                json.dump(subtitles, f, indent=2)

            # Add subtitles to video
            add_subtitles_to_video(input_path, output_path, subtitles)

            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"      ✅ Done! {size_mb:.1f}MB\n")

        print()

    print("=" * 60)
    print(f"✅ SUCCESS! All subtitles added")
    print(f"📁 Output: {subtitled_dir}/")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 add_subtitles.py <game_name>")
        print("\nExample: python3 add_subtitles.py monsterlab")
        sys.exit(1)

    game_name = sys.argv[1]
    process_game_shorts(game_name)