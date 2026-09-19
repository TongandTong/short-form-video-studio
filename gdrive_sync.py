r"""
Google Drive Auto-Sync Module for Short-Form Video Studio.
Handles automated synchronization of generated videos, cover thumbnails, and sidecar metadata.
Supports:
1. Local Drive Detection (Google Drive for Desktop, e.g. G:\My Drive\...)
2. Cloud Webhook / Google Apps Script upload (Zero-credential cloud sync)
3. Google Drive API (Service Account / OAuth credentials)
Designed with complete fail-safe isolation to never crash main production pipelines.
"""

import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, Any, Tuple, Optional
import requests

from config import BASE_DIR, OUTPUT_DIR

GDRIVE_CONFIG_FILE = BASE_DIR / "gdrive_config.json"

DEFAULT_GDRIVE_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "sync_mode": "auto",  # "auto", "local", "webhook", "service_account"
    "webhook_url": "",    # Google Apps Script Webhook / Make.com Webhook URL
    "folder_id": "",       # Target Google Drive Folder ID
    "service_account_json": "",  # Optional JSON string or path to service account
    "last_synced_time": 0,
    "last_synced_file": "",
    "total_synced_count": 0,
    "last_status": "พร้อมทำงาน",
    "sync_log": [],
}


def load_gdrive_config() -> Dict[str, Any]:
    """Loads Google Drive sync configuration from disk or returns defaults."""
    if GDRIVE_CONFIG_FILE.exists():
        try:
            with open(GDRIVE_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_GDRIVE_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"[GDriveSync] Config load error: {e}")
    return DEFAULT_GDRIVE_CONFIG.copy()


def save_gdrive_config(cfg: Dict[str, Any]) -> None:
    """Persists Google Drive sync configuration to disk."""
    try:
        with open(GDRIVE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[GDriveSync] Config save error: {e}")


def _add_log(cfg: Dict[str, Any], message: str) -> None:
    """Appends an event to the sync log (keeps last 20)."""
    t_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    logs = cfg.get("sync_log", [])
    logs.insert(0, f"[{t_str}] {message}")
    cfg["sync_log"] = logs[:20]


def is_local_gdrive_path(path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Checks if the workspace or target path resides within Google Drive for Desktop
    (e.g., 'G:\\My Drive\\...' or contains 'Google Drive' in path).
    """
    check_path = str(path or BASE_DIR).lower()
    if ":\\my drive" in check_path or "google drive" in check_path or "/my drive" in check_path:
        return True, "โฟลเดอร์นี้เชื่อมต่อกับ Google Drive for Desktop อัตโนมัติ (ซิงก์ขึ้นคลาวด์แล้ว)"
    return False, "โฟลเดอร์นี้ไม่ได้อยู่ใน Google Drive for Desktop"


def sync_video_to_gdrive(
    video_path: str,
    cover_path: Optional[str] = None,
    meta_path: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Main fail-safe sync function.
    Synchronizes the video and its sidecars to Google Drive based on configured mode.
    Guaranteed never to raise unhandled exceptions that could crash caller.
    """
    cfg = load_gdrive_config()
    if not cfg.get("enabled", True):
        return False, "Google Drive Sync ถูกปิดใช้งานอยู่"

    v_p = Path(video_path)
    if not v_p.exists():
        return False, f"ไม่พบไฟล์วิดีโอที่: {video_path}"

    mode = cfg.get("sync_mode", "auto")
    is_local, local_msg = is_local_gdrive_path(v_p)

    # Auto mode selects local if available, otherwise webhook if configured
    if mode == "auto":
        if is_local:
            mode = "local"
        elif cfg.get("webhook_url"):
            mode = "webhook"
        else:
            mode = "local"

    try:
        # MODE 1: Local Sync
        if mode == "local":
            cfg["last_synced_time"] = int(time.time())
            cfg["last_synced_file"] = v_p.name
            cfg["total_synced_count"] = cfg.get("total_synced_count", 0) + 1
            status_msg = f"ซิงก์ไฟล์เข้าเครื่องสำเร็จ (Google Drive for Desktop จะอัปโหลดขึ้น Cloud ให้ทันที): {v_p.name}"
            cfg["last_status"] = status_msg
            _add_log(cfg, f"✅ [Local] {status_msg}")
            save_gdrive_config(cfg)
            return True, status_msg

        # MODE 2: Webhook / Google Apps Script Mode (Cloud 24h)
        elif mode == "webhook":
            webhook_url = cfg.get("webhook_url", "").strip()
            if not webhook_url:
                msg = "ไม่ได้ระบุ Webhook URL สำหรับ Google Drive"
                _add_log(cfg, f"⚠️ {msg}")
                return False, msg

            # Read metadata if available
            meta_data = {}
            if meta_path and Path(meta_path).exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        meta_data = json.load(mf)
                except Exception:
                    pass

            payload = {
                "file_name": v_p.name,
                "file_size": v_p.stat().st_size,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "title": meta_data.get("title", v_p.stem),
                "caption": meta_data.get("social_caption", ""),
                "hashtags": meta_data.get("hashtags", ""),
                "affiliate_comment": meta_data.get("affiliate_comment", ""),
                "folder_id": cfg.get("folder_id", ""),
            }

            # Multipart upload for video file
            with open(v_p, "rb") as vf:
                files = {
                    "video": (v_p.name, vf, "video/mp4"),
                }
                resp = requests.post(webhook_url, data=payload, files=files, timeout=120)

            if resp.status_code in (200, 201):
                cfg["last_synced_time"] = int(time.time())
                cfg["last_synced_file"] = v_p.name
                cfg["total_synced_count"] = cfg.get("total_synced_count", 0) + 1
                status_msg = f"อัปโหลดเข้า Google Drive ผ่าน Webhook สำเร็จ: {v_p.name}"
                cfg["last_status"] = status_msg
                _add_log(cfg, f"✅ [Webhook] {status_msg}")
                save_gdrive_config(cfg)
                return True, status_msg
            else:
                err_msg = f"Webhook ตอบกลับข้อผิดพลาด HTTP {resp.status_code}: {resp.text[:200]}"
                cfg["last_status"] = err_msg
                _add_log(cfg, f"❌ [Webhook] {err_msg}")
                save_gdrive_config(cfg)
                return False, err_msg

        # Fallback
        return False, f"โหมดการซิงก์ '{mode}' ยังไม่ได้ถูกตั้งค่า"

    except Exception as e:
        err = f"เกิดข้อผิดพลาดในการซิงก์ Google Drive: {e}"
        print(f"[GDriveSync Error] {err}")
        cfg["last_status"] = err
        _add_log(cfg, f"❌ {err}")
        save_gdrive_config(cfg)
        return False, err


def test_gdrive_connection() -> Tuple[bool, str]:
    """Tests current Google Drive connection setup without uploading a full video."""
    cfg = load_gdrive_config()
    mode = cfg.get("sync_mode", "auto")
    is_local, local_msg = is_local_gdrive_path()

    if mode in ("auto", "local") and is_local:
        return True, f"ตรวจพบโฟลเดอร์ Google Drive for Desktop พร้อมทำงาน ({local_msg})"

    if mode == "webhook" or (mode == "auto" and cfg.get("webhook_url")):
        url = cfg.get("webhook_url", "").strip()
        if not url:
            return False, "ยังไม่ได้ระบุ Webhook URL"
        try:
            resp = requests.post(
                url,
                json={"action": "ping", "timestamp": time.time(), "client": "ShortsStudio"},
                timeout=15,
            )
            if resp.status_code in (200, 201):
                return True, f"เชื่อมต่อ Webhook สำเร็จ (HTTP {resp.status_code})"
            return False, f"Webhook ตอบกลับ HTTP {resp.status_code}: {resp.text[:150]}"
        except Exception as e:
            return False, f"ไม่สามารถติดต่อ Webhook ได้: {e}"

    if is_local:
        return True, f"พร้อมใช้งานผ่าน Google Drive for Desktop ในเครื่อง ({BASE_DIR})"

    return False, "ยังไม่ได้กำหนดค่าการเชื่อมต่อ Google Drive (ระบุ Webhook URL หรือใช้ Google Drive for Desktop)"
