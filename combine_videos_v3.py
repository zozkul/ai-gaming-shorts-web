#!/usr/bin/env python3
import subprocess, os, json

def get_duration(path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', path]
    return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())

def create_srt(commentary, path):
    srt = []
    intro = commentary.get('intro_display', '')[:50]
    srt.append(f"1\n00:00:00,000 --> 00:00:03,000\n{intro}\n")
    
    for i, r in enumerate(commentary.get('reactions', []), 2):
        ts = int(r['timestamp'])
        text = r.get('display_text', '')[:40]
        srt.append(f"{i}\n00:00:{ts:02d},000 --> 00:00:{ts+2:02d},500\n{text}\n")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(srt))
    return path

print("🎬 Creating vertical short (30% influencer / 70% gameplay)...")

inf = "temp/gameplay_influencer.mp4"
game = "input/gameplay.mp4"
out = "output/final_short_v3.mp4"

dur = max(get_duration(inf), get_duration(game))
print(f"⏱️  Duration: {dur:.1f}s")

w, h = 1080, 1920
top_h = int(h * 0.30)
bot_h = h - top_h

print(f"📐 Layout: Top={top_h}px (30%), Bottom={bot_h}px (70%)")

sub_file = None
try:
    with open('input/gameplay_commentary_v3.json', 'r') as f:
        commentary = json.load(f)
    sub_file = "temp/subs_v3.srt"
    create_srt(commentary, sub_file)
    print("✅ Subtitles created")
except:
    print("⚠️  No subtitles")

filt = (
    f'[0:v]scale={w}:{top_h}:force_original_aspect_ratio=increase,'
    f'crop={w}:{top_h},setpts=PTS-STARTPTS,loop=-1:1:0[top];'
    f'[1:v]scale={w}:{bot_h}:force_original_aspect_ratio=increase,'
    f'crop={w}:{bot_h},setpts=PTS-STARTPTS,loop=-1:1:0[bot];'
    f'[top][bot]vstack[stack];'
)

if sub_file and os.path.exists(sub_file):
    sub_esc = sub_file.replace('\\', '\\\\').replace(':', '\\:')
    filt += (
        f"[stack]subtitles='{sub_esc}':force_style='"
        f"FontName=Helvetica Neue,FontSize=20,Bold=1,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,BorderStyle=4,Outline=2,Shadow=1,"
        f"Alignment=2,MarginV=80'[v]"
    )
    map_v = '[v]'
else:
    map_v = '[stack]'

cmd = [
    'ffmpeg', '-y', '-i', inf, '-i', game,
    '-filter_complex', filt,
    '-map', map_v, '-map', '0:a?',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
    '-c:a', 'aac', '-b:a', '192k',
    '-t', str(dur), out
]

os.makedirs('output', exist_ok=True)
print("🎞️  Rendering...")

subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
size = os.path.getsize(out) / (1024 * 1024)

print(f"\n✅ SUCCESS!\n📱 {out}\n💾 {size:.1f}MB")
print("✅ 30% influencer (top)\n✅ 70% gameplay (bottom)\n✅ Small subtitles\n✅ No black bars")
