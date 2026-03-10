#!/usr/bin/env python3
"""
FULL AUTOMATION PIPELINE
Run entire workflow with one command
"""

import os
import sys
import subprocess

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")

def run_command(script, args, description):
    """Run a script and handle errors"""
    print(f"▶️  {description}...")
    cmd = ['python3', script] + args

    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"✅ {description} - DONE\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"   Error: {e}")
        return False

def main(game_name, video_filename=None, skip_steps=[]):
    """
    Run full pipeline for a game

    Args:
        game_name: Name of the game (valorant, fortnite, etc.)
        video_filename: Raw gameplay video (optional, skips step 1 if not provided)
        skip_steps: List of step numbers to skip
    """

    print_header("🚀 AI GAMING SHORTS - FULL AUTOMATION PIPELINE")

    print(f"🎮 Game: {game_name}")
    if video_filename:
        print(f"📹 Video: {video_filename}")
    print(f"⏭️  Skip steps: {skip_steps if skip_steps else 'None'}\n")

    # Check if game directory exists
    game_dir = f"games/{game_name}"
    if not os.path.exists(game_dir):
        print(f"❌ Game directory not found: {game_dir}")
        print(f"\nAvailable games:")
        for g in os.listdir('games'):
            if os.path.isdir(f'games/{g}'):
                print(f"  - {g}")
        return

    # STEP 1: Extract viral clips
    if 1 not in skip_steps:
        print_header("STEP 1: Extract Viral Clips")

        if not video_filename:
            # Check for videos in raw/
            raw_dir = f"{game_dir}/raw"
            videos = [f for f in os.listdir(raw_dir) if f.endswith('.mp4')]

            if not videos:
                print(f"❌ No videos found in {raw_dir}")
                print(f"\nPlease add a video:")
                print(f"  cp your_gameplay.mp4 {raw_dir}/")
                return

            video_filename = videos[0]
            print(f"📹 Using: {video_filename}")

        success = run_command(
            'scripts/1_extract_viral_clips.py',
            [game_name, video_filename],
            "Extracting viral clips"
        )

        if not success:
            print("❌ Pipeline stopped at Step 1")
            return
    else:
        print("⏭️  Skipping Step 1: Extract viral clips\n")

    # STEP 2: Generate Veo3 prompts
    if 2 not in skip_steps:
        print_header("STEP 2: Generate Veo3 Prompts")

        success = run_command(
            'scripts/2_generate_veo3_prompts.py',
            [game_name],
            "Generating Veo3 prompts"
        )

        if not success:
            print("❌ Pipeline stopped at Step 2")
            return

        print("\n⏸️  MANUAL STEP REQUIRED:")
        print("=" * 70)
        print(f"1. Open: games/{game_name}/clips/veo3_prompts.json")
        print(f"2. Copy prompts to Veo3 (Google AI Studio)")
        print(f"3. Generate influencer videos")
        print(f"4. Save as: games/{game_name}/influencers/clip_XX_influencer.mp4")
        print(f"5. Run again with: --skip 1,2")
        print("=" * 70)
        return
    else:
        print("⏭️  Skipping Step 2: Generate Veo3 prompts\n")

    # STEP 3: Create final shorts
    if 3 not in skip_steps:
        print_header("STEP 3: Create Final Shorts")

        # Check if influencer videos exist
        influencer_dir = f"{game_dir}/influencers"
        influencer_videos = [f for f in os.listdir(influencer_dir) if f.endswith('.mp4')]

        if not influencer_videos:
            print(f"❌ No influencer videos found in {influencer_dir}")
            print(f"\nPlease add influencer videos first:")
            print(f"  Format: clip_01_influencer.mp4, clip_02_influencer.mp4, etc.")
            return

        print(f"✅ Found {len(influencer_videos)} influencer videos\n")

        success = run_command(
            'scripts/3_create_final_shorts.py',
            [game_name],
            "Creating final shorts"
        )

        if not success:
            print("❌ Pipeline stopped at Step 3")
            return
    else:
        print("⏭️  Skipping Step 3: Create final shorts\n")

    # STEP 4: Upload to social media
    if 4 not in skip_steps:
        print_header("STEP 4: Upload to Social Media")

        success = run_command(
            'scripts/4_upload_to_social.py',
            [game_name],
            "Uploading to social media"
        )

        # Note: This step is informational only (APIs not implemented yet)
    else:
        print("⏭️  Skipping Step 4: Upload to social media\n")

    # COMPLETION
    print_header("✅ PIPELINE COMPLETE!")

    print(f"📁 All outputs:")
    print(f"  Clips:      games/{game_name}/clips/")
    print(f"  Prompts:    games/{game_name}/clips/veo3_prompts.json")
    print(f"  Shorts:     games/{game_name}/output/")
    print(f"\n🎉 Ready to share on social media!")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI Gaming Shorts - Full Pipeline')
    parser.add_argument('game', help='Game name (valorant, fortnite, apex)')
    parser.add_argument('--video', help='Raw gameplay video filename (in games/GAME/raw/)')
    parser.add_argument('--skip', help='Skip steps (comma-separated, e.g., 1,2)')

    args = parser.parse_args()

    skip_steps = []
    if args.skip:
        skip_steps = [int(s) for s in args.skip.split(',')]

    main(args.game, args.video, skip_steps)
