"""
Automated Free Image Fetcher & Minimal Badge Generator for Items A & B.
Features:
1. Wikimedia Commons API: Searches high-resolution free images without API keys.
2. DuckDuckGo image search fallback.
3. Minimalist Typography Card Generator: If no image found or for abstract topics
   (e.g., 'กองทัพ', 'การศึกษา', 'GDP'), creates a clean, modern, high-contrast 1:1 badge.
"""

import json
import os
from pathlib import Path
import re
from typing import Optional
import urllib.parse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

from config import ASSETS_DIR, IMAGES_DIR, TEMP_DIR, FONT_REGULAR, FONT_BOLD


def _get_font(size: int = 36, bold: bool = True) -> ImageFont.FreeTypeFont:
    font_path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(str(font_path), size)
    except Exception:
        try:
            return ImageFont.truetype("arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def search_wikimedia_image(query: str) -> Optional[str]:
    """Searches Wikimedia Commons for a high-res image URL (100% free, no key)."""
    clean_q = re.sub(r"\(.*?\)", "", query).strip()
    clean_q = re.sub(r"[^\w\s\u0E00-\u0E7F]", "", clean_q).strip()
    if not clean_q:
        return None

    url = (
        f"https://en.wikipedia.org/w/api.php?action=query&format=json"
        f"&prop=pageimages&piprop=original&titles={urllib.parse.quote(clean_q)}"
    )
    headers = {"User-Agent": "ShortsStudioBot/3.0 (Educational Content Generator)"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            for _, pdata in pages.items():
                if "original" in pdata and "source" in pdata["original"]:
                    return pdata["original"]["source"]
    except Exception:
        pass

    # Secondary search via Wikipedia opensearch
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&format=json&search={urllib.parse.quote(clean_q)}&limit=1"
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(search_url, timeout=5) as resp:
            s_data = json.loads(resp.read().decode("utf-8"))
            if len(s_data) > 1 and s_data[1]:
                first_title = s_data[1][0]
                return search_wikimedia_image(first_title)
    except Exception:
        pass

    return None


def search_duckduckgo_image(query: str) -> Optional[str]:
    """Lightweight DuckDuckGo image query without requiring external libraries."""
    clean_q = re.sub(r"\(.*?\)", "", query).strip()
    clean_q = clean_q + " isolated product"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(clean_q)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            urls = re.findall(r"//external-content\.duckduckgo\.com/iu/\?u=([^&\"']+)", html)
            if urls:
                return urllib.parse.unquote(urls[0])
    except Exception:
        pass
    return None


def download_and_crop_square(image_url: str, output_path: Path, target_size: int = 500) -> Optional[Path]:
    """Downloads an image and center-crops it into a high-res 1:1 square PNG."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    temp_dl = output_path.parent / f"raw_{output_path.name}"

    try:
        req = urllib.request.Request(image_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp, open(temp_dl, "wb") as f:
            f.write(resp.read())

        with Image.open(temp_dl) as img:
            img = img.convert("RGBA")
            w, h = img.size
            min_dim = min(w, h)
            left = (w - min_dim) // 2
            top = (h - min_dim) // 2
            cropped = img.crop((left, top, left + min_dim, top + min_dim))
            resized = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
            resized.save(output_path, "PNG")

        if temp_dl.exists():
            temp_dl.unlink()
        return output_path
    except Exception:
        if temp_dl.exists():
            temp_dl.unlink()
        return None


def generate_fallback_badge(
    item_name: str,
    output_path: Path,
    target_size: int = 500,
    accent_color: str = "#2A2A40",
    is_item_b: bool = False,
) -> Path:
    """
    Generates a gorgeous, minimalist 1:1 graphic card with clear typography,
    accent badge, and clean modern aesthetic. Perfect for abstract topics.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Rounded background container
    radius = 32
    bg_color = (250, 250, 252, 255) if not is_item_b else (248, 250, 255, 255)
    border_color = (220, 225, 235, 255) if not is_item_b else (210, 225, 255, 255)
    draw.rounded_rectangle(
        [8, 8, target_size - 8, target_size - 8],
        radius=radius,
        fill=bg_color,
        outline=border_color,
        width=3,
    )

    # Top indicator pill
    pill_text = "🟢 ฝั่ง A" if not is_item_b else "🔵 ฝั่ง B"
    pill_bg = (50, 205, 50, 35) if not is_item_b else (30, 144, 255, 35)
    pill_border = (50, 205, 50, 180) if not is_item_b else (30, 144, 255, 180)
    pill_font = _get_font(24, bold=True)
    pw, ph = 150, 44
    px = (target_size - pw) // 2
    py = 42
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=22, fill=pill_bg, outline=pill_border, width=2)
    draw.text((target_size // 2, py + ph // 2), pill_text, font=pill_font, fill=(40, 40, 50), anchor="mm")

    # Center Item Name with smart wrapping
    name_clean = item_name.strip()
    font_size = 46 if len(name_clean) <= 12 else (36 if len(name_clean) <= 24 else 28)
    name_font = _get_font(font_size, bold=True)

    # Wrap name into lines
    words = name_clean.split(" ")
    lines = []
    curr = ""
    for w in words:
        test = f"{curr} {w}".strip()
        bbox = name_font.getbbox(test)
        if (bbox[2] - bbox[0]) < target_size - 60:
            curr = test
        else:
            if curr:
                lines.append(curr)
            curr = w
    if curr:
        lines.append(curr)

    line_h = font_size + 14
    total_h = len(lines) * line_h
    start_y = (target_size - total_h) // 2 + 30

    for i, line in enumerate(lines):
        y = start_y + (i * line_h)
        draw.text((target_size // 2, y), line, font=name_font, fill=(25, 25, 35), anchor="mm")

    img.save(output_path, "PNG")
    return output_path


def auto_fetch_or_create_image(
    item_name: str,
    output_path: Path,
    is_item_b: bool = False,
    allow_web_search: bool = True,
) -> Path:
    """
    Orchestrates fetching:
    1. Tries Wikimedia Commons / Web.
    2. If downloaded & cropped successfully, returns path.
    3. Else, falls back to generating a gorgeous typographic badge card.
    """
    if allow_web_search and item_name:
        # 1. Try Wikimedia
        wiki_url = search_wikimedia_image(item_name)
        if wiki_url:
            res = download_and_crop_square(wiki_url, output_path)
            if res and res.exists() and res.stat().st_size > 1000:
                return res

        # 2. Try DuckDuckGo
        ddg_url = search_duckduckgo_image(item_name)
        if ddg_url:
            res = download_and_crop_square(ddg_url, output_path)
            if res and res.exists() and res.stat().st_size > 1000:
                return res

    # 3. Fallback Graphic Card
    return generate_fallback_badge(
        item_name=item_name or ("Item A" if not is_item_b else "Item B"),
        output_path=output_path,
        is_item_b=is_item_b,
    )
