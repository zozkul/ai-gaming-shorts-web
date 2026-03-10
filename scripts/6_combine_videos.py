"""
Influencer videosunu ve gameplay videosunu birleştir
Vertical format (9:16) - TikTok/Shorts için
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_video_info(video_path):
    """Video bilgilerini al"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,duration',
        '-of', 'json',
        video_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)

    stream = info['streams'][0]
    return {
        'width': int(stream['width']),
        'height': int(stream['height']),
        'duration': float(stream.get('duration', 0))
    }

def combine_videos(influencer_video, gameplay_video, audio_manifest, output_path):
    """Videoları vertical formatta birleştir"""

    # Ayarlar
    OUTPUT_WIDTH = int(os.getenv('OUTPUT_WIDTH', 1080))
    OUTPUT_HEIGHT = int(os.getenv('OUTPUT_HEIGHT', 1920))
    INFLUENCER_PERCENT = int(os.getenv('INFLUENCER_HEIGHT_PERCENT', 70))
    GAMEPLAY_PERCENT = int(os.getenv('GAMEPLAY_HEIGHT_PERCENT', 30))

    influencer_height = int(OUTPUT_HEIGHT * INFLUENCER_PERCENT / 100)
    gameplay_height = OUTPUT_HEIGHT - influencer_height

    print(f"📐 Çıktı boyutları: {OUTPUT_WIDTH}x{OUTPUT_HEIGHT}")
    print(f"   Influencer: {OUTPUT_WIDTH}x{influencer_height} (üst %{INFLUENCER_PERCENT})")
    print(f"   Gameplay: {OUTPUT_WIDTH}x{gameplay_height} (alt %{GAMEPLAY_PERCENT})")

    # FFmpeg komutu
    # 1. Her iki videoyu da resize et
    # 2. Dikey olarak birleştir
    # 3. Ses track'ini ekle

    # Tüm sesleri birleştir
    audio_files = []
    if audio_manifest.get('intro'):
        audio_files.append(audio_manifest['intro'])
    for reaction in audio_manifest.get('reactions', []):
        audio_files.append(reaction['file'])
    if audio_manifest.get('outro'):
        audio_files.append(audio_manifest['outro'])

    # Geçici audio birleştirme
    audio_list_file = "temp/audio_list.txt"
    with open(audio_list_file, 'w') as f:
        for audio in audio_files:
            f.write(f"file '{os.path.abspath(audio)}'\n")

    combined_audio = "temp/combined_audio.mp3"

    # Sesleri birleştir
    print("🎵 Sesler birleştiriliyor...")
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', audio_list_file,
        '-c', 'copy',
        combined_audio
    ], check=True)

    # Videoları birleştir
    print("🎬 Videolar birleştiriliyor...")

    ffmpeg_cmd = [
        'ffmpeg', '-y',
        # Input 1: Influencer video
        '-i', influencer_video,
        # Input 2: Gameplay video
        '-i', gameplay_video,
        # Input 3: Combined audio
        '-i', combined_audio,
        # Filter complex
        '-filter_complex',
        f'[0:v]scale={OUTPUT_WIDTH}:{influencer_height}:force_original_aspect_ratio=decrease,pad={OUTPUT_WIDTH}:{influencer_height}:(ow-iw)/2:(oh-ih)/2[top];'
        f'[1:v]scale={OUTPUT_WIDTH}:{gameplay_height}:force_original_aspect_ratio=decrease,pad={OUTPUT_WIDTH}:{gameplay_height}:(ow-iw)/2:(oh-ih)/2[bottom];'
        f'[top][bottom]vstack=inputs=2[outv]',
        # Map
        '-map', '[outv]',
        '-map', '2:a',  # Audio from combined audio
        # Codec ayarları
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        # Metadata
        '-metadata', 'title=AI Gaming Short',
        '-metadata', 'comment=Generated with AI',
        # Output
        output_path
    ]

    subprocess.run(ffmpeg_cmd, check=True)

    print(f"✅ Video oluşturuldu: {output_path}")

    # Video bilgilerini göster
    output_info = get_video_info(output_path)
    print(f"📊 Çıktı: {output_info['width']}x{output_info['height']}, {output_info['duration']:.1f}s")

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 4:
        print("Kullanım: python 6_combine_videos.py <influencer_video> <gameplay_video> <audio_manifest.json>")
        print("\nÖrnek:")
        print("  python 6_combine_videos.py veo3_output.mp4 input/gameplay.mp4 temp/gameplay_audio/audio_manifest.json")
        sys.exit(1)

    influencer_video = sys.argv[1]
    gameplay_video = sys.argv[2]
    audio_manifest_file = sys.argv[3]

    # Dosya kontrolleri
    if not os.path.exists(influencer_video):
        print(f"❌ Influencer videosu bulunamadı: {influencer_video}")
        sys.exit(1)

    if not os.path.exists(gameplay_video):
        print(f"❌ Gameplay videosu bulunamadı: {gameplay_video}")
        sys.exit(1)

    if not os.path.exists(audio_manifest_file):
        print(f"❌ Audio manifest bulunamadı: {audio_manifest_file}")
        sys.exit(1)

    # Audio manifest yükle
    with open(audio_manifest_file, 'r') as f:
        audio_manifest = json.load(f)

    # Output path
    os.makedirs('output', exist_ok=True)
    base_name = Path(gameplay_video).stem
    output_path = f"output/{base_name}_final.mp4"

    # Birleştir
    combine_videos(influencer_video, gameplay_video, audio_manifest, output_path)

    print(f"\n🎉 TAMAMLANDI!")
    print(f"📱 Vertical short hazır: {output_path}")
    print(f"💡 TikTok, Instagram Reels veya YouTube Shorts'a yüklenebilir!")

if __name__ == '__main__':
    main()
