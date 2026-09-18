"""
Generates starter sample assets (Image A, Image B, Character Avatar, and Script JSON)
for instant testing of the video generation pipeline.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json
from config import IMAGES_DIR, SCRIPTS_DIR, get_font_path


def create_sample_assets():
    """Create sample images and script file."""
    font_path = get_font_path("bold")
    try:
        font_large = ImageFont.truetype(font_path, 48)
        font_sub = ImageFont.truetype(font_path, 28)
    except Exception:
        font_large = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # 1. Item A: Coffee Drip Image (500x500)
    img_a = Image.new("RGBA", (500, 500), (243, 233, 220, 255))
    draw_a = ImageDraw.Draw(img_a)
    # Coffee Pot / Dripper graphic
    draw_a.polygon([(180, 160), (320, 160), (270, 260), (230, 260)], fill=(139, 69, 19, 255)) # Cone
    draw_a.ellipse([210, 255, 290, 270], fill=(101, 67, 33, 255)) # Filter base
    draw_a.rounded_rectangle([200, 270, 300, 390], radius=15, fill=(210, 180, 140, 200), outline=(100, 70, 40, 255), width=4) # Pot
    draw_a.arc([290, 290, 340, 360], start=270, end=90, fill=(100, 70, 40, 255), width=5) # Handle
    draw_a.text((250, 430), "กาแฟดริป (Drip)", font=font_sub, fill=(60, 40, 20, 255), anchor="mm")
    path_a = IMAGES_DIR / "item_a_drip.png"
    img_a.save(path_a)
    print(f"Created: {path_a}")

    # 2. Item B: Coffee Capsule Image (500x500)
    img_b = Image.new("RGBA", (500, 500), (225, 235, 245, 255))
    draw_b = ImageDraw.Draw(img_b)
    # Capsule Machine graphic
    draw_b.rounded_rectangle([190, 150, 310, 380], radius=25, fill=(40, 55, 71, 255)) # Machine body
    draw_b.ellipse([230, 180, 270, 200], fill=(52, 152, 219, 255)) # Power button
    draw_b.rounded_rectangle([210, 260, 290, 340], radius=10, fill=(189, 195, 199, 255)) # Cup tray
    # Cup with espresso
    draw_b.rounded_rectangle([225, 290, 275, 330], radius=5, fill=(255, 255, 255, 255), outline=(150, 150, 150, 255), width=2)
    draw_b.text((250, 430), "กาแฟแคปซูล (Capsule)", font=font_sub, fill=(30, 40, 60, 255), anchor="mm")
    path_b = IMAGES_DIR / "item_b_capsule.png"
    img_b.save(path_b)
    print(f"Created: {path_b}")

    # 3. Character Sprite Avatar (600x700 with Alpha Transparency)
    char_img = Image.new("RGBA", (600, 700), (0, 0, 0, 0))
    draw_c = ImageDraw.Draw(char_img)
    # Body & shoulders
    draw_c.ellipse([140, 380, 460, 760], fill=(41, 128, 185, 255))
    # Shirt Collar
    draw_c.polygon([(250, 390), (350, 390), (300, 480)], fill=(255, 255, 255, 255))
    # Modern tie / badge
    draw_c.rounded_rectangle([285, 460, 315, 600], radius=6, fill=(230, 126, 34, 255))
    # Head & ears
    draw_c.ellipse([180, 160, 420, 400], fill=(255, 224, 189, 255))
    draw_c.ellipse([165, 250, 195, 300], fill=(255, 224, 189, 255))
    draw_c.ellipse([405, 250, 435, 300], fill=(255, 224, 189, 255))
    # Hair
    draw_c.ellipse([170, 100, 430, 260], fill=(44, 62, 80, 255))
    # Eyes
    draw_c.ellipse([235, 245, 270, 280], fill=(44, 62, 80, 255))
    draw_c.ellipse([330, 245, 365, 280], fill=(44, 62, 80, 255))
    draw_c.ellipse([245, 250, 255, 260], fill=(255, 255, 255, 255))
    draw_c.ellipse([340, 250, 350, 260], fill=(255, 255, 255, 255))
    # Cute glasses
    draw_c.rounded_rectangle([215, 230, 285, 295], radius=12, outline=(30, 30, 30, 255), width=6)
    draw_c.rounded_rectangle([315, 230, 385, 295], radius=12, outline=(30, 30, 30, 255), width=6)
    draw_c.line([285, 260, 315, 260], fill=(30, 30, 30, 255), width=6)
    # Smile
    draw_c.arc([265, 305, 335, 350], start=15, end=165, fill=(192, 57, 43, 255), width=6)

    path_c = IMAGES_DIR / "character_host.png"
    char_img.save(path_c)
    print(f"Created: {path_c}")

    # 4. Sample JSON Script with Affiliate Links
    sample_script = {
        "topic": "กาแฟดริป VS กาแฟแคปซูล",
        "name_a": "กาแฟดริป",
        "name_b": "กาแฟแคปซูล",
        "hook": "สายกาแฟห้ามพลาด! ดริปเองกับแคปซูล แบบไหนตอบโจทย์ชีวิตคุณมากกว่ากัน?",
        "item_a": "กาแฟดริป ได้กลิ่นหอมกรุ่นแบบสโลว์ไลฟ์ ดึงรสชาติเมล็ดกาแฟแท้ๆ ออกมาได้ชัดเจน เหมาะกับสายสุนทรีย์มีเวลาละเมียดละไม",
        "item_b": "กาแฟแคปซูล ตอบโจทย์ความเร็วในชั่วโมงเร่งด่วน แค่กดปุ่มเดียวก็ได้รสชาติเข้มข้นคงที่ ได้มาตรฐานร้านหรูในสิบวินาที",
        "conclusion": "ชอบความหอมคลาสสิกเลือกดริป ชอบความง่ายทันใจเลือกแคปซูล คอมเมนต์บอกกันหน่อยนะ ส่วนพิกัดของแท้ราคาโปร แปะไว้ในคอมเมนต์แรกแล้วครับ",
        "affiliate_comment": "📍 พิกัดของแท้ราคาโปรโมชั่นพิเศษ:\n👉 กาแฟดริป: https://shopee.co.th/sample_drip\n👉 กาแฟแคปซูล: https://shopee.co.th/sample_capsule\n(ใครสนใจตัวไหน จิ้มดูพิกัดในลิงก์ได้เลยครับ)"
    }
    path_script = SCRIPTS_DIR / "coffee_comparison.json"
    with open(path_script, "w", encoding="utf-8") as f:
        json.dump(sample_script, f, ensure_ascii=False, indent=2)
    print(f"Created: {path_script}")


if __name__ == "__main__":
    create_sample_assets()
