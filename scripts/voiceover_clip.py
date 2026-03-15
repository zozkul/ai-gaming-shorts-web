#!/usr/bin/env python3
import os, sys, json, subprocess, re, tempfile
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_duration(path):
    cmd = ['ffprobe','-v','error','-show_entries','format=duration',
           '-of','default=noprint_wrappers=1:nokey=1', path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0

def auto_generate_commentary(clip, game_name):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"Write short viral gaming commentary for TikTok. English. Natural streamer voice. Max 10 seconds (~25 words). Return ONLY spoken text."},
            {"role":"user","content":f"Game: {game_name}\nTitle: {clip.get('title','')}\nDesc: {clip.get('description','')}\nEmotion: {clip.get('emotion','excited')}"}
        ],
        max_tokens=80, temperature=0.9
    )
    return response.choices[0].message.content.strip()

def text_to_speech(text, output_path, voice="y8mBjGEqtMV3PO41kDm0", voice_settings=None):
    import requests as _req
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY .env dosyasinda bulunamadi!")
    if voice_settings is None:
        voice_settings = {"stability":0.5,"similarity_boost":0.5,"style":0.5,"use_speaker_boost":True,"speed":1.1}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {"Accept":"audio/mpeg","Content-Type":"application/json","xi-api-key":api_key}
    body = {"text":text,"model_id":"eleven_v3","voice_settings":voice_settings}
    r = _req.post(url, json=body, headers=headers)
    if r.status_code != 200:
        raise Exception(f"ElevenLabs error {r.status_code}: {r.text[:200]}")
    with open(output_path,"wb") as f:
        f.write(r.content)
    print(f"   ElevenLabs TTS OK ({len(text)} chars, {os.path.getsize(output_path)//1024}KB)")

def get_word_timestamps(audio_path, language=None):
    with open(audio_path,'rb') as f:
        kwargs = dict(
            model="whisper-1", file=f,
            response_format="verbose_json",
            timestamp_granularities=["word"]
        )
        if language:
            kwargs["language"] = language
        t = client.audio.transcriptions.create(**kwargs)
    return t.words or []

import platform as _platform
if _platform.system() == "Windows":
    IMPACT_FONT = "C:/Windows/Fonts/impact.ttf"
    UNICODE_FONT = "C:/Windows/Fonts/arial.ttf"
else:
    IMPACT_FONT = "/System/Library/Fonts/Supplemental/Impact.ttf"
    UNICODE_FONT = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"

def _ffmpeg_safe(text):
    """Escape characters unsafe for FFmpeg drawtext while preserving Unicode (Turkish etc.)"""
    text = re.sub(r"[':!?\\]", "", text)
    return text

def _pick_font(text):
    """Use Arial Unicode if text contains non-ASCII (e.g. Turkish), else Impact."""
    try:
        text.encode('ascii')
        return IMPACT_FONT
    except UnicodeEncodeError:
        return UNICODE_FONT

def build_subtitle_filter(words, clip_title, audio_start=0.5):
    filters = []
    safe_title = _ffmpeg_safe(clip_title.upper())[:30]
    title_font = _pick_font(safe_title)
    if safe_title:
        filters.append(
            f"drawtext=fontfile='{title_font}':"
            f"text='{safe_title}':fontsize=70:fontcolor=yellow:bordercolor=black:borderw=8:"
            f"x=(w-text_w)/2:y=h-200:enable='between(t,0,{audio_start})'"
        )
    for w in words:
        word = _ffmpeg_safe(w.word.strip().upper()).strip()
        if len(word) < 2:
            continue
        start = audio_start + w.start
        end   = audio_start + w.end
        dur   = end - start
        color = '#FFFF00' if any(e in word for e in ['NO','WOW','INSANE','CRAZY','WHAT','OH','YES','BOOM','GO','WAIT','YOK','VAY','INAN','DELI','NE','AY','EVET','PATLADI','GIT','DUR']) else 'white'
        shadow = '#FF6B00' if color == '#FFFF00' else '#0080FF'
        shake = 5 if dur < 0.4 else 2
        word_font = _pick_font(word)
        filters.append(
            f"drawtext=fontfile='{word_font}':"
            f"text='{word}':fontsize=100:fontcolor={shadow}:"
            f"x='(w-text_w)/2+sin((t-{start})*20)*{shake}+4':y='h-200+4':"
            f"enable='between(t,{start},{end})':alpha='0.8'"
        )
        filters.append(
            f"drawtext=fontfile='{word_font}':"
            f"text='{word}':fontsize=100:fontcolor={color}:bordercolor=black:borderw=10:"
            f"x='(w-text_w)/2+sin((t-{start})*20)*{shake}':y='h-200':"
            f"enable='between(t,{start},{end})'"
        )
    return ','.join(filters)

def create_voiceover_video(gameplay_clip, tts_audio, words, clip_title, output_path):
    game_dur  = get_duration(gameplay_clip)
    audio_dur = get_duration(tts_audio)
    audio_start = 0.5
    total_dur = round(audio_dur + audio_start + 0.3, 2)
    print(f"   Gameplay: {game_dur:.1f}s | TTS: {audio_dur:.1f}s | Cikis: {total_dur:.1f}s")

    subtitle_filter = build_subtitle_filter(words, clip_title, audio_start)
    overlay_end = f",{subtitle_filter}[vout]" if subtitle_filter else ",setsar=1[vout]"

    # Clamp total_dur to gameplay clip length
    total_dur = min(total_dur, game_dur)

    filter_complex = (
        # Explicit split to avoid ffmpeg auto-split issues (prevents choppy output)
        f"[0:v]trim=duration={total_dur},setpts=PTS-STARTPTS,split=2[v1][v2];"
        # Background: fill portrait frame with blurred gameplay
        f"[v1]scale=1080:1920:force_original_aspect_ratio=increase,"
        f"crop=1080:1920,gblur=sigma=20,setsar=1[bg];"
        # Foreground: gameplay letterboxed to fit portrait width
        f"[v2]scale=1080:-2,setsar=1[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2{overlay_end};"
        # Audio: boost game audio, mix with TTS
        f"[0:a]atrim=duration={total_dur},asetpts=PTS-STARTPTS,volume=1.5[game_a];"
        f"[1:a]volume=2.5,adelay={int(audio_start*1000)}|{int(audio_start*1000)}[tts_a];"
        f"[game_a][tts_a]amix=inputs=2:duration=longest:normalize=0[aout]"
    )
    # Write filter_complex to a temp file to avoid Windows command line length limit
    fc_file = os.path.join(tempfile.gettempdir(), "fc_filter.txt")
    with open(fc_file, "w", encoding="utf-8") as f:
        f.write(filter_complex)
    cmd = [
        "ffmpeg", "-y",
        "-i", gameplay_clip,
        "-i", tts_audio,
        "-filter_complex_script", fc_file,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-t", str(total_dur),
        output_path
    ]
    subprocess.run(cmd, check=True, capture_output=False)

def process_voiceover(game_name, text_input=None, voice="y8mBjGEqtMV3PO41kDm0", platforms=None, voice_settings=None):
    clips_dir  = f"games/{game_name}/clips"
    output_dir = f"games/{game_name}/output"
    os.makedirs(output_dir, exist_ok=True)

    if platforms is None:
        config_file = f"games/{game_name}/session_config.json"
        if os.path.exists(config_file):
            with open(config_file) as cf:
                platforms = json.load(cf).get("platforms",["tiktok","youtube","instagram_reels","instagram_story"])
        else:
            platforms = ["tiktok","youtube","instagram_reels","instagram_story"]
    print(f"   Platformlar: {', '.join(platforms)}")

    metadata_file = f"{clips_dir}/clips_metadata.json"
    if not os.path.exists(metadata_file):
        print("No clips metadata. Run extract first.")
        return False

    with open(metadata_file) as f:
        data = json.load(f)
    clips = data['clips']

    print("="*60)
    print(f"VOICEOVER MODE | {game_name} | {len(clips)} clips | voice: {voice}")
    print("="*60)

    platform_suffix = {
        "tiktok":"_tiktok","youtube":"_youtube",
        "instagram_reels":"_ig_reels","instagram_story":"_ig_story"
    }

    created = 0
    for i, clip in enumerate(clips, 1):
        clip_num = f"{i:02d}"
        title    = clip.get('title', f'Clip {i}')
        score    = clip.get('viral_score', 8)

        matches = list(Path(clips_dir).glob(f"clip_{clip_num}_*viral*.mp4"))
        if not matches:
            matches = [m for m in Path(clips_dir).glob(f"clip_{clip_num}_*.mp4") if 'influencer' not in m.name]
        if not matches:
            print(f"Clip {i}: gameplay bulunamadi")
            continue

        gameplay_path = str(sorted(matches)[-1])
        print(f"\nClip {i}/{len(clips)}: {title}")

        if text_input:
            commentary = text_input
        else:
            print(f"   GPT-4o ile yorum uretiliyor...")
            commentary = auto_generate_commentary(clip, game_name)
        print(f"   Yorum: {commentary[:80]}")

        tts_path = os.path.join(tempfile.gettempdir(), f"tts_{game_name}_{clip_num}.mp3")
        text_to_speech(commentary, tts_path, voice=voice, voice_settings=voice_settings)

        print(f"   Whisper ile timestamp aliniyor...")
        # Auto-detect language for manual input (e.g. Turkish); force English for auto-generated commentary
        whisper_lang = None if text_input else "en"
        words = get_word_timestamps(tts_path, language=whisper_lang)
        print(f"   {len(words)} kelime")

        for platform in platforms:
            suffix = platform_suffix.get(platform, f"_{platform}")
            output_name = f"short_{clip_num}_{score:.0f}{suffix}.mp4"
            output_path = f"{output_dir}/{output_name}"
            print(f"   {platform.upper()}...", end=' ', flush=True)
            try:
                create_voiceover_video(gameplay_path, tts_path, words, title, output_path)
                dur = get_duration(output_path)
                mb  = os.path.getsize(output_path)/(1024*1024)
                print(f"OK {dur:.1f}s, {mb:.1f}MB")
                created += 1
            except Exception as e:
                print(f"HATA: {e}")

        if os.path.exists(tts_path):
            os.remove(tts_path)

    print("\n"+"="*60)
    print(f"Tamamlandi: {created} video -> {output_dir}/")
    if created > 0:
        print(f"NEXT: python3 AUTOMATION_MASTER.py {game_name} finalize")
    print("="*60)
    return created > 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/voiceover_clip.py <game_name> [voice_id]")
        sys.exit(1)
    process_voiceover(sys.argv[1], voice=sys.argv[2] if len(sys.argv)>2 else "y8mBjGEqtMV3PO41kDm0")
