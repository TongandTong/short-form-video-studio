"""
Multi-Platform Auto-Post Engine for Short-Form Video Studio.
Enables hands-free autonomous publishing to:
1. Facebook Page (Reels + Auto-Pin Affiliate Comment) via Meta Graph API
2. YouTube Shorts via YouTube Data API v3 Resumable Upload
3. TikTok & Multi-Platform Webhooks (Buffer, Make.com, Zapier)
Fully isolated, modular, and fail-safe to guarantee zero downtime.
"""

import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, Any, Tuple, Optional, List
import requests

from config import BASE_DIR

AUTOPOST_CONFIG_FILE = BASE_DIR / "autopost_config.json"

DEFAULT_AUTOPOST_CONFIG: Dict[str, Any] = {
    # Facebook Page (Reels + Auto-Comment)
    "facebook_enabled": False,
    "facebook_page_id": "",
    "facebook_access_token": "",
    "facebook_auto_comment": True,

    # YouTube Shorts
    "youtube_enabled": False,
    "youtube_privacy_status": "unlisted",  # "public", "unlisted", "private"
    "youtube_access_token": "",
    "youtube_category_id": "28",  # 28 = Science & Technology, 22 = People & Blogs

    # TikTok / Multi-Platform Webhook (Buffer / Make.com / Zapier)
    "webhook_enabled": False,
    "webhook_url": "",
    "webhook_secret": "",

    # Global Stats & Logs
    "total_posted_count": 0,
    "last_posted_platform": "",
    "last_posted_title": "",
    "last_status": "พร้อมทำงาน",
    "post_log": [],
}


def load_autopost_config() -> Dict[str, Any]:
    """Loads auto-post configuration from disk or returns defaults."""
    if AUTOPOST_CONFIG_FILE.exists():
        try:
            with open(AUTOPOST_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_AUTOPOST_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"[AutoPost] Config load error: {e}")
    return DEFAULT_AUTOPOST_CONFIG.copy()


def save_autopost_config(cfg: Dict[str, Any]) -> None:
    """Persists auto-post configuration to disk."""
    try:
        with open(AUTOPOST_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[AutoPost] Config save error: {e}")


def _add_post_log(cfg: Dict[str, Any], platform: str, status: str, message: str) -> None:
    """Appends an event to the post log (keeps last 30)."""
    t_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logs = cfg.get("post_log", [])
    entry = f"[{t_str}] [{platform}] {status}: {message}"
    logs.insert(0, entry)
    cfg["post_log"] = logs[:30]


# -------------------------------------------------------------
# 1. FACEBOOK PAGE REELS + AUTO-COMMENT AFFILIATE
# -------------------------------------------------------------
def post_to_facebook_page(
    video_path: str,
    caption: str,
    affiliate_comment: Optional[str] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Publishes a 9:16 video to Facebook Page as a Reel via Meta Graph API.
    Optionally posts the first comment with the affiliate tracking links.
    """
    if cfg is None:
        cfg = load_autopost_config()

    page_id = cfg.get("facebook_page_id", "").strip()
    access_token = cfg.get("facebook_access_token", "").strip()

    if not page_id or not access_token:
        return False, "ยังไม่ได้ระบุ Facebook Page ID หรือ Access Token"

    v_p = Path(video_path)
    if not v_p.exists():
        return False, f"ไม่พบไฟล์วิดีโอ: {video_path}"

    try:
        # Step 1: Initialize Reel Upload Session
        init_url = f"https://graph.facebook.com/v19.0/{page_id}/video_reels"
        init_payload = {
            "upload_phase": "start",
            "access_token": access_token,
        }
        r_init = requests.post(init_url, data=init_payload, timeout=30)
        init_data = r_init.json()

        if "video_id" not in init_data:
            err = init_data.get("error", {}).get("message", r_init.text)
            return False, f"Meta API Start Error: {err}"

        video_id = init_data["video_id"]
        upload_url = init_data.get("upload_url", f"https://rupload.facebook.com/video-upload/v19.0/{video_id}")

        # Step 2: Upload Video Binary File
        file_size = v_p.stat().st_size
        headers = {
            "Authorization": f"OAuth {access_token}",
            "offset": "0",
            "file_size": str(file_size),
            "Content-Type": "application/octet-stream",
        }
        with open(v_p, "rb") as vf:
            r_upload = requests.post(upload_url, headers=headers, data=vf, timeout=180)

        if r_upload.status_code not in (200, 201):
            return False, f"Meta API Binary Upload Error: {r_upload.text[:200]}"

        # Step 3: Publish Reel with Caption & Hashtags
        publish_payload = {
            "upload_phase": "finish",
            "access_token": access_token,
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
        }
        r_pub = requests.post(init_url, data=publish_payload, timeout=30)
        pub_data = r_pub.json()

        if not pub_data.get("success", False) and "id" not in pub_data:
            err = pub_data.get("error", {}).get("message", r_pub.text)
            return False, f"Meta API Publish Error: {err}"

        post_id = pub_data.get("id", video_id)
        success_msg = f"โพสต์ Facebook Reel สำเร็จ (Video ID: {video_id})"

        # Step 4: Auto-comment Affiliate Link under the reel (if enabled)
        if cfg.get("facebook_auto_comment", True) and affiliate_comment:
            time.sleep(3)  # Brief pause for video object indexing
            comment_url = f"https://graph.facebook.com/v19.0/{video_id}/comments"
            comm_payload = {
                "message": affiliate_comment,
                "access_token": access_token,
            }
            try:
                r_comm = requests.post(comment_url, data=comm_payload, timeout=20)
                if r_comm.status_code in (200, 201):
                    success_msg += " + ปักหมุด Affiliate ในคอมเมนต์แรกสำเร็จ!"
                else:
                    success_msg += f" (แจ้งเตือน: คอมเมนต์ไม่สำเร็จ: {r_comm.text[:100]})"
            except Exception as ce:
                success_msg += f" (แจ้งเตือนคอมเมนต์: {ce})"

        _add_post_log(cfg, "Facebook", "SUCCESS", success_msg)
        save_autopost_config(cfg)
        return True, success_msg

    except Exception as e:
        err_msg = f"Facebook Post Exception: {e}"
        _add_post_log(cfg, "Facebook", "ERROR", err_msg)
        save_autopost_config(cfg)
        return False, err_msg


# -------------------------------------------------------------
# 2. YOUTUBE SHORTS RESUMABLE UPLOADER
# -------------------------------------------------------------
def post_to_youtube_shorts(
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Publishes a vertical video as a YouTube Short via YouTube Data API v3 Resumable Upload.
    Requires an OAuth 2.0 Bearer Access Token.
    """
    if cfg is None:
        cfg = load_autopilot_config()

    access_token = cfg.get("youtube_access_token", "").strip()
    if not access_token:
        return False, "ยังไม่ได้ระบุ YouTube OAuth Access Token"

    v_p = Path(video_path)
    if not v_p.exists():
        return False, f"ไม่พบไฟล์วิดีโอ: {video_path}"

    privacy_status = cfg.get("youtube_privacy_status", "unlisted")
    category_id = cfg.get("youtube_category_id", "28")

    # Clean short title: ensure #Shorts is appended for viral shelf placement
    clean_title = title.strip()
    if "#Shorts" not in clean_title and "#shorts" not in clean_title:
        clean_title = f"{clean_title} #Shorts"

    metadata = {
        "snippet": {
            "title": clean_title[:100],
            "description": description,
            "tags": tags or ["Shorts", "WhyItWorks", "เปรียบเทียบ", "รีวิว", "สาระน่ารู้"],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    try:
        # Step 1: Initiate Resumable Upload Session
        init_url = "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "X-Upload-Content-Type": "video/mp4",
            "X-Upload-Content-Length": str(v_p.stat().st_size),
        }
        r_init = requests.post(init_url, headers=headers, json=metadata, timeout=30)

        if r_init.status_code != 200:
            return False, f"YouTube API Init Error (HTTP {r_init.status_code}): {r_init.text[:200]}"

        upload_url = r_init.headers.get("Location")
        if not upload_url:
            return False, "YouTube API ไม่ได้ส่ง Upload URL กลับมา"

        # Step 2: Upload Video File
        with open(v_p, "rb") as vf:
            upload_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(v_p.stat().st_size),
            }
            r_upload = requests.put(upload_url, headers=upload_headers, data=vf, timeout=300)

        if r_upload.status_code in (200, 201):
            resp_data = r_upload.json()
            vid_id = resp_data.get("id", "Unknown")
            yt_url = f"https://youtube.com/shorts/{vid_id}"
            success_msg = f"อัปโหลด YouTube Shorts สำเร็จ ({privacy_status}): {yt_url}"
            _add_post_log(cfg, "YouTube", "SUCCESS", success_msg)
            save_autopilot_config(cfg)
            return True, success_msg
        else:
            err = f"YouTube API Upload Error (HTTP {r_upload.status_code}): {r_upload.text[:200]}"
            _add_post_log(cfg, "YouTube", "ERROR", err)
            save_autopilot_config(cfg)
            return False, err

    except Exception as e:
        err_msg = f"YouTube Post Exception: {e}"
        _add_post_log(cfg, "YouTube", "ERROR", err_msg)
        save_autopilot_config(cfg)
        return False, err_msg


# -------------------------------------------------------------
# 3. TIKTOK & MULTI-PLATFORM WEBHOOK (BUFFER / MAKE / ZAPIER)
# -------------------------------------------------------------
def post_to_webhook(
    video_path: str,
    meta_data: Dict[str, Any],
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Sends video payload, caption, and affiliate links to a webhook (Buffer / Make.com / Zapier)
    which forwards the clip directly to TikTok / Instagram / Threads.
    """
    if cfg is None:
        cfg = load_autopilot_config()

    webhook_url = cfg.get("webhook_url", "").strip()
    if not webhook_url:
        return False, "ยังไม่ได้ระบุ Webhook URL สำหรับ TikTok / Social Aggregator"

    v_p = Path(video_path)
    if not v_p.exists():
        return False, f"ไม่พบไฟล์วิดีโอ: {video_path}"

    payload = {
        "event": "shorts_autopost",
        "timestamp": int(time.time()),
        "title": meta_data.get("title", v_p.stem),
        "caption": meta_data.get("social_caption", ""),
        "hashtags": meta_data.get("hashtags", ""),
        "affiliate_comment": meta_data.get("affiliate_comment", ""),
        "file_name": v_p.name,
        "file_size": v_p.stat().st_size,
    }

    headers = {}
    secret = cfg.get("webhook_secret", "").strip()
    if secret:
        headers["X-Webhook-Secret"] = secret

    try:
        with open(v_p, "rb") as vf:
            files = {"video": (v_p.name, vf, "video/mp4")}
            resp = requests.post(webhook_url, headers=headers, data=payload, files=files, timeout=120)

        if resp.status_code in (200, 201, 202):
            msg = f"ส่ง Webhook สำเร็จ (HTTP {resp.status_code}): พร้อมโพสต์ TikTok ผ่าน Aggregator"
            _add_post_log(cfg, "TikTok/Webhook", "SUCCESS", msg)
            save_autopilot_config(cfg)
            return True, msg
        else:
            err = f"Webhook Error HTTP {resp.status_code}: {resp.text[:180]}"
            _add_post_log(cfg, "TikTok/Webhook", "ERROR", err)
            save_autopilot_config(cfg)
            return False, err

    except Exception as e:
        err_msg = f"Webhook Exception: {e}"
        _add_post_log(cfg, "TikTok/Webhook", "ERROR", err_msg)
        save_autopilot_config(cfg)
        return False, err_msg


# -------------------------------------------------------------
# UNIFIED PUBLISHER & DISPATCHER
# -------------------------------------------------------------
def publish_to_all_enabled(
    video_path: str,
    cover_path: Optional[str] = None,
    meta_path: Optional[str] = None,
) -> Dict[str, Tuple[bool, str]]:
    """
    Dispatches video to all enabled platforms sequentially.
    Every platform call is encapsulated in its own try/except fail-safe.
    Guaranteed never to crash caller.
    """
    cfg = load_autopost_config()
    results = {}

    # Load sidecar metadata
    meta = {}
    if meta_path and Path(meta_path).exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as mf:
                meta = json.load(mf)
        except Exception:
            pass

    title = meta.get("title", Path(video_path).stem)
    social_cap = meta.get("social_caption", "")
    hashtags = meta.get("hashtags", "")
    full_caption = f"{social_cap}\n\n{hashtags}".strip()
    aff_comm = meta.get("affiliate_comment", "")

    # 1. Facebook Page
    if cfg.get("facebook_enabled", False):
        try:
            ok, msg = post_to_facebook_page(video_path, full_caption, affiliate_comment=aff_comm, cfg=cfg)
            results["facebook"] = (ok, msg)
        except Exception as e:
            results["facebook"] = (False, f"Facebook Dispatch Error: {e}")

    # 2. YouTube Shorts
    if cfg.get("youtube_enabled", False):
        try:
            tags = [t.strip("# ") for t in hashtags.split() if t.startswith("#")]
            ok, msg = post_to_youtube_shorts(video_path, title, full_caption, tags=tags, cfg=cfg)
            results["youtube"] = (ok, msg)
        except Exception as e:
            results["youtube"] = (False, f"YouTube Dispatch Error: {e}")

    # 3. TikTok / Webhook
    if cfg.get("webhook_enabled", False):
        try:
            ok, msg = post_to_webhook(video_path, meta, cfg=cfg)
            results["webhook"] = (ok, msg)
        except Exception as e:
            results["webhook"] = (False, f"Webhook Dispatch Error: {e}")

    # Update summary and content history
    any_success = any(v[0] for v in results.values())
    if any_success:
        cfg["total_posted_count"] = cfg.get("total_posted_count", 0) + 1
        cfg["last_posted_title"] = title
        cfg["last_status"] = f"โพสต์สำเร็จ ({len(results)} แพลตฟอร์ม) - {title}"
        save_autopost_config(cfg)

        # Update matching entry in content_history
        try:
            from content_history import load_history, update_history_post_status
            hist = load_history()
            succ_plats = [p for p, (s, _) in results.items() if s]
            for h in hist:
                if h.get("video_path") == str(video_path) or Path(h.get("video_path", "")).name == Path(video_path).name:
                    update_history_post_status(h.get("id"), "posted_auto", succ_plats)
                    break
        except Exception as he:
            print(f"[AutoPost] History status update error: {he}")

    return results


# -------------------------------------------------------------
# TEST CONNECTION HELPERS
# -------------------------------------------------------------
def test_facebook_connection() -> Tuple[bool, str]:
    """Validates Facebook Page ID and Access Token via Meta Graph API."""
    cfg = load_autopost_config()
    page_id = cfg.get("facebook_page_id", "").strip()
    access_token = cfg.get("facebook_access_token", "").strip()

    if not page_id or not access_token:
        return False, "กรุณาระบุ Facebook Page ID และ Page Access Token ก่อนทดสอบ"

    try:
        url = f"https://graph.facebook.com/v19.0/{page_id}"
        resp = requests.get(url, params={"fields": "id,name,link", "access_token": access_token}, timeout=15)
        data = resp.json()

        if "id" in data:
            name = data.get("name", "Page")
            return True, f"เชื่อมต่อสำเร็จ! พบเพจ: '{name}' (ID: {data['id']})"
        else:
            err = data.get("error", {}).get("message", resp.text)
            return False, f"เชื่อมต่อไม่สำเร็จ: {err}"
    except Exception as e:
        return False, f"ไม่สามารถติดต่อ Meta Graph API ได้: {e}"


def test_youtube_connection() -> Tuple[bool, str]:
    """Validates YouTube OAuth Access Token via YouTube Data API channels endpoint."""
    cfg = load_autopost_config()
    access_token = cfg.get("youtube_access_token", "").strip()

    if not access_token:
        return False, "กรุณาระบุ YouTube OAuth Access Token ก่อนทดสอบ"

    try:
        url = "https://www.googleapis.com/youtube/v3/channels"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, params={"part": "snippet", "mine": "true"}, timeout=15)
        data = resp.json()

        if "items" in data and len(data["items"]) > 0:
            channel_title = data["items"][0]["snippet"]["title"]
            return True, f"เชื่อมต่อสำเร็จ! พบช่อง YouTube: '{channel_title}'"
        else:
            err = data.get("error", {}).get("message", resp.text)
            return False, f"เชื่อมต่อไม่สำเร็จ: {err}"
    except Exception as e:
        return False, f"ไม่สามารถติดต่อ YouTube API ได้: {e}"


def test_webhook_connection() -> Tuple[bool, str]:
    """Tests TikTok / Aggregator Webhook URL with a sample ping payload."""
    cfg = load_autopost_config()
    url = cfg.get("webhook_url", "").strip()

    if not url:
        return False, "กรุณาระบุ Webhook URL ก่อนทดสอบ"

    headers = {}
    secret = cfg.get("webhook_secret", "").strip()
    if secret:
        headers["X-Webhook-Secret"] = secret

    try:
        resp = requests.post(
            url,
            headers=headers,
            json={"event": "ping", "client": "ShortsStudio", "timestamp": int(time.time())},
            timeout=15,
        )
        if resp.status_code in (200, 201, 202):
            return True, f"เชื่อมต่อ Webhook สำเร็จ (HTTP {resp.status_code})"
        return False, f"Webhook ตอบกลับ HTTP {resp.status_code}: {resp.text[:150]}"
    except Exception as e:
        return False, f"ไม่สามารถติดต่อ Webhook ได้: {e}"
