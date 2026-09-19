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


from collections import deque
import numpy as np


def remove_fake_checkerboard_bg(img: Image.Image) -> Image.Image:
    """
    Intelligently detects and removes fake checkerboard patterns (grey & white squares)
    or near-white solid backgrounds from uploaded mascot PNGs, making them 100% transparent.
    """
    img = img.convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]

    # Check if border pixels have light neutral colors (typical fake transparency)
    def is_bg_pixel(r, g, b):
        return min(r, g, b) >= 165 and (max(r, g, b) - min(r, g, b)) <= 28

    visited = np.zeros((h, w), dtype=bool)
    q = deque()

    # Seed from outer perimeter
    for x in range(w):
        for y in [0, h - 1]:
            if is_bg_pixel(*arr[y, x, :3]):
                q.append((x, y))
                visited[y, x] = True
    for y in range(h):
        for x in [0, w - 1]:
            if not visited[y, x] and is_bg_pixel(*arr[y, x, :3]):
                q.append((x, y))
                visited[y, x] = True

    # Flood fill
    cleared_count = 0
    while q:
        cx, cy = q.popleft()
        arr[cy, cx, 3] = 0
        cleared_count += 1
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx]:
                if is_bg_pixel(*arr[ny, nx, :3]):
                    visited[ny, nx] = True
                    q.append((nx, ny))

    if cleared_count > 50:
        return Image.fromarray(arr)
    return img


def search_wikimedia_image(query: str) -> Optional[str]:
    """
    Searches Thai and English Wikipedia / Wikimedia Commons for a high-res image.
    Supports bilingual lookup, automatic redirect resolution, and raster thumbnail extraction.
    """
    eng_term = None
    m = re.search(r"\(([A-Za-z0-9\s]+)\)", query)
    if m:
        eng_term = m.group(1).strip()

    clean_q = re.sub(r"\(.*?\)", "", query).strip()
    clean_q = re.sub(r"[^\w\s\u0E00-\u0E7F]", "", clean_q).strip()
    if not clean_q and not eng_term:
        return None

    headers = {"User-Agent": "VSIFYBot/3.5 (Educational Comparison Studio; contact: admin@vsify.app)"}

    # Step 1: Search Thai Wikipedia (fast & accurate for Thai names)
    if clean_q:
        try:
            url_th = (
                f"https://th.wikipedia.org/w/api.php?action=query&format=json&redirects=1"
                f"&prop=pageimages&piprop=thumbnail|original&pithumbsize=800&titles={urllib.parse.quote(clean_q)}"
            )
            req = urllib.request.Request(url_th, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for _, pdata in pages.items():
                    if "thumbnail" in pdata and "source" in pdata["thumbnail"]:
                        return pdata["thumbnail"]["source"]
                    if "original" in pdata and "source" in pdata["original"]:
                        return pdata["original"]["source"]
        except Exception:
            pass

        # Step 1b: Thai Wikipedia OpenSearch fallback
        try:
            search_th = f"https://th.wikipedia.org/w/api.php?action=opensearch&format=json&search={urllib.parse.quote(clean_q)}&limit=1"
            req = urllib.request.Request(search_th, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                s_data = json.loads(resp.read().decode("utf-8"))
                if len(s_data) > 1 and s_data[1] and s_data[1][0] != clean_q:
                    found_title = s_data[1][0]
                    url_th2 = (
                        f"https://th.wikipedia.org/w/api.php?action=query&format=json&redirects=1"
                        f"&prop=pageimages&piprop=thumbnail|original&pithumbsize=800&titles={urllib.parse.quote(found_title)}"
                    )
                    req2 = urllib.request.Request(url_th2, headers=headers)
                    with urllib.request.urlopen(req2, timeout=5) as resp2:
                        data2 = json.loads(resp2.read().decode("utf-8"))
                        pages2 = data2.get("query", {}).get("pages", {})
                        for _, pdata in pages2.items():
                            if "thumbnail" in pdata and "source" in pdata["thumbnail"]:
                                return pdata["thumbnail"]["source"]
                            if "original" in pdata and "source" in pdata["original"]:
                                return pdata["original"]["source"]
        except Exception:
            pass

    # Step 2: Search English Wikipedia (using English term in parentheses if available, or clean_q)
    en_queries = [q for q in [eng_term, clean_q] if q]
    for eq in en_queries:
        try:
            url_en = (
                f"https://en.wikipedia.org/w/api.php?action=query&format=json&redirects=1"
                f"&prop=pageimages&piprop=thumbnail|original&pithumbsize=800&titles={urllib.parse.quote(eq)}"
            )
            req = urllib.request.Request(url_en, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for _, pdata in pages.items():
                    if "thumbnail" in pdata and "source" in pdata["thumbnail"]:
                        return pdata["thumbnail"]["source"]
                    if "original" in pdata and "source" in pdata["original"]:
                        return pdata["original"]["source"]
        except Exception:
            pass

    return None


CARTOON_STYLES = {
    "3d_pixar": {
        "name": "✨ 3D Pixar / Cute 3D (อนิเมชั่น 3 มิติ สตูดิโอคลีน)",
        "prompt": "3D cute stylized cartoon illustration of {name}, vibrant soft pastel colors, Pixar 3D animation style, clean white studio background, smooth lighting, octane render, 4k",
    },
    "2d_flat": {
        "name": "🎨 2D Flat Vector (การ์ตูนเวกเตอร์ มินิมอล สีสดใส)",
        "prompt": "Modern 2D flat vector cartoon illustration of {name}, cute kawaii icon, minimalist clean line art, bold pastel colors, white isolated background, graphic design sticker style",
    },
    "ghibli": {
        "name": "🍃 Studio Ghibli (ลายเส้นอนิเมะ อบอุ่น นุ่มนวล ละมุนตา)",
        "prompt": "Studio Ghibli style anime illustration of {name}, Hayao Miyazaki aesthetic, nostalgic soft watercolor lighting, charming detailed hand-drawn anime art, clean light background",
    },
    "claymation": {
        "name": "🧸 Claymation / Stop-Motion (ดินน้ำมันปั้น 3D น่ารัก)",
        "prompt": "Cute claymation clay sculpture illustration of {name}, plasticine stop-motion aesthetic, handmade craft texture, soft warm studio lighting, clean background, Aardman style",
    },
    "cyberpunk": {
        "name": "⚡ Cyberpunk / Neon Glow (ไซเบอร์พังก์ นีออน สตรีทล้ำยุค)",
        "prompt": "Stylized futuristic cyberpunk 3D icon of {name}, glowing neon accents, synthwave aesthetic, sleek high-tech edges, clean dark-studio isolated render",
    },
}


def generate_ai_cartoon_image(
    item_name: str,
    output_path: Path,
    target_size: int = 500,
    art_style: str = "3d_pixar",
) -> Optional[Path]:
    """
    Generates a charming stylized cartoon illustration via free AI engine (Pollinations.ai).
    Supports presets: '3d_pixar', '2d_flat', 'ghibli', 'claymation', 'cyberpunk'.
    Includes bilingual English extraction, randomized seed, and automatic retry.
    """
    # Extract English term inside parentheses if present (e.g. "Light Roast" in "กาแฟคั่วอ่อน (Light Roast)")
    eng_match = re.search(r"\(([A-Za-z0-9\s\-]+)\)", item_name)
    eng_term = eng_match.group(1).strip() if eng_match else ""

    clean_name = re.sub(r"\(.*?\)", "", item_name).strip()
    if not clean_name:
        clean_name = item_name.strip()
    if not clean_name:
        return None

    ai_subject = f"{eng_term}, {clean_name}" if eng_term else clean_name

    style_cfg = CARTOON_STYLES.get(art_style, CARTOON_STYLES["3d_pixar"])
    prompt = style_cfg["prompt"].format(name=ai_subject)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    import random
    import time
    seed = random.randint(1000, 999999)

    prompts_to_try = [
        prompt,
        f"cute 3D cartoon illustration of {ai_subject}, clean white studio background, vibrant colors, product spotlight",
    ]
    if eng_term:
        prompts_to_try.append(f"3D cute miniature of {eng_term}, clean plain background, high detail render")

    for attempt_idx, p_text in enumerate(prompts_to_try):
        try:
            encoded_prompt = urllib.parse.quote(p_text)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&seed={seed + attempt_idx}&nologo=true"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=16) as resp:
                raw_bytes = resp.read()
                if len(raw_bytes) > 2000:
                    import io
                    with Image.open(io.BytesIO(raw_bytes)) as img:
                        img = img.convert("RGBA")
                        w, h = img.size
                        min_dim = min(w, h)
                        left = (w - min_dim) // 2
                        top = (h - min_dim) // 2
                        cropped = img.crop((left, top, left + min_dim, top + min_dim))
                        resized = cropped.resize((target_size, target_size), Image.Resampling.LANCZOS)
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        resized.save(output_path, "PNG")
                        return output_path
        except Exception as e:
            if attempt_idx < len(prompts_to_try) - 1:
                time.sleep(0.8)
                continue
            print(f"[ImageFetcher] AI cartoon generation failed for ({clean_name}): {e}")

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
    image_mode: str = "ai_cartoon",  # "ai_cartoon" | "web_search" | "minimal_card"
    art_style: str = "3d_pixar",
) -> Path:
    """
    Orchestrates smart image acquisition:
    - 'ai_cartoon': Generates stylized illustration via AI (with selected art_style), with web fallback.
    - 'web_search': Searches Thai/English Wikipedia & Wikimedia Commons for real photos.
    - 'minimal_card': Instant modern minimalist typographic card.
    """
    if not item_name:
        return generate_fallback_badge(
            item_name="Item A" if not is_item_b else "Item B",
            output_path=output_path,
            is_item_b=is_item_b,
        )

    # 1. Mode: AI Cartoon Illustration (Zero-touch Render with selected style)
    if image_mode == "ai_cartoon" and allow_web_search:
        ai_res = generate_ai_cartoon_image(item_name, output_path, art_style=art_style)
        if ai_res and ai_res.exists() and ai_res.stat().st_size > 1500:
            return ai_res

    # 2. Mode: Web Search (Wikimedia Thai/English + DuckDuckGo)
    if allow_web_search and image_mode in ("ai_cartoon", "web_search"):
        wiki_url = search_wikimedia_image(item_name)
        if wiki_url:
            res = download_and_crop_square(wiki_url, output_path)
            if res and res.exists() and res.stat().st_size > 1000:
                return res

        ddg_url = search_duckduckgo_image(item_name)
        if ddg_url:
            res = download_and_crop_square(ddg_url, output_path)
            if res and res.exists() and res.stat().st_size > 1000:
                return res

    # 3. Mode: Typographic Minimalist Card Fallback
    return generate_fallback_badge(
        item_name=item_name,
        output_path=output_path,
        is_item_b=is_item_b,
    )
