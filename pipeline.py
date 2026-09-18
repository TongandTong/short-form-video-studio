"""
Main Automation Pipeline CLI for Automated Short-Form Comparison Videos (9:16 Vertical).
Orchestrates AI Script Generation, Multi-segment TTS, Timeline Sync, and Video Rendering.
"""

import argparse
import json
import os
from pathlib import Path
import sys
import time

from config import (
    ASSETS_DIR,
    IMAGES_DIR,
    SCRIPTS_DIR,
    OUTPUT_DIR,
    COLOR_BG_CREAM,
    COLOR_HIGHLIGHT_LIME,
)
from ai_script_generator import AIScriptGenerator
from tts_engine import TTSEngine
from video_builder import VideoBuilder

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def hex_to_rgb(hex_str: str):
    """Convert hex string (e.g. #F5F2EB or F5F2EB) to RGB tuple."""
    clean = hex_str.lstrip("#")
    if len(clean) != 6:
        return (245, 242, 235)
    return tuple(int(clean[i : i + 2], 16) for i in (0, 2, 4))


def run_pipeline(
    topic: str,
    name_a: str,
    name_b: str,
    image_a: Path,
    image_b: Path,
    character: Path,
    script_data: dict,
    output_path: Path,
    voice: str = "edge_niwat",
    bg_color_hex: str = "#F5F2EB",
    highlight_color_hex: str = "#32CD32",
    custom_bg_path: Path = None,
    enable_bgm: bool = True,
    enable_sfx: bool = True,
) -> Path:
    """Execute the complete video creation pipeline."""
    print("=" * 60)
    print("🚀 STARTING AUTOMATED SHORT-FORM COMPARISON VIDEO PIPELINE")
    print("=" * 60)
    print(f"📌 Topic: {topic}")
    print(f"📦 Item A: {name_a} | Image: {image_a}")
    print(f"📦 Item B: {name_b} | Image: {image_b}")
    print(f"🎭 Character: {character}")
    print(f"🎙️ Voice: {voice}")
    print(f"🎨 Background Color: {bg_color_hex} | Highlight: {highlight_color_hex}")

    # 1. Prepare/Verify Script
    print("\n[Step 1/3] Processing Script & Metadata...")
    print(f"  Hook: {script_data.get('hook', '')}")
    print(f"  Item A: {script_data.get('item_a', '')}")
    print(f"  Item B: {script_data.get('item_b', '')}")
    print(f"  CTA: {script_data.get('conclusion', '')}")
    if "affiliate_comment" in script_data:
        print("\n💬 [Affiliate Pinned Comment Preview]:")
        print("-" * 40)
        print(script_data["affiliate_comment"])
        print("-" * 40)

    # 2. Text-to-Speech & Exact Audio Timestamps
    print("\n[Step 2/3] Generating Audio & Computing Timeline...")
    tts = TTSEngine(voice_key=voice)
    master_audio_path = output_path.parent / f"{output_path.stem}_audio.mp3"
    timeline, master_audio_file, total_duration = tts.build_timeline(
        script_data=script_data,
        output_master_audio=master_audio_path,
        include_bgm=enable_bgm,
        include_sfx=enable_sfx,
    )

    print("\n  Segment Timeline:")
    for seg in timeline:
        print(
            f"    [{seg.start_time:5.2f}s -> {seg.end_time:5.2f}s] "
            f"Highlight: {seg.highlight_target:4} | {seg.text[:35]}..."
        )

    # 3. Video Rendering & Compositing
    print("\n[Step 3/3] Compositing & Rendering Video...")
    bg_rgb = hex_to_rgb(bg_color_hex)
    hl_rgb = hex_to_rgb(highlight_color_hex)

    builder = VideoBuilder(bg_color=bg_rgb, highlight_color=hl_rgb)
    final_video = builder.build_video(
        image_a_path=image_a,
        image_b_path=image_b,
        character_path=character,
        topic=topic,
        name_a=name_a,
        name_b=name_b,
        timeline=timeline,
        master_audio_path=master_audio_file,
        output_video_path=output_path,
        custom_bg_path=custom_bg_path,
    )

    # Save metadata summary
    meta_path = output_path.parent / f"{output_path.stem}_meta.json"
    metadata = {
        "topic": topic,
        "name_a": name_a,
        "name_b": name_b,
        "video_path": str(final_video),
        "total_duration_seconds": total_duration,
        "affiliate_pinned_comment": script_data.get("affiliate_comment", ""),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("✅ VIDEO GENERATION COMPLETE!")
    print(f"🎬 Video File: {final_video}")
    print(f"🖼️ Cover Image: {output_path.parent / f'{output_path.stem}_cover.jpg'}")
    print(f"📄 Metadata: {meta_path}")
    print("=" * 60)
    return final_video


def main():
    parser = argparse.ArgumentParser(
        description="Automated Short-Form Comparison Video Generation Pipeline (9:16 Vertical)"
    )
    parser.add_argument("--topic", type=str, default="กาแฟดริป VS กาแฟแคปซูล", help="Comparison Topic")
    parser.add_argument("--name_a", type=str, default="กาแฟดริป", help="Item A Name")
    parser.add_argument("--name_b", type=str, default="กาแฟแคปซูล", help="Item B Name")
    parser.add_argument("--image_a", type=str, default=str(IMAGES_DIR / "item_a_drip.png"), help="Path to Image A")
    parser.add_argument("--image_b", type=str, default=str(IMAGES_DIR / "item_b_capsule.png"), help="Path to Image B")
    parser.add_argument(
        "--character",
        type=str,
        default=str(IMAGES_DIR / "character_host.png"),
        help="Path to 2D Character Avatar PNG",
    )
    parser.add_argument("--script_file", type=str, default=None, help="Path to JSON script file")
    parser.add_argument(
        "--ai_draft",
        action="store_true",
        help="Generate script draft via Gemini AI before rendering",
    )
    parser.add_argument("--affiliate_a", type=str, default="", help="Affiliate Link for Item A")
    parser.add_argument("--affiliate_b", type=str, default="", help="Affiliate Link for Item B")
    parser.add_argument("--voice", type=str, default="edge_niwat", choices=["edge_niwat", "edge_premwadee", "gcloud_neural", "gtts_thai"], help="TTS Voice Preset")
    parser.add_argument("--no_bgm", action="store_true", help="Disable background music")
    parser.add_argument("--no_sfx", action="store_true", help="Disable transition sound effects")
    parser.add_argument("--bg_color", type=str, default="#F5F2EB", help="Background color hex")
    parser.add_argument("--highlight_color", type=str, default="#32CD32", help="Active highlight border color hex")
    parser.add_argument("--bg_image", type=str, default=None, help="Custom background image path")
    parser.add_argument("--output", type=str, default=None, help="Output MP4 file path")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run end-to-end generation immediately using default sample assets",
    )

    args = parser.parse_args()

    # Determine paths
    img_a = Path(args.image_a)
    img_b = Path(args.image_b)
    char_img = Path(args.character)
    custom_bg = Path(args.bg_image) if args.bg_image else None

    # Determine script data
    if args.ai_draft:
        print("\n✨ Generating script with Gemini AI...")
        generator = AIScriptGenerator()
        script_data = generator.generate_script(
            topic=args.topic,
            name_a=args.name_a,
            name_b=args.name_b,
            affiliate_link_a=args.affiliate_a,
            affiliate_link_b=args.affiliate_b,
        )
        # Save draft
        draft_path = SCRIPTS_DIR / f"draft_{int(time.time())}.json"
        with open(draft_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)
        print(f"Saved AI script draft: {draft_path}")
    elif args.script_file and Path(args.script_file).exists():
        with open(args.script_file, "r", encoding="utf-8") as f:
            script_data = json.load(f)
    else:
        # Fallback to sample script
        sample_path = SCRIPTS_DIR / "coffee_comparison.json"
        if sample_path.exists():
            with open(sample_path, "r", encoding="utf-8") as f:
                script_data = json.load(f)
        else:
            script_data = {
                "topic": args.topic,
                "name_a": args.name_a,
                "name_b": args.name_b,
                "hook": f"สองตัวนี้เลือกอะไรดี? มาดูความต่างระหว่าง {args.name_a} กับ {args.name_b} กันครับ!",
                "item_a": f"{args.name_a} ให้ความรู้สึกและรสชาติที่เป็นธรรมชาติ ดึงจุดเด่นออกมาได้เต็มที่",
                "item_b": f"ส่วน {args.name_b} ตอบโจทย์ความสะดวก รวดเร็ว และรสชาติมาตรฐานทุกครั้ง",
                "conclusion": "คุณชอบสไตล์ไหน คอมเมนต์บอกกันหน่อย ส่วนพิกัดของแท้ราคาโปร แปะไว้ในคอมเมนต์แล้วครับ!",
                "affiliate_comment": f"📍 พิกัดของแท้ราคาโปร:\n👉 {args.name_a}: {args.affiliate_a or '[ลิงก์ A]'}\n👉 {args.name_b}: {args.affiliate_b or '[ลิงก์ B]'}\nจิ้มดูได้เลยครับ!",
            }

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c if c.isalnum() else "_" for c in args.name_a)[:10]
        output_file = OUTPUT_DIR / f"shorts_{safe_name}_{timestamp}.mp4"

    run_pipeline(
        topic=args.topic,
        name_a=args.name_a,
        name_b=args.name_b,
        image_a=img_a,
        image_b=img_b,
        character=char_img,
        script_data=script_data,
        output_path=output_file,
        voice=args.voice,
        bg_color_hex=args.bg_color,
        highlight_color_hex=args.highlight_color,
        custom_bg_path=custom_bg,
        enable_bgm=not args.no_bgm,
        enable_sfx=not args.no_sfx,
    )


if __name__ == "__main__":
    main()
