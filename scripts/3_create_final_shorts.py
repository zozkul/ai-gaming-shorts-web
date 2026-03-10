#!/usr/bin/env python3
"""Script 3: Combine gameplay clips + influencer videos"""

import os, sys, json, subprocess
from pathlib import Path

def get_duration(path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
           '-of', 'default=noprint_wrappers=1:nokey=1', path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip()) if result.stdout.strip() else 0.0

def find_gameplay_clip(clips_dir, clip_num):
    matches = list(Path(clips_dir).glob(f"clip_{clip_num:02d}_*viral*.mp4"))
    if not matches:
        matches = list(Path(clips_dir).glob(f"clip_{clip_num:02d}_*.mp4"))
        matches = [m for m in matches if 'influencer' not in m.name]
    return str(sorted(matches)[-1]) if matches else None

def create_short(influencer_video, gameplay_clip, output_path, platform='tiktok'):
    inf_dur = get_duration(influencer_video)
    game_dur = get_duration(gameplay_clip)

    platform_specs = {
        'tiktok':           {'viral_start': 4.0, 'max_dur': 15},
        'youtube':          {'viral_start': 4.0, 'max_dur': 15},
        'instagram_reels':  {'viral_start': 4.0, 'max_dur': 15},
        'instagram_story':  {'viral_start': 3.0, 'max_dur': 13},
    }
    specs = platform_specs.get(platform, platform_specs['tiktok'])
    viral_start = specs['viral_start']
    if game_dur > specs['max_dur']:
        game_dur = specs['max_dur']
    viral_end = min(viral_start + inf_dur, game_dur)

    W, H = 1080, 1920
    split_top = 700    # ~37% - yüz için daha geniş alan
    split_bot = 1220   # ~63% - gameplay

    video_filter = (
        # Seg1: Sadece gameplay (influencer başlamadan önce)
        f"[1:v]fps=60,scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:0:0,setsar=1,"
        f"trim=start=0:end={viral_start},setpts=PTS-STARTPTS[seg1];"

        # Influencer: scale et, TEPEDEN kes (y=0) → yüzü göster
        f"[0:v]fps=60,scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{split_top}:0:0,setsar=1[inf_v];"

        # Gameplay (split screen kısmı)
        f"[1:v]fps=60,scale={W}:{split_bot}:force_original_aspect_ratio=increase,"
        f"crop={W}:{split_bot}:0:0,setsar=1,"
        f"trim=start={viral_start}:end={viral_end},setpts=PTS-STARTPTS[game_v];"

        f"[inf_v][game_v]vstack=inputs=2,setsar=1[seg2];"

        # Seg3: Sadece gameplay (influencer bittikten sonra)
        f"[1:v]fps=60,scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H}:0:0,setsar=1,"
        f"trim=start={viral_end}:end={game_dur},setpts=PTS-STARTPTS[seg3];"

        f"[seg1][seg2][seg3]concat=n=3:v=1:a=0[vout]"
    )

    audio_filter = (
        f"[1:a]atrim=duration={game_dur},asetpts=PTS-STARTPTS[game_full];"
        f"[game_full]volume='if(lt(t,{viral_start}),1.0,"
        f"if(lt(t,{viral_start+0.5}),0.75,"
        f"if(lt(t,{viral_end-0.5}),0.75,"
        f"if(lt(t,{viral_end}),1.0,1.0))))'[game_mixed];"
        f"[0:a]volume=2.0,adelay={int(viral_start*1000)}|{int(viral_start*1000)},"
        f"apad=pad_dur={game_dur}[inf_full];"
        f"[game_mixed][inf_full]amix=inputs=2:duration=first[aout]"
    )

    cmd = [
        'ffmpeg', '-y',
        '-i', influencer_video,
        '-i', gameplay_clip,
        '-filter_complex', video_filter + ';' + audio_filter,
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-r', '60', '-pix_fmt', 'yuv420p',
        '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
        '-movflags', '+faststart',
        output_path
    ]

    subprocess.run(cmd, check=True, capture_output=False)

def process_game(game_name):
    clips_dir      = f"games/{game_name}/clips"
    influencer_dir = f"games/{game_name}/influencers"
    output_dir     = f"games/{game_name}/output"
    metadata_file  = f"{clips_dir}/clips_metadata.json"

    if not os.path.exists(metadata_file):
        print(f"❌ No clips metadata. Run extract first.")
        return False

    with open(metadata_file) as f:
        data = json.load(f)

    clips = data['clips']
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 60)
    print("🎬 FINAL SHORTS CREATOR")
    print("=" * 60)
    print(f"\n🎮 Game: {game_name} | 📹 {len(clips)} clips\n")

    import json as _json
    _config = f"games/{game_name}/session_config.json"
    if os.path.exists(_config):
        with open(_config) as _cf:
            platforms = _json.load(_cf).get("platforms", ["tiktok","youtube","instagram_reels","instagram_story"])
    else:
        platforms = ["tiktok","youtube","instagram_reels","instagram_story"]
    print("   Platformlar: " + ", ".join(platforms))
    platform_suffix = {
        'tiktok': '_tiktok', 'youtube': '_youtube',
        'instagram_reels': '_ig_reels', 'instagram_story': '_ig_story',
    }

    created = 0
    for i, clip in enumerate(clips, 1):
        clip_num_str = f"{i:02d}"
        title = clip.get('title', f'Clip {i}')
        viral_score = clip.get('viral_score', 8)

        influencer_path = f"{influencer_dir}/clip_{clip_num_str}_influencer.mp4"
        if not os.path.exists(influencer_path):
            print(f"⏭️  Clip {i}: No influencer video")
            continue

        gameplay_path = find_gameplay_clip(clips_dir, i)
        if not gameplay_path:
            print(f"⏭️  Clip {i}: No gameplay clip found")
            continue

        print(f"🎬 Clip {i}/{len(clips)}: {title} (score: {viral_score})")
        print(f"   🎮 {os.path.basename(gameplay_path)}")
        print(f"   🎤 clip_{clip_num_str}_influencer.mp4\n")

        for platform in platforms:
            suffix = platform_suffix[platform]
            output_name = f"short_{clip_num_str}_{viral_score:.0f}{suffix}.mp4"
            output_path = f"{output_dir}/{output_name}"
            print(f"   📱 {platform.upper()}...", end=' ', flush=True)
            try:
                create_short(influencer_path, gameplay_path, output_path, platform=platform)
                dur = get_duration(output_path)
                mb = os.path.getsize(output_path) / (1024*1024)
                print(f"✅ {dur:.1f}s, {mb:.1f}MB")
                created += 1
            except Exception as e:
                print(f"❌ {e}")
        print()

    print("=" * 60)
    print(f"✅ Created {created} shorts → {output_dir}/")
    if created > 0:
        print(f"NEXT: python3 AUTOMATION_MASTER.py {game_name} finalize")
    print("=" * 60)
    return created > 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 3_create_final_shorts.py <game_name>")
        sys.exit(1)
    process_game(sys.argv[1])
