"""
Video Builder Module for Automated Short-Form Comparison Videos (9:16 Vertical).
Composites 1080x1920 video with Pillow & MoviePy 2.x.
Features:
- Dynamic Lime-Green Highlight Borders keyed to audio timestamps
- Animated Sliding Pointer / Indicator switching from A to B
- High-contrast Thai subtitles rendered with Pillow
- 2D Character sprite with idle breathing motion
- Customizable backgrounds, typography, and cover thumbnail export.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math
import os
import re
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from moviepy import VideoClip, AudioFileClip

from config import (
    CANVAS_WIDTH,
    CANVAS_HEIGHT,
    FPS,
    COLOR_BG_CREAM,
    COLOR_WHITE,
    COLOR_TEXT_DARK,
    COLOR_BORDER_DEFAULT,
    COLOR_HIGHLIGHT_LIME,
    COLOR_BADGE_A,
    COLOR_BADGE_B,
    COLOR_TOPIC_BADGE,
    BOX_A_RECT,
    BOX_B_RECT,
    BORDER_WIDTH_DEFAULT,
    BORDER_WIDTH_ACTIVE,
    LABEL_A_RECT,
    LABEL_B_RECT,
    TOPIC_BOX,
    SUBTITLE_BOX,
    CHARACTER_BOX,
    get_font_path,
    get_regular_font_path,
    OUTPUT_DIR,
    IMAGES_DIR,
    WATERMARK_SAFE_ZONES,
)
from tts_engine import SegmentTimeline
from image_fetcher import remove_fake_checkerboard_bg

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class VideoBuilder:
    """Renders 1080x1920 vertical comparison short-form video."""

    def __init__(
        self,
        bg_color: Tuple[int, int, int] = COLOR_BG_CREAM,
        highlight_color: Tuple[int, int, int] = COLOR_HIGHLIGHT_LIME,
        font_path: Optional[str] = None,
        animation_style: str = "pointer_and_border",  # "pointer_and_border", "border_only", "scale_pulse"
    ):
        self.bg_color = bg_color
        self.highlight_color = highlight_color
        self.animation_style = animation_style
        self.font_bold_path = font_path or get_font_path("bold")
        self.font_regular_path = get_regular_font_path()

    def _load_font(self, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        f_path = self.font_bold_path if bold else self.font_regular_path
        try:
            return ImageFont.truetype(f_path, size)
        except Exception:
            return ImageFont.load_default()

    def _prepare_box_image(self, img_path: Path, width: int, height: int, radius: int) -> Image.Image:
        """Loads and crops image to square with smooth rounded corners."""
        if not img_path.exists():
            img = Image.new("RGBA", (width, height), (220, 220, 220, 255))
            draw = ImageDraw.Draw(img)
            draw.text((width // 2, height // 2), "No Image", fill=(100, 100, 100), anchor="mm")
        else:
            img = Image.open(img_path).convert("RGBA")
            src_w, src_h = img.size
            scale = max(width / src_w, height / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - width) // 2
            top = (new_h - height) // 2
            img = img.crop((left, top, left + width, top + height))

        mask = Image.new("L", (width, height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)

        rounded = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        rounded.paste(img, (0, 0), mask)
        return rounded

    def _render_box_frame(
        self,
        rect: Dict[str, Any],
        is_active: bool,
        pulse_val: float = 0.0,
    ) -> Image.Image:
        """Renders border overlay for a box with glowing neon effect when active."""
        w, h = rect["w"], rect["h"]
        pad = 20
        frame_img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame_img)

        rx, ry = pad, pad
        radius = rect["radius"]

        if is_active:
            border_w = BORDER_WIDTH_ACTIVE
            border_color = self.highlight_color + (255,)
            glow_color = self.highlight_color + (int(70 + pulse_val * 50),)
            for g in range(border_w + 8, border_w, -2):
                draw.rounded_rectangle(
                    [rx - g // 2, ry - g // 2, rx + w + g // 2, ry + h + g // 2],
                    radius=radius + g // 2,
                    outline=glow_color,
                    width=2,
                )
            draw.rounded_rectangle(
                [rx, ry, rx + w, ry + h],
                radius=radius,
                outline=border_color,
                width=border_w,
            )
        else:
            border_w = BORDER_WIDTH_DEFAULT
            border_color = COLOR_BORDER_DEFAULT + (255,)
            draw.rounded_rectangle(
                [rx, ry, rx + w, ry + h],
                radius=radius,
                outline=border_color,
                width=border_w,
            )

        return frame_img

    def _render_pointing_indicator(self, text: str = "กำลังพูดถึง 👇") -> Image.Image:
        """Renders a modern animated neon pointing pill."""
        w, h = 260, 60
        indicator = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(indicator)

        # Lime green glowing pill
        draw.rounded_rectangle([0, 0, w, h], radius=30, fill=self.highlight_color + (250,))
        draw.rounded_rectangle([2, 2, w - 2, h - 2], radius=28, outline=(255, 255, 255, 200), width=2)

        font = self._load_font(24, bold=True)
        draw.text((w // 2, h // 2), text, font=font, fill=(10, 10, 10, 255), anchor="mm")
        return indicator

    def _render_topic_banner(self, topic: str) -> Image.Image:
        """Renders the top topic capsule."""
        w, h = TOPIC_BOX["w"], TOPIC_BOX["h"]
        banner = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(banner)

        draw.rounded_rectangle(
            [0, 0, w, h],
            radius=TOPIC_BOX["radius"],
            fill=COLOR_TOPIC_BADGE + (255,),
        )

        font = self._load_font(34, bold=True)
        text = f"🔥 {topic} 🔥"
        draw.text((w // 2, h // 2), text, font=font, fill=COLOR_WHITE, anchor="mm")
        return banner

    def _render_label_badge(self, text: str, bg_color: Tuple[int, int, int], width: int, height: int = 95) -> Image.Image:
        """Renders stylish paper-sticker name label above item box."""
        badge = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)

        # Drop shadow for paper sticker
        draw.rounded_rectangle([16, 8, width - 16, height - 2], radius=18, fill=(0, 0, 0, 26))
        # Sticker white body
        draw.rounded_rectangle([14, 4, width - 14, height - 6], radius=18, fill=(255, 255, 255, 250), outline=(225, 220, 210, 240), width=2)

        # Strip prefixes like "A: " or "B: "
        clean_text = re.sub(r"^[ABab]\s*[:：]\s*", "", text).strip()

        # Split Thai / English if present, e.g. "ลาเต้ (Latte)" or "กาแฟคั่วเข้ม (Dark Roast)"
        m = re.search(r"^(.*?)\s*[\(\[]([A-Za-z0-9\s\-]+)[\)\]]", clean_text)
        if m:
            th_text = m.group(1).strip()
            en_text = m.group(2).strip()
            font_th = self._load_font(32, bold=True)
            font_en = self._load_font(26, bold=True)
            draw.text((width // 2, (height - 6) // 2 - 14), th_text, font=font_th, fill=(25, 25, 30), anchor="mm")
            draw.text((width // 2, (height - 6) // 2 + 18), en_text, font=font_en, fill=(80, 80, 90), anchor="mm")
        else:
            font = self._load_font(32, bold=True)
            draw.text((width // 2, (height - 6) // 2), clean_text, font=font, fill=(25, 25, 30), anchor="mm")

        return badge

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        cluster_pat = re.compile(r'[\u0E40-\u0E44]?[\u0E01-\u0E2E][\u0E30-\u0E3A\u0E47-\u0E4E]*|[A-Za-z0-9]+|[^\s\u0E00-\u0E7F]|\s+')
        words = text.split(" ") if " " in text else [text]
        tokens = []
        for word in words:
            bbox = font.getbbox(word) if hasattr(font, "getbbox") else (0, 0, len(word) * 20, 30)
            if (bbox[2] - bbox[0]) > max_width:
                # Break long unbroken Thai sentence into clusters
                clusters = cluster_pat.findall(word)
                tokens.extend(clusters)
            else:
                tokens.append(word)

        lines = []
        current_line = ""
        for token in tokens:
            connector = " " if current_line and not current_line.endswith(" ") and not re.match(r'[\u0E00-\u0E7F]', token) else ""
            test_line = f"{current_line}{connector}{token}".strip()
            bbox = font.getbbox(test_line)
            line_w = bbox[2] - bbox[0]
            if line_w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = token

        if current_line:
            lines.append(current_line)
        return lines if lines else [text]

    def _render_subtitle_card(self, text: str, round_label: str = "", style: str = "clean_floating") -> Image.Image:
        """Renders subtitle card with high-contrast text. Supports clean_floating (no card) or paper_card."""
        w, h = SUBTITLE_BOX["w"], SUBTITLE_BOX["h"]
        card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)

        text_offset_y = 4
        if style == "paper_card":
            # Drop shadow for paper sticker card
            draw.rounded_rectangle([18, 10, w - 18, h - 2], radius=SUBTITLE_BOX["radius"], fill=(0, 0, 0, 30))
            # White paper sticker card body
            draw.rounded_rectangle(
                [14, 4, w - 14, h - 8],
                radius=SUBTITLE_BOX["radius"],
                fill=(255, 255, 255, 250),
                outline=(225, 220, 210, 240),
                width=2,
            )

            # Optional Round / Dimension Badge at the top
            if round_label:
                badge_font = self._load_font(20, bold=True)
                bbox = badge_font.getbbox(round_label)
                bw = (bbox[2] - bbox[0]) + 30
                bh = 32
                bx = (w - bw) // 2
                by = 12
                draw.rounded_rectangle(
                    [bx, by, bx + bw, by + bh],
                    radius=16,
                    fill=(40, 40, 40, 245),
                    outline=self.highlight_color + (220,),
                    width=2,
                )
                draw.text((w // 2, by + bh // 2), round_label, font=badge_font, fill=(255, 255, 255, 255), anchor="mm")
                text_offset_y = 22

        if not text:
            return card

        # Dynamic font sizing: In clean_floating mode, text is punchy and readable
        base_size = 38 if style == "clean_floating" else 34
        if len(text) > 65:
            base_size = 28 if style == "clean_floating" else 26
        elif len(text) > 40:
            base_size = 33 if style == "clean_floating" else 30

        font = self._load_font(base_size, bold=True)
        max_txt_w = w - 40 if style == "clean_floating" else w - 80
        lines = self._wrap_text(text, font, max_width=max_txt_w)

        if len(lines) > 2 and base_size > 26:
            base_size = 26
            font = self._load_font(base_size, bold=True)
            lines = self._wrap_text(text, font, max_width=max_txt_w)

        line_height = int(base_size * 1.65)
        total_text_h = len(lines) * line_height
        start_y = max(8, (h - total_text_h) // 2 + text_offset_y)

        space_w = int(font.getlength(" ")) if hasattr(font, "getlength") else 14

        for i, line in enumerate(lines):
            y = start_y + (i * line_height)

            if style == "clean_floating":
                # Clean Floating Text: High-contrast white text with bold dark outline and drop shadow
                if " " not in line:
                    # Drop shadow
                    draw.text((w // 2 + 2, y + 3), line, font=font, fill=(0, 0, 0, 180), anchor="ma")
                    # Main text with thick dark outline
                    draw.text(
                        (w // 2, y),
                        line,
                        font=font,
                        fill=(255, 255, 255, 255),
                        stroke_width=4,
                        stroke_fill=(15, 15, 20, 245),
                        anchor="ma",
                    )
                else:
                    line_w = int(font.getlength(line)) if hasattr(font, "getlength") else (font.getbbox(line)[2] - font.getbbox(line)[0])
                    curr_x = (w - line_w) // 2
                    words = line.split(" ")
                    for word in words:
                        if not word:
                            curr_x += space_w
                            continue
                        w_w = int(font.getlength(word)) if hasattr(font, "getlength") else (font.getbbox(word)[2] - font.getbbox(word)[0])
                        is_num_or_stat = bool(re.search(r"(\d+|Hz|GB|%|บาท|ล้าน|แสน|ปี|เท่า)", word))
                        word_fill = (255, 220, 50, 255) if is_num_or_stat else (255, 255, 255, 255)

                        # Drop shadow
                        draw.text((curr_x + 2, y + 3), word, font=font, fill=(0, 0, 0, 180), anchor="la")
                        # Main text with outline
                        draw.text(
                            (curr_x, y),
                            word,
                            font=font,
                            fill=word_fill,
                            stroke_width=4,
                            stroke_fill=(15, 15, 20, 245),
                            anchor="la",
                        )
                        curr_x += w_w + space_w
            else:
                # Paper Card Mode
                if " " not in line:
                    draw.text((w // 2 + 1, y + 1), line, font=font, fill=(210, 210, 210, 180), anchor="ma")
                    draw.text((w // 2, y), line, font=font, fill=COLOR_TEXT_DARK, anchor="ma")
                else:
                    line_w = int(font.getlength(line)) if hasattr(font, "getlength") else (font.getbbox(line)[2] - font.getbbox(line)[0])
                    curr_x = (w - line_w) // 2
                    words = line.split(" ")
                    for word in words:
                        if not word:
                            curr_x += space_w
                            continue
                        w_w = int(font.getlength(word)) if hasattr(font, "getlength") else (font.getbbox(word)[2] - font.getbbox(word)[0])
                        is_num_or_stat = bool(re.search(r"(\d+|Hz|GB|%|บาท|ล้าน|แสน|ปี|เท่า)", word))
                        word_color = (20, 140, 20) if is_num_or_stat else COLOR_TEXT_DARK

                        draw.text((curr_x + 1, y + 1), word, font=font, fill=(210, 210, 210, 200), anchor="la")
                        draw.text((curr_x, y), word, font=font, fill=word_color, anchor="la")
                        curr_x += w_w + space_w

        return card

    def _render_watermark_badge(
        self,
        logo_path: Optional[Path] = None,
        text: Optional[str] = None,
        opacity: float = 0.75,
    ) -> Optional[Image.Image]:
        """Renders an anti-theft branding pill badge with semi-transparency."""
        if not logo_path and not text:
            return None

        alpha_int = max(30, min(255, int(255 * opacity)))
        font = self._load_font(20, bold=True)

        logo_img = None
        if logo_path and Path(logo_path).exists():
            try:
                logo_raw = Image.open(logo_path).convert("RGBA")
                logo_raw.thumbnail((36, 36), Image.Resampling.LANCZOS)
                r, g, b, a = logo_raw.split()
                a = a.point(lambda p: int(p * opacity))
                logo_img = Image.merge("RGBA", (r, g, b, a))
            except Exception:
                logo_img = None

        text_w = 0
        if text:
            bbox = font.getbbox(text)
            text_w = bbox[2] - bbox[0]

        pad_x = 14
        h = 42
        w = pad_x * 2 + text_w + (44 if logo_img else 0)
        w = max(w, 80)

        badge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)

        # Semi-transparent dark pill background
        bg_alpha = int(140 * opacity)
        draw.rounded_rectangle(
            [0, 0, w, h],
            radius=h // 2,
            fill=(20, 20, 20, bg_alpha),
            outline=(255, 255, 255, int(60 * opacity)),
            width=1,
        )

        curr_x = pad_x
        if logo_img:
            lw, lh = logo_img.size
            badge.paste(logo_img, (curr_x, (h - lh) // 2), logo_img)
            curr_x += lw + 8

        if text:
            draw.text((curr_x, h // 2), text, font=font, fill=(255, 255, 255, alpha_int), anchor="lm")

        return badge

    def _prepare_character_poses(
        self,
        character_path: Optional[Path] = None,
        character_poses: Optional[Dict[str, Path]] = None,
    ) -> Dict[str, Dict[str, Image.Image]]:
        """
        Loads character sprites for 4 poses: 'thinking', 'point_a', 'point_b', 'neutral'.
        For each pose, provides 'closed' and 'open' mouth frames.
        Supports:
        1. Explicit pose dictionary (character_poses).
        2. System sample multi-pose assets in IMAGES_DIR (char_{pose}_{closed|open}.png).
        3. Single custom image with auto-horizontal mirroring for 'point_b' and auto-talking bounce.
        """
        max_w, max_h = CHARACTER_BOX["max_width"], CHARACTER_BOX["max_height"]

        def _load_and_resize(source) -> Image.Image:
            if isinstance(source, Image.Image):
                img = source.convert("RGBA")
            elif not source or not Path(source).exists():
                return self._generate_sample_character(max_w, max_h)
            else:
                img = Image.open(source).convert("RGBA")

            try:
                img = remove_fake_checkerboard_bg(img)
            except Exception:
                pass

            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            return img

        # 1. If explicit poses dictionary passed
        if character_poses:
            poses = {}
            for pose_name in ["thinking", "point_a", "point_b", "neutral"]:
                item = character_poses.get(pose_name)
                if isinstance(item, dict):
                    img_closed = _load_and_resize(item.get("closed"))
                    img_open = _load_and_resize(item.get("open") or item.get("closed"))
                    poses[pose_name] = {"closed": img_closed, "open": img_open}
                elif item and Path(item).exists():
                    open_f = character_poses.get(f"{pose_name}_open")
                    closed_f = character_poses.get(f"{pose_name}_closed", item)
                    img_closed = _load_and_resize(Path(closed_f))
                    img_open = _load_and_resize(Path(open_f)) if open_f and Path(open_f).exists() else img_closed
                    poses[pose_name] = {"closed": img_closed, "open": img_open}
                else:
                    poses[pose_name] = None

            base_pose = poses.get("neutral") or poses.get("thinking") or poses.get("point_a")
            if not base_pose:
                base_img = self._generate_sample_character(max_w, max_h)
                base_pose = {"closed": base_img, "open": base_img}

            for p in ["thinking", "point_a", "neutral"]:
                if not poses.get(p):
                    poses[p] = base_pose

            if not poses.get("point_b"):
                ref_closed = poses["point_a"]["closed"]
                ref_open = poses["point_a"]["open"]
                poses["point_b"] = {
                    "closed": ImageOps.mirror(ref_closed),
                    "open": ImageOps.mirror(ref_open),
                }
            return poses

        # 2. If character_path is an animated GIF
        if character_path and character_path.exists() and character_path.suffix.lower() == ".gif":
            try:
                gif_im = Image.open(character_path)
                frames = []
                for f_i in range(getattr(gif_im, "n_frames", 1)):
                    gif_im.seek(f_i)
                    f_rgba = gif_im.convert("RGBA")
                    f_clean = _load_and_resize(f_rgba)
                    frames.append(f_clean)
                if frames:
                    closed_f = frames[0]
                    open_f = frames[len(frames) // 2] if len(frames) > 1 else frames[0]
                    mirrored_closed = ImageOps.mirror(closed_f)
                    mirrored_open = ImageOps.mirror(open_f)
                    mirrored_frames = [ImageOps.mirror(f) for f in frames]
                    return {
                        "thinking": {"closed": closed_f, "open": open_f, "frames": frames},
                        "point_a": {"closed": closed_f, "open": open_f, "frames": frames},
                        "point_b": {"closed": mirrored_closed, "open": mirrored_open, "frames": mirrored_frames},
                        "neutral": {"closed": closed_f, "open": open_f, "frames": frames},
                    }
            except Exception as e:
                print(f"[VideoBuilder] GIF load error: {e}")

        # 3. If character_path is a custom user-uploaded single image
        if character_path and character_path.exists() and character_path.name != "character_host.png":
            base_img = _load_and_resize(character_path)
            mirrored_img = ImageOps.mirror(base_img)
            return {
                "thinking": {"closed": base_img, "open": base_img},
                "point_a": {"closed": base_img, "open": base_img},
                "point_b": {"closed": mirrored_img, "open": mirrored_img},
                "neutral": {"closed": base_img, "open": base_img},
            }

        # 3. Check for system multi-pose assets in IMAGES_DIR
        has_sample_poses = all(
            (IMAGES_DIR / f"char_{p}_closed.png").exists() for p in ["thinking", "point_a", "point_b", "neutral"]
        )
        if has_sample_poses:
            poses = {}
            for p in ["thinking", "point_a", "point_b", "neutral"]:
                closed_p = IMAGES_DIR / f"char_{p}_closed.png"
                open_p = IMAGES_DIR / f"char_{p}_open.png"
                img_closed = _load_and_resize(closed_p)
                img_open = _load_and_resize(open_p) if open_p.exists() else img_closed
                poses[p] = {"closed": img_closed, "open": img_open}
            return poses

        # 4. Fallback to master character_host.png
        fallback_path = character_path or (IMAGES_DIR / "character_host.png")
        base_img = _load_and_resize(fallback_path)
        mirrored_img = ImageOps.mirror(base_img)
        return {
            "thinking": {"closed": base_img, "open": base_img},
            "point_a": {"closed": base_img, "open": base_img},
            "point_b": {"closed": mirrored_img, "open": mirrored_img},
            "neutral": {"closed": base_img, "open": base_img},
        }

    def _prepare_character_sprite(self, char_path: Path) -> Image.Image:
        """Legacy helper for backwards compatibility."""
        max_w, max_h = CHARACTER_BOX["max_width"], CHARACTER_BOX["max_height"]
        if not char_path.exists():
            return self._generate_sample_character(max_w, max_h)
        char_img = Image.open(char_path).convert("RGBA")
        char_img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        return char_img

    def _generate_sample_character(self, max_w: int, max_h: int) -> Image.Image:
        w, h = 600, 680
        avatar = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(avatar)

        draw.ellipse([150, 360, 450, 720], fill=(52, 73, 94, 255))
        draw.polygon([(250, 380), (350, 380), (300, 470)], fill=(236, 240, 241, 255))
        draw.polygon([(290, 440), (310, 440), (320, 560), (300, 590), (280, 560)], fill=(231, 76, 60, 255))
        draw.ellipse([190, 140, 410, 380], fill=(255, 219, 172, 255))
        draw.ellipse([170, 90, 430, 250], fill=(44, 62, 80, 255))
        draw.ellipse([240, 240, 270, 280], fill=(44, 62, 80, 255))
        draw.ellipse([330, 240, 360, 280], fill=(44, 62, 80, 255))
        draw.ellipse([245, 245, 255, 258], fill=(255, 255, 255, 255))
        draw.ellipse([335, 245, 345, 258], fill=(255, 255, 255, 255))
        draw.rounded_rectangle([220, 225, 285, 290], radius=10, outline=(20, 20, 20, 255), width=6)
        draw.rounded_rectangle([315, 225, 380, 290], radius=10, outline=(20, 20, 20, 255), width=6)
        draw.line([285, 255, 315, 255], fill=(20, 20, 20, 255), width=5)
        draw.arc([270, 290, 330, 340], start=20, end=160, fill=(192, 57, 43, 255), width=6)
        return avatar

    def build_video(
        self,
        image_a_path: Path,
        image_b_path: Path,
        character_path: Optional[Path] = None,
        topic: str = "",
        name_a: str = "",
        name_b: str = "",
        timeline: List[SegmentTimeline] = None,
        master_audio_path: Path = None,
        output_video_path: Path = None,
        custom_bg_path: Optional[Path] = None,
        character_poses: Optional[Dict[str, Path]] = None,
        watermark_logo_path: Optional[Path] = None,
        watermark_text: Optional[str] = None,
        watermark_opacity: float = 0.75,
        round_assets: Optional[Dict[int, Dict[str, Any]]] = None,
        subtitle_style: str = "clean_floating",
        subtitle_anim: str = "typewriter",
    ) -> Path:
        """Main video rendering pipeline with animated pointing and synchronized highlights."""
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        print("[VideoBuilder] Pre-rendering visual layers...")

        # 1. Base Background
        if custom_bg_path and Path(custom_bg_path).exists():
            bg_base = Image.open(custom_bg_path).convert("RGBA")
            bg_base = bg_base.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
            dim_overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 35))
            bg_base = Image.alpha_composite(bg_base, dim_overlay)
        else:
            bg_base = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), self.bg_color + (255,))

        # 2. Topic Banner
        topic_img = self._render_topic_banner(topic)
        bg_base.paste(topic_img, (TOPIC_BOX["x"], TOPIC_BOX["y"]), topic_img)

        # 3. Label Badges & Box Images (Single-topic vs Multi-topic Round Assets)
        prepared_rounds: Dict[int, Dict[str, Image.Image]] = {}
        if round_assets:
            for r_num, r_data in round_assets.items():
                r_name_a = r_data.get("name_a", name_a)
                r_name_b = r_data.get("name_b", name_b)
                r_img_a_path = r_data.get("image_a_path", image_a_path)
                r_img_b_path = r_data.get("image_b_path", image_b_path)

                r_badge_a = self._render_label_badge(f"A: {r_name_a}", COLOR_BADGE_A, LABEL_A_RECT["w"])
                r_badge_b = self._render_label_badge(f"B: {r_name_b}", COLOR_BADGE_B, LABEL_B_RECT["w"])
                r_box_a = self._prepare_box_image(r_img_a_path, BOX_A_RECT["w"], BOX_A_RECT["h"], BOX_A_RECT["radius"])
                r_box_b = self._prepare_box_image(r_img_b_path, BOX_B_RECT["w"], BOX_B_RECT["h"], BOX_B_RECT["radius"])
                prepared_rounds[r_num] = {
                    "badge_a": r_badge_a,
                    "badge_b": r_badge_b,
                    "box_a": r_box_a,
                    "box_b": r_box_b,
                }
        else:
            badge_a = self._render_label_badge(f"A: {name_a}", COLOR_BADGE_A, LABEL_A_RECT["w"])
            badge_b = self._render_label_badge(f"B: {name_b}", COLOR_BADGE_B, LABEL_B_RECT["w"])
            bg_base.paste(badge_a, (LABEL_A_RECT["x"], LABEL_A_RECT["y"]), badge_a)
            bg_base.paste(badge_b, (LABEL_B_RECT["x"], LABEL_B_RECT["y"]), badge_b)

            box_a_img = self._prepare_box_image(image_a_path, BOX_A_RECT["w"], BOX_A_RECT["h"], BOX_A_RECT["radius"])
            box_b_img = self._prepare_box_image(image_b_path, BOX_B_RECT["w"], BOX_B_RECT["h"], BOX_B_RECT["radius"])
            bg_base.paste(box_a_img, (BOX_A_RECT["x"], BOX_A_RECT["y"]), box_a_img)
            bg_base.paste(box_b_img, (BOX_B_RECT["x"], BOX_B_RECT["y"]), box_b_img)

        # 5. Pre-render Border Frames
        pad = 20
        border_a_inactive = self._render_box_frame(BOX_A_RECT, is_active=False)
        border_a_active = self._render_box_frame(BOX_A_RECT, is_active=True, pulse_val=1.0)
        border_b_inactive = self._render_box_frame(BOX_B_RECT, is_active=False)
        border_b_active = self._render_box_frame(BOX_B_RECT, is_active=True, pulse_val=1.0)

        # 6. Pre-render Subtitles with Progressive Typewriter Speech Reveal
        thai_cluster_re = re.compile(r'[\u0E40-\u0E44]?[\u0E01-\u0E2E][\u0E30-\u0E3A\u0E47-\u0E4E]*|[A-Za-z0-9]+|\s+|.')
        subtitle_progressions: Dict[str, List[Image.Image]] = {}
        for seg in (timeline or []):
            text = seg.text.strip()
            r_lbl = getattr(seg, "round_label", "")
            clusters = thai_cluster_re.findall(text)
            steps = []
            if len(clusters) > 1 and subtitle_anim == "typewriter":
                total_c = len(clusters)
                num_steps = max(8, min(24, total_c))
                for s_i in range(1, num_steps + 1):
                    c_idx = max(1, int(total_c * (s_i / num_steps)))
                    partial = "".join(clusters[:c_idx])
                    steps.append(self._render_subtitle_card(partial, r_lbl, style=subtitle_style))
            else:
                steps = [self._render_subtitle_card(text, r_lbl, style=subtitle_style)]

            if not steps:
                steps = [self._render_subtitle_card(text, r_lbl, style=subtitle_style)]
            subtitle_progressions[seg.segment_id] = steps

        default_sub_card = self._render_subtitle_card(f"กำลังเปรียบเทียบ: {name_a} vs {name_b}", style=subtitle_style)

        # 7. Animated Pointing Indicator
        pointer_img = self._render_pointing_indicator("กำลังพูดถึง 👇")
        pointer_w, pointer_h = pointer_img.size
        pos_x_a = (BOX_A_RECT["x"] + BOX_A_RECT["w"] // 2) - (pointer_w // 2)
        pos_x_b = (BOX_B_RECT["x"] + BOX_B_RECT["w"] // 2) - (pointer_w // 2)
        base_pointer_y = BOX_A_RECT["y"] - pointer_h - 10

        # 8. Character Sprite Poses & Mouth Flaps
        poses = self._prepare_character_poses(character_path=character_path, character_poses=character_poses)

        # 8b. Anti-Theft Dynamic Watermark Badge
        watermark_badge = self._render_watermark_badge(
            logo_path=watermark_logo_path,
            text=watermark_text,
            opacity=watermark_opacity,
        )

        # Read audio duration
        audio_clip = AudioFileClip(str(master_audio_path))
        total_duration = audio_clip.duration
        print(f"[VideoBuilder] Rendering video with active pointers (Duration: {total_duration:.2f}s, FPS: {FPS})...")

        def make_frame(t: float) -> np.ndarray:
            frame = bg_base.copy()

            is_speaking = False
            active_target = "none"
            active_card = default_sub_card
            active_seg_id = ""
            active_seg = None

            for seg in (timeline or []):
                if seg.start_time <= t <= seg.end_time:
                    is_speaking = True
                    active_target = seg.highlight_target
                    active_seg_id = seg.segment_id
                    active_seg = seg
                    break

            if active_seg:
                step_list = subtitle_progressions.get(active_seg.segment_id, [default_sub_card])
                dur = max(0.1, active_seg.duration)
                # Progressive reveal reaches full sentence at 82% of audio duration so viewer can read smoothly
                rel_p = max(0.0, min(1.0, (t - active_seg.start_time) / (dur * 0.82)))
                step_idx = min(len(step_list) - 1, int(rel_p * len(step_list)))
                active_card = step_list[step_idx]
            else:
                active_card = default_sub_card

            # If multi-round assets are configured, dynamically paste active round images & badges
            if prepared_rounds:
                active_round = 1
                if active_seg_id.startswith("round_"):
                    try:
                        active_round = int(active_seg_id.split("_")[1])
                    except Exception:
                        active_round = 1
                elif active_seg_id == "conclusion":
                    active_round = max(prepared_rounds.keys())

                r_cur = prepared_rounds.get(active_round) or prepared_rounds.get(1)
                if r_cur:
                    frame.paste(r_cur["badge_a"], (LABEL_A_RECT["x"], LABEL_A_RECT["y"]), r_cur["badge_a"])
                    frame.paste(r_cur["badge_b"], (LABEL_B_RECT["x"], LABEL_B_RECT["y"]), r_cur["badge_b"])
                    frame.paste(r_cur["box_a"], (BOX_A_RECT["x"], BOX_A_RECT["y"]), r_cur["box_a"])
                    frame.paste(r_cur["box_b"], (BOX_B_RECT["x"], BOX_B_RECT["y"]), r_cur["box_b"])

            # Composite Borders & Highlight
            bob = int(math.sin(t * 6.0) * 4)  # Bouncy animation

            if active_target == "A":
                frame.paste(border_a_active, (BOX_A_RECT["x"] - pad, BOX_A_RECT["y"] - pad), border_a_active)
                frame.paste(border_b_inactive, (BOX_B_RECT["x"] - pad, BOX_B_RECT["y"] - pad), border_b_inactive)

            elif active_target == "B":
                frame.paste(border_a_inactive, (BOX_A_RECT["x"] - pad, BOX_A_RECT["y"] - pad), border_a_inactive)
                frame.paste(border_b_active, (BOX_B_RECT["x"] - pad, BOX_B_RECT["y"] - pad), border_b_active)

            else:
                frame.paste(border_a_inactive, (BOX_A_RECT["x"] - pad, BOX_A_RECT["y"] - pad), border_a_inactive)
                frame.paste(border_b_inactive, (BOX_B_RECT["x"] - pad, BOX_B_RECT["y"] - pad), border_b_inactive)

            # Composite Subtitle Card
            frame.paste(active_card, (SUBTITLE_BOX["x"], SUBTITLE_BOX["y"]), active_card)

            # 9. Dynamic Mascot Pose Selection & Mouth-Flap
            if active_target == "A":
                current_pose_key = "point_a"
            elif active_target == "B":
                current_pose_key = "point_b"
            else:
                if active_seg_id == "hook" or "hook" in active_seg_id or (not active_seg_id and t < total_duration * 0.20):
                    current_pose_key = "thinking"
                elif active_seg_id in ["conclusion", "affiliate_comment"] or "conclusion" in active_seg_id or (not active_seg_id and t > total_duration * 0.80):
                    current_pose_key = "neutral"
                else:
                    current_pose_key = "thinking"

            # Mouth Flap State
            if is_speaking:
                # Talking flap frequency ~7.5 Hz (matches Thai syllables)
                mouth_state = "open" if (int(t * 7.5) % 2 == 1) else "closed"
            else:
                mouth_state = "closed"

            # Check for GIF animated frames
            pose_dict = poses.get(current_pose_key, poses.get("neutral", poses.get("point_a")))
            if is_speaking and "frames" in pose_dict and len(pose_dict["frames"]) > 1:
                f_list = pose_dict["frames"]
                char_sprite = f_list[int(t * 8) % len(f_list)]
            else:
                char_sprite = pose_dict.get(mouth_state, pose_dict.get("closed"))

            char_w, char_h = char_sprite.size

            # Ground-anchored full-body placement (feet at ground level, head close to subtitles)
            ground_y = CHARACTER_BOX.get("ground_y", 1780)
            char_x = (CANVAS_WIDTH - char_w) // 2
            char_y = ground_y - char_h

            # Ensure head doesn't collide into subtitle card
            sub_bottom = SUBTITLE_BOX["y"] + SUBTITLE_BOX["h"]
            if char_y < sub_bottom + 12:
                char_y = sub_bottom + 12

            # Subtle studio contact shadow under feet for a grounded, professional look
            shadow_w = max(40, int(char_w * 0.55))
            shadow_h = 24
            shadow_x = (CANVAS_WIDTH - shadow_w) // 2
            shadow_y = min(CANVAS_HEIGHT - 30, char_y + char_h - 10)
            shadow_img = Image.new("RGBA", (shadow_w, shadow_h), (0, 0, 0, 0))
            s_draw = ImageDraw.Draw(shadow_img)
            s_draw.ellipse([0, 0, shadow_w, shadow_h], fill=(0, 0, 0, 35))
            frame.paste(shadow_img, (shadow_x, shadow_y), shadow_img)

            frame.paste(char_sprite, (char_x, char_y), char_sprite)

            # 10. Anti-Theft Dynamic Watermark Badge (Relocates safely per round)
            if watermark_badge:
                if "round_1" in active_seg_id:
                    z_idx = 1
                elif "round_2" in active_seg_id:
                    z_idx = 2
                elif "round_3" in active_seg_id:
                    z_idx = 3
                elif "conclusion" in active_seg_id:
                    z_idx = 1
                else:
                    z_idx = 0
                zone = WATERMARK_SAFE_ZONES[z_idx % len(WATERMARK_SAFE_ZONES)]
                frame.paste(watermark_badge, (zone["x"], zone["y"]), watermark_badge)

            return np.array(frame.convert("RGB"))

        # Save Cover Thumbnail
        cover_frame_np = make_frame(min(2.0, total_duration / 2))
        cover_img = Image.fromarray(cover_frame_np)
        cover_path = output_video_path.parent / f"{output_video_path.stem}_cover.jpg"
        cover_img.save(cover_path, "JPEG", quality=95)
        print(f"[VideoBuilder] Cover thumbnail saved: {cover_path}")

        video = VideoClip(make_frame, duration=total_duration)
        video = video.with_audio(audio_clip)

        video.write_videofile(
            str(output_video_path),
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            ffmpeg_params=["-crf", "22", "-pix_fmt", "yuv420p"],
            logger="bar",
        )

        video.close()
        audio_clip.close()

        # Free memory buffers immediately
        import gc
        gc.collect()
        self._cleanup_old_temp_files()

        print(f"[VideoBuilder] Video exported successfully: {output_video_path}")
        return output_video_path

    def _cleanup_old_temp_files(self, max_age_hours: int = 2):
        """Removes temporary audio/image artifacts older than max_age_hours to prevent disk bloat."""
        import time
        now = time.time()
        cutoff = now - (max_age_hours * 3600)
        for p in TEMP_DIR.glob("*"):
            try:
                if p.is_file() and p.stat().st_mtime < cutoff:
                    p.unlink()
            except Exception:
                pass
