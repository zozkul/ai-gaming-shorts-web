"""
Analiz sonuçlarına göre Türkçe yorum scriptleri oluştur
"""
import os
import json
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_commentary(analysis, influencer_name="Ayşe"):
    """Analiz sonuçlarına göre yorum scripti oluştur"""
    print("💬 Yorum scriptleri oluşturuluyor...")

    highlights = analysis.get('highlights', [])
    summary = analysis.get('summary', '')
    vibe = analysis.get('overall_vibe', 'action')

    prompt = f"""Sen "{influencer_name}" adında genç, enerjik bir gaming influencer'sın.
Gameplay videolarına spontane, doğal tepkiler veriyorsun.

Video özeti: {summary}
Genel vibe: {vibe}

Bu videoda {len(highlights)} ilginç an tespit edildi:

"""

    for i, h in enumerate(highlights, 1):
        prompt += f"""
{i}. {h['timestamp']:.1f} saniyede:
   - Ne oldu: {h['description']}
   - Neden ilginç: {h['why_interesting']}
   - Emotion: {h['emotion']}
   - Viral skor: {h['viral_score']}/10
"""

    prompt += """

Görevin:
1. Video başı için kısa bir giriş (2-3 cümle, heyecan yaratmalı)
2. Her highlight için doğal bir tepki/yorum (1-2 cümle)
3. Video sonu için kapanış (call-to-action)

Önemli:
- Türkçe argoda konuş (ama küfür yok)
- Kısa ve dinamik cümleler
- Emoji kullanabilirsin (😱 🔥 💯 vs.)
- "WOOW", "YOK ARTIK", "EFSANE" gibi doğal tepkiler
- Izleyiciyle konuş ("Gördünüz mü şimdi?", "Bekleyin daha neler var!")

JSON formatında cevap ver:
{
    "intro": "Video başı giriş scripti",
    "reactions": [
        {
            "timestamp": 12.5,
            "text": "Bu ana tepki scripti",
            "emotion": "surprised",
            "energy_level": 8
        }
    ],
    "outro": "Video sonu kapanış scripti"
}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Sen profesyonel bir gaming content writer'sın. Türkçe içerik üretiyorsun."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=1500
    )

    result_text = response.choices[0].message.content

    try:
        # JSON parse
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        commentary = json.loads(result_text)
        return commentary
    except json.JSONDecodeError:
        print("⚠️ JSON parse hatası:")
        print(result_text)
        return None

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("Kullanım: python 3_generate_commentary.py <analysis_json_dosyası>")
        sys.exit(1)

    analysis_file = sys.argv[1]

    if not os.path.exists(analysis_file):
        print(f"❌ Analiz dosyası bulunamadı: {analysis_file}")
        sys.exit(1)

    # Analizi yükle
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis = json.load(f)

    # Yorum oluştur
    commentary = generate_commentary(analysis)

    if commentary:
        # Kaydet
        output_file = analysis_file.replace('_analysis.json', '_commentary.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(commentary, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Yorum scriptleri oluşturuldu!")
        print(f"\n📝 Intro: {commentary['intro'][:100]}...")
        print(f"💬 {len(commentary['reactions'])} tepki scripti")
        print(f"💾 Kaydedildi: {output_file}")
    else:
        print("❌ Yorum oluşturulamadı!")

if __name__ == '__main__':
    main()
