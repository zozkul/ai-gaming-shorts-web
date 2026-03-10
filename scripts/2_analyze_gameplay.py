"""
GPT-4 Vision ile gameplay videosunu analiz et
En ilginç/heyecanlı/komik anları tespit et
"""
import os
import cv2
import base64
import json
from openai import OpenAI
from dotenv import load_dotenv
import sys

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def extract_frames(video_path, num_frames=8):
    """Videodan belirli sayıda frame çıkar"""
    cap = cv2.VideoCapture(video_path)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    duration = total_frames / fps

    # Eşit aralıklarla frame al
    frame_indices = [int(total_frames * i / num_frames) for i in range(num_frames)]

    frames = []
    timestamps = []

    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()

        if ret:
            # Frame'i base64'e çevir
            _, buffer = cv2.imencode('.jpg', frame)
            base64_frame = base64.b64encode(buffer).decode('utf-8')
            frames.append(base64_frame)
            timestamps.append(idx / fps)

    cap.release()

    return frames, timestamps, duration

def analyze_gameplay(video_path):
    """GPT-4 Vision ile gameplay analizi"""
    print(f"🎬 Video analiz ediliyor: {os.path.basename(video_path)}")

    frames, timestamps, duration = extract_frames(video_path, num_frames=8)

    # GPT-4 Vision'a gönder
    messages = [
        {
            "role": "system",
            "content": """Sen bir gaming content creator asistanısın.
Gameplay videolarını analiz edip, viral olabilecek en ilginç anları tespit ediyorsun.
Türkçe konuşan genç bir kitleye hitap edecek komik ve heyecanlı yorumlar yapıyorsun."""
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Bu gameplay videosunun {len(frames)} frame'ini görüyorsun.
Video {duration:.1f} saniye uzunluğunda.

Görevlerin:
1. En ilginç/heyecanlı/komik 3-5 anı tespit et
2. Her an için:
   - Hangi timestamp'te olduğu
   - Ne olduğu (kısa açıklama)
   - Neden ilginç/komik/heyecanlı
   - Viral potansiyeli (1-10)

3. Genel video özeti (1 cümle)

JSON formatında cevap ver:
{
    "summary": "video özeti",
    "highlights": [
        {
            "timestamp": 12.5,
            "description": "ne oldu",
            "why_interesting": "neden ilginç",
            "viral_score": 8,
            "emotion": "surprise/excitement/funny"
        }
    ],
    "overall_vibe": "action/comedy/epic/fail"
}"""
                }
            ]
        }
    ]

    # Frame'leri ekle
    for i, (frame, ts) in enumerate(zip(frames, timestamps)):
        messages[1]["content"].append({
            "type": "text",
            "text": f"\n--- Frame {i+1} (t={ts:.1f}s) ---"
        })
        messages[1]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{frame}",
                "detail": "low"
            }
        })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1000,
        temperature=0.7
    )

    result_text = response.choices[0].message.content

    # JSON'ı parse et
    try:
        # Markdown kod bloğu varsa temizle
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        analysis = json.loads(result_text)
        return analysis
    except json.JSONDecodeError:
        print("⚠️ JSON parse hatası, ham cevap:")
        print(result_text)
        return None

def main():
    """Ana fonksiyon"""
    if len(sys.argv) < 2:
        print("Kullanım: python 2_analyze_gameplay.py <video_dosyası>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"❌ Video bulunamadı: {video_path}")
        sys.exit(1)

    analysis = analyze_gameplay(video_path)

    if analysis:
        # Sonuçları kaydet
        output_file = video_path.replace('.mp4', '_analysis.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analiz tamamlandı!")
        print(f"📊 Özet: {analysis['summary']}")
        print(f"🎯 {len(analysis['highlights'])} highlight bulundu")
        print(f"💾 Kaydedildi: {output_file}")
    else:
        print("❌ Analiz başarısız!")

if __name__ == '__main__':
    main()
