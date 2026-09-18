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
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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
)
from tts_engine import SegmentTimeline

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

    def _render_label_badge(self, text: str, bg_color: Tuple[int, int, int], width: int) -> Image.Image:
        """Renders name label under item box."""
        badge = Image.new("RGBA", (width, 50), (0, 0, 0, 0))
        draw = ImageDraw.Draw(badge)
        draw.rounded_rectangle([20, 0, width - 20, 50], radius=15, fill=bg_color + (255,))
        font = self._load_font(26, bold=True)
        draw.text((width // 2, 25), text, font=font, fill=COLOR_WHITE, anchor="mm")
        return badge

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = font.getbbox(test_line)
            line_w = bbox[2] - bbox[0]
            if line_w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)
        return lines if lines else [text]

    def _render_subtitle_card(self, text: str) -> Image.Image:
        """Renders subtitle card with high-contrast text and semi-transparent backdrop."""
        w, h = SUBTITLE_BOX["w"], SUBTITLE_BOX["h"]
        card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)

        draw.rounded_rectangle(
            [0, 0, w, h],
            radius=SUBTITLE_BOX["radius"],
            fill=(255, 255, 255, 240),
            outline=(210, 205, 195, 200),
            width=2,
        )

        font = self._load_font(40, bold=True)
        lines = self._wrap_text(text, font, max_width=w - 80)

        line_height = 55
        total_text_h = len(lines) * line_height
        start_y = (h - total_text_h) // 2 + 25

        for i, line in enumerate(lines):
            y = start_y + (i * line_height)
            draw.text((w // 2 + 1, y + 1), line, font=font, fill=(180, 180, 180), anchor="mm")
            draw.text((w // 2, y), line, font=font, fill=COLOR_TEXT_DARK, anchor="mm")

        return card

    def _prepare_character_sprite(self, char_path: Path) -> Image.Image:
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
        character_path: Path,
        topic: str,
        name_a: str,
        name_b: str,
        timeline: List[SegmentTimeline],
        master_audio_path: Path,
        output_video_path: Path,
        custom_bg_path: Optional[Path] = None,
    ) -> Path:
        """Main video rendering pipeline with animated pointing and synchronized highlights."""
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        print("[VideoBuilder] Pre-rendering visual layers...")

        # 1. Base Background
        if custom_bg_path and custom_bg_path.exists():
            bg_base = Image.open(custom_bg_path).convert("RGBA")
            bg_base = bg_base.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
        else:
            bg_base = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), self.bg_color + (255,))

        # 2. Topic Banner
        topic_img = self._render_topic_banner(topic)
        bg_base.paste(topic_img, (TOPIC_BOX["x"], TOPIC_BOX["y"]), topic_img)

        # 3. Label Badges
        badge_a = self._render_label_badge(f"A: {name_a}", COLOR_BADGE_A, LABEL_A_RECT["w"])
        badge_b = self._render_label_badge(f"B: {name_b}", COLOR_BADGE_B, LABEL_B_RECT["w"])
        bg_base.paste(badge_a, (LABEL_A_RECT["x"], LABEL_A_RECT["y"]), badge_a)
        bg_base.paste(badge_b, (LABEL_B_RECT["x"], LABEL_B_RECT["y"]), badge_b)

        # 4. Box Images A and B
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

        # 6. Pre-render Subtitle Cards
        subtitle_cards: Dict[str, Image.Image] = {}
        for seg in timeline:
            subtitle_cards[seg.segment_id] = self._render_subtitle_card(seg.text)
        default_sub_card = self._render_subtitle_card(f"กำลังเปรียบเทียบ: {name_a} vs {name_b}")

        # 7. Animated Pointing Indicator
        pointer_img = self._render_pointing_indicator("กำลังพูดถึง 👇")
        pointer_w, pointer_h = pointer_img.size
        # Target X coordinates (center of Box A = 277, center of Box B = 803)
        pos_x_a = (BOX_A_RECT["x"] + BOX_A_RECT["w"] // 2) - (pointer_w // 2)
        pos_x_b = (BOX_B_RECT["x"] + BOX_B_RECT["w"] // 2) - (pointer_w // 2)
        base_pointer_y = BOX_A_RECT["y"] - pointer_h - 10

        # 8. Character Sprite
        char_sprite = self._prepare_character_sprite(character_path)
        char_w, char_h = char_sprite.size
        char_x = (CANVAS_WIDTH - char_w) // 2
        base_char_y = CANVAS_HEIGHT - char_h + 30

        # Read audio duration
        audio_clip = AudioFileClip(str(master_audio_path))
        total_duration = audio_clip.duration
        print(f"[VideoBuilder] Rendering video with active pointers (Duration: {total_duration:.2f}s, FPS: {FPS})...")

        def make_frame(t: float) -> np.ndarray:
            frame = bg_base.copy()

            active_target = "none"
            active_card = default_sub_card

            for seg in timeline:
                if seg.start_time <= t <= seg.end_time:
                    active_target = seg.highlight_target
                    active_card = subtitle_cards.get(seg.segment_id, default_sub_card)
                    break

            # Composite Borders & Pointer
            bob = int(math.sin(t * 6.0) * 4)  # Bouncy animation

            if active_target == "A":
                frame.paste(border_a_active, (BOX_A_RECT["x"] - pad, BOX_A_RECT["y"] - pad), border_a_active)
                frame.paste(border_b_inactive, (BOX_B_RECT["x"] - pad, BOX_B_RECT["y"] - pad), border_b_inactive)
                # Show pointer above Box A
                frame.paste(pointer_img, (pos_x_a, base_pointer_y + bob), pointer_img)

            elif active_target == "B":
                frame.paste(border_a_inactive, (BOX_A_RECT["x"] - pad, BOX_A_RECT["y"] - pad), border_a_inactive)
                frame.paste(border_b_active, (BOX_B_RECT["x"] - pad, BOX_B_RECT["y"] - pad), border_b_active)
                # Show pointer above Box B
                frame.paste(pointer_img, (pos_x_b, base_pointer_y + bob), pointer_img)

            else:
                frame.paste(border_a_inactive, (BOX_A_RECT["x"] - pad, BOX_A_RECT["y"] - pad), border_a_inactive)
                frame.paste(border_b_inactive, (BOX_B_RECT["x"] - pad, BOX_B_RECT["y"] - pad), border_b_inactive)

            # Composite Subtitle Card
            frame.paste(active_card, (SUBTITLE_BOX["x"], SUBTITLE_BOX["y"]), active_card)

            # Composite Character Sprite
            breathe_offset = int(math.sin(t * 3.2) * 5)
            frame.paste(char_sprite, (char_x, base_char_y + breathe_offset), char_sprite)

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

        print(f"[VideoBuilder] Video exported successfully: {output_video_path}")
        return output_video_path
