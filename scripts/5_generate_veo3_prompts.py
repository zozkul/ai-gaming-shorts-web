"""
Veo 3 için prompt'lar oluştur
(Veo 3 API olmadığı için, manuel olarak kullanacağınız prompt'ları hazırlar)
"""
import os
import json
import sys
from pathlib import Path
from mutagen.mp3 import MP3

def get_audio_duration(audio_path):
    """MP3 dosyasının süresini al"""
    try:
        audio = MP3(audio_path)
        return audio.info.length
    except:
        return 0

def generate_veo3_prompt(commentary, audio_manifest, analysis):
    """Veo 3 için detaylı prompt oluştur"""

    vibe = analysis.get('overall_vibe', 'action')
    summary = analysis.get('summary', '')

    # Karakter tanımı
    character_desc = """Genç kadın gaming influencer (20'li yaşlarda):
- Pembe-turuncu degradeli uzun saçlar
- Rahat krem renkli hoodie
- Gaming koltuğunda oturuyor
- Önünde profesyonel podcast mikrofonu
- Arkada RGB ışıklandırma ve gaming setup
- Modern, temiz bir streaming odası"""

    # Temel prompt
    base_prompt = f"""{character_desc}

VIDEO TİPİ: Gaming reaction video
SÜRE: ~{sum([get_audio_duration(r['file']) for r in audio_manifest['reactions']])} saniye
GENEL HAVAİSİ: {vibe}

SENARYO:
Influencer ekrana (kameraya) bakıyor ve gameplay videosuna tepki veriyor.

"""

    # Her reaksiyon için timing ve emotion ekle
    scenes = []

    # Intro
    intro_duration = get_audio_duration(audio_manifest['intro'])
    scenes.append(f"""
[0-{intro_duration:.1f}s] GİRİŞ:
- Enerjik, gülümseyen
- Kameraya bakıyor
- El hareketleri yapıyor
- Text: "{commentary['intro'][:80]}..."
""")

    # Reaksiyonlar
    current_time = intro_duration
    for i, reaction in enumerate(commentary['reactions'], 1):
        audio_info = audio_manifest['reactions'][i-1]
        duration = get_audio_duration(audio_info['file'])

        emotion = reaction.get('emotion', 'excited')
        energy = reaction.get('energy_level', 7)

        emotion_map = {
            'surprised': 'Şaşkın, gözleri açık, kaşlar yukarı',
            'excited': 'Heyecanlı, gülüyor, enerji dolu',
            'funny': 'Gülerek, eğlenceli mimikler',
            'shocked': 'Şok olmuş, ağzı açık, geri çekilme',
            'impressed': 'Etkilenmiş, başını sallıyor, gülümseme'
        }

        emotion_desc = emotion_map.get(emotion, 'Heyecanlı tepki')

        scenes.append(f"""
[{current_time:.1f}-{current_time+duration:.1f}s] REAKSİYON {i}:
- {emotion_desc}
- Enerji seviyesi: {energy}/10
- Doğal el ve yüz hareketleri
- Text: "{reaction['text'][:80]}..."
""")

        current_time += duration

    # Outro
    outro_duration = get_audio_duration(audio_manifest['outro'])
    scenes.append(f"""
[{current_time:.1f}-{current_time+outro_duration:.1f}s] KAPANIŞ:
- Gülerek veda ediyor
- El sallıyor
- Pozitif enerji
- Text: "{commentary['outro'][:80]}..."
""")

    full_prompt = base_prompt + "\n".join(scenes)

    # Ek talimatlar
    full_prompt += """

ÖNEMLİ:
- Tüm video boyunca aynı kişi olmalı (tutarlılık)
- Doğal, spontane hareketler
- Ağız hareketleri sesle senkronize
- Gaming influencer tarzı (GenZ/Millennial)
- Rahat, samimi atmosfer
- 4K kalite, iyi ışıklandırma
"""

    return full_prompt

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 4:
        print("Kullanım: python 5_generate_veo3_prompts.py <commentary.json> <audio_manifest.json> <analysis.json>")
        sys.exit(1)

    commentary_file = sys.argv[1]
    audio_manifest_file = sys.argv[2]
    analysis_file = sys.argv[3]

    # Dosyaları yükle
    with open(commentary_file, 'r', encoding='utf-8') as f:
        commentary = json.load(f)

    with open(audio_manifest_file, 'r', encoding='utf-8') as f:
        audio_manifest = json.load(f)

    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    # Prompt oluştur
    prompt = generate_veo3_prompt(commentary, audio_manifest, analysis)

    # Kaydet
    base_name = Path(commentary_file).stem.replace('_commentary', '')
    output_file = f"temp/{base_name}_veo3_prompt.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    print(f"✅ Veo 3 prompt oluşturuldu!")
    print(f"📄 Dosya: {output_file}")
    print(f"\n{'='*60}")
    print(prompt)
    print(f"{'='*60}")
    print(f"\nBu prompt'u Veo 3'e yapıştırın ve videoyu oluşturun.")
    print(f"Video hazır olunca 6_combine_videos.py ile birleştirin.")

if __name__ == '__main__':
    main()
