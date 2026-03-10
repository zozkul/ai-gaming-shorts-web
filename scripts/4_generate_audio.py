"""
OpenAI TTS ile yorum scriptlerini seslendir
"""
import os
import json
import sys
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_tts(text, output_path, voice="alloy", speed=1.1):
    """Text-to-Speech oluştur"""
    print(f"🎤 Seslendirme: {text[:50]}...")

    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,  # alloy, echo, fable, onyx, nova, shimmer
        input=text,
        speed=speed
    )

    response.stream_to_file(output_path)
    print(f"   ✓ Kaydedildi: {output_path}")

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("Kullanım: python 4_generate_audio.py <commentary_json_dosyası>")
        sys.exit(1)

    commentary_file = sys.argv[1]

    if not os.path.exists(commentary_file):
        print(f"❌ Yorum dosyası bulunamadı: {commentary_file}")
        sys.exit(1)

    # Yorumları yükle
    with open(commentary_file, 'r', encoding='utf-8') as f:
        commentary = json.load(f)

    # Output klasörü
    base_name = Path(commentary_file).stem.replace('_commentary', '')
    audio_dir = f"temp/{base_name}_audio"
    os.makedirs(audio_dir, exist_ok=True)

    # Ses ayarları
    voice = os.getenv('INFLUENCER_VOICE', 'nova')  # nova: kadın sesi

    audio_files = {
        'intro': None,
        'reactions': [],
        'outro': None
    }

    # Intro seslendirme
    print("\n📢 Intro seslendiriliyor...")
    intro_path = f"{audio_dir}/intro.mp3"
    generate_tts(commentary['intro'], intro_path, voice=voice, speed=1.15)
    audio_files['intro'] = intro_path

    # Reaksiyonları seslendir
    print("\n💬 Reaksiyonlar seslendiriliyor...")
    for i, reaction in enumerate(commentary['reactions']):
        reaction_path = f"{audio_dir}/reaction_{i+1}.mp3"

        # Enerji seviyesine göre hız ayarla
        energy = reaction.get('energy_level', 7)
        speed = 1.0 + (energy / 20)  # 1.0 - 1.5 arası

        generate_tts(reaction['text'], reaction_path, voice=voice, speed=speed)

        audio_files['reactions'].append({
            'file': reaction_path,
            'timestamp': reaction['timestamp'],
            'text': reaction['text']
        })

    # Outro seslendirme
    print("\n👋 Outro seslendiriliyor...")
    outro_path = f"{audio_dir}/outro.mp3"
    generate_tts(commentary['outro'], outro_path, voice=voice, speed=1.1)
    audio_files['outro'] = outro_path

    # Manifest kaydet
    manifest_path = f"{audio_dir}/audio_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(audio_files, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Tüm sesler oluşturuldu!")
    print(f"📁 Klasör: {audio_dir}")
    print(f"📋 Manifest: {manifest_path}")

if __name__ == '__main__':
    main()
