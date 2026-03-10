import os, json, sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def fix_pronunciation(text):
    replacements = {
        'NO WAY': 'no way', 'WOAH': 'woah', 'INSANE': 'insane',
        'YOOO': 'yo', 'NOO': 'no', 'OMG': 'oh my god'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def generate_commentary(analysis):
    print("💬 Generating game-focused commentary...")
    highlights = analysis.get('highlights', [])
    summary = analysis.get('summary', '')

    prompt = f"""You are a gaming content creator promoting an upcoming game.

Video: {summary}

Create commentary focused on the GAME itself (NOT follow/like requests):
- Talk about gameplay mechanics, features, release date
- Use phrases like "coming soon", "releasing soon", "available soon"
- Hype the game, not your channel
- NO "follow me", "like", "subscribe" - focus on the GAME

JSON format with TTS-friendly text:
{{
    "intro": "Check out this upcoming game! It's releasing soon...",
    "intro_display": "NEW GAME COMING SOON! 🎮",
    "reactions": [
        {{
            "timestamp": 6.0,
            "text": "woah, look at these graphics! This releases next month",
            "display_text": "RELEASING NEXT MONTH 🔥",
            "emotion": "excited",
            "energy_level": 8
        }}
    ],
    "outro": "This game launches in two weeks, don't miss it!",
    "outro_display": "LAUNCHES IN 2 WEEKS ⚡"
}}

CRITICAL: lowercase in "text" for TTS!"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You promote upcoming games, not social media."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    result = response.choices[0].message.content
    if "```json" in result:
        result = result.split("```json")[1].split("```")[0].strip()
    
    commentary = json.loads(result)
    commentary['intro'] = fix_pronunciation(commentary.get('intro', ''))
    commentary['outro'] = fix_pronunciation(commentary.get('outro', ''))
    for r in commentary.get('reactions', []):
        r['text'] = fix_pronunciation(r['text'])
    
    return commentary

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 3_generate_commentary_EN_v3.py input/video_analysis.json")
        sys.exit(1)
    
    with open(sys.argv[1], 'r') as f:
        analysis = json.load(f)
    
    commentary = generate_commentary(analysis)
    output = sys.argv[1].replace('_analysis.json', '_commentary_v3.json')
    
    with open(output, 'w') as f:
        json.dump(commentary, f, indent=2)
    
    print(f"✅ Saved: {output}")
EOF,cat > combine_videos_v3.py << 'EOF'
#!/usr/bin/env python3
import subprocess, os, json

def get_duration(path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', path]
    return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())

def create_srt(commentary, path):
    srt = []
    # Intro (top of screen, small)
    intro = commentary.get('intro_display', '')[:50]
    srt.append(f"1\n00:00:00,000 --> 00:00:03,000\n{intro}\n")
    
    # Reactions
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

# Layout: 30% top (influencer), 70% bottom (gameplay)
w, h = 1080, 1920
top_h = int(h * 0.30)  # 30%
bot_h = h - top_h       # 70%

print(f"📐 Layout: Top={top_h}px (30%), Bottom={bot_h}px (70%)")

# Subtitles
sub_file = None
try:
    with open('input/gameplay_commentary_v3.json', 'r') as f:
        commentary = json.load(f)
    sub_file = "temp/subs_v3.srt"
    create_srt(commentary, sub_file)
    print("✅ Subtitles created")
except:
    print("⚠️  No subtitles")

# Filter: crop to fill, small readable subtitles
filt = (
    f'[0:v]scale={w}:{top_h}:force_original_aspect_ratio=increase,'
    f'crop={w}:{top_h},setpts=PTS-STARTPTS,loop=-1:1:0[top];'
    f'[1:v]scale={w}:{bot_h}:force_original_aspect_ratio=increase,'
    f'crop={w}:{bot_h},setpts=PTS-STARTPTS,loop=-1:1:0[bot];'
    f'[top][bot]vstack[stack];'
)

if sub_file and os.path.exists(sub_file):
    sub_esc = sub_file.replace('\\', '\\\\').replace(':', '\\:')
    # Smaller, modern font at TOP (won't cover gameplay)
    filt += (
        f"[stack]subtitles='{sub_esc}':force_style='"
        f"FontName=Helvetica Neue,FontSize=20,Bold=1,PrimaryColour=&HFFFFFF,"
        f"OutlineColour=&H000000,BorderStyle=4,Outline=2,Shadow=1,"
        f"Alignment=2,MarginV=80'[v]"  # Alignment=2 = top center, MarginV=80 keeps it in influencer area
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
print("✅ 30% influencer (top)\n✅ 70% gameplay (bottom)\n✅ Small subtitles (top area)\n✅ No black bars")
