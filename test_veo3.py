import os
import time
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

print("🎬 Veo3 API test başlatılıyor...")

operation = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt="A young gaming streamer in a hoodie sitting at a gaming desk, hands on keyboard and mouse, reacting to an exciting game moment. Natural webcam angle, RGB lighting. The streamer says 'no way, let's GO!' with genuine excitement. 8 seconds.",
    config=types.GenerateVideosConfig(
        aspect_ratio="9:16",
        duration_seconds=8,
        number_of_videos=1,
    ),
)

print("⏳ Video üretiliyor, bekleniyor...")
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)
    print("⏳ Hala üretiliyor...")

print("✅ Tamamlandı!")
generated_video = operation.result.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("test_veo3_output.mp4")
print("✅ test_veo3_output.mp4 kaydedildi!")
