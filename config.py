"""
Configuration module for Automated Short-Form Comparison Video Pipeline (9:16 Vertical).
Handles canvas layout, colors, typography, coordinates, and directory paths.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
FONTS_DIR = ASSETS_DIR / "fonts"
FONT_BOLD = FONTS_DIR / "Kanit-Bold.ttf"
FONT_REGULAR = FONTS_DIR / "Sarabun-Bold.ttf"
SCRIPTS_DIR = ASSETS_DIR / "scripts"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

for d in [ASSETS_DIR, IMAGES_DIR, FONTS_DIR, SCRIPTS_DIR, AUDIO_DIR, OUTPUT_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Canvas & Video Settings
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920
FPS = 30

# Colors (RGB Tuples & Hex)
COLOR_BG_CREAM = (245, 242, 235)       # Minimalist solid warm cream (#F5F2EB)
COLOR_WHITE = (255, 255, 255)
COLOR_TEXT_DARK = (31, 31, 31)         # Dark charcoal (#1F1F1F)
COLOR_BORDER_DEFAULT = (216, 211, 200) # Subtle warm gray (#D8D3C8)
COLOR_HIGHLIGHT_LIME = (50, 205, 50)   # Bright lime-green (#32CD32)
COLOR_CARD_SUBTITLE = (255, 255, 255, 240) # Semi-transparent white card
COLOR_BADGE_A = (235, 87, 87)          # Reddish coral for Item A badge
COLOR_BADGE_B = (47, 128, 237)         # Sky blue for Item B badge
COLOR_TOPIC_BADGE = (40, 40, 40)       # Dark charcoal topic pill

# Layout Coordinates (1080 x 1920 Canvas)
# Top Topic Header
TOPIC_BOX = {
    "x": 60,
    "y": 60,
    "w": 960,
    "h": 70,
    "radius": 35
}

# Top Section: Paper-Sticker Labels Above Boxes (Y: 110 to 205)
LABEL_A_RECT = {"x": 30, "y": 110, "w": 490, "h": 95}
LABEL_B_RECT = {"x": 560, "y": 110, "w": 490, "h": 95}

# Comparison Product Boxes (Y: 220 to 680)
BOX_A_RECT = {
    "x": 30,
    "y": 220,
    "w": 490,
    "h": 460,
    "radius": 24
}

BOX_B_RECT = {
    "x": 560,
    "y": 220,
    "w": 490,
    "h": 460,
    "radius": 24
}

# Border dimensions
BORDER_WIDTH_DEFAULT = 4
BORDER_WIDTH_ACTIVE = 10

# Middle Section - Dynamic Thai Subtitles (Y: 710 to 900)
SUBTITLE_BOX = {
    "x": 60,
    "y": 710,
    "w": 960,
    "h": 190,
    "radius": 22
}

# Bottom Section - Full-Body 2D Character Cutout (Elevated & Ground-Anchored)
CHARACTER_BOX = {
    "center_x": 540,
    "ground_y": 1780,
    "max_width": 820,
    "max_height": 850
}

# Inter-segment silence gap for TTS (seconds)
TTS_SILENCE_GAP = 0.25

# Font Finder
def get_font_path(font_type: str = "bold") -> str:
    """
    Finds the best available Thai-supported font.
    Checks assets/fonts/ first, then Windows system fonts.
    """
    preferred_fonts = [
        FONTS_DIR / "Kanit-Bold.ttf",
        FONTS_DIR / "Sarabun-Bold.ttf",
        FONTS_DIR / "Kanit-Regular.ttf",
        FONTS_DIR / "Sarabun-Regular.ttf",
        Path("C:/Windows/Fonts/LeelawUI.ttf"),
        Path("C:/Windows/Fonts/leelawad.ttf"),
        Path("C:/Windows/Fonts/tahomabd.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
    ]
    for font_path in preferred_fonts:
        if font_path.exists():
            return str(font_path)
    return "arial.ttf"

def get_regular_font_path() -> str:
    preferred_fonts = [
        FONTS_DIR / "Sarabun-Regular.ttf",
        FONTS_DIR / "Kanit-Regular.ttf",
        FONTS_DIR / "Sarabun-Bold.ttf",
        FONTS_DIR / "Kanit-Bold.ttf",
        Path("C:/Windows/Fonts/LeelawUI.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
    ]
    for font_path in preferred_fonts:
        if font_path.exists():
            return str(font_path)
    return get_font_path("bold")

# Watermark Safe Zones for 9:16 vertical canvas (avoids Header, Boxes, Subtitles, Mascot & Platform UI)
WATERMARK_SAFE_ZONES = [
    {"name": "top_left", "x": 60, "y": 140},
    {"name": "top_right", "x": 820, "y": 140},
    {"name": "mid_left", "x": 60, "y": 1070},
    {"name": "mid_right", "x": 820, "y": 1070},
]

PROFILE_FILE = BASE_DIR / "channel_profile.json"

DEFAULT_CHANNEL_PROFILE = {
    "channel_name": "VSIFY",
    "tagline": "See Both. Know Better.",
    "watermark_text": "@vsify.official",
    "watermark_opacity": 0.75,
    "default_outro_cta": "ถ้าอยากเลือกให้ชัวร์และรู้ลึกกว่าเดิม อย่าลืมกดติดตาม VSIFY ไว้นะครับ! See Both. Know Better.",
    "default_affiliate_a": "https://shopee.co.th",
    "default_affiliate_b": "https://shopee.co.th",
    "logo_path": "",
    "default_voice": "edge_niwat",
    "default_emotion": "viral",
    "default_rate": "+10%",
    "default_pitch": "+2Hz",
    "default_enable_bgm": True,
    "default_bgm_vol": 0.12,
    "default_enable_sfx": True,
    "default_bg_mode": "color",
    "default_bg_color": "#F5F2EB",
    "default_highlight_color": "#32CD32",
    "default_anim_style": "pointer_and_border",
    "default_char_mode": "builtin",
    "char_single_path": "",
    "char_mouth_closed": "",
    "char_mouth_open": "",
    "char_gif_path": "",
    "char_pose_think": "",
    "char_pose_a": "",
    "char_pose_b": "",
    "char_pose_neutral": "",
    "default_image_mode": "ai_cartoon",  # "ai_cartoon" | "web_search" | "minimal_card"
    "default_art_style": "3d_pixar",    # "3d_pixar" | "2d_flat" | "ghibli" | "claymation" | "cyberpunk"
}

def load_channel_profile() -> dict:
    """Loads saved channel profile or returns default."""
    if PROFILE_FILE.exists():
        try:
            import json
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                res = DEFAULT_CHANNEL_PROFILE.copy()
                res.update(data)
                return res
        except Exception:
            pass
    return DEFAULT_CHANNEL_PROFILE.copy()

def save_channel_profile(data: dict) -> None:
    """Persists channel profile to local JSON."""
    import json
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_active_character_assets(prof: dict = None) -> tuple:
    """
    Returns (character_path, character_poses) based on channel profile.
    Supports:
    - 'builtin': Built-in smart 4-pose character
    - 'single_upload': Custom single mascot image (system auto-flips for point B)
    - 'mouth_pair': 2 images (closed mouth + open mouth) with auto-mirroring & talking mouth sync
    - 'gif_animation': Transparent animated GIF with auto-mirroring
    - 'multi_pose': Custom 4 distinct poses (think, point A, point B, neutral)
    """
    if prof is None:
        prof = load_channel_profile()

    char_mode = prof.get("default_char_mode", "builtin")
    builtin_path = IMAGES_DIR / "character_host.png"

    if char_mode == "single_upload":
        sp = prof.get("char_single_path", "")
        if sp and Path(sp).exists():
            return Path(sp), None
    elif char_mode == "mouth_pair":
        closed_p = prof.get("char_mouth_closed", "") or prof.get("char_single_path", "")
        open_p = prof.get("char_mouth_open", "")
        if closed_p and Path(closed_p).exists():
            poses = {
                "thinking": {"closed": Path(closed_p), "open": Path(open_p) if open_p and Path(open_p).exists() else Path(closed_p)},
                "point_a": {"closed": Path(closed_p), "open": Path(open_p) if open_p and Path(open_p).exists() else Path(closed_p)},
                "neutral": {"closed": Path(closed_p), "open": Path(open_p) if open_p and Path(open_p).exists() else Path(closed_p)},
            }
            return Path(closed_p), poses
    elif char_mode == "gif_animation":
        gp = prof.get("char_gif_path", "")
        if gp and Path(gp).exists():
            return Path(gp), None
    elif char_mode == "multi_pose":
        poses = {}
        for key, prop in [
            ("neutral", "char_pose_neutral"),
            ("point_a", "char_pose_a"),
            ("point_b", "char_pose_b"),
            ("think", "char_pose_think"),
        ]:
            val = prof.get(prop, "")
            if val and Path(val).exists():
                poses[key] = Path(val)
        if poses:
            base_p = poses.get("neutral") or list(poses.values())[0]
            return base_p, poses

    return builtin_path, None

# Auto-delegation if Streamlit Cloud or user executes config.py as main entrypoint
if __name__ == "__main__":
    import sys
    sys.modules["config"] = sys.modules[__name__]
    import runpy
    _web_app_file = BASE_DIR / "web_app.py"
    if _web_app_file.exists():
        runpy.run_path(str(_web_app_file), run_name="__main__")

