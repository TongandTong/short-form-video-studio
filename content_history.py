"""
Content History and Production Library Tracker.
Stores generated videos, scripts, social captions, and affiliate comments locally
so users can easily re-access, re-download, or copy past captions.
"""

import json
import os
from pathlib import Path
import time
from typing import List, Dict, Any, Optional

from config import BASE_DIR

HISTORY_FILE = BASE_DIR / "content_history.json"


def load_history() -> List[Dict[str, Any]]:
    """Loads content generation history from disk and migrates schema if needed."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # Ensure post_status exists on all items
                modified = False
                for item in data:
                    if "post_status" not in item:
                        item["post_status"] = "draft"  # "draft", "posted_auto", "posted_manual"
                        item["post_platforms"] = []
                        item["posted_at"] = ""
                        modified = True
                if modified:
                    save_history(data)
                return data
            return []
    except Exception as e:
        print(f"[History] Load warning: {e}")
        return []


def save_history(history: List[Dict[str, Any]]) -> None:
    """Saves history list to disk."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[History] Save warning: {e}")


def add_history_entry(
    topic: str,
    name_a: str,
    name_b: str,
    video_path: Optional[str],
    cover_path: Optional[str],
    social_caption: str,
    hashtags: str,
    affiliate_comment: str,
    framework: str,
    duration_mode: str,
    duration_seconds: float = 0.0,
    post_status: str = "draft",
    post_platforms: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Appends a new video production record to history (keeps latest 50)."""
    history = load_history()
    t_now = int(time.time())
    entry = {
        "id": f"vid_{t_now}",
        "timestamp": t_now,
        "date_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_now)),
        "topic": topic,
        "name_a": name_a,
        "name_b": name_b,
        "video_path": str(video_path) if video_path else None,
        "cover_path": str(cover_path) if cover_path else None,
        "social_caption": social_caption,
        "hashtags": hashtags,
        "affiliate_comment": affiliate_comment,
        "framework": framework,
        "duration_mode": duration_mode,
        "duration_seconds": round(duration_seconds, 1),
        "post_status": post_status,  # "draft", "posted_auto", "posted_manual"
        "post_platforms": post_platforms or [],
        "posted_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_now)) if post_status != "draft" else "",
    }
    # Prepend new entry
    history.insert(0, entry)
    # Keep latest 50
    history = history[:50]
    save_history(history)
    return entry


def update_history_post_status(
    entry_id: str,
    post_status: str,
    platforms: Optional[List[str]] = None,
) -> bool:
    """Updates the posting status of a history entry (e.g. 'draft', 'posted_auto', 'posted_manual')."""
    history = load_history()
    updated = False
    for h in history:
        if h.get("id") == entry_id:
            h["post_status"] = post_status
            if post_status == "draft":
                h["posted_at"] = ""
                h["post_platforms"] = []
            else:
                h["posted_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                if platforms is not None:
                    h["post_platforms"] = platforms
            updated = True
            break
    if updated:
        save_history(history)
    return updated


def delete_history_entry(entry_id: str) -> None:
    """Deletes an entry by ID from history."""
    history = load_history()
    filtered = [h for h in history if h.get("id") != entry_id]
    save_history(filtered)
