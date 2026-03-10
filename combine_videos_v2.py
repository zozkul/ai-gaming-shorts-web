#!/usr/bin/env python3
import subprocess
import os
import json

def get_video_duration(video_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def create_subtitle_file(commentary, output_path):
    srt_content = []
    counter = 1
    
    # Intro
    intro_text = commentary.get('intro_display', commentary.get('intro', ''))[:60]
    srt_content.append(f"{counter}\n00:00:00,000 --> 00:00:03,500\n{intro_text}\n")
    counter += 1
    
    # Reactions
    for reaction in commentary.get('reactions', []):
        ts = int(reaction['timestamp'])
        display = reaction.get('display_text', reaction.get('text', ''))[:70]
        srt_content.append(f"{counter}\n00:00:{ts:02d},000 --> 00:00:{ts+3:02d},000\n{display}\n")
        counter += 1
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt_content))
    return output_path

print("🎬 Creating professional vertical short (v2)...")

influencer = "temp/gameplay_influencer.mp4"
gameplay = "input/gameplay.mp4"
output = "output/final_short_v2.mp4"

inf_dur = get_video_duration(influencer)
game_dur = get_video_duration(gameplay)
target_dur = max(inf_dur, game_dur)

print(f"⏱️  Durations: Influencer={inf_dur:.1f}s, Gameplay={game_dur:.1f}s, Target={target_dur:.1f}s")

# Create subtitles
subtitle_file = None
try:
    with open('input/gameplay_commentary_v2.json', 'r') as f:
        commentary = json.load(f)
    subtitle_file = "temp/subtitles.srt"
    create_subtitle_file(commentary, subtitle_file)
    print(f"✅ Subtitles created")
except:
    print("⚠️  No commentary, skipping subtitles")

width = 1080
height = 1920
top_h = int(height * 0.7)
bottom_h = height - top_h

print(f"📐 Layout: {width}x{height}, Top={top_h}px, Bottom={bottom_h}px")

# FFmpeg filter - CROP TO FILL (no black bars)
filter_complex = (
    f'[0:v]scale={width}:{top_h}:force_original_aspect_ratio=increase,'
    f'crop={width}:{top_h},setpts=PTS-STARTPTS,loop=loop=-1:size=1:start=0[top];'
    f'[1:v]scale={width}:{bottom_h}:force_original_aspect_ratio=increase,'
    f'crop={width}:{bottom_h},setpts=PTS-STARTPTS,loop=loop=-1:size=1:start=0[bottom];'
    f'[top][bottom]vstack=inputs=2[stacked];'
)

if subtitle_file and os.path.exists(subtitle_file):
    sub_esc = subtitle_file.replace('\\', '\\\\').replace(':', '\\:')
    filter_complex += (
        f"[stacked]subtitles='{sub_esc}':force_style='"
        f"FontName=Arial Bold,FontSize=28,Bold=1,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,BorderStyle=3,Outline=3,Shadow=2,MarginV=50'[v]"
    )
    map_v = '[v]'
else:
    map_v = '[stacked]'

cmd = [
    'ffmpeg', '-y',
    '-i', influencer,
    '-i', gameplay,
    '-filter_complex', filter_complex,
    '-map', map_v,
    '-map', '0:a?',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
    '-c:a', 'aac', '-b:a', '192k',
    '-t', str(target_dur),
    output
]

os.makedirs('output', exist_ok=True)
print(f"\n🎞️  Rendering...")

try:
    subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
    final_dur = get_video_duration(output)
    size_mb = os.path.getsize(output) / (1024 * 1024)
    
    print(f"\n✅ SUCCESS!")
    print(f"📱 {output}")
    print(f"⏱️  {final_dur:.1f}s")
    print(f"💾 {size_mb:.1f}MB")
    print(f"\n🎉 Features:")
    print(f"✅ No black bars (cropped)")
    print(f"✅ Full duration")
    print(f"✅ Vertical 9:16")
    if subtitle_file:
        print(f"✅ Subtitles included")
except subprocess.CalledProcessError as e:
    print(f"\n❌ Error: {e.stderr.decode() if e.stderr else 'Unknown'}")
    exit(1)
