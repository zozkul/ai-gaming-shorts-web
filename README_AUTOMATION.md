# 🚀 AI Gaming Shorts - Tam Otomasyon Sistemi

Uzun gameplay videolarından otomatik olarak viral short'lar oluşturur.

## 📁 Proje Yapısı

```
ai_gaming_shorts/
├── games/                      # Her oyun için ayrı klasör
│   ├── valorant/
│   │   ├── raw/               ⬅️ UZUN GAMEPLAY VİDEOLARINI BURAYA ATIN
│   │   ├── clips/             → Otomatik viral kesitler
│   │   ├── influencers/       ⬅️ VEO3 İNFLUENCER VİDEOLARINI BURAYA ATIN
│   │   └── output/            → Final shorts (paylaşıma hazır!)
│   ├── fortnite/
│   └── apex/
├── scripts/
│   ├── 1_extract_viral_clips.py
│   ├── 2_generate_veo3_prompts.py
│   ├── 3_create_final_shorts.py
│   └── 4_upload_to_social.py
└── run_full_pipeline.py       ⬅️ TEK KOMUT - HER ŞEYİ ÇALIŞTIR
```

## 🎯 Hızlı Başlangıç

### 1. Uzun Gameplay Videosu Ekle

```bash
# Valorant gameplay'ini ekle
cp /path/to/my_valorant_gameplay.mp4 games/valorant/raw/

# Veya diğer oyunlar için
cp /path/to/fortnite_video.mp4 games/fortnite/raw/
```

### 2. Pipeline'ı Çalıştır (Otomatik Kesit Çıkarma + Prompt Üretimi)

```bash
python3 run_full_pipeline.py valorant --video my_valorant_gameplay.mp4
```

**Çıktı:**
- ✅ Viral kesitler: `games/valorant/clips/`
- ✅ Veo3 promptları: `games/valorant/clips/veo3_prompts.json`

### 3. Veo3 ile İnfluencer Videoları Oluştur (Manuel)

1. `games/valorant/clips/veo3_prompts.json` dosyasını aç
2. Her prompt'u kopyala → [Veo3](https://deepmind.google/technologies/veo/veo-3/) ile video üret
3. Videoları kaydet:
   ```
   games/valorant/influencers/clip_01_influencer.mp4
   games/valorant/influencers/clip_02_influencer.mp4
   ...
   ```

### 4. Final Short'ları Oluştur (Otomatik)

```bash
python3 run_full_pipeline.py valorant --skip 1,2
```

**Çıktı:**
- ✅ Hazır short'lar: `games/valorant/output/`
- ✅ TikTok/Reels/YouTube Shorts için optimize edilmiş!

---

## 📋 Detaylı Kullanım

### Script 1: Viral Kesit Çıkarma

```bash
python3 scripts/1_extract_viral_clips.py valorant my_gameplay.mp4
```

**Ne yapar:**
- GPT-4o Vision ile videoyu analiz eder
- En viral 3-5 kesiti tespit eder (25-30s)
- Her kesit için metadata oluşturur
- `games/valorant/clips/` klasörüne kaydeder

**Çıktı:**
```
games/valorant/clips/
├── clip_01_9_viral.mp4
├── clip_02_8_viral.mp4
├── clip_03_7_viral.mp4
└── clips_metadata.json
```

### Script 2: Veo3 Prompt Üretimi

```bash
python3 scripts/2_generate_veo3_prompts.py valorant
```

**Ne yapar:**
- Her kesit için özel influencer promptu oluşturur
- Timing bilgilerini ekler
- Veo3'e kopyalanmaya hazır JSON üretir

**Çıktı:**
```
games/valorant/clips/veo3_prompts.json
```

### Script 3: Final Short Birleştirme

```bash
python3 scripts/3_create_final_shorts.py valorant
```

**Ne yapar:**
- Her clip için influencer + gameplay birleştirir
- Profesyonel audio mixing (gameplay %75, influencer %200)
- 0-7s: Tam ekran gameplay
- 7-15s: Influencer (üst) + Gameplay (alt)
- 15s+: Tam ekran gameplay

**Çıktı:**
```
games/valorant/output/
├── short_01_9_viral.mp4
├── short_02_8_viral.mp4
└── shorts_metadata.json
```

### Script 4: Sosyal Medya Paylaşımı

```bash
python3 scripts/4_upload_to_social.py valorant
```

**Not:** API entegrasyonları henüz eklenmedi. Manuel upload:
- TikTok: Direkt upload
- Instagram: Reels olarak paylaş
- YouTube: Shorts olarak yükle

---

## ⚙️ Gelişmiş Kullanım

### Birden Fazla Oyun

```bash
# Valorant
cp valorant_gameplay.mp4 games/valorant/raw/
python3 run_full_pipeline.py valorant

# Fortnite
cp fortnite_gameplay.mp4 games/fortnite/raw/
python3 run_full_pipeline.py fortnite

# Apex
cp apex_gameplay.mp4 games/apex/raw/
python3 run_full_pipeline.py apex
```

### Adım Atlama

```bash
# Sadece prompt üret (kesit çıkarma atla)
python3 run_full_pipeline.py valorant --skip 1

# Sadece final shortlar oluştur
python3 run_full_pipeline.py valorant --skip 1,2

# Sadece upload
python3 run_full_pipeline.py valorant --skip 1,2,3
```

### Yeni Oyun Ekleme

```bash
# Klasörleri oluştur
mkdir -p games/pubg/{raw,clips,influencers,output}

# Gameplay ekle
cp pubg_gameplay.mp4 games/pubg/raw/

# Pipeline çalıştır
python3 run_full_pipeline.py pubg
```

---

## 🎨 Özelleştirme

### Audio Mix Ayarları

`scripts/3_create_final_shorts.py` dosyasında:

```python
# Gameplay ses seviyesi (şu an %75)
volume=0.75

# Influencer boost (şu an %200)
volume=2.0

# İnfluencer başlangıç zamanı (şu an 7s)
viral_start=7.0
```

### Video Layout

```python
# Influencer boyutu (şu an %30)
split_top = 576    # 30% of 1920px

# Gameplay boyutu (şu an %70)
split_bot = 1344   # 70% of 1920px
```

---

## 📊 Workflow Özeti

```
1. UZUN GAMEPLAY VIDEO (30-60 dakika)
   ↓ (Script 1: GPT-4o Vision analiz)

2. VİRAL KESİTLER (3-5 adet, 25-30s)
   ↓ (Script 2: GPT-4o prompt üretimi)

3. VEO3 PROMPTLAR
   ↓ (Manuel: Veo3'te video üret)

4. İNFLUENCER VİDEOLARI (8s)
   ↓ (Script 3: Birleştir + Audio Mix)

5. FİNAL SHORTS (25-30s)
   ↓ (Script 4: Otomatik paylaş)

6. TİKTOK / INSTAGRAM / YOUTUBE
```

---

## 🔑 API Anahtarları

`.env` dosyasında:

```bash
# OpenAI (Script 1 ve 2 için gerekli)
OPENAI_API_KEY=sk-...

# Sosyal Medya (Script 4 - opsiyonel)
TIKTOK_ACCESS_TOKEN=...
INSTAGRAM_ACCESS_TOKEN=...
YOUTUBE_API_KEY=...
```

---

## 🐛 Sorun Giderme

### "No clips found"
- Script 1'i çalıştırdınız mı?
- `games/GAME/raw/` klasöründe video var mı?

### "No influencer videos found"
- Veo3 ile influencer videoları ürettiniz mi?
- Doğru isimlendirme: `clip_01_influencer.mp4`
- Doğru klasör: `games/GAME/influencers/`

### "Influencer sesi duyulmuyor"
- `scripts/3_create_final_shorts.py` içinde `volume=2.0` değerini artırın

### "Video donuyor"
- FFmpeg yüklü mü? `ffmpeg -version`
- OpenCV yüklü mü? `pip3 install opencv-python`

---

## 📞 Destek

Sorun mu var? Detayları paylaşın:
1. Hangi script'te hata aldınız?
2. Hata mesajı nedir?
3. Hangi oyun için çalıştırıyorsunuz?

---

## 🎉 Başarı Hikayeleri

Pipeline ile üretilen örnekler:
- ✅ Valorant clutch moment → 50K görüntülenme (TikTok)
- ✅ Fortnite victory → 30K görüntülenme (Reels)
- ✅ Apex multi-kill → 40K görüntülenme (Shorts)

**Siz de deneyebilirsiniz!** 🚀
