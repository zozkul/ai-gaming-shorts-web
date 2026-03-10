import subprocess
import os

print("🎬 Combining videos into vertical short...")

# Video paths
influencer = "temp/gameplay_influencer.mp4"
gameplay = "input/gameplay.mp4"
output = "output/final_short.mp4"

# Settings
width = 1080
height = 1920
top_height = int(height * 0.7)  # 70% influencer
bottom_height = height - top_height  # 30% gameplay

print(f"📐 Output: {width}x{height}")
print(f"   Top (Influencer): {width}x{top_height}")
print(f"   Bottom (Gameplay): {width}x{bottom_height}")

# FFmpeg command
cmd = [
    'ffmpeg', '-y',
    '-i', influencer,
    '-i', gameplay,
    '-filter_complex',
    f'[0:v]scale={width}:{top_height}:force_original_aspect_ratio=decrease,pad={width}:{top_height}:(ow-iw)/2:(oh-ih)/2,setsar=1[top];'
    f'[1:v]scale={width}:{bottom_height}:force_original_aspect_ratio=decrease,pad={width}:{bottom_height}:(ow-iw)/2:(oh-ih)/2,setsar=1[bottom];'
    f'[top][bottom]vstack=inputs=2[v]',
    '-map', '[v]',
    '-map', '0:a?',
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-c:a', 'aac',
    '-shortest',
    output
]

os.makedirs('output', exist_ok=True)
subprocess.run(cmd, check=True)

print(f"\n✅ Done! Your vertical short is ready:")
print(f"📱 {output}")
print(f"\n🎉 Upload to TikTok/Reels/Shorts!")
