"""
Configuration module for Automated Short-Form Comparison Video Pipeline (9:16 Vertical).
Handles canvas layout, colors, typography, coordinates, and directory paths.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_DIR / "images"
FONTS_DIR = ASSETS_DIR / "fonts"
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

# Top Section (Y: 150 to 850)
# Canvas width 1080: Box 500x500 + Box 500x500 + gap 26 + left/right 27
BOX_A_RECT = {
    "x": 27,
    "y": 170,
    "w": 500,
    "h": 500,
    "radius": 24
}

BOX_B_RECT = {
    "x": 553,
    "y": 170,
    "w": 500,
    "h": 500,
    "radius": 24
}

# Border dimensions
BORDER_WIDTH_DEFAULT = 4
BORDER_WIDTH_ACTIVE = 10

# Labels under boxes
LABEL_A_RECT = {"x": 27, "y": 685, "w": 500, "h": 50}
LABEL_B_RECT = {"x": 553, "y": 685, "w": 500, "h": 50}

# Middle Section - Dynamic Thai Subtitles (Y: 760 to 1080)
SUBTITLE_BOX = {
    "x": 50,
    "y": 770,
    "w": 980,
    "h": 280,
    "radius": 20
}

# Bottom Section - 2D Character Cutout (Y: 1120 to 1920)
CHARACTER_BOX = {
    "center_x": 540,
    "bottom_y": 1920,
    "max_width": 780,
    "max_height": 780
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

# Auto-delegation if Streamlit Cloud or user executes config.py as main entrypoint
if __name__ == "__main__":
    _web_app_file = BASE_DIR / "web_app.py"
    if _web_app_file.exists():
        with open(_web_app_file, "r", encoding="utf-8") as _f:
            _code = _f.read()
        exec(_code, globals())

