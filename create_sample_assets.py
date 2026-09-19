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

    # 3. Multi-Pose Character Mascot with Talking Mouth Flaps (600x720)
    def draw_mascot(pose="neutral", mouth_open=False, w=600, h=720):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Body / Suit
        draw.ellipse([140, 390, 460, 770], fill=(41, 128, 185, 255))
        # Shirt Collar
        draw.polygon([(250, 400), (350, 400), (300, 485)], fill=(255, 255, 255, 255))
        # Modern tie
        draw.rounded_rectangle([285, 465, 315, 605], radius=6, fill=(230, 126, 34, 255))

        # Arms / Hands based on Pose
        suit_color = (31, 97, 141, 255)
        skin_color = (255, 224, 189, 255)

        if pose == "point_a":
            # Pointing up-left towards Box A
            draw.line([(180, 430), (90, 320), (50, 210)], fill=suit_color, width=38, joint="curve")
            draw.ellipse([30, 180, 75, 225], fill=skin_color)
            draw.line([(55, 195), (35, 145)], fill=skin_color, width=16)  # index finger
        elif pose == "point_b":
            # Pointing up-right towards Box B
            draw.line([(420, 430), (510, 320), (550, 210)], fill=suit_color, width=38, joint="curve")
            draw.ellipse([525, 180, 570, 225], fill=skin_color)
            draw.line([(545, 195), (565, 145)], fill=skin_color, width=16)  # index finger
        elif pose == "thinking":
            # Hand under chin / contemplating
            draw.line([(420, 450), (410, 380), (340, 365)], fill=suit_color, width=34, joint="curve")
            draw.ellipse([320, 345, 360, 385], fill=skin_color)  # hand on chin
            draw.line([(180, 450), (170, 540)], fill=suit_color, width=34)
        else:  # neutral
            draw.line([(180, 440), (150, 560)], fill=suit_color, width=34)
            draw.line([(420, 440), (450, 560)], fill=suit_color, width=34)

        # Head & Ears
        draw.ellipse([180, 160, 420, 400], fill=skin_color)
        draw.ellipse([165, 250, 195, 300], fill=skin_color)
        draw.ellipse([405, 250, 435, 300], fill=skin_color)
        # Hair
        draw.ellipse([170, 100, 430, 260], fill=(44, 62, 80, 255))

        # Eyebrows
        if pose == "thinking":
            draw.line([(225, 215), (275, 225)], fill=(30, 30, 30, 255), width=5)
            draw.line([(325, 220), (375, 210)], fill=(30, 30, 30, 255), width=5)
        else:
            draw.line([(225, 220), (275, 220)], fill=(30, 30, 30, 255), width=5)
            draw.line([(325, 220), (375, 220)], fill=(30, 30, 30, 255), width=5)

        # Eyes
        eye_offset_y = -10 if pose == "thinking" else 0
        eye_offset_x = -5 if pose == "point_a" else (5 if pose == "point_b" else 0)
        draw.ellipse([235 + eye_offset_x, 245 + eye_offset_y, 270 + eye_offset_x, 280 + eye_offset_y], fill=(44, 62, 80, 255))
        draw.ellipse([330 + eye_offset_x, 245 + eye_offset_y, 365 + eye_offset_x, 280 + eye_offset_y], fill=(44, 62, 80, 255))
        draw.ellipse([245 + eye_offset_x, 250 + eye_offset_y, 255 + eye_offset_x, 260 + eye_offset_y], fill=(255, 255, 255, 255))
        draw.ellipse([340 + eye_offset_x, 250 + eye_offset_y, 350 + eye_offset_x, 260 + eye_offset_y], fill=(255, 255, 255, 255))

        # Glasses
        draw.rounded_rectangle([215, 230, 285, 295], radius=12, outline=(30, 30, 30, 255), width=6)
        draw.rounded_rectangle([315, 230, 385, 295], radius=12, outline=(30, 30, 30, 255), width=6)
        draw.line([285, 260, 315, 260], fill=(30, 30, 30, 255), width=6)

        # Mouth (Talking Flap)
        if mouth_open:
            draw.ellipse([275, 320, 325, 360], fill=(160, 30, 30, 255))
            draw.chord([280, 320, 320, 335], start=0, end=180, fill=(255, 255, 255, 255))
            draw.ellipse([285, 342, 315, 358], fill=(230, 100, 100, 255))
        else:
            draw.arc([265, 315, 335, 355], start=15, end=165, fill=(192, 57, 43, 255), width=6)

        return img

    for p in ["thinking", "point_a", "point_b", "neutral"]:
        for m in [False, True]:
            img = draw_mascot(pose=p, mouth_open=m)
            suffix = "open" if m else "closed"
            save_path = IMAGES_DIR / f"char_{p}_{suffix}.png"
            img.save(save_path)

    # Master legacy fallback
    path_c = IMAGES_DIR / "character_host.png"
    draw_mascot("neutral", False).save(path_c)
    print(f"Created all multi-pose mascot sprites and: {path_c}")

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
