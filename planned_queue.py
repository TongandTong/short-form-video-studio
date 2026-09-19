"""
Planned Production Queue Manager for VSIFY Studio.
Allows users to prepare, review, and queue multiple comparison topics in advance:
- Accurate pre-selected/uploaded Image A & Image B
- Dedicated Affiliate links A & B
- Execution mode: 'render_only' or 'render_and_post'
- Jump-to-top / Priority queueing for breaking news or urgent topics
- FIFO ordering with move up / move down / delete controls
"""

import json
import os
from pathlib import Path
import shutil
import time
from typing import List, Dict, Any, Optional

from config import BASE_DIR, ASSETS_DIR

PLANNED_QUEUE_FILE = BASE_DIR / "planned_queue.json"
QUEUE_ASSETS_DIR = ASSETS_DIR / "queue"
QUEUE_ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def load_planned_queue() -> List[Dict[str, Any]]:
    """Loads all planned queue items from disk, sorted by current queue order."""
    if not PLANNED_QUEUE_FILE.exists():
        return []
    try:
        with open(PLANNED_QUEUE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception as e:
        print(f"[PlannedQueue] Error loading queue: {e}")
    return []


def save_planned_queue(items: List[Dict[str, Any]]) -> bool:
    """Persists planned queue items to disk."""
    try:
        with open(PLANNED_QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[PlannedQueue] Error saving queue: {e}")
        return False


def save_queue_image_asset(item_id: str, side: str, src_path_or_bytes) -> Optional[str]:
    """
    Saves an image permanently into assets/queue/{item_id}_{side}.png.
    Accepts a filepath (str or Path) or raw bytes.
    Returns the absolute path string.
    """
    target_path = QUEUE_ASSETS_DIR / f"{item_id}_{side}.png"
    try:
        if isinstance(src_path_or_bytes, (str, Path)):
            src_p = Path(src_path_or_bytes)
            if src_p.exists():
                shutil.copy2(src_p, target_path)
                return str(target_path)
        elif isinstance(src_path_or_bytes, bytes):
            with open(target_path, "wb") as f:
                f.write(src_path_or_bytes)
            return str(target_path)
    except Exception as e:
        print(f"[PlannedQueue] Failed to save queue image {item_id}_{side}: {e}")
    return None


def add_to_planned_queue(
    topic: str,
    name_a: str,
    name_b: str,
    script_data: Dict[str, Any],
    image_a_path: Optional[str] = None,
    image_b_path: Optional[str] = None,
    affiliate_link_a: str = "",
    affiliate_link_b: str = "",
    post_mode: str = "render_only",  # 'render_only' or 'render_and_post'
    jump_to_top: bool = False,
    details_a: str = "",
    details_b: str = "",
    target_audience: str = "",
    key_angles: str = "",
    framework: str = "persona",
    duration_mode: str = "standard_3round",
) -> Dict[str, Any]:
    """
    Creates a new queue entry and appends or inserts at top.
    Images are safely copied into assets/queue/ to prevent accidental loss.
    """
    t_now = int(time.time())
    item_id = f"pq_{t_now}_{os.urandom(2).hex()}"

    # Safely persist images
    saved_img_a = save_queue_image_asset(item_id, "a", image_a_path) if image_a_path else ""
    saved_img_b = save_queue_image_asset(item_id, "b", image_b_path) if image_b_path else ""

    item = {
        "id": item_id,
        "topic": topic,
        "name_a": name_a,
        "name_b": name_b,
        "details_a": details_a,
        "details_b": details_b,
        "target_audience": target_audience,
        "key_angles": key_angles,
        "framework": framework,
        "duration_mode": duration_mode,
        "script_data": script_data,
        "image_a_path": saved_img_a or (image_a_path or ""),
        "image_b_path": saved_img_b or (image_b_path or ""),
        "affiliate_link_a": affiliate_link_a,
        "affiliate_link_b": affiliate_link_b,
        "post_mode": post_mode,
        "priority": jump_to_top,
        "status": "ready",  # 'ready', 'draft', 'processing', 'completed', 'error'
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t_now)),
        "completed_at": None,
        "video_path": None,
        "cover_path": None,
        "error_message": None,
    }

    queue = load_planned_queue()
    if jump_to_top:
        # Insert at the beginning of the queue (ahead of pending items)
        queue.insert(0, item)
    else:
        queue.append(item)

    save_planned_queue(queue)
    return item


def update_planned_item(item_id: str, updates: Dict[str, Any]) -> bool:
    """Updates an existing item's fields by ID."""
    queue = load_planned_queue()
    found = False
    for item in queue:
        if item.get("id") == item_id:
            item.update(updates)
            found = True
            break
    if found:
        return save_planned_queue(queue)
    return False


def delete_planned_item(item_id: str) -> bool:
    """Removes an item from the queue and cleans up its dedicated queue images."""
    queue = load_planned_queue()
    new_queue = []
    found = False
    for item in queue:
        if item.get("id") == item_id:
            found = True
            # Clean up queue assets
            for side in ["a", "b"]:
                f_path = QUEUE_ASSETS_DIR / f"{item_id}_{side}.png"
                if f_path.exists():
                    try:
                        f_path.unlink()
                    except Exception:
                        pass
        else:
            new_queue.append(item)

    if found:
        return save_planned_queue(new_queue)
    return False


def move_queue_item(item_id: str, direction: str) -> bool:
    """
    Moves an item 'up', 'down', or 'top' (jump to top) in queue order.
    Preserves all other items untouched.
    """
    queue = load_planned_queue()
    idx = -1
    for i, item in enumerate(queue):
        if item.get("id") == item_id:
            idx = i
            break

    if idx == -1:
        return False

    if direction == "up" and idx > 0:
        queue[idx - 1], queue[idx] = queue[idx], queue[idx - 1]
    elif direction == "down" and idx < len(queue) - 1:
        queue[idx + 1], queue[idx] = queue[idx], queue[idx + 1]
    elif direction == "top" and idx > 0:
        target = queue.pop(idx)
        target["priority"] = True
        queue.insert(0, target)
    else:
        return False

    return save_planned_queue(queue)


def get_next_ready_queue_item() -> Optional[Dict[str, Any]]:
    """
    Returns the first item in the queue that has status == 'ready'.
    Respects FIFO queue order and priority placements.
    """
    queue = load_planned_queue()
    for item in queue:
        if item.get("status") == "ready":
            return item
    return None
