"""
Shopee Auto-Affiliate Module for Short-Form Video Studio.
Enables automated generation of Shopee affiliate tracking links:
1. Shopee Affiliate Open API (GraphQL generateShortLink) using App ID & Secret
2. Custom Universal Tracking Link generator (with your Shopee Affiliate Sub-ID / Affiliate ID)
3. Auto-Matcher: Automatically finds & attaches Shopee affiliate links to products A & B
"""

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Dict, Any, Tuple, Optional, List
import requests

from config import BASE_DIR

SHOPEE_CONFIG_FILE = BASE_DIR / "shopee_config.json"

DEFAULT_SHOPEE_CONFIG: Dict[str, Any] = {
    "enabled": True,
    "app_id": "",           # Shopee Affiliate Open API App ID
    "secret": "",           # Shopee Affiliate Open API Secret
    "affiliate_id": "",     # Your Shopee Affiliate Username/ID (e.g. whyitworks)
    "default_shop_url": "https://shopee.co.th",
    "auto_shorten": True,
    "sub_ids": ["WhyItWorks", "ShortsVideo"],
}


def load_shopee_config() -> Dict[str, Any]:
    """Loads Shopee affiliate configuration from disk."""
    if SHOPEE_CONFIG_FILE.exists():
        try:
            with open(SHOPEE_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = DEFAULT_SHOPEE_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            print(f"[ShopeeAffiliate] Config load error: {e}")
    return DEFAULT_SHOPEE_CONFIG.copy()


def save_shopee_config(cfg: Dict[str, Any]) -> None:
    """Persists Shopee affiliate configuration to disk."""
    try:
        with open(SHOPEE_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ShopeeAffiliate] Config save error: {e}")


def generate_shopee_affiliate_link(
    original_url: str,
    sub_id: Optional[str] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """
    Converts a standard Shopee product URL or search term into an Affiliate Tracking Link.
    Uses Official Shopee Affiliate Open API if credentials exist,
    otherwise formats a direct Shopee search/product affiliate link.
    """
    if not original_url or not original_url.strip():
        return False, "URL ว่างเปล่า"

    if cfg is None:
        cfg = load_shopee_config()

    url_clean = original_url.strip()
    app_id = cfg.get("app_id", "").strip()
    secret = cfg.get("secret", "").strip()
    sub1 = sub_id or (cfg.get("sub_ids", ["WhyItWorks"])[0] if cfg.get("sub_ids") else "WhyItWorks")

    # If already an affiliate link, return as is
    if "s.shopee.co.th" in url_clean or "shope.ee" in url_clean:
        return True, url_clean

    # If it's just a product name (e.g. "กาแฟดริป"), turn it into a Shopee search URL
    if not url_clean.startswith("http://") and not url_clean.startswith("https://"):
        import urllib.parse
        encoded_query = urllib.parse.quote(url_clean)
        url_clean = f"https://shopee.co.th/search?keyword={encoded_query}"

    # Method 1: Official Shopee Affiliate Open API (GraphQL)
    if app_id and secret:
        try:
            timestamp = int(time.time())
            # Signature calculation: SHA256(app_id + timestamp + payload + secret)
            payload_str = json.dumps({
                "query": f'mutation {{ generateShortLink(input: {{ originUrl: "{url_clean}", subIds: ["{sub1}"] }}) {{ shortLink }} }}'
            })
            sign_str = f"{app_id}{timestamp}{payload_str}{secret}"
            signature = hashlib.sha256(sign_str.encode("utf-8")).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}",
            }

            resp = requests.post(
                "https://open-api.affiliate.shopee.co.th/graphql",
                headers=headers,
                data=payload_str,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                short_link = (
                    data.get("data", {})
                    .get("generateShortLink", {})
                    .get("shortLink")
                )
                if short_link:
                    return True, short_link
        except Exception as e:
            print(f"[ShopeeAffiliate] API conversion error: {e}")

    # Method 2: Smart Universal Link Generator (Fallback)
    aff_id = cfg.get("affiliate_id", "").strip()
    delimiter = "&" if "?" in url_clean else "?"
    if aff_id:
        fallback_link = f"{url_clean}{delimiter}utm_source=an_{aff_id}&utm_medium=affiliates&utm_campaign={sub1}"
    else:
        fallback_link = f"{url_clean}{delimiter}utm_medium=affiliates&utm_campaign={sub1}"

    return True, fallback_link


def auto_generate_affiliate_comments(
    name_a: str,
    name_b: str,
    link_a: Optional[str] = None,
    link_b: Optional[str] = None,
    cfg: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates a ready-to-pin Affiliate comment with converted Shopee links.
    """
    if cfg is None:
        cfg = load_shopee_config()

    # Convert or fallback link A
    target_a = link_a.strip() if link_a and link_a.strip() else name_a
    _, aff_link_a = generate_shopee_affiliate_link(target_a, sub_id="ItemA", cfg=cfg)

    # Convert or fallback link B
    target_b = link_b.strip() if link_b and link_b.strip() else name_b
    _, aff_link_b = generate_shopee_affiliate_link(target_b, sub_id="ItemB", cfg=cfg)

    comment_template = (
        f"📍 พิกัดของแท้และราคาโปรโมชั่นพิเศษ:\n"
        f"👉 ฝั่ง A ({name_a}): {aff_link_a}\n"
        f"👉 ฝั่ง B ({name_b}): {aff_link_b}\n\n"
        f"(ใครชอบตัวไหน คอมเมนต์โหวตกันได้เลยนะครับ 👇)"
    )
    return comment_template
