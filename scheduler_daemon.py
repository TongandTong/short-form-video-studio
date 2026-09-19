"""
Autonomous Background Scheduler Daemon for 24/7 Video Production.
Runs as a background daemon thread that generates short-form comparison videos,
social captions, hashtags, and affiliate comments on a configurable hourly schedule.
Prepares all video files and JSON metadata sidecars for future automated social posting.
"""

import json
import os
from pathlib import Path
import threading
import time
import traceback
from typing import Dict, Any, Tuple, Optional

from config import (
    BASE_DIR,
    OUTPUT_DIR,
    ASSETS_DIR,
    IMAGES_DIR,
    load_channel_profile,
    get_active_character_assets,
)
from ai_script_generator import (
    AIScriptGenerator,
    get_random_idea,
    generate_social_caption,
    FRAMEWORK_PRESETS,
    DURATION_MODES,
    CATEGORIES,
)
from tts_engine import TTSEngine
from video_builder import VideoBuilder
from pipeline import hex_to_rgb
from image_fetcher import auto_fetch_or_create_image
from content_history import add_history_entry

AUTOPILOT_CONFIG_FILE = BASE_DIR / "autopilot_config.json"

DEFAULT_AUTOPILOT_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "interval_hours": 3.0,
    "last_run_timestamp": 0,
    "next_run_timestamp": 0,
    "default_affiliate_a": "https://shopee.co.th",
    "default_affiliate_b": "https://shopee.co.th",
    "target_category": "ทั้งหมด (สุ่มทุกหมวด)",
    "target_framework": "all",
    "target_duration_mode": "standard_3round",
    "auto_search_images": True,
    "status": "idle",  # "idle", "running", "error"
    "last_run_status": "พร้อมทำงาน",
    "last_topic": "",
    "last_video_path": "",
    "total_generated": 0,
    "history_log": [],
}

# Global process lock to ensure only one video renders at a time
_scheduler_lock = threading.Lock()
_daemon_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def load_autopilot_config() -> Dict[str, Any]:
    """Loads scheduler configuration from disk or returns defaults."""
    if AUTOPILOT_CONFIG_FILE.exists():
        try:
            with open(AUTOPILOT_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_AUTOPILOT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"[Scheduler] Config load error: {e}")
    return DEFAULT_AUTOPILOT_CONFIG.copy()


def save_autopilot_config(cfg: Dict[str, Any]) -> None:
    """Persists scheduler configuration to disk."""
    try:
        with open(AUTOPILOT_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Scheduler] Config save error: {e}")


def _add_log(cfg: Dict[str, Any], message: str) -> None:
    """Appends an event to the circular log list (keeps last 20)."""
    t_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logs = cfg.get("history_log", [])
    logs.insert(0, f"[{t_str}] {message}")
    cfg["history_log"] = logs[:20]


def run_autopilot_cycle(is_manual: bool = False) -> Tuple[bool, str]:
    """
    Executes a single autonomous production pipeline run:
    1. Picks viral topic according to schedule filters.
    2. Deep AI research & script synthesis with fallback affiliate links.
    3. Auto-fetches/generates image assets for A and B.
    4. Neural Voice synthesis & BGM/SFX audio mastering.
    5. 1080x1920 MP4 Video rendering + Cover thumbnail.
    6. Saves social caption, hashtags, and affiliate comment to history & sidecar JSON.
    """
    if not _scheduler_lock.acquire(blocking=False):
        return False, "ระบบกำลังเรนเดอร์วิดีโออยู่ กรุณารอสักครู่"

    cfg = load_autopilot_config()
    cfg["status"] = "running"
    trigger_type = "ผู้ใช้สั่งรันทันที" if is_manual else "ระบบตั้งเวลาอัตโนมัติ"
    cfg["last_run_status"] = f"กำลังดำเนินการผลิต ({trigger_type})..."
    _add_log(cfg, f"🚀 เริ่มผลิตคลิป ({trigger_type})")
    save_autopilot_config(cfg)

    try:
        t_start = time.time()
        t_now = int(t_start)

        # 1. Pick viral idea
        cat = cfg.get("target_category", "ทั้งหมด (สุ่มทุกหมวด)")
        fw = cfg.get("target_framework", "all")
        dur_mode = cfg.get("target_duration_mode", "standard_3round")
        template = get_random_idea(category=cat, framework=fw)

        topic = template["topic"]
        name_a = template["name_a"]
        name_b = template["name_b"]
        details_a = template.get("details_a", "")
        details_b = template.get("details_b", "")
        target_audience = template.get("target_audience", "")
        key_angles = template.get("key_angles", "")
        
        # Affiliate links with fallback
        aff_a = template.get("affiliate_link_a") or cfg.get("default_affiliate_a", "https://shopee.co.th")
        aff_b = template.get("affiliate_link_b") or cfg.get("default_affiliate_b", "https://shopee.co.th")
        chosen_fw = template.get("framework", fw if fw != "all" else "persona")

        profile = load_channel_profile()
        outro_cta = profile.get("default_outro_cta", "")

        _add_log(cfg, f"🤖 AI Deep Research: '{topic}' ({name_a} vs {name_b})")
        save_autopilot_config(cfg)

        # 2. AI Script Generation
        gen = AIScriptGenerator()
        script_data = gen.generate_script(
            topic=topic,
            name_a=name_a,
            name_b=name_b,
            details_a=details_a,
            details_b=details_b,
            target_audience=target_audience,
            key_angles=key_angles,
            affiliate_link_a=aff_a,
            affiliate_link_b=aff_b,
            script_mode=dur_mode,
            channel_outro_cta=outro_cta,
            framework=chosen_fw,
        )

        # 3. Auto-fetch Images
        allow_search = cfg.get("auto_search_images", True)
        img_mode = profile.get("default_image_mode", "ai_cartoon")
        img_a_path = ASSETS_DIR / "images" / f"auto_a_{t_now}.png"
        img_b_path = ASSETS_DIR / "images" / f"auto_b_{t_now}.png"
        auto_fetch_or_create_image(name_a, img_a_path, is_item_b=False, allow_web_search=allow_search, image_mode=img_mode)
        time.sleep(0.5)
        auto_fetch_or_create_image(name_b, img_b_path, is_item_b=True, allow_web_search=allow_search, image_mode=img_mode)

        # 4. Neural Voice & Audio Mixing
        output_mp4 = OUTPUT_DIR / f"shorts_autopilot_{t_now}.mp4"
        master_audio = output_mp4.parent / f"{output_mp4.stem}_audio.mp3"
        tts = TTSEngine(voice_key="edge_niwat", speech_rate="+10%", speech_pitch="+2Hz")
        timeline, audio_file, total_duration = tts.build_timeline(
            script_data=script_data,
            output_master_audio=master_audio,
            include_bgm=True,
            bgm_volume=0.12,
            include_sfx=True,
        )

        # 5. Video Rendering
        builder = VideoBuilder(
            bg_color=hex_to_rgb("#F5F2EB"),
            highlight_color=hex_to_rgb("#32CD32"),
            animation_style="pointer_and_border",
        )
        wm_text = profile.get("watermark_text", "@WhyItWorks")
        wm_opac = float(profile.get("watermark_opacity", 0.75))
        saved_logo = profile.get("logo_path", "")
        wm_logo = Path(saved_logo) if saved_logo and Path(saved_logo).exists() else None

        char_path, char_poses = get_active_character_assets(profile)

        final_video = builder.build_video(
            image_a_path=img_a_path,
            image_b_path=img_b_path,
            character_path=char_path,
            character_poses=char_poses,
            topic=topic,
            name_a=name_a,
            name_b=name_b,
            timeline=timeline,
            master_audio_path=audio_file,
            output_video_path=output_mp4,
            watermark_logo_path=wm_logo,
            watermark_text=wm_text,
            watermark_opacity=wm_opac,
        )

        cover_path = output_mp4.parent / f"{output_mp4.stem}_cover.jpg"

        # 6. Save Social Caption, Hashtags & Sidecar Metadata for auto-posting
        caption_dict = generate_social_caption(script_data)
        social_cap = script_data.get("social_caption") or caption_dict.get("social_caption", "")
        hashtags = script_data.get("hashtags") or caption_dict.get("hashtags", "")
        aff_comm = script_data.get("affiliate_comment", "")

        # Save sidecar metadata JSON (ready for auto-posting scripts / webhooks)
        sidecar_meta = {
            "title": topic,
            "video_path": str(final_video),
            "cover_path": str(cover_path) if cover_path.exists() else None,
            "social_caption": social_cap,
            "hashtags": hashtags,
            "affiliate_comment": aff_comm,
            "name_a": name_a,
            "name_b": name_b,
            "framework": chosen_fw,
            "duration_seconds": round(total_duration, 1),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_now)),
            "autopilot": True,
        }
        meta_path = output_mp4.parent / f"{output_mp4.stem}_meta.json"
        try:
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(sidecar_meta, mf, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # 7. Add to Central History
        add_history_entry(
            topic=topic,
            name_a=name_a,
            name_b=name_b,
            video_path=str(final_video),
            cover_path=str(cover_path) if cover_path.exists() else None,
            social_caption=social_cap,
            hashtags=hashtags,
            affiliate_comment=aff_comm,
            framework=chosen_fw,
            duration_mode=dur_mode,
            duration_seconds=total_duration,
        )

        # 8. Fail-safe Google Drive Sync
        try:
            from gdrive_sync import sync_video_to_gdrive
            gd_ok, gd_msg = sync_video_to_gdrive(
                video_path=str(final_video),
                cover_path=str(cover_path) if cover_path.exists() else None,
                meta_path=str(meta_path) if meta_path.exists() else None,
            )
            if gd_ok:
                _add_log(cfg, f"☁️ GDrive: {gd_msg}")
        except Exception as gde:
            _add_log(cfg, f"⚠️ GDrive Sync: {gde}")

        # 9. Fail-safe Multi-Platform Auto-Posting (Facebook Reels, YouTube Shorts, TikTok Webhook)
        try:
            from autopost_engine import publish_to_all_enabled
            post_results = publish_to_all_enabled(
                video_path=str(final_video),
                cover_path=str(cover_path) if cover_path.exists() else None,
                meta_path=str(meta_path) if meta_path.exists() else None,
            )
            for plat, (p_ok, p_msg) in post_results.items():
                p_icon = "🚀" if p_ok else "⚠️"
                _add_log(cfg, f"{p_icon} [{plat.upper()}] {p_msg}")
        except Exception as ape:
            _add_log(cfg, f"⚠️ Auto-Post: {ape}")

        # 10. Update Scheduler Config
        elapsed = round(time.time() - t_start, 1)
        cfg = load_autopilot_config()  # reload fresh
        cfg["status"] = "idle"
        cfg["last_run_timestamp"] = t_now
        interval_secs = int(float(cfg.get("interval_hours", 3.0)) * 3600)
        cfg["next_run_timestamp"] = t_now + interval_secs
        cfg["last_topic"] = topic
        cfg["last_video_path"] = str(final_video)
        cfg["total_generated"] = cfg.get("total_generated", 0) + 1
        cfg["last_run_status"] = f"สำเร็จ ({elapsed}s) - {topic}"
        _add_log(cfg, f"✅ ผลิตสำเร็จใน {elapsed}s: {topic}")
        save_autopilot_config(cfg)

        msg = f"ผลิตคลิปสำเร็จ: '{topic}' ({total_duration:.1f} วินาที)"
        print(f"[Scheduler] {msg}")
        return True, msg

    except Exception as e:
        err_msg = f"เกิดข้อผิดพลาด: {e}"
        print(f"[Scheduler Error] {traceback.format_exc()}")
        cfg = load_autopilot_config()
        cfg["status"] = "error"
        cfg["last_run_status"] = f"เกิดข้อผิดพลาด: {e}"
        _add_log(cfg, f"❌ ผิดพลาด: {e}")
        save_autopilot_config(cfg)
        return False, err_msg

    finally:
        _scheduler_lock.release()


def _worker_loop():
    """Background thread loop that checks timers and triggers automated production."""
    print("[Scheduler Daemon] Started background worker loop.")
    while not _stop_event.is_set():
        try:
            cfg = load_autopilot_config()
            if cfg.get("enabled", False):
                now = time.time()
                next_run = cfg.get("next_run_timestamp", 0)
                interval_hours = float(cfg.get("interval_hours", 3.0))
                interval_secs = int(interval_hours * 3600)

                # Initialize next_run if not set or corrupted
                if next_run == 0 or next_run < (now - interval_secs * 2):
                    next_run = now + interval_secs
                    cfg["next_run_timestamp"] = next_run
                    save_autopilot_config(cfg)

                if now >= next_run:
                    print(f"[Scheduler Daemon] Timer fired! Starting autopilot production...")
                    run_autopilot_cycle(is_manual=False)

            # Sleep in short increments for responsive shutdown
            for _ in range(15):
                if _stop_event.is_set():
                    break
                time.sleep(1)

        except Exception as loop_e:
            print(f"[Scheduler Daemon] Loop exception: {loop_e}")
            time.sleep(10)


def ensure_scheduler_running():
    """Starts the background worker thread if not already active."""
    global _daemon_thread
    if _daemon_thread is None or not _daemon_thread.is_alive():
        _stop_event.clear()
        _daemon_thread = threading.Thread(target=_worker_loop, name="WhyItWorks_Scheduler", daemon=True)
        _daemon_thread.start()
        print("[Scheduler Daemon] Launched worker thread.")


def is_scheduler_alive() -> bool:
    """Checks if the background daemon thread is currently running."""
    global _daemon_thread
    return _daemon_thread is not None and _daemon_thread.is_alive()


def run_autopilot_batch(count: int = 3, progress_callback=None) -> Tuple[int, int, list]:
    """
    Produces multiple videos in sequence (stockpiling clips).
    Yields or reports progress, cleans up resources after each run.
    Returns (success_count, fail_count, list_of_messages).
    """
    import gc
    success_count = 0
    fail_count = 0
    results = []

    for i in range(1, count + 1):
        msg_start = f"กำลังสร้างคลิปที่ {i}/{count}..."
        if progress_callback:
            progress_callback(i, count, msg_start)
        print(f"[Batch Producer] {msg_start}")
        
        ok, res_msg = run_autopilot_cycle(is_manual=True)
        if ok:
            success_count += 1
            results.append(f"คลิปที่ {i}: สำเร็จ ({res_msg})")
        else:
            fail_count += 1
            results.append(f"คลิปที่ {i}: ไม่สำเร็จ ({res_msg})")

        # Memory garbage collection between heavy video renders
        gc.collect()
        time.sleep(2)

    return success_count, fail_count, results

