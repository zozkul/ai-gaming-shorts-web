#!/usr/bin/env python3
"""Auto-generate influencer videos with Gemini Veo3 API"""
import os, sys, json, time
from dotenv import load_dotenv
load_dotenv()

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("❌ Install: pip install google-genai")
    sys.exit(1)

API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    print("❌ GEMINI_API_KEY not found in .env")
    sys.exit(1)

client = genai.Client(api_key=API_KEY)

def generate_video(prompt, output_path, clip_num):
    print(f"   🎬 Generating video with Veo3...")
    print(f"   📝 {prompt[:120]}...")
    try:
        operation = client.models.generate_videos(
            model="veo-3.0-generate-001",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio="9:16",
                duration_seconds=8,
                number_of_videos=1,
            ),
        )
        print(f"   ⏳ Waiting for generation (this takes ~2-5 min)...")
        waited = 0
        while not operation.done:
            time.sleep(20)
            waited += 20
            operation = client.operations.get(operation)
            print(f"   ⏳ {waited}s elapsed...")

        if operation.response and operation.response.generated_videos:
            video = operation.response.generated_videos[0].video
            print(f"   💾 Downloading video...")
            video_bytes = client.files.download(file=video)
            with open(output_path, 'wb') as f:
                f.write(video_bytes)
            size_mb = os.path.getsize(output_path) / (1024*1024)
            print(f"   ✅ Saved: {output_path} ({size_mb:.1f}MB)")
            return True
        else:
            print(f"   ❌ No video in response")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main(game_name):
    prompts_file = f"games/{game_name}/clips/veo3_prompts.json"
    influencers_dir = f"games/{game_name}/influencers"
    os.makedirs(influencers_dir, exist_ok=True)

    if not os.path.exists(prompts_file):
        print(f"❌ Run 'prompts' step first!")
        sys.exit(1)

    with open(prompts_file) as f:
        data = json.load(f)

    prompts = data['prompts']
    print("=" * 60)
    print(f"🎬 VEO3 AUTO INFLUENCER GENERATOR")
    print(f"🎮 Game: {game_name} | 📹 {len(prompts)} videos to generate")
    print("=" * 60)

    success = 0
    for p in prompts:
        i = p['clip_number']
        clip_num = f"{i:02d}"
        output_path = f"{influencers_dir}/clip_{clip_num}_influencer.mp4"

        print(f"\n🎬 Clip {i}/{len(prompts)}: {p['clip_title']}")

        if os.path.exists(output_path):
            print(f"   ⏭️  Already exists, skipping")
            success += 1
            continue

        dialogue = p.get('dialogue', {})
        full_prompt = p['veo3_prompt']
        if dialogue:
            full_prompt += f"\n\nDialogue guide: '{dialogue.get('build_up','')}' then '{dialogue.get('peak_reaction','')}' then '{dialogue.get('aftermath','')}'"

        if generate_video(full_prompt, output_path, clip_num):
            success += 1

    print("\n" + "=" * 60)
    print(f"✅ Generated {success}/{len(prompts)} influencer videos")
    print(f"📁 Saved to: {influencers_dir}/")
    if success == len(prompts):
        print(f"\nNEXT: python3 AUTOMATION_MASTER.py {game_name} combine")
    print("=" * 60)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/auto_veo3.py <game_name>")
        sys.exit(1)
    main(sys.argv[1])
