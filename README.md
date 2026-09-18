# 🎬 Automated Short-Form Comparison Video Generation Pipeline (9:16 Vertical)

ระบบสร้างวิดีโอสั้นแนวตั้ง (1080x1920) สำหรับ **Reels, TikTok และ YouTube Shorts** อัตโนมัติในสไตล์ **"A vs B Side-by-Side Comparison"**
มาพร้อมระบบคิดบทด้วย **Google Gemini AI**, ระบบสร้างเสียงพากย์ภาษาไทย (**Google Cloud TTS / gTTS**), แอนิเมชันกรอบไฟไฮไลต์ตามเสียง (**Dynamic Lime-Green Border**), ซับไตเติลภาษาไทยคมชัด, ตัวละคร 2D Host และระบบ **Affiliate Marketing Call-to-Action (CTA)** ปักหมุดคอมเมนต์อัตโนมัติ

---

## 📱 Canvas Layout & Visual Architecture (1080 x 1920)

```
+-------------------------------------------------------------+ (Y: 0)
|                     TOPIC BADGE (Y: 60 - 130)               |
|            ⚡ [กาแฟดริป VS กาแฟแคปซูล] ⚡                   |
+-------------------------------------------------------------+
|                                                             |
|   +-----------------------+     +-----------------------+   | (Y: 170)
|   |                       |     |                       |   |
|   |      ITEM A (1:1)     |     |      ITEM B (1:1)     |   |
|   |        (500x500)      |     |        (500x500)      |   |
|   |                       |     |                       |   |
|   +-----------------------+     +-----------------------+   | (Y: 670)
|       [ A: กาแฟดริป ]               [ B: กาแฟแคปซูล ]       |
|                                                             |
|   💡 Dynamic Border: สีเขียวมะนาว (#32CD32) หนา 10px สลับ   |
|      ไปที่ Box A เมื่อพูดถึง A และสลับไปที่ B เมื่อพูดถึง B |
+-------------------------------------------------------------+
|                                                             |
|             DYNAMIC THAI SUBTITLES (Y: 770 - 1050)          |
|      +-----------------------------------------------+      |
|      |  "กาแฟดริป ได้กลิ่นหอมกรุ่นแบบสโลว์ไลฟ์..."   |      |
|      +-----------------------------------------------+      |
+-------------------------------------------------------------+
|                                                             |
|            2D CHARACTER AVATAR (Y: 1120 - 1920)             |
|             (PNG ไดคัทโปร่งใส พร้อม Idle Breathing)         |
|                                                             |
+-------------------------------------------------------------+ (Y: 1920)
```

---

## 🌟 จุดเด่นของระบบ (Key Highlights)

1. **AI Script Generation with Gemini**:
   - วิเคราะห์และดึงจุดเด่นจริงของสินค้า A และ B ออกมาเป็น 4 ท่อน: Hook, Item A, Item B และ Conclusion
   - เสริมประโยค Call to Action แบบเนียนๆ สไตล์ Affiliate Marketer เช่น *"พิกัดของแท้ราคาโปร แปะไว้ในคอมเมนต์แรกแล้วนะครับ"*
   - สร้างข้อความสำหรับปักหมุดคอมเมนต์แรกใต้คลิปพร้อมลิงก์ Affiliate อัตโนมัติ
2. **Audio-Video Synchronization แม่นยำระดับเฟรม**:
   - วัดเวลาไฟล์เสียงจริงระดับมิลลิวินาที
   - กรอบไฟสว่างสีเขียวมะนาว (`#32CD32`) จะสลับเปิด-ปิดตามไทม์ไลน์ของเสียงพูดตรงจังหวะ 100%
3. **Pillow Font Engine (หมดปัญหา TextClip แครชบน Windows)**:
   - เรนเดอร์ตัวหนังสือภาษาไทยด้วย Pillow โดยตรง รองรับฟอนต์ Sarabun, Kanit และ Leelawadee UI สระและวรรณยุกต์ไทยคมชัด ไม่จมไม่ลอย และไม่ต้องลง ImageMagick
4. **Dual-Engine TTS**:
   - ใช้ Google Cloud Text-to-Speech (Neural2/WaveNet Thai) เมื่อตั้งค่า Service Account
   - Fallback ไปยัง gTTS (Google Translate ภาษาไทย) อัตโนมัติ ใช้งานได้ฟรีทันทีโดยไม่ต้องตั้งค่าใดๆ
5. **Interactive Web UI (Streamlit)**:
   - มีหน้าเว็บให้เปิดใช้ผ่านเบราว์เซอร์ ลากรูปมาวาง ใส่ลิงก์ กดให้ AI ร่างบท ตรวจและแก้ไขข้อความ จากนั้นกดเรนเดอร์และพรีวิวคลิปได้ทันที

---

## 📂 โครงสร้างโฟลเดอร์โปรเจกต์

```
Why It Works/
├── assets/
│   ├── fonts/           # เก็บฟอนต์ภาษาไทย (Kanit-Bold.ttf, Sarabun-Bold.ttf)
│   ├── images/          # เก็บรูปภาพสินค้า A, B และรูปตัวละคร Avatar
│   ├── scripts/         # เก็บไฟล์สคริปต์ JSON
│   └── audio/           # เก็บไฟล์เสียง Master Audio
├── output/              # โฟลเดอร์จัดเก็บคลิปวิดีโอ MP4 และภาพปก Cover
├── config.py            # การตั้งค่า Canvas, พิกัด Layout, สี และฟอนต์
├── ai_script_generator.py # โมดูลเรียก Gemini API คิดบท 4 ท่อนและคอมเมนต์ Affiliate
├── tts_engine.py        # โมดูลสังเคราะห์เสียงพากย์และสร้าง Timeline วัดเวลา
├── video_builder.py     # โมดูลตัดต่อ ผสมเลเยอร์ และเรนเดอร์ MP4 1080x1920
├── pipeline.py          # CLI Command สำหรับสั่งรันอัตโนมัติ
├── web_app.py           # Web UI (Streamlit) สำหรับใช้งานผ่านหน้าเว็บ
├── create_sample_assets.py # ตัวสร้างไฟล์ตัวอย่างสำหรับทดสอบ
├── requirements.txt     # รายการ Python dependencies
└── .env                 # เก็บ API Keys (Gemini API Key)
```

---

## 🚀 วิธีการติดตั้งและเริ่มต้นใช้งาน

### 1. ติดตั้ง Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 2. ตั้งค่าไฟล์ `.env`
สร้างไฟล์ `.env` ในโฟลเดอร์โปรเจกต์ (หรือแก้ไขค่า):
```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=
```

---

## 💻 วิธีการสั่งงาน (3 รูปแบบ)

### รูปแบบที่ 1: เปิดใช้งานผ่านหน้าเว็บ Web UI (แนะนำสำหรับมือใหม่)
เปิดหน้า Dashboard เพื่ออัปโหลดรูป พิมพ์ข้อมูล ให้ AI ช่วยคิดบท และดูวิดีโอแบบเรียลไทม์:
```powershell
python -m streamlit run web_app.py
```
เปิดเบราว์เซอร์ที่ `http://localhost:8501`

---

### รูปแบบที่ 2: สั่งงานผ่าน Command-Line (CLI)
#### ก. รันทดสอบทันทีด้วยชุดข้อมูลตัวอย่าง (Sample Mode)
```powershell
python pipeline.py --sample
```

#### ข. ให้ AI ช่วยคิดบทอัตโนมัติ พร้อมระบุลิงก์ Affiliate
```powershell
python pipeline.py `
  --topic "iPad Air vs iPad Pro" `
  --name_a "iPad Air" `
  --name_b "iPad Pro" `
  --image_a "assets/images/air.jpg" `
  --image_b "assets/images/pro.jpg" `
  --affiliate_a "https://shopee.co.th/ipad_air" `
  --affiliate_b "https://shopee.co.th/ipad_pro" `
  --ai_draft
```

#### ค. สั่งรันด้วยไฟล์สคริปต์ JSON ที่เตรียมไว้เอง
```powershell
python pipeline.py `
  --topic "กาแฟดริป VS กาแฟแคปซูล" `
  --name_a "กาแฟดริป" `
  --name_b "กาแฟแคปซูล" `
  --script_file "assets/scripts/coffee_comparison.json"
```

---

### รูปแบบที่ 3: โครงสร้างไฟล์ JSON สคริปต์ (`assets/scripts/*.json`)
```json
{
  "topic": "กาแฟดริป VS กาแฟแคปซูล",
  "name_a": "กาแฟดริป",
  "name_b": "กาแฟแคปซูล",
  "hook": "สายกาแฟห้ามพลาด! ดริปเองกับแคปซูล แบบไหนตอบโจทย์ชีวิตคุณมากกว่ากัน?",
  "item_a": "กาแฟดริป ได้กลิ่นหอมกรุ่นแบบสโลว์ไลฟ์ ดึงรสชาติเมล็ดกาแฟแท้ๆ ออกมาได้ชัดเจน",
  "item_b": "กาแฟแคปซูล ตอบโจทย์ความเร็วในชั่วโมงเร่งด่วน กดปุ่มเดียวได้รสชาติเข้มข้นคงที่",
  "conclusion": "ชอบตัวไหน คอมเมนต์บอกกันหน่อยนะ พิกัดของแท้ราคาโปร แปะไว้ในคอมเมนต์แรกแล้วครับ",
  "affiliate_comment": "📍 พิกัดของแท้ราคาโปรโมชั่นพิเศษ:\n👉 กาแฟดริป: https://shopee.co.th/sample_drip\n👉 กาแฟแคปซูล: https://shopee.co.th/sample_capsule\n(จิ้มดูในลิงก์ได้เลยครับ)"
}
```

---

## 🔮 Roadmap เฟสถัดไป (Phase 2 & Phase 3)

1. **Auto-Post to Social Media**:
   - **YouTube Shorts API**: โพสต์คลิปตั้งเวลา หรือลงทันที พร้อมดึง Thumbnail
   - **Meta Graph API**: โพสต์ลง Facebook Reels และ Instagram Reels
   - **TikTok Content Posting API**: โพสต์ลง TikTok อัตโนมัติ
   - **Auto-Comment Bot**: ปักหมุดคอมเมนต์แรกพร้อมลิงก์ Affiliate ทันทีที่คลิปเผยแพร่
2. **LINE OA Integration**:
   - ส่งรูป A, รูป B และหัวข้อเข้าห้องแชท LINE OA
   - บอทประมวลผล ส่งสคริปต์ให้ตรวจ และส่งไฟล์วิดีโอ MP4 คืนกลับมาในแชท
3. **Sound Effects (SFX) & Background Music (BGM)**:
   - สุ่มเพลงดนตรี Lo-fi คลอเบาๆ (-22dB)
   - เสียง "Whoosh" / "Pop" สลับตามจังหวะที่กรอบไฟเขียวเปลี่ยนฝั่ง
