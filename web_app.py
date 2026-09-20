"""
VSIFY — See Both. Know Better.
Short-Form Comparison Video Studio (9:16 Vertical).
Structured 5-Tab Production Architecture:
1. Script Studio (Input, AI Deep Research, Script Review & AI Rewriter)
2. Render Studio (Asset Manager, 1080x1920 Video Builder, Player & Caption Copy)
3. Auto-Pilot (24/7 Autonomous Daemon & Batch Stockpiling)
4. Queue & Post Manager (Post Status Tracker, Social Dispatch & Drive Sync)
5. Global Settings (One-Time Setup for Brand, Logo Upload, Voice, Avatar & APIs)
"""

import json
import os
from pathlib import Path
import socket
import sys
import time
from PIL import Image
import streamlit as st

# Page Configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="VSIFY — See Both. Know Better.",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import (
    ASSETS_DIR,
    IMAGES_DIR,
    SCRIPTS_DIR,
    OUTPUT_DIR,
    AUDIO_DIR,
    TEMP_DIR,
    COLOR_BG_CREAM,
    COLOR_HIGHLIGHT_LIME,
    load_channel_profile,
    save_channel_profile,
    DEFAULT_CHANNEL_PROFILE,
    get_active_character_assets,
)
from ai_script_generator import (
    AIScriptGenerator,
    get_random_idea,
    FRAMEWORK_PRESETS,
    DURATION_MODES,
    CATEGORIES,
    CLIP_TYPES,
    RELATION_TYPES,
    generate_social_caption,
    extract_names_from_topic,
)
from tts_engine import TTSEngine
from video_builder import VideoBuilder
from pipeline import hex_to_rgb
from image_fetcher import auto_fetch_or_create_image, CARTOON_STYLES, remove_fake_checkerboard_bg
from content_history import load_history, add_history_entry, delete_history_entry, update_history_post_status
from planned_queue import (
    load_planned_queue,
    save_planned_queue,
    add_to_planned_queue,
    update_planned_item,
    delete_planned_item,
    move_queue_item,
    get_next_ready_queue_item,
    save_queue_image_asset,
)
from scheduler_daemon import (
    ensure_scheduler_running,
    load_autopilot_config,
    save_autopilot_config,
    run_autopilot_cycle,
    run_autopilot_batch,
    run_planned_queue_batch,
    is_scheduler_alive,
)
from gdrive_sync import (
    load_gdrive_config,
    save_gdrive_config,
    sync_video_to_gdrive,
    test_gdrive_connection,
    is_local_gdrive_path,
)
from autopost_engine import (
    load_autopost_config,
    save_autopost_config,
    publish_to_all_enabled,
    test_facebook_connection,
    test_youtube_connection,
    test_webhook_connection,
)
from shopee_affiliate import (
    load_shopee_config,
    save_shopee_config,
    generate_shopee_affiliate_link,
    auto_generate_affiliate_comments,
)

# Start background autonomous daemon
ensure_scheduler_running()

# iOS Design System Stylesheet
st.markdown(
    """
    <style>
    /* Apple SF Pro Typography & Clean iOS Base */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        letter-spacing: -0.011em;
    }

    /* iOS Frosted Glass Header */
    .ios-header {
        background: linear-gradient(135deg, rgba(28, 28, 30, 0.95) 0%, rgba(44, 44, 46, 0.92) 100%);
        backdrop-filter: blur(25px) saturate(190%);
        -webkit-backdrop-filter: blur(25px) saturate(190%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 24px 30px;
        margin-bottom: 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
        color: #FFFFFF;
    }
    .ios-badge {
        display: inline-block;
        background: rgba(0, 122, 255, 0.2);
        border: 1px solid rgba(0, 122, 255, 0.4);
        color: #5AC8FA;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        padding: 4px 10px;
        border-radius: 9999px;
        margin-bottom: 8px;
    }

    /* Smooth Scrolling */
    html {
        scroll-behavior: smooth !important;
    }

    /* Prevent sticky breakage from overflow hidden */
    [data-testid="stAppViewContainer"],
    section[data-testid="stMain"],
    .main {
        overflow-x: clip !important;
    }

    /* iOS Segmented Control Tabs - Sticky & Locked at Top */
    div[data-baseweb="tab-list"],
    .stTabs [data-baseweb="tab-list"] {
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 3.4rem !important;
        z-index: 99999 !important;
        background: rgba(246, 246, 248, 0.96) !important;
        backdrop-filter: blur(25px) saturate(190%) !important;
        -webkit-backdrop-filter: blur(25px) saturate(190%) !important;
        border-radius: 16px !important;
        padding: 8px !important;
        gap: 8px !important;
        border: 1px solid rgba(0, 0, 0, 0.12) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.09) !important;
        margin-bottom: 22px !important;
    }
    div[data-baseweb="tab"] {
        border-radius: 10px !important;
        border: none !important;
        font-weight: 500 !important;
        color: #3C3C43 !important;
        padding: 8px 16px !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    div[data-baseweb="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.6) !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFFFFF !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.06) !important;
        color: #000000 !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* iOS Rounded Pill Buttons */
    .stButton > button {
        border-radius: 9999px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 0.5rem 1.3rem !important;
        border: 1px solid transparent !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #007AFF 0%, #0051D5 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(0, 122, 255, 0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) scale(1.01) !important;
        box-shadow: 0 6px 20px rgba(0, 122, 255, 0.45) !important;
    }
    .stButton > button[kind="secondary"] {
        background: #F2F2F7 !important;
        color: #007AFF !important;
        border: 1px solid rgba(0, 122, 255, 0.2) !important;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #E5E5EA !important;
        transform: translateY(-1px) !important;
    }
    .stButton > button:active {
        transform: scale(0.97) !important;
    }

    /* iOS Cards & Containers */
    .ios-card {
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 18px;
        padding: 20px 22px;
        margin-bottom: 18px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04), 0 2px 6px -1px rgba(0, 0, 0, 0.02);
    }

    /* iOS Rounded Inputs */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        border-radius: 12px !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {
        border-color: #007AFF !important;
        box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15) !important;
    }

    /* iOS Expanders */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        border-radius: 16px !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02) !important;
        overflow: hidden !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header
st.markdown(
    """
    <div class="ios-header">
        <div class="ios-badge"> VSIFY Studio • See Both. Know Better.</div>
        <h1 style="margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.02em;">⚡ VSIFY — Short-Form Video Studio</h1>
        <p style="margin: 6px 0 0 0; color: #AEAEB2; font-size: 14.5px; line-height: 1.45;">
            แพลตฟอร์มสร้างคลิปเปรียบเทียบ A vs B อัตโนมัติ (See Both. Know Better.) — AI Deep Research, เสียง Neural คนจริง, อนิเมชั่นตัวชี้, แคปชั่นไวรัล และระบบ Auto-Pilot 24 ชม.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Load Global Channel Profile
if "channel_profile" not in st.session_state:
    st.session_state.channel_profile = load_channel_profile()
prof = st.session_state.channel_profile

# Sidebar: Network, Status & Navigation
with st.sidebar:
    saved_logo = prof.get("logo_path", "")
    if saved_logo and Path(saved_logo).exists():
        st.image(saved_logo, width=130)
    st.markdown(f"### ⚡ {prof.get('channel_name', 'VSIFY')}")
    st.caption(f"*{prof.get('tagline', 'See Both. Know Better.')}*")
    st.divider()

    st.header("🌐 การเชื่อมต่อ")
    is_cloud = os.getenv("STREAMLIT_SHARING_HOST") is not None or "HOSTNAME" in os.environ and "streamlit" in os.environ.get("HOSTNAME", "").lower()
    
    if is_cloud:
        st.success("☁️ กำลังทำงานบน Streamlit Cloud 24 ชม.")
        st.caption("เปิดใช้งานได้จากมือถือและทุกอุปกรณ์โดยไม่ต้องเปิดคอม")
    else:
        try:
            host_name = socket.gethostname()
            local_ip = socket.gethostbyname(host_name)
        except Exception:
            local_ip = "127.0.0.1"

        st.markdown(
            f"""
            **สำหรับเครื่องนี้:**  
            `http://localhost:8501`  

            **สำหรับคนอื่นในวง Wi-Fi:**  
            `http://{local_ip}:8501`
            """
        )
        st.info("💡 **แชร์ข้ามเน็ตฟรี:** `npx localtunnel --port 8501`")

    st.divider()
    st.markdown("### 📚 คลังประวัติคลิปที่สร้าง")
    history_items = load_history()
    with st.expander(f"🎬 ประวัติคลิปย้อนหลัง ({len(history_items)} คลิป)", expanded=False):
        if not history_items:
            st.caption("ยังไม่มีประวัติการสร้างคลิปในระบบ")
        else:
            for item in history_items[:8]:
                st.markdown(f"**📌 {item.get('topic', 'ไม่มีหัวข้อ')}**")
                p_st = item.get("post_status", "draft")
                if p_st == "posted_auto":
                    st.markdown("🟢 <span style='font-size:12px; color:#34C759; font-weight:600;'>โพสต์อัตโนมัติแล้ว</span>", unsafe_allow_html=True)
                elif p_st == "posted_manual":
                    st.markdown("🔵 <span style='font-size:12px; color:#007AFF; font-weight:600;'>โพสต์เองแล้ว</span>", unsafe_allow_html=True)
                else:
                    st.markdown("🟡 <span style='font-size:12px; color:#FF9500; font-weight:600;'>บันทึกเก็บไว้ (Draft)</span>", unsafe_allow_html=True)
                v_p = item.get("video_path")
                if v_p and Path(v_p).exists():
                    st.caption(f"📁 {Path(v_p).name}")
                st.divider()

    st.info("⚙️ **อัปโหลดโลโก้, ลายน้ำ & ตั้งค่า API:** ไปที่แท็บ **4. ตั้งค่าส่วนกลาง** ด้านบน")

# Initialize Script Data in Session State
if "script_data" not in st.session_state:
    st.session_state.script_data = {
        "topic": "กาแฟดริป VS กาแฟแคปซูล",
        "name_a": "กาแฟดริป",
        "name_b": "กาแฟแคปซูล",
        "mode": "standard_3round",
        "framework": "persona",
        "num_rounds": 3,
        "research_summary": "เปรียบเทียบเจาะลึก 3 ยก: ยก 1 รสชาติและกลิ่นอโรม่า, ยก 2 ความสะดวกรวดเร็วในการชง, ยก 3 ความคุ้มค่าและราคาต่อแก้วระยะยาว",
        "hook": "สายกาแฟห้ามพลาด! ดริปเองกับแคปซูล เทียบกันหมัดต่อหมัดแบบไหนตอบโจทย์ชีวิตคุณมากกว่ากัน?",
        "round_1_title": "คุณภาพ & กลิ่นรส",
        "round_1_a": "ยกแรกเรื่องรสชาติ กาแฟดริปชนะเรื่องความสุนทรีย์ กลิ่นหอมกรุ่นอโรม่า ดึงเอกลักษณ์เมล็ดแท้ได้ละเมียดละไม",
        "round_1_b": "แต่กาแฟแคปซูล สวนกลับด้วยความเข้มข้นมาตรฐาน แรงดันสม่ำเสมอ ได้รสชาติเหมือนบาริสต้าชงให้ทุกแก้ว",
        "round_2_title": "ความสะดวก & เวลา",
        "round_2_a": "ยกที่สองเรื่องเวลา กาแฟดริปต้องใช้เวลาบด ต้มน้ำ ดริป และล้างอุปกรณ์ เหมาะกับวันสบายๆ มีเวลาสโลว์ไลฟ์",
        "round_2_b": "ในขณะที่แคปซูล ตอบโจทย์ชั่วโมงเร่งด่วน แค่หยอดแคปซูลแล้วกดปุ่ม สิบวินาทีก็ได้ดื่ม ไม่เลอะเทอะ",
        "round_3_title": "ความคุ้มค่า & ราคา",
        "round_3_a": "ยกสุดท้ายเรื่องความคุ้ม กาแฟดริปต้นทุนต่อแก้วประหยัดกว่ามาก ซื้อเมล็ดถุงเดียวชงได้หลายสิบแก้ว",
        "round_3_b": "ส่วนแคปซูล ตัวเครื่องราคาจับต้องได้ง่าย แต่ราคาแคปซูลต่อแก้วจะสูงกว่า แลกกับความสะดวกสบาย",
        "conclusion": "สรุปฟันธง: ชอบความหอมละเมียดเลือกดริป ชอบความง่ายทันใจเลือกแคปซูล คอมเมนต์บอกกันหน่อยนะ พิกัดของแท้อยู่ในคอมเมนต์แรกแล้วครับ",
        "affiliate_comment": "📍 พิกัดของแท้ราคาโปรโมชั่นพิเศษ:\n👉 กาแฟดริป: https://shopee.co.th/sample_drip\n👉 กาแฟแคปซูล: https://shopee.co.th/sample_capsule\n(ใครชอบตัวไหน โหวตกันในคอมเมนต์ได้เลยครับ)",
    }
    st.session_state.script_data["segments"] = [
        {"id": "hook", "text": st.session_state.script_data["hook"], "highlight": "none", "round_label": "🔥 เปิดประเด็น"},
        {"id": "round_1_a", "text": st.session_state.script_data["round_1_a"], "highlight": "A", "round_label": "🥊 ยกที่ 1: คุณภาพ & กลิ่นรส"},
        {"id": "round_1_b", "text": st.session_state.script_data["round_1_b"], "highlight": "B", "round_label": "🥊 ยกที่ 1: คุณภาพ & กลิ่นรส"},
        {"id": "round_2_a", "text": st.session_state.script_data["round_2_a"], "highlight": "A", "round_label": "🥊 ยกที่ 2: ความสะดวก & เวลา"},
        {"id": "round_2_b", "text": st.session_state.script_data["round_2_b"], "highlight": "B", "round_label": "🥊 ยกที่ 2: ความสะดวก & เวลา"},
        {"id": "round_3_a", "text": st.session_state.script_data["round_3_a"], "highlight": "A", "round_label": "🥊 ยกที่ 3: ความคุ้มค่า & ราคา"},
        {"id": "round_3_b", "text": st.session_state.script_data["round_3_b"], "highlight": "B", "round_label": "🥊 ยกที่ 3: ความคุ้มค่า & ราคา"},
        {"id": "conclusion", "text": st.session_state.script_data["conclusion"], "highlight": "none", "round_label": "🏁 สรุปฟันธง"},
    ]

if "rendered_video_path" not in st.session_state:
    st.session_state.rendered_video_path = None

if "script_version" not in st.session_state:
    st.session_state.script_version = 1

# Initialize Form Keys if not present
if "input_topic" not in st.session_state:
    st.session_state.input_topic = st.session_state.script_data.get("topic", "กาแฟดริป VS กาแฟแคปซูล")
if "input_name_a" not in st.session_state:
    st.session_state.input_name_a = st.session_state.script_data.get("name_a", "กาแฟดริป")
if "input_name_b" not in st.session_state:
    st.session_state.input_name_b = st.session_state.script_data.get("name_b", "กาแฟแคปซูล")
if "input_details_a" not in st.session_state:
    st.session_state.input_details_a = ""
if "input_details_b" not in st.session_state:
    st.session_state.input_details_b = ""
if "input_target" not in st.session_state:
    st.session_state.input_target = ""
if "input_angles" not in st.session_state:
    st.session_state.input_angles = ""
if "input_aff_a" not in st.session_state:
    st.session_state.input_aff_a = ""
if "input_aff_b" not in st.session_state:
    st.session_state.input_aff_b = ""
if "input_framework" not in st.session_state:
    st.session_state.input_framework = st.session_state.script_data.get("framework", "persona")
if "input_clip_type" not in st.session_state:
    st.session_state.input_clip_type = st.session_state.script_data.get("clip_type", "commerce")
if "input_relation_type" not in st.session_state:
    st.session_state.input_relation_type = st.session_state.script_data.get("relation_type", "compare")

# -------------------------------------------------------------
# 4 DIRECT PRODUCTION TABS (NO QUEUE OVERHEAD)
# -------------------------------------------------------------
tab_script, tab_render, tab_history, tab_settings = st.tabs([
    "📝 1. ร่างบท & สตูดิโอ (Script Studio)",
    "🎬 2. เรนเดอร์ & ออโต้โพสต์/เซฟ (Render & Publish)",
    "🚀 3. คลังคลิปสำเร็จ & ประวัติโพสต์ (Video Vault & History)",
    "⚙️ 4. ตั้งค่าส่วนกลาง (Global Settings)",
])

# =============================================================
# TAB 1: SCRIPT STUDIO (INPUT, DEEP RESEARCH & REWRITER)
# =============================================================
with tab_script:
    st.markdown("### 📌 ขั้นตอนที่ 1: กำหนดหัวข้อ & กรอบแนวคิด (Topic & Framework)")

    col_ctype, col_rel = st.columns([1, 1], gap="medium")
    with col_ctype:
        c_types_keys = list(CLIP_TYPES.keys())
        cur_ctype = st.session_state.get("input_clip_type", "commerce")
        c_idx = c_types_keys.index(cur_ctype) if cur_ctype in c_types_keys else 0
        selected_clip_type = st.radio(
            "🎯 รูปแบบ / วัตถุประสงค์ของคลิป:",
            options=c_types_keys,
            format_func=lambda k: CLIP_TYPES[k]["name"],
            index=c_idx,
            horizontal=True,
            key="selected_clip_type",
            help="เลือกระหว่าง 'คลิปขายของ/ป้ายยา' (เน้นสินค้า & พิกัด Shopee) หรือ 'คลิปไวรัลสาระความรู้' (เน้นเปรียบเทียบข้อเท็จจริง สาระ ประวัติศาสตร์ วัฒนธรรม โดยไม่เน้นขายของ)",
        )
        st.session_state.input_clip_type = selected_clip_type
    with col_rel:
        rel_keys = list(RELATION_TYPES.keys())
        cur_rel = st.session_state.get("input_relation_type", "compare")
        r_idx = rel_keys.index(cur_rel) if cur_rel in rel_keys else 0
        selected_relation = st.selectbox(
            "📐 ฟังก์ชัน / มุมมองคู่เทียบ:",
            options=rel_keys,
            format_func=lambda k: RELATION_TYPES[k]["name"],
            index=r_idx,
            key="selected_relation",
            help="กำหนดมุมมองการวิเคราะห์ เช่น เปรียบเทียบตรงๆ (VS), เจาะลึกความต่าง (แตกต่าง), วิเคราะห์การทำงานร่วมกัน (เข้ากัน), หรือมุมมองอิสระ",
        )
        st.session_state.input_relation_type = selected_relation

    st.caption(f"💡 **แนวทาง:** {CLIP_TYPES[selected_clip_type]['desc']} | **มุมมอง:** {RELATION_TYPES[selected_relation]['desc']}")

    num_fw = len(FRAMEWORK_PRESETS)
    st.markdown(
        f"""
        <div style="background: rgba(0, 122, 255, 0.07); border: 1px solid rgba(0, 122, 255, 0.25); border-radius: 14px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="font-weight: 700; font-size: 16px; color: #007AFF; margin-bottom: 3px;">💡 สุ่มหัวข้อไวรัลใน 1 คลิก (คัดสรร {num_fw} กรอบจิตวิทยา & 10 หมวดหมู่)</div>
            <div style="font-size: 13px; color: #555;">ดึงหัวข้อคู่เปรียบเทียบ สเปก กลุ่มเป้าหมาย และกรอบความคิดไวรัลมาเติมลงในฟอร์มทันที</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "seen_topics" not in st.session_state:
        st.session_state.seen_topics = []

    with st.expander("🎲 ตัวช่วยคิดหัวข้อ: สุ่มไอเดียไวรัล หรือ ให้ AI คิดสดใหม่ (Optional)", expanded=False):
        st.caption("พิมพ์สินค้า/ไอเดียที่อยากทำ หรือเลือกหมวดหมู่ แล้วกดให้ AI ช่วยจับคู่ หรือสุ่มไอเดียได้ทันที")

        seed_kw = st.text_input(
            "💡 พิมพ์ไอเดีย/สินค้าตั้งต้น (ไม่บังคับ):",
            placeholder="เช่น ศาสนาพุทธ, ไทย VS พม่า, แปรงสีฟันไฟฟ้า, ยาดม (หรือเว้นว่างไว้หากต้องการสุ่มอิสระ)" if selected_clip_type == "viral_knowledge" else "เช่น ยาดม, ชาเขียว, แปรงสีฟันไฟฟ้า, คอลลาเจน (หรือเว้นว่างไว้หากต้องการสุ่มอิสระ)",
            key="seed_topic_kw",
            help="หากพิมพ์คำค้น AI จะวิเคราะห์และจับคู่เปรียบเทียบกับคู่ตรงข้าม/คู่ตัวแทนที่น่าสนใจให้โดยอัตโนมัติตามรูปแบบคลิปที่เลือก",
        )

        cat_options = ["ทั้งหมด (สุ่มทุกหมวด)"] + CATEGORIES
        selected_cat = st.selectbox("📂 หมวดหมู่สินค้า/เนื้อหา:", cat_options, index=0)

        fw_filter_options = [("all", f"🎯 สุ่มทุกแนวทาง ({num_fw} Frameworks)")] + [
            (k, FRAMEWORK_PRESETS[k]["name"]) for k in FRAMEWORK_PRESETS
        ]
        selected_fw_filter = st.selectbox(
            "🎯 แนวทางเนื้อหา (Framework):",
            options=[x[0] for x in fw_filter_options],
            format_func=lambda x: dict(fw_filter_options).get(x, x),
            index=0,
        )

        kw_clean = (seed_kw or "").strip()
        random_label = f"🎲 สุ่มไอเดียหัวข้อ{'เกี่ยวกับ ' + kw_clean if kw_clean else ' (จากคลัง 60+ หัวข้อ)'}"
        if st.button(random_label, use_container_width=True, type="secondary"):
            cat_param = None if selected_cat == "ทั้งหมด (สุ่มทุกหมวด)" else selected_cat
            fw_param = None if selected_fw_filter == "all" else selected_fw_filter
            idea = get_random_idea(
                category=cat_param,
                framework=fw_param,
                use_ai=False,
                seen_topics=st.session_state.seen_topics,
                keyword=kw_clean if kw_clean else None,
                clip_type=selected_clip_type,
                relation_type=selected_relation,
            )
            st.session_state.seen_topics.append(idea["topic"])
            if len(st.session_state.seen_topics) > 30:
                st.session_state.seen_topics.pop(0)
            st.session_state.input_topic = idea["topic"]
            st.session_state.in_topic = idea["topic"]
            st.session_state.input_name_a = idea["name_a"]
            st.session_state.in_name_a = idea["name_a"]
            st.session_state.input_name_b = idea["name_b"]
            st.session_state.in_name_b = idea["name_b"]
            st.session_state.input_details_a = idea.get("details_a", "")
            st.session_state.in_details_a = idea.get("details_a", "")
            st.session_state.input_details_b = idea.get("details_b", "")
            st.session_state.in_details_b = idea.get("details_b", "")
            st.session_state.input_target = idea.get("target_audience", "")
            st.session_state.in_target = idea.get("target_audience", "")
            st.session_state.input_angles = idea.get("key_angles", "")
            st.session_state.in_angles = idea.get("key_angles", "")
            st.session_state.input_aff_a = idea.get("affiliate_a", "") or idea.get("affiliate_link_a", "")
            st.session_state.aff_a = idea.get("affiliate_a", "") or idea.get("affiliate_link_a", "")
            st.session_state.input_aff_b = idea.get("affiliate_b", "") or idea.get("affiliate_link_b", "")
            st.session_state.aff_b = idea.get("affiliate_b", "") or idea.get("affiliate_link_b", "")
            st.session_state.input_framework = idea.get("framework", "persona")
            if "clip_type" in idea:
                st.session_state.input_clip_type = idea["clip_type"]
            if "relation_type" in idea:
                st.session_state.input_relation_type = idea["relation_type"]
            st.session_state.last_parsed_topic = idea["topic"]
            st.rerun()

        ai_label = f"🤖 ให้ AI ช่วยหาคู่เปรียบเทียบสำหรับ '{kw_clean}'" if kw_clean else "🤖 ให้ AI วิเคราะห์คิดหัวข้อสดใหม่"
        if st.button(ai_label, use_container_width=True, type="primary"):
            cat_param = None if selected_cat == "ทั้งหมด (สุ่มทุกหมวด)" else selected_cat
            fw_param = None if selected_fw_filter == "all" else selected_fw_filter
            spinner_msg = f"🤖 AI กำลังค้นหาและจับคู่เปรียบเทียบสุดไวรัลสำหรับ '{kw_clean}'..." if kw_clean else "🤖 AI กำลังคิดหัวข้อเปรียบเทียบสุดไวรัล..."
            with st.spinner(spinner_msg):
                idea = get_random_idea(
                    category=cat_param,
                    framework=fw_param,
                    use_ai=True,
                    keyword=kw_clean if kw_clean else None,
                    clip_type=selected_clip_type,
                    relation_type=selected_relation,
                )
                st.session_state.seen_topics.append(idea["topic"])
                st.session_state.input_topic = idea["topic"]
                st.session_state.in_topic = idea["topic"]
                st.session_state.input_name_a = idea["name_a"]
                st.session_state.in_name_a = idea["name_a"]
                st.session_state.input_name_b = idea["name_b"]
                st.session_state.in_name_b = idea["name_b"]
                st.session_state.input_details_a = idea.get("details_a", "")
                st.session_state.in_details_a = idea.get("details_a", "")
                st.session_state.input_details_b = idea.get("details_b", "")
                st.session_state.in_details_b = idea.get("details_b", "")
                st.session_state.input_target = idea.get("target_audience", "")
                st.session_state.in_target = idea.get("target_audience", "")
                st.session_state.input_angles = idea.get("key_angles", "")
                st.session_state.in_angles = idea.get("key_angles", "")
                st.session_state.input_aff_a = idea.get("affiliate_a", "") or idea.get("affiliate_link_a", "")
                st.session_state.aff_a = idea.get("affiliate_a", "") or idea.get("affiliate_link_a", "")
                st.session_state.input_aff_b = idea.get("affiliate_b", "") or idea.get("affiliate_link_b", "")
                st.session_state.aff_b = idea.get("affiliate_b", "") or idea.get("affiliate_link_b", "")
                st.session_state.input_framework = idea.get("framework", "persona")
                if "clip_type" in idea:
                    st.session_state.input_clip_type = idea["clip_type"]
                if "relation_type" in idea:
                    st.session_state.input_relation_type = idea["relation_type"]
                st.session_state.last_parsed_topic = idea["topic"]
                st.rerun()

    # Input form (เรียงแถวเดียวตามลำดับการทำงาน สวยงาม เป็นระเบียบ ไม่ข้ามไปมา)
    cur_topic = st.session_state.get("in_topic", st.session_state.input_topic)
    is_viral = (selected_clip_type == "viral_knowledge")
    topic_placeholder = "เช่น ศาสนาพุทธ VS ศาสนาคริสต์ หรือ ไทย VS พม่า" if is_viral else "เช่น กาแฟดริป VS กาแฟแคปซูล"
    in_topic = st.text_input("📌 1. หัวข้อเปรียบเทียบ (Topic):", value=cur_topic, placeholder=topic_placeholder, key="in_topic")

    # Auto-detect product names whenever Topic changes
    if "last_parsed_topic" not in st.session_state:
        st.session_state.last_parsed_topic = in_topic

    if in_topic and in_topic != st.session_state.last_parsed_topic:
        p_a, p_b = extract_names_from_topic(in_topic)
        if p_a and p_b:
            st.session_state.input_name_a = p_a
            st.session_state.in_name_a = p_a
            st.session_state.input_name_b = p_b
            st.session_state.in_name_b = p_b
        st.session_state.last_parsed_topic = in_topic

    # Dedicated Button & Live Detection Status
    col_tbtn, col_tinfo = st.columns([1, 1], gap="small")
    with col_tbtn:
        btn_update_label = "🔄 อัปเดตแยกชื่อประเด็น A & B จากหัวข้อ" if is_viral else "🔄 อัปเดตแยกชื่อสินค้า A & B จากหัวข้อ"
        if st.button(btn_update_label, use_container_width=True, help="คลิกเพื่อแยกชื่อ A และ B จากหัวข้อมาใส่ในช่องข้อมูลด้านล่างทันที"):
            p_a, p_b = extract_names_from_topic(in_topic)
            if p_a and p_b:
                st.session_state.input_name_a = p_a
                st.session_state.in_name_a = p_a
                st.session_state.input_name_b = p_b
                st.session_state.in_name_b = p_b
                st.session_state.last_parsed_topic = in_topic
                st.toast(f"✅ อัปเดต: A = {p_a} | B = {p_b}")
                st.rerun()
            else:
                st.warning("ไม่พบคำเชื่อมเปรียบเทียบ (เช่น VS, กับ, หรือ) ในหัวข้อนี้ กรุณาระบุชื่อในช่องด้านล่าง")
    with col_tinfo:
        p_a_view, p_b_view = extract_names_from_topic(in_topic)
        if p_a_view and p_b_view:
            status_tag = "ประเด็นที่ตรวจพบ" if is_viral else "สินค้าที่ตรวจพบ"
            st.caption(f"💡 {status_tag}: 🟢 **{p_a_view}** VS 🔵 **{p_b_view}**")
        else:
            st.caption("💡 เคล็ดลับ: พิมพ์คั่นด้วย 'VS', 'กับ', หรือ 'หรือ' ระบบจะแยกชื่อให้อัตโนมัติ")

    fw_options = list(FRAMEWORK_PRESETS.keys())
    cur_fw_idx = fw_options.index(st.session_state.input_framework) if st.session_state.input_framework in fw_options else 0
    selected_fw = st.selectbox(
        "🧠 2. กรอบแนวทางเนื้อหา (Framework):",
        options=fw_options,
        index=cur_fw_idx,
        format_func=lambda k: FRAMEWORK_PRESETS[k]["name"],
        help="เลือกเทคนิคการเล่าเรื่อง เช่น Persona (ตามไลฟ์สไตล์), Price vs Quality, หรือ Mythbusters",
    )
    st.caption(f"💡 {FRAMEWORK_PRESETS[selected_fw]['desc']}")

    mode_options = list(DURATION_MODES.keys())
    selected_mode = st.selectbox(
        "⏱️ 3. รูปแบบความยาวคลิป (Duration Mode):",
        options=mode_options,
        index=1,
        format_func=lambda k: DURATION_MODES[k]["name"],
        help="เลือกระยะเวลาที่เหมาะสมกับเนื้อหา",
    )
    st.caption(f"💡 {DURATION_MODES[selected_mode]['desc']}")

    sec4_title = "##### 🔍 4. ข้อมูลประเด็น / สาระเปรียบเทียบ (ฝั่ง A vs ฝั่ง B)" if is_viral else "##### 📦 4. ข้อมูลสินค้า / ตัวเลือกเปรียบเทียบ (ฝั่ง A vs ฝั่ง B)"
    st.markdown(sec4_title)
    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        st.markdown("###### 🟢 ฝั่ง A")
        val_name_a = st.session_state.get("in_name_a", st.session_state.input_name_a)
        label_a = "ชื่อหัวข้อ/ประเด็น A:" if is_viral else "ชื่อสินค้า/ตัวเลือก A:"
        ph_a = "เช่น ศาสนาพุทธ" if is_viral else "เช่น กาแฟดริป"
        in_name_a = st.text_input(label_a, value=val_name_a, placeholder=ph_a, key="in_name_a")

        det_label_a = "จุดเด่น / สาระสำคัญ / ข้อมูล A:" if is_viral else "จุดเด่น / สเปก / ข้อดี A:"
        det_ph_a = "หลักคำสอน แนวปฏิบัติ จุดเน้น หรือข้อมูลสำคัญ" if is_viral else "จุดเด่น สเปก หรือข้อดีของสินค้า A"
        in_details_a = st.text_area(det_label_a, value=st.session_state.input_details_a, height=75, placeholder=det_ph_a, key="in_details_a")

        aff_label_a = "🔗 ลิงก์อ้างอิง/ข้อมูลเพิ่มเติม A (ไม่บังคับ):" if is_viral else "🔗 ลิงก์ Shopee สินค้า A:"
        aff_ph_a = "ลิงก์บทความ หรือเว้นว่างไว้" if is_viral else "ลิงก์สินค้า A เช่น https://shopee.co.th/..."
        aff_a = st.text_input(aff_label_a, value=st.session_state.input_aff_a, placeholder=aff_ph_a, key="aff_a")
    with col_b:
        st.markdown("###### 🔵 ฝั่ง B")
        val_name_b = st.session_state.get("in_name_b", st.session_state.input_name_b)
        label_b = "ชื่อหัวข้อ/ประเด็น B:" if is_viral else "ชื่อสินค้า/ตัวเลือก B:"
        ph_b = "เช่น ศาสนาคริสต์" if is_viral else "เช่น กาแฟแคปซูล"
        in_name_b = st.text_input(label_b, value=val_name_b, placeholder=ph_b, key="in_name_b")

        det_label_b = "จุดเด่น / สาระสำคัญ / ข้อมูล B:" if is_viral else "จุดเด่น / สเปก / ข้อดี B:"
        det_ph_b = "หลักคำสอน แนวปฏิบัติ จุดเน้น หรือข้อมูลสำคัญ" if is_viral else "จุดเด่น สเปก หรือข้อดีของสินค้า B"
        in_details_b = st.text_area(det_label_b, value=st.session_state.input_details_b, height=75, placeholder=det_ph_b, key="in_details_b")

        aff_label_b = "🔗 ลิงก์อ้างอิง/ข้อมูลเพิ่มเติม B (ไม่บังคับ):" if is_viral else "🔗 ลิงก์ Shopee สินค้า B:"
        aff_ph_b = "ลิงก์บทความ หรือเว้นว่างไว้" if is_viral else "ลิงก์สินค้า B เช่น https://shopee.co.th/..."
        aff_b = st.text_input(aff_label_b, value=st.session_state.input_aff_b, placeholder=aff_ph_b, key="aff_b")

    st.markdown("##### 🎯 5. กลุ่มเป้าหมาย & มุมมองที่เน้น")
    col_tgt, col_ang = st.columns(2, gap="medium")
    with col_tgt:
        tgt_ph = "เช่น ผู้สนใจปรัชญาและประวัติศาสตร์, คนทั่วไป" if is_viral else "ระบุกลุ่มคนที่สนใจคลิปนี้"
        in_target = st.text_input("กลุ่มเป้าหมาย (เช่น สายประหยัด, คอกาแฟ):", value=st.session_state.input_target, placeholder=tgt_ph, key="in_target")
    with col_ang:
        ang_ph = "เช่น จุดกำเนิด, คำสอนเรื่องชีวิตหลังความตาย" if is_viral else "ระบุมุมมองเปรียบเทียบที่ต้องการเน้น"
        in_angles = st.text_input("มุมมองที่ต้องการเน้น (เช่น ความคุ้มค่า, พกพาสะดวก):", value=st.session_state.input_angles, placeholder=ang_ph, key="in_angles")

    st.markdown("##### 🚀 6. สั่ง AI ผลิตบทพากย์")
    if st.button("🚀 สั่ง Gemini ร่างบททันที (พร้อมค้นหาข้อมูลเชิงลึก)", type="primary", use_container_width=True):
        # Auto-resolve names from topic if user forgot to click update
        eff_name_a = in_name_a
        eff_name_b = in_name_b
        if (eff_name_a == "กาแฟดริป" and "กาแฟ" not in in_topic) or not eff_name_a or not eff_name_b:
            p_a, p_b = extract_names_from_topic(in_topic)
            if p_a and p_b:
                eff_name_a, eff_name_b = p_a, p_b
                st.session_state.in_name_a = eff_name_a
                st.session_state.in_name_b = eff_name_b
                st.session_state.input_name_a = eff_name_a
                st.session_state.input_name_b = eff_name_b
        with st.spinner("🤖 Gemini กำลังทำ Deep Research วิเคราะห์ข้อมูล จุดเน้น และร่างบทตาม Framework..."):
            try:
                gen = AIScriptGenerator()
                new_data = gen.generate_script(
                    topic=in_topic,
                    name_a=eff_name_a,
                    name_b=eff_name_b,
                    details_a=in_details_a,
                    details_b=in_details_b,
                    target_audience=in_target,
                    key_angles=in_angles,
                    affiliate_link_a=aff_a,
                    affiliate_link_b=aff_b,
                    script_mode=selected_mode,
                    channel_outro_cta=prof.get("default_outro_cta", ""),
                    framework=selected_fw,
                    clip_type=selected_clip_type,
                    relation_type=selected_relation,
                )
                st.session_state.script_data = new_data
                st.session_state.script_version += 1
                st.toast("✅ Gemini ร่างบทเสร็จเรียบร้อยแล้ว!")
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเรียก AI: {e}")

    col_ap_opt, col_ap_btn = st.columns([1, 2], gap="small")
    with col_ap_opt:
        t1_dest_mode = st.radio(
            "ปลายทางหลังสร้างเสร็จ:",
            ["📦 เซฟเก็บไว้ดู / ดาวน์โหลด", "🚀 ออโต้โพสต์ลงโซเชียลทันที"],
            index=0,
            key="t1_dest_mode_sel",
        )
    with col_ap_btn:
        btn_1click = st.button("⚡ 1-Click Viral Auto-Pilot (เรนเดอร์จบในคลิกเดียว)", type="secondary", use_container_width=True)

    if btn_1click:
        # Auto-resolve names from topic if user forgot to click update
        eff_name_a = in_name_a
        eff_name_b = in_name_b
        if (eff_name_a == "กาแฟดริป" and "กาแฟ" not in in_topic) or not eff_name_a or not eff_name_b:
            p_a, p_b = extract_names_from_topic(in_topic)
            if p_a and p_b:
                eff_name_a, eff_name_b = p_a, p_b
                st.session_state.in_name_a = eff_name_a
                st.session_state.in_name_b = eff_name_b
                st.session_state.input_name_a = eff_name_a
                st.session_state.input_name_b = eff_name_b
        status_box = st.status("⚡ กำลังรันโหมด Auto-Pilot สร้างคลิปครบวงจร...", expanded=True)
        with status_box:
            try:
                st.write("🤖 1/4: Gemini กำลังทำ Deep Research & เขียนบท...")
                gen = AIScriptGenerator()
                new_data = gen.generate_script(
                    topic=in_topic,
                    name_a=eff_name_a,
                    name_b=eff_name_b,
                    details_a=in_details_a,
                    details_b=in_details_b,
                    target_audience=in_target,
                    key_angles=in_angles,
                    affiliate_link_a=aff_a,
                    affiliate_link_b=aff_b,
                    script_mode=selected_mode,
                    channel_outro_cta=prof.get("default_outro_cta", ""),
                    framework=selected_fw,
                    clip_type=selected_clip_type,
                    relation_type=selected_relation,
                )
                st.session_state.script_data = new_data
                st.session_state.script_version += 1

                t_now = int(time.time())
                img_mode_def = prof.get("default_image_mode", "ai_cartoon")
                art_style_def = prof.get("default_art_style", "3d_pixar")

                is_multi = new_data.get("mode") == "multi_battle_3round"
                round_assets = None

                if is_multi:
                    st.write(f"📸 2/4: กำลังสร้าง/ค้นหารูปภาพแบทเทิล 3 คู่ย่อย ({art_style_def})...")
                    round_assets = {}
                    for r in range(1, 4):
                        r_name_a = new_data.get(f"round_{r}_name_a") or f"{in_name_a} #{r}"
                        r_name_b = new_data.get(f"round_{r}_name_b") or f"{in_name_b} #{r}"
                        r_path_a = ASSETS_DIR / "images" / f"auto_a_r{r}_{t_now}.png"
                        r_path_b = ASSETS_DIR / "images" / f"auto_b_r{r}_{t_now}.png"
                        auto_fetch_or_create_image(r_name_a, r_path_a, is_item_b=False, allow_web_search=True, image_mode=img_mode_def, art_style=art_style_def)
                        time.sleep(0.5)
                        auto_fetch_or_create_image(r_name_b, r_path_b, is_item_b=True, allow_web_search=True, image_mode=img_mode_def, art_style=art_style_def)
                        round_assets[r] = {
                            "name_a": r_name_a,
                            "name_b": r_name_b,
                            "image_a_path": r_path_a,
                            "image_b_path": r_path_b,
                        }
                    img_a_path = round_assets[1]["image_a_path"]
                    img_b_path = round_assets[1]["image_b_path"]
                else:
                    st.write(f"📸 2/4: กำลังค้นหา/สร้างรูปภาพสำหรับ '{in_name_a}' และ '{in_name_b}'...")
                    img_a_path = ASSETS_DIR / "images" / f"auto_a_{t_now}.png"
                    img_b_path = ASSETS_DIR / "images" / f"auto_b_{t_now}.png"
                    auto_fetch_or_create_image(in_name_a, img_a_path, is_item_b=False, allow_web_search=True, image_mode=img_mode_def, art_style=art_style_def)
                    time.sleep(0.5)
                    auto_fetch_or_create_image(in_name_b, img_b_path, is_item_b=True, allow_web_search=True, image_mode=img_mode_def, art_style=art_style_def)

                st.write("🎙️ 3/4: สังเคราะห์เสียงพากย์ Edge Neural + มิกซ์ Lo-Fi BGM & SFX...")
                v_key = prof.get("default_voice", "edge_niwat")
                v_rate = prof.get("default_rate", "+10%")
                v_pitch = prof.get("default_pitch", "+2Hz")
                tts = TTSEngine(voice_key=v_key, speech_rate=v_rate, speech_pitch=v_pitch)
                output_mp4 = OUTPUT_DIR / f"shorts_autopilot_{t_now}.mp4"
                master_audio_path = output_mp4.parent / f"{output_mp4.stem}_audio.mp3"
                timeline, audio_file, total_duration = tts.build_timeline(
                    script_data=st.session_state.script_data,
                    output_master_audio=master_audio_path,
                    include_bgm=bool(prof.get("default_enable_bgm", True)),
                    bgm_volume=float(prof.get("default_bgm_vol", 0.12)),
                    include_sfx=bool(prof.get("default_enable_sfx", True)),
                )

                st.write("🎬 4/4: กำลังตัดต่อวิดีโอ 1080x1920 (9:16) พร้อมอนิเมชั่น...")
                builder = VideoBuilder(
                    bg_color=hex_to_rgb(prof.get("default_bg_color", "#F5F2EB")),
                    highlight_color=hex_to_rgb(prof.get("default_highlight_color", "#32CD32")),
                    animation_style=prof.get("default_anim_style", "pointer_and_border"),
                )

                wm_text = prof.get("watermark_text", "@vsify.official")
                wm_opac = float(prof.get("watermark_opacity", 0.75))
                saved_logo = prof.get("logo_path", "")
                wm_logo = Path(saved_logo) if saved_logo and Path(saved_logo).exists() else None

                char_path, char_poses = get_active_character_assets(prof)

                final_video = builder.build_video(
                    image_a_path=img_a_path,
                    image_b_path=img_b_path,
                    character_path=char_path,
                    character_poses=char_poses,
                    topic=new_data.get("topic"),
                    name_a=new_data.get("name_a"),
                    name_b=new_data.get("name_b"),
                    timeline=timeline,
                    master_audio_path=audio_file,
                    output_video_path=output_mp4,
                    watermark_logo_path=wm_logo,
                    watermark_text=wm_text,
                    watermark_opacity=wm_opac,
                    round_assets=round_assets,
                    subtitle_style=prof.get("default_subtitle_style", "clean_floating"),
                    subtitle_anim=prof.get("default_subtitle_anim", "typewriter"),
                )

                cover_path = output_mp4.parent / f"{output_mp4.stem}_cover.jpg"
                add_history_entry(
                    topic=new_data.get("topic"),
                    name_a=new_data.get("name_a"),
                    name_b=new_data.get("name_b"),
                    video_path=str(final_video),
                    cover_path=str(cover_path) if cover_path.exists() else None,
                    social_caption=new_data.get("social_caption", ""),
                    hashtags=new_data.get("hashtags", ""),
                    affiliate_comment=new_data.get("affiliate_comment", ""),
                    framework=selected_fw,
                    duration_mode=selected_mode,
                    duration_seconds=total_duration,
                )

                st.session_state.rendered_video_path = str(final_video)

                if "ออโต้โพสต์" in t1_dest_mode:
                    st.write("🚀 5/5: กำลังส่งคลิปขึ้น Facebook / YouTube / TikTok อัตโนมัติ...")
                    m_p = output_mp4.parent / f"{output_mp4.stem}_meta.json"
                    res = publish_to_all_enabled(
                        video_path=str(final_video),
                        cover_path=str(cover_path) if cover_path.exists() else None,
                        meta_path=str(m_p) if m_p.exists() else None,
                    )
                    if res:
                        status_box.update(label=f"🎉 เรนเดอร์ & ออโต้โพสต์สำเร็จ {len(res)} ช่องทาง!", state="complete")
                        st.toast(f"🚀 ออโต้โพสต์สำเร็จ {len(res)} แพลตฟอร์ม!")
                    else:
                        status_box.update(label="🎉 เรนเดอร์สำเร็จ! (ยังไม่ได้เปิดใช้งาน API โซเชียลในแท็บตั้งค่า)", state="complete")
                else:
                    status_box.update(label=f"🎉 เรนเดอร์และบันทึกเสร็จสมบูรณ์ใน {total_duration:.1f} วินาที", state="complete")
                    st.toast("✅ บันทึกคลิปเสร็จแล้ว! ไปดูที่แท็บ '2. เรนเดอร์ & ออโต้โพสต์/เซฟ'")
                st.rerun()
            except Exception as e:
                status_box.update(label=f"เกิดข้อผิดพลาด: {e}", state="error")
                st.error(f"เกิดข้อผิดพลาด: {e}")

    st.markdown("---")

    # Script Review Section
    st.markdown("### ✍️ ขั้นตอนที่ 2: ตรวจทานบทพูด & สั่ง AI รีไรท์ (Script Studio)")
    active_fw = st.session_state.script_data.get("framework", selected_fw)
    fw_info = FRAMEWORK_PRESETS.get(active_fw, FRAMEWORK_PRESETS["persona"])
    st.markdown(
        f"""
        <div style="background: rgba(30, 144, 255, 0.08); border: 1px solid rgba(30, 144, 255, 0.3); border-radius: 10px; padding: 10px 16px; margin-bottom: 14px;">
            <span style="font-weight: 700; color: #0056b3;">🎯 กรอบเนื้อหาปัจจุบัน:</span> 
            <span style="font-weight: 600; color: #111;">{fw_info['name']}</span> 
            <span style="color: #666; font-size: 13px;">— {fw_info['desc']}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    summary_text = st.session_state.script_data.get("research_summary", "")
    if summary_text:
        with st.expander("📊 สรุปข้อมูลเจาะลึกจาก AI (Research Fact Sheet)", expanded=True):
            st.info(summary_text)

    is_multi = (
        st.session_state.script_data.get("mode") in DURATION_MODES
        or st.session_state.script_data.get("mode") == "multi_round"
        or "round_1_a" in st.session_state.script_data
    )
    v = st.session_state.get("script_version", 1)

    if is_multi:
        num_rounds = st.session_state.script_data.get("num_rounds")
        if not num_rounds:
            if "round_4_a" in st.session_state.script_data:
                num_rounds = 4
            elif "round_3_a" in st.session_state.script_data:
                num_rounds = 3
            elif "round_2_a" in st.session_state.script_data:
                num_rounds = 2
            else:
                num_rounds = 1

        mode_label = DURATION_MODES.get(st.session_state.script_data.get("mode"), {}).get("name", f"{num_rounds} ยก")
        st.markdown(f"#### 🥊 บทพากย์ {num_rounds} ยก สลับชี้ A vs B ({mode_label})")
        s_hook = st.text_area("🎯 Hook (เปิดประเด็นชวนสงสัย):", value=st.session_state.script_data.get("hook", ""), height=70, key=f"inp_hook_v{v}")

        round_data = {}
        for r in range(1, num_rounds + 1):
            r_title_key = f"round_{r}_title"
            r_title_val = st.session_state.script_data.get(r_title_key, f"มิติที่ {r}")
            st.markdown(f"##### 🥊 ยกที่ {r}: {r_title_val}")
            col_ra, col_rb = st.columns(2, gap="medium")
            with col_ra:
                s_ra = st.text_area(f"🟢 ฝั่ง A ({st.session_state.script_data.get('name_a', 'A')}):", value=st.session_state.script_data.get(f"round_{r}_a", ""), height=75, key=f"inp_r{r}_a_v{v}")
            with col_rb:
                s_rb = st.text_area(f"🔵 ฝั่ง B ({st.session_state.script_data.get('name_b', 'B')}):", value=st.session_state.script_data.get(f"round_{r}_b", ""), height=75, key=f"inp_r{r}_b_v{v}")
            round_data[r] = {"title": r_title_val, "a": s_ra, "b": s_rb}

        s_conclusion = st.text_area("🏁 สรุปฟันธง + CTA ติดตามช่อง:", value=st.session_state.script_data.get("conclusion", ""), height=75, key=f"inp_conc_v{v}")
        if st.button("🔄 ใส่บทส่งท้ายประจำเพจ", key=f"btn_outro_multi_v{v}"):
            cur_outro = prof.get("default_outro_cta", "")
            if cur_outro and cur_outro not in st.session_state.script_data.get("conclusion", ""):
                st.session_state.script_data["conclusion"] = (st.session_state.script_data.get("conclusion", "").strip() + " " + cur_outro).strip()
                st.session_state.script_version += 1
                st.rerun()

        s_comment = st.text_area("📌 พิกัด Affiliate ปักหมุดคอมเมนต์แรก:", value=st.session_state.script_data.get("affiliate_comment", ""), height=85, key=f"inp_aff_v{v}")

        st.session_state.script_data["hook"] = s_hook
        st.session_state.script_data["num_rounds"] = num_rounds
        for r, d in round_data.items():
            st.session_state.script_data[f"round_{r}_a"] = d["a"]
            st.session_state.script_data[f"round_{r}_b"] = d["b"]
        st.session_state.script_data["conclusion"] = s_conclusion
        st.session_state.script_data["affiliate_comment"] = s_comment

        new_segments = [{"id": "hook", "text": s_hook, "highlight": "none", "round_label": "🔥 เปิดประเด็น"}]
        for r in range(1, num_rounds + 1):
            r_title = round_data[r]["title"]
            if round_data[r]["a"]:
                new_segments.append({"id": f"round_{r}_a", "text": round_data[r]["a"], "highlight": "A", "round_label": f"🥊 {r_title}"})
            if round_data[r]["b"]:
                new_segments.append({"id": f"round_{r}_b", "text": round_data[r]["b"], "highlight": "B", "round_label": f"🥊 {r_title}"})
        new_segments.append({"id": "conclusion", "text": s_conclusion, "highlight": "none", "round_label": "🏁 สรุปฟันธง"})
        st.session_state.script_data["segments"] = new_segments
    else:
        st.markdown("#### ✍️ บทพากย์ 4 ท่อน")
        s_hook = st.text_area("🎯 Hook:", value=st.session_state.script_data.get("hook", ""), height=70, key=f"inp_hook_v{v}")
        col_ia, col_ib = st.columns(2, gap="medium")
        with col_ia:
            s_item_a = st.text_area(f"🟢 จุดเด่น {st.session_state.script_data.get('name_a', 'Item A')}:", value=st.session_state.script_data.get("item_a", ""), height=85, key=f"inp_item_a_v{v}")
        with col_ib:
            s_item_b = st.text_area(f"🔵 จุดเด่น {st.session_state.script_data.get('name_b', 'Item B')}:", value=st.session_state.script_data.get("item_b", ""), height=85, key=f"inp_item_b_v{v}")
        s_conclusion = st.text_area("🏁 สรุปฟันธง + CTA:", value=st.session_state.script_data.get("conclusion", ""), height=85, key=f"inp_conc_v{v}")
        s_comment = st.text_area("📌 ปักหมุดคอมเมนต์:", value=st.session_state.script_data.get("affiliate_comment", ""), height=85, key=f"inp_aff_v{v}")

        st.session_state.script_data["hook"] = s_hook
        st.session_state.script_data["item_a"] = s_item_a
        st.session_state.script_data["item_b"] = s_item_b
        st.session_state.script_data["conclusion"] = s_conclusion
        st.session_state.script_data["affiliate_comment"] = s_comment

        name_a_val = st.session_state.script_data.get('name_a', 'A')
        name_b_val = st.session_state.script_data.get('name_b', 'B')
        st.session_state.script_data["segments"] = [
            {"id": "hook", "text": s_hook, "highlight": "none", "round_label": "🔥 เปิดประเด็น"},
            {"id": "item_a", "text": s_item_a, "highlight": "A", "round_label": f"📦 {name_a_val}"},
            {"id": "item_b", "text": s_item_b, "highlight": "B", "round_label": f"📦 {name_b_val}"},
            {"id": "conclusion", "text": s_conclusion, "highlight": "none", "round_label": "🏁 สรุปฟันธง"},
        ]

    st.markdown("#### 🔄 สั่ง AI ปรับแก้ / รีไรท์ใหม่ (AI Rewrite)")
    st.caption("สั่งให้ AI ปรับสไตล์คำได้ทันทีตามใจชอบ")
    rewrite_tone = st.selectbox(
        "เลือกโทนอารมณ์ที่ต้องการ:",
        options=[
            "น่าตื่นเต้น ไวรัล กระชับ (Energetic & Viral)",
            "เจาะลึกสเปก เป็นกลาง น่าเชื่อถือ (Professional & In-depth)",
            "ป้ายยาเนียนๆ ฮิตติดเทรนด์ (Affiliate & Friendly)",
            "ตลก มีม สนุกสนาน (Humorous & Casual)",
        ],
    )
    rewrite_instruction = st.text_area(
        "คำสั่งปรับแก้เพิ่มเติม:",
        placeholder="เช่น ขอยก 2 ให้เห็นความเร็วชัดขึ้น และใช้คำสแลงวัยรุ่น...",
        height=85,
    )

    if st.button("⚡ สั่ง AI รีไรท์บทเดี๋ยวนี้", use_container_width=True, type="secondary"):
        if not rewrite_instruction.strip():
            rewrite_instruction = "ช่วยปรับปรุงสำนวนให้กระชับ ชวนติดตาม และได้ใจความมากขึ้น"
        with st.spinner("🤖 AI กำลังรีไรท์บทใหม่ตามคำสั่ง..."):
            try:
                gen = AIScriptGenerator()
                rewritten = gen.rewrite_script(
                    current_script=st.session_state.script_data,
                    instruction=rewrite_instruction,
                    tone=rewrite_tone,
                )
                st.session_state.script_data.update(rewritten)
                st.session_state.script_version += 1
                st.toast("✅ รีไรท์สำเร็จแล้ว!")
                st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")

    st.markdown("---")
    st.markdown(
        """
        <div style="background: rgba(52, 199, 89, 0.08); border: 1px solid rgba(52, 199, 89, 0.3); border-radius: 14px; padding: 16px 20px; margin-top: 20px;">
            <div style="font-weight: 700; font-size: 16px; color: #28a745;">🎉 ได้บทที่พอใจแล้วใช่ไหม?</div>
            <div style="font-size: 13.5px; color: #555; margin-top: 3px;">
                คลิกที่แท็บ <b>'🎬 2. เรนเดอร์ & ออโต้โพสต์/เซฟ'</b> ด้านบน เพื่อใส่รูปสินค้าและกดเรนเดอร์วิดีโอ 1080x1920 พร้อมเลือกว่าจะเซฟเก็บไว้หรือออโต้โพสต์ขึ้นโซเชียลได้ทันที!
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =============================================================
# TAB 2: RENDER STUDIO (IMAGES, VIDEO BUILDER, PLAYER & CAPTIONS)
# =============================================================
with tab_render:
    st.subheader("🎬 สตูดิโอเรนเดอร์วิดีโอ 1080x1920 (9:16)")
    st.caption("ใส่รูปภาพสินค้า หรือเลือกให้ออโต้ค้นหาภาพ ตรวจสอบการตั้งค่า แล้วสั่งเรนเดอร์คลิปพร้อมรับชมได้ทันที")

    # Current Script Card
    st.markdown(
        f"""
        <div class="ios-card" style="border-left: 5px solid #007AFF;">
            <div style="font-size: 13px; color: #8E8E93; font-weight: 600;">คลิปที่กำลังจะเรนเดอร์:</div>
            <div style="font-size: 20px; font-weight: 700; color: #1C1C1E; margin-top: 2px;">
                {st.session_state.script_data.get('topic', 'ไม่มีหัวข้อ')}
            </div>
            <div style="font-size: 13px; color: #636366; margin-top: 4px;">
                🟢 <b>สินค้า A:</b> {st.session_state.script_data.get('name_a', 'A')} &nbsp;|&nbsp; 
                🔵 <b>สินค้า B:</b> {st.session_state.script_data.get('name_b', 'B')} &nbsp;|&nbsp; 
                ⏱️ <b>รูปแบบ:</b> {DURATION_MODES.get(st.session_state.script_data.get('mode', 'standard_3round'), {}).get('name', '3 ยก')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Product Images Selection
    st.markdown("### 🖼️ ขั้นตอนที่ 1: ตรวจสอบรูปภาพสินค้า A & B (รูปจริง / การ์ตูน AI)")
    col_rnd_a, col_rnd_b = st.columns(2, gap="medium")
    with col_rnd_a:
        st.markdown(f"**🟢 สินค้า A: {st.session_state.script_data.get('name_a', 'Item A')}**")
        up_img_a = st.file_uploader("อัปโหลดรูป A (1:1 จัตุรัส PNG/JPG):", type=["png", "jpg", "jpeg"], key="rnd_up_a")
    with col_rnd_b:
        st.markdown(f"**🔵 สินค้า B: {st.session_state.script_data.get('name_b', 'Item B')}**")
        up_img_b = st.file_uploader("อัปโหลดรูป B (1:1 จัตุรัส PNG/JPG):", type=["png", "jpg", "jpeg"], key="rnd_up_b")

    auto_fetch_chk = st.checkbox("📸 ดึง/สร้างรูปภาพอัตโนมัติ (หากไม่ได้อัปโหลดรูป)", value=True)
    rnd_img_mode = st.selectbox(
        "สไตล์ภาพอัตโนมัติ:",
        options=["ai_cartoon", "web_search", "minimal_card"],
        index=["ai_cartoon", "web_search", "minimal_card"].index(prof.get("default_image_mode", "ai_cartoon")),
        format_func=lambda x: {
            "ai_cartoon": "✨ สร้างภาพการ์ตูน AI ตามธีมเพจ (แนะนำ)",
            "web_search": "🌐 ค้นหาภาพจริงจากเว็บ/วิกิพีเดีย",
            "minimal_card": "🔲 การ์ดข้อความกราฟิกโมเดิร์น",
        }[x],
        key="rnd_img_mode_sel",
    )
    rnd_art_style = st.selectbox(
        "ลายเส้นการ์ตูน AI:",
        options=list(CARTOON_STYLES.keys()),
        index=list(CARTOON_STYLES.keys()).index(prof.get("default_art_style", "3d_pixar")) if prof.get("default_art_style") in CARTOON_STYLES else 0,
        format_func=lambda k: CARTOON_STYLES[k]["name"],
        key="rnd_art_style_sel",
    )

    # Optional Override Expanders
    st.markdown("### 🎙️ ขั้นตอนที่ 2: ปรับแต่งเฉพาะคลิปนี้ (เสียงพากย์, เพลงคลอ & สีพื้นหลัง)")
    with st.expander("🎨 ปรับแต่งตัวเลือกเพิ่มเติม (เสียงพากย์, BGM & สไตล์กราฟิก)", expanded=False):
        voice_options = list(TTSEngine.VOICE_PRESETS.keys())
        cur_voice_idx = voice_options.index(prof.get("default_voice", "edge_niwat")) if prof.get("default_voice") in voice_options else 0
        voice_choice = st.selectbox(
            "ผู้บรรยายเสียงพากย์:",
            options=voice_options,
            index=cur_voice_idx,
            format_func=lambda x: TTSEngine.VOICE_PRESETS[x]["desc"],
        )
        if st.button("🔊 ฟังตัวอย่างเสียงนี้ (Preview Voice)", key="btn_test_voice_ov", use_container_width=True):
            with st.spinner("กำลังสังเคราะห์ตัวอย่างเสียง..."):
                try:
                    t_engine = TTSEngine(voice_key=voice_choice)
                    sample_p = TEMP_DIR / f"sample_{voice_choice}.mp3"
                    t_engine.synthesize_segment("สวัสดีครับ ยินดีต้อนรับสู่ช่อง เปรียบเทียบสาระน่ารู้", sample_p)
                    st.audio(str(sample_p), format="audio/mp3")
                except Exception as e:
                    st.error(f"ไม่สามารถเล่นตัวอย่างเสียงได้: {e}")
        ov_rate = st.selectbox("ความเร็วเสียง:", ["-10%", "-5%", "+0%", "+5%", "+10%", "+15%", "+20%"], index=4)
        ov_pitch = st.selectbox("ระดับเสียง:", ["-5Hz", "-2Hz", "+0Hz", "+1Hz", "+2Hz", "+5Hz"], index=4)
        ov_bgm = st.toggle("เปิดเพลงคลอ Lo-Fi BGM", value=bool(prof.get("default_enable_bgm", True)), key="ov_bgm_tog")
        ov_bgm_vol = st.slider("ระดับเสียง BGM:", 0.05, 0.30, float(prof.get("default_bgm_vol", 0.12)), 0.01) if ov_bgm else 0.0
        ov_bg_color = st.color_picker("สีพื้นหลัง:", value=prof.get("default_bg_color", "#F5F2EB"))
        ov_hl_color = st.color_picker("สีกรอบไฟไฮไลต์:", value=prof.get("default_highlight_color", "#32CD32"))
        ov_wm_enable = st.toggle("เปิดลายน้ำกันก๊อป", value=True)

    # Render Action Button
    st.markdown("### 🎬 ขั้นตอนที่ 3: สั่งเรนเดอร์และเลือกระบบปลายทาง")
    col_act1, col_act2 = st.columns([1, 1], gap="medium")
    with col_act1:
        post_target_choice = st.radio(
            "🎯 ปลายทางหลังเรนเดอร์เสร็จ:",
            options=["📦 เซฟเก็บไว้ดู / ดาวน์โหลด (Save Only)", "🚀 ออโต้โพสต์ลงโซเชียลทันที (Auto-Post)"],
            index=0,
            key="post_target_choice",
            help="เลือกว่าต้องการแค่เซฟไฟล์วิดีโอไว้ดู หรือให้อัปโหลดไปยัง Facebook Reels / YouTube Shorts / TikTok อัตโนมัติทันทีที่เรนเดอร์เสร็จ",
        )
    with col_act2:
        st.caption("💡 หากเลือก **ออโต้โพสต์** ระบบจะส่งคลิป แคปชั่น แฮชแท็ก และคอมเมนต์ปักหมุดไปยังโซเชียลทุกช่องทางที่คุณเปิดใช้งานในแท็บตั้งค่าทันทีที่เรนเดอร์เสร็จ")

    if st.button("🚀 สั่งเรนเดอร์คลิปวิดีโอ 1080x1920 (9:16)", type="primary", use_container_width=True):
        status_box = st.status("🎬 กำลังเรนเดอร์วิดีโอ 1080x1920 (9:16)...", expanded=True)
        with status_box:
            try:
                t_stamp = int(time.time())
                img_a_path = ASSETS_DIR / "images" / f"item_a_{t_stamp}.png"
                img_b_path = ASSETS_DIR / "images" / f"item_b_{t_stamp}.png"

                is_multi = st.session_state.script_data.get("mode") == "multi_battle_3round"
                round_assets = None

                if is_multi:
                    st.write(f"🎨 กำลังสร้าง/ค้นหารูปภาพแบทเทิล 3 คู่ย่อย ({rnd_art_style})...")
                    round_assets = {}
                    for r in range(1, 4):
                        r_name_a = st.session_state.script_data.get(f"round_{r}_name_a") or f"{st.session_state.script_data.get('name_a')} #{r}"
                        r_name_b = st.session_state.script_data.get(f"round_{r}_name_b") or f"{st.session_state.script_data.get('name_b')} #{r}"
                        r_path_a = ASSETS_DIR / "images" / f"item_a_r{r}_{t_stamp}.png"
                        r_path_b = ASSETS_DIR / "images" / f"item_b_r{r}_{t_stamp}.png"
                        auto_fetch_or_create_image(r_name_a, r_path_a, is_item_b=False, allow_web_search=auto_fetch_chk, image_mode=rnd_img_mode, art_style=rnd_art_style)
                        time.sleep(0.5)
                        auto_fetch_or_create_image(r_name_b, r_path_b, is_item_b=True, allow_web_search=auto_fetch_chk, image_mode=rnd_img_mode, art_style=rnd_art_style)
                        round_assets[r] = {
                            "name_a": r_name_a,
                            "name_b": r_name_b,
                            "image_a_path": r_path_a,
                            "image_b_path": r_path_b,
                        }
                    img_a_path = round_assets[1]["image_a_path"]
                    img_b_path = round_assets[1]["image_b_path"]
                else:
                    if up_img_a:
                        img_a = Image.open(up_img_a)
                        img_a.save(img_a_path)
                    else:
                        auto_fetch_or_create_image(
                            st.session_state.script_data.get("name_a"),
                            img_a_path,
                            is_item_b=False,
                            allow_web_search=auto_fetch_chk,
                            image_mode=rnd_img_mode,
                            art_style=rnd_art_style,
                        )

                    time.sleep(0.5)

                    if up_img_b:
                        img_b = Image.open(up_img_b)
                        img_b.save(img_b_path)
                    else:
                        auto_fetch_or_create_image(
                            st.session_state.script_data.get("name_b"),
                            img_b_path,
                            is_item_b=True,
                            allow_web_search=auto_fetch_chk,
                            image_mode=rnd_img_mode,
                            art_style=rnd_art_style,
                        )

                st.write("🎙️ 1/3: สังเคราะห์เสียงพากย์ Edge Neural...")
                tts = TTSEngine(voice_key=voice_choice, speech_rate=ov_rate, speech_pitch=ov_pitch)
                output_mp4 = OUTPUT_DIR / f"shorts_vsify_{t_stamp}.mp4"
                master_audio_path = output_mp4.parent / f"{output_mp4.stem}_audio.mp3"

                timeline, audio_file, total_duration = tts.build_timeline(
                    script_data=st.session_state.script_data,
                    output_master_audio=master_audio_path,
                    include_bgm=ov_bgm,
                    bgm_volume=ov_bgm_vol,
                    include_sfx=bool(prof.get("default_enable_sfx", True)),
                )

                st.write("🎞️ 2/3: ตัดต่อคลิป 1080x1920 Dynamic Highlight & Watermark...")
                builder = VideoBuilder(
                    bg_color=hex_to_rgb(ov_bg_color),
                    highlight_color=hex_to_rgb(ov_hl_color),
                    animation_style=prof.get("default_anim_style", "pointer_and_border"),
                )

                wm_text = prof.get("watermark_text", "@vsify.official") if ov_wm_enable else None
                wm_opac = float(prof.get("watermark_opacity", 0.75))
                saved_logo = prof.get("logo_path", "")
                wm_logo = Path(saved_logo) if (ov_wm_enable and saved_logo and Path(saved_logo).exists()) else None

                char_path, char_poses = get_active_character_assets(prof)

                final_video = builder.build_video(
                    image_a_path=img_a_path,
                    image_b_path=img_b_path,
                    character_path=char_path,
                    character_poses=char_poses,
                    topic=st.session_state.script_data.get("topic"),
                    name_a=st.session_state.script_data.get("name_a"),
                    name_b=st.session_state.script_data.get("name_b"),
                    timeline=timeline,
                    master_audio_path=audio_file,
                    output_video_path=output_mp4,
                    watermark_logo_path=wm_logo,
                    watermark_text=wm_text,
                    watermark_opacity=wm_opac,
                    round_assets=round_assets,
                    subtitle_style=prof.get("default_subtitle_style", "clean_floating"),
                    subtitle_anim=prof.get("default_subtitle_anim", "typewriter"),
                )

                st.write("📱 3/3: สร้างภาพปกและบันทึกลงคลัง...")
                cover_path = output_mp4.parent / f"{output_mp4.stem}_cover.jpg"
                social_cap_dict = generate_social_caption(st.session_state.script_data)

                add_history_entry(
                    topic=st.session_state.script_data.get("topic"),
                    name_a=st.session_state.script_data.get("name_a"),
                    name_b=st.session_state.script_data.get("name_b"),
                    video_path=str(final_video),
                    cover_path=str(cover_path) if cover_path.exists() else None,
                    social_caption=social_cap_dict.get("social_caption", ""),
                    hashtags=social_cap_dict.get("hashtags", ""),
                    affiliate_comment=st.session_state.script_data.get("affiliate_comment", ""),
                    framework=st.session_state.script_data.get("framework", "persona"),
                    duration_mode=st.session_state.script_data.get("mode", "standard_3round"),
                    duration_seconds=total_duration,
                )

                st.session_state.rendered_video_path = str(final_video)

                if "ออโต้โพสต์" in post_target_choice:
                    st.write("🚀 4/4: กำลังส่งคลิปขึ้น Facebook / YouTube / TikTok อัตโนมัติ...")
                    m_p = output_mp4.parent / f"{output_mp4.stem}_meta.json"
                    res = publish_to_all_enabled(
                        video_path=str(final_video),
                        cover_path=str(cover_path) if cover_path.exists() else None,
                        meta_path=str(m_p) if m_p.exists() else None,
                    )
                    if res:
                        status_box.update(label=f"🎉 เรนเดอร์ & ออโต้โพสต์สำเร็จ {len(res)} ช่องทาง! ความยาว {total_duration:.1f} วินาที", state="complete")
                        st.toast(f"🚀 ออโต้โพสต์สำเร็จ {len(res)} แพลตฟอร์ม!")
                    else:
                        status_box.update(label=f"🎉 เรนเดอร์สำเร็จ! ความยาว {total_duration:.1f} วินาที (ยังไม่ได้เปิด API โซเชียลในแท็บตั้งค่า)", state="complete")
                else:
                    status_box.update(label=f"🎉 เรนเดอร์และบันทึกเสร็จสมบูรณ์! ความยาว {total_duration:.1f} วินาที", state="complete")
                    st.toast("✅ สร้างวิดีโอเรียบร้อยแล้ว!")
            except Exception as e:
                status_box.update(label=f"เกิดข้อผิดพลาด: {e}", state="error")
                st.error(f"เกิดข้อผิดพลาด: {e}")

    # Video Player & Output Preview
    v_path_str = st.session_state.rendered_video_path
    if not v_path_str:
        out_videos = sorted(OUTPUT_DIR.glob("shorts_*.mp4"), key=os.path.getmtime, reverse=True)
        if out_videos:
            v_path_str = str(out_videos[0])

    if v_path_str and Path(v_path_str).exists():
        v_path = Path(v_path_str)
        cover_path = v_path.parent / f"{v_path.stem}_cover.jpg"

        st.markdown("---")
        st.subheader("📱 ตัวอย่างวิดีโอและภาพปกที่สร้างเสร็จสมบูรณ์")

        with st.container(border=True):
            col_vid, col_cover = st.columns([1, 1], gap="medium")
            with col_vid:
                st.markdown("##### 🎬 คลิปวิดีโอ (1080x1920)")
                st.video(str(v_path))
                with open(v_path, "rb") as f:
                    st.download_button(
                        "⬇️ ดาวน์โหลดวิดีโอ MP4",
                        data=f,
                        file_name=v_path.name,
                        mime="video/mp4",
                        use_container_width=True,
                        type="primary",
                    )
            with col_cover:
                st.markdown("##### 🖼️ ภาพปกคลิป (Cover Thumbnail)")
                if cover_path.exists():
                    st.image(str(cover_path), caption=f"ภาพปก: {cover_path.name}", use_container_width=True)
                    with open(cover_path, "rb") as f:
                        st.download_button(
                            "⬇️ ดาวน์โหลดภาพปกคลิป",
                            data=f,
                            file_name=cover_path.name,
                            mime="image/jpeg",
                            use_container_width=True,
                        )
                else:
                    st.info("ยังไม่มีไฟล์ภาพปกสำหรับคลิปนี้ (จะถูกสร้างอัตโนมัติเมื่อเรนเดอร์)")

        st.markdown("#### 📱 แคปชั่น & แฮชแท็กสำหรับโพสต์ลงโซเชียล:")
        social_cap = st.session_state.script_data.get("social_caption") or generate_social_caption(st.session_state.script_data)["social_caption"]
        st.code(social_cap, language="text")

        is_viral_cur = st.session_state.script_data.get("clip_type") == "viral_knowledge"
        comment_header = "#### 💬 ข้อความสำหรับปักหมุดชวนคุยคอมเมนต์แรก (Discussion Prompt):" if is_viral_cur else "#### 📌 ข้อความสำหรับปักหมุดคอมเมนต์แรก (Shopee Affiliate):"
        st.markdown(comment_header)
        st.code(st.session_state.script_data.get("affiliate_comment", ""), language="text")

        if st.button("🚀 สั่งโพสต์คลิปนี้ลงโซเชียลเดี๋ยวนี้", type="secondary", use_container_width=True):
            with st.spinner("กำลังส่งคลิปไปยังแพลตฟอร์มที่เปิดใช้งาน..."):
                m_p = v_path.parent / f"{v_path.stem}_meta.json"
                res = publish_to_all_enabled(
                    video_path=str(v_path),
                    cover_path=str(cover_path) if cover_path.exists() else None,
                    meta_path=str(m_p) if m_p.exists() else None,
                )
                if res:
                    st.success(f"ส่งคำสั่งโพสต์แล้ว ({len(res)} ช่องทาง) ตรวจสอบที่แท็บ '3. คลังคลิปสำเร็จ & ประวัติโพสต์'")
                else:
                    st.warning("ยังไม่ได้เปิดใช้งานโซเชียลใดๆ (ไปตั้งค่าได้ที่แท็บ '4. ตั้งค่าส่วนกลาง')")

# =============================================================
# TAB 3: VIDEO VAULT & HISTORY (POST TRACKER & SOCIAL LOGS)
# =============================================================
with tab_history:
    st.subheader("🚀 คลังคลิปสำเร็จ & ประวัติการโพสต์ (Video Vault & Post History)")
    st.caption("ตรวจสอบคลิปทั้งหมดที่สร้างเสร็จแล้ว ดาวน์โหลด MP4 / ภาพปก หรือสั่งโพสต์ไปยังโซเชียลได้ทันที")

    all_history = load_history()
    draft_count = sum(1 for h in all_history if h.get("post_status", "draft") == "draft")
    auto_count = sum(1 for h in all_history if h.get("post_status") == "posted_auto")
    manual_count = sum(1 for h in all_history if h.get("post_status") == "posted_manual")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("📦 คลิปทั้งหมด", f"{len(all_history)} คลิป")
    with col_m2:
        st.metric("🟡 บันทึกเก็บไว้ (Draft)", f"{draft_count} คลิป")
    with col_m3:
        st.metric("🟢 โพสต์อัตโนมัติแล้ว", f"{auto_count} คลิป")
    with col_m4:
        st.metric("🔵 โพสต์เองแล้ว", f"{manual_count} คลิป")

    filter_choice = st.radio(
        "กรองตามสถานะ:",
        options=["ทั้งหมด", "🟡 บันทึกเก็บไว้ (Draft)", "🟢 โพสต์อัตโนมัติแล้ว", "🔵 โพสต์เองแล้ว"],
        horizontal=True,
        key="rad_filter_post_status",
    )

    filtered_list = all_history
    if filter_choice == "🟡 บันทึกเก็บไว้ (Draft)":
        filtered_list = [h for h in all_history if h.get("post_status", "draft") == "draft"]
    elif filter_choice == "🟢 โพสต์อัตโนมัติแล้ว":
        filtered_list = [h for h in all_history if h.get("post_status") == "posted_auto"]
    elif filter_choice == "🔵 โพสต์เองแล้ว":
        filtered_list = [h for h in all_history if h.get("post_status") == "posted_manual"]

    if not filtered_list:
        st.info("💡 ยังไม่มีคลิปในหมวดหมู่นี้ — คุณสามารถสร้างและเรนเดอร์คลิปใหม่ได้จากแท็บ '1. ร่างบท & สตูดิโอ' หรือ '2. เรนเดอร์'")
    else:
        for idx, item in enumerate(filtered_list):
            item_id = item.get("id", f"item_{idx}")
            item_status = item.get("post_status", "draft")
            status_badge = {
                "draft": "🟡 บันทึกเก็บไว้ (Save Only)",
                "posted_auto": f"🟢 โพสต์อัตโนมัติแล้ว ({', '.join(item.get('post_platforms', [])) or 'โซเชียล'})",
                "posted_manual": "🔵 โพสต์เองแล้ว (Manual Posted)",
            }.get(item_status, "🟡 บันทึกเก็บไว้")

            with st.expander(f"📌 {item.get('topic', 'ไม่มีชื่อ')} — {status_badge}", expanded=(idx < 2)):
                st.caption(f"⏱️ สร้างเมื่อ: {item.get('date_str', '')} | ความยาว: {item.get('duration_seconds', 0)} วินาที | กรอบ: {item.get('framework', '')}")
                if item.get("posted_at"):
                    st.caption(f"📢 โพสต์เมื่อ: {item.get('posted_at')}")

                v_path = item.get("video_path")
                c_path = item.get("cover_path")
                if v_path and Path(v_path).exists():
                    col_pv, col_pc = st.columns([1.2, 1])
                    with col_pv:
                        st.markdown("**🎬 วิดีโอ (9:16):**")
                        st.video(v_path)
                        with open(v_path, "rb") as vf:
                            st.download_button(
                                "⬇️ ดาวน์โหลดวิดีโอ MP4",
                                data=vf,
                                file_name=Path(v_path).name,
                                mime="video/mp4",
                                key=f"dl_vid_t4_{item_id}",
                                use_container_width=True,
                            )
                    with col_pc:
                        if c_path and Path(c_path).exists():
                            st.markdown("**🖼️ ภาพปกคลิป:**")
                            st.image(c_path, use_container_width=True)
                            with open(c_path, "rb") as cf:
                                st.download_button(
                                    "⬇️ ดาวน์โหลดภาพปก",
                                    data=cf,
                                    file_name=Path(c_path).name,
                                    mime="image/jpeg",
                                    key=f"dl_cov_t4_{item_id}",
                                    use_container_width=True,
                                )

                st.markdown("**📱 แคปชั่น & แฮชแท็ก:**")
                st.code(f"{item.get('social_caption', '')}\n\n{item.get('hashtags', '')}", language="text")

                if item.get("affiliate_comment"):
                    st.markdown("**📌 พิกัด Affiliate ปักหมุด:**")
                    st.code(item.get("affiliate_comment", ""), language="text")

                st.markdown("##### 🛠️ จัดการการโพสต์โซเชียล")
                if st.button("🚀 สั่งโพสต์คลิปนี้ลงโซเชียลทันที", key=f"btn_pub_single_{item_id}", type="primary", use_container_width=True):
                    v_p = item.get("video_path")
                    if not v_p or not Path(v_p).exists():
                        st.error("ไม่พบไฟล์วิดีโอในเครื่อง")
                    else:
                        c_p = item.get("cover_path")
                        m_p = Path(v_p).parent / f"{Path(v_p).stem}_meta.json"
                        with st.spinner(f"กำลังส่งคลิป '{item.get('topic')}' ไปยังแพลตฟอร์มที่เปิดใช้งาน..."):
                            res = publish_to_all_enabled(
                                video_path=v_p,
                                cover_path=c_p if c_p and Path(c_p).exists() else None,
                                meta_path=str(m_p) if m_p.exists() else None,
                            )
                            if res:
                                update_history_post_status(item_id, "posted_auto", platforms=list(res.keys()))
                                st.success(f"🎉 ส่งคำสั่งโพสต์แล้ว ({len(res)} ช่องทาง: {', '.join(res.keys())})")
                                st.rerun()
                            else:
                                st.warning("ยังไม่ได้เปิดใช้งานหรือกรอก Token ในแพลตฟอร์มใดๆ (ไปตั้งค่าได้ที่แท็บ '4. ตั้งค่าส่วนกลาง')")

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if item_status != "posted_manual":
                        if st.button("✅ ทำเครื่องหมาย 'โพสต์เองแล้ว'", key=f"btn_mark_manual_{item_id}", use_container_width=True):
                            update_history_post_status(item_id, "posted_manual")
                            st.toast(f"บันทึกสถานะ 'โพสต์เองแล้ว' สำหรับคลิป: {item.get('topic')} เรียบร้อย!")
                            st.rerun()
                with col_b2:
                    if item_status != "draft":
                        if st.button("🔄 รีเซ็ตกลับเป็น 'บันทึกเก็บไว้' (Draft)", key=f"btn_reset_draft_{item_id}", use_container_width=True):
                            update_history_post_status(item_id, "draft")
                            st.toast(f"รีเซ็ตคลิป: {item.get('topic')} กลับเป็น Draft แล้ว!")
                            st.rerun()

    st.divider()
    st.markdown("#### 📜 ประวัติการส่งโพสต์โซเชียล (Live Auto-Post Logs)")
    post_cfg = load_autopost_config()
    p_logs = post_cfg.get("post_log", [])
    if not p_logs:
        st.caption("ยังไม่มีประวัติการส่งโพสต์ในระบบ")
    else:
        st.text_area("Social Post Activity", value="\n".join(p_logs), height=180, disabled=True)

# =============================================================
# TAB 4: GLOBAL SETTINGS (ONE-TIME SETUP FOR BRAND, LOGO, VOICE & APIS)
# =============================================================
with tab_settings:
    st.subheader("⚙️ ตั้งค่าระบบส่วนกลาง (VSIFY Global Settings)")
    st.caption("ตั้งค่าแบรนด์ อัปโหลดโลโก้เพจ เลือกลายน้ำ เสียงพากย์เริ่มต้น มาสคอต และเชื่อมต่อ API แบบครั้งเดียวจบ ระบบจะจดจำและนำไปใช้กับทุกคลิปอัตโนมัติ")

    # SECTION 1: BRANDING & WATERMARK
    st.markdown("### 🏢 หมวดที่ 1: ข้อมูลแบรนด์เพจ & ลายน้ำกันก๊อป (Branding & Watermark)")

    s_name = st.text_input("ชื่อเพจ / ช่อง (Channel Name):", value=prof.get("channel_name", "VSIFY"))
    s_tagline = st.text_input("สโลแกนประจำช่อง (Tagline):", value=prof.get("tagline", "See Both. Know Better."))
    s_wm_text = st.text_input("ข้อความลายน้ำในคลิป (Watermark Text):", value=prof.get("watermark_text", "@vsify.official"))
    s_wm_opac = st.slider("ความชัดของลายน้ำ (Opacity):", 0.2, 1.0, float(prof.get("watermark_opacity", 0.75)), 0.05)

    st.markdown("**🛡️ อัปโหลดโลโก้เพจ / ตราลายน้ำ (PNG พื้นใส)**")
    up_logo = st.file_uploader("เลือกไฟล์โลโก้เพจ (แนะนำ PNG พื้นใส):", type=["png"], key="set_logo_uploader")
    cur_logo = prof.get("logo_path", "")
    if up_logo:
        save_logo_p = ASSETS_DIR / "images" / "channel_logo.png"
        with open(save_logo_p, "wb") as f:
            f.write(up_logo.getbuffer())
        prof["logo_path"] = str(save_logo_p)
        st.success("✅ อัปโหลดโลโก้ใหม่สำเร็จ!")
        st.image(up_logo, caption="พรีวิวโลโก้เพจที่จะแสดงเป็นลายน้ำในคลิป", width=180)
    elif cur_logo and Path(cur_logo).exists():
        st.image(cur_logo, caption="โลโก้เพจปัจจุบันที่ระบบใช้อยู่", width=180)
    else:
        st.info("ℹ️ ยังไม่มีการอัปโหลดโลโก้ (ระบบจะใช้ข้อความลายน้ำแทน)")

    s_outro = st.text_area("บทส่งท้ายประจำเพจ (Default Outro CTA):", value=prof.get("default_outro_cta", "ถ้าอยากเลือกให้ชัวร์และรู้ลึกกว่าเดิม อย่าลืมกดติดตาม VSIFY ไว้นะครับ! See Both. Know Better."), height=70)

    st.divider()

    # SECTION 2: DEFAULT VOICE & BGM
    st.markdown("### 🎙️ หมวดที่ 2: เสียงพากย์ & เพลงคลอ BGM เริ่มต้น (Default Voice & Sound)")

    voice_keys = list(TTSEngine.VOICE_PRESETS.keys())
    cur_def_v_idx = voice_keys.index(prof.get("default_voice", "edge_senior_male")) if prof.get("default_voice") in voice_keys else 0
    v_def_key = st.selectbox(
        "ผู้บรรยายเสียงพากย์หลัก (Voice):",
        options=voice_keys,
        index=cur_def_v_idx,
        format_func=lambda x: TTSEngine.VOICE_PRESETS[x]["desc"],
        key="set_def_voice",
    )
    if st.button("🔊 ทดลองฟังเสียงนี้ทันที (Sample Preview)", key="btn_test_voice", use_container_width=True):
        with st.spinner("กำลังสังเคราะห์ตัวอย่างเสียง..."):
            try:
                t_engine = TTSEngine(voice_key=v_def_key)
                sample_p = TEMP_DIR / f"sample_{v_def_key}.mp3"
                t_engine.synthesize_segment("สวัสดีครับ ยินดีต้อนรับสู่ช่อง เปรียบเทียบสาระน่ารู้", sample_p)
                st.audio(str(sample_p), format="audio/mp3")
            except Exception as e:
                st.error(f"ไม่สามารถเล่นตัวอย่างเสียงได้: {e}")

    v_def_emo = st.selectbox(
        "อารมณ์เสียงเริ่มต้น (Emotion):",
        options=list(TTSEngine.EMOTION_PRESETS.keys()),
        index=list(TTSEngine.EMOTION_PRESETS.keys()).index(prof.get("default_emotion", "story")) if prof.get("default_emotion") in TTSEngine.EMOTION_PRESETS else 1,
        format_func=lambda k: TTSEngine.EMOTION_PRESETS[k]["name"],
        key="set_def_emo",
    )

    s_def_rate = st.selectbox("ความเร็วเริ่มต้น:", ["-10%", "-8%", "-5%", "-2%", "+0%", "+5%", "+10%", "+15%", "+20%"], index=4, key="set_def_rate")
    s_def_pitch = st.selectbox("ระดับเสียงเริ่มต้น:", ["-14Hz", "-10Hz", "-8Hz", "-5Hz", "-2Hz", "+0Hz", "+1Hz", "+2Hz", "+5Hz"], index=5, key="set_def_pitch")

    s_def_bgm = st.toggle("เปิดเพลงคลอ Lo-Fi BGM เสมอ", value=bool(prof.get("default_enable_bgm", True)), key="set_def_bgm")
    s_def_bgm_vol = st.slider("ระดับเสียง BGM เริ่มต้น:", 0.05, 0.30, float(prof.get("default_bgm_vol", 0.12)), 0.01, key="set_def_bgm_vol") if s_def_bgm else 0.0
    s_def_sfx = st.toggle("เปิดเสียง Effect (Pop / Whoosh) ตอนสลับกรอบชี้", value=bool(prof.get("default_enable_sfx", True)), key="set_def_sfx")

    st.divider()

    # SECTION 3: VISUALS, BACKGROUND & MASCOT
    st.markdown("### 🎭 หมวดที่ 3: งานภาพ, สีพื้นหลัง & ตัวละคร Mascot Animation (8 ท่าทางบันทึกถาวร)")

    st.markdown("##### 🎨 การตั้งค่างานภาพ & ซับไตเติล (Visuals & Subtitles)")
    s_sub_style = st.selectbox(
        "สไตล์แสดงผลซับไตเติล (Subtitle Display Style):",
        options=["clean_floating", "paper_card"],
        index=0 if prof.get("default_subtitle_style", "clean_floating") == "clean_floating" else 1,
        format_func=lambda x: "✨ ข้อความลอยโปร่งใส ไร้กรอบ (Clean Floating — สไตล์ TikTok/Reels คมชัด)" if x == "clean_floating" else "📄 การ์ดสติกเกอร์สีขาว (Paper Card — สไตล์เพจแตกต่างกันอย่างไร)",
        key="set_sub_style",
        help="เลือกระหว่างข้อความลอยไร้กรอบพื้นหลัง หรือการ์ดสติกเกอร์สีขาว",
    )
    s_sub_anim = st.selectbox(
        "แอนิเมชันตัวหนังสือ (Subtitle Animation):",
        options=["typewriter", "sentence_pop"],
        index=0 if prof.get("default_subtitle_anim", "typewriter") == "typewriter" else 1,
        format_func=lambda x: "⌨️ พิมพ์ทีละตัวอักษรตามเสียงพูด (Typewriter Effect)" if x == "typewriter" else "💬 แสดงทีละทั้งประโยค (Sentence Pop — อ่านสบายตา)",
        key="set_sub_anim",
    )
    s_anim_style = st.selectbox(
        "สไตล์ตัวชี้และกรอบไฟ:",
        options=["pointer_and_border", "border_only"],
        index=0 if prof.get("default_anim_style", "pointer_and_border") == "pointer_and_border" else 1,
        format_func=lambda x: "ตัวชี้ลอยสลับไปมา + กรอบไฟนีออน (แนะนำ)" if x == "pointer_and_border" else "กรอบไฟนีออนอย่างเดียว",
        key="set_anim_style",
    )
    s_img_mode = st.selectbox(
        "โหมดสร้างรูปภาพคู่เปรียบเทียบ A & B เริ่มต้น:",
        options=["ai_cartoon", "web_search", "minimal_card"],
        index=["ai_cartoon", "web_search", "minimal_card"].index(prof.get("default_image_mode", "ai_cartoon")),
        format_func=lambda x: {
            "ai_cartoon": "✨ สร้างภาพการ์ตูน AI ตามธีมเพจ (แนะนำ)",
            "web_search": "🌐 ค้นหาภาพจริงจากเว็บ/วิกิพีเดีย (Wikipedia & Web)",
            "minimal_card": "🔲 การ์ดข้อความกราฟิกโมเดิร์น (Minimal Graphic Card)",
        }[x],
        key="set_img_mode",
    )
    s_art_style = st.selectbox(
        "🎨 สไตล์ลายเส้นการ์ตูน AI เริ่มต้น (Cartoon Art Style):",
        options=list(CARTOON_STYLES.keys()),
        index=list(CARTOON_STYLES.keys()).index(prof.get("default_art_style", "3d_pixar")) if prof.get("default_art_style") in CARTOON_STYLES else 0,
        format_func=lambda k: CARTOON_STYLES[k]["name"],
        key="set_art_style",
        help="เลือกลายเส้นสำหรับภาพการ์ตูน AI เช่น 3D Pixar, 2D Flat, Studio Ghibli, Claymation หรือ Cyberpunk",
    )
    s_bg_color = st.color_picker("สีพื้นหลังเริ่มต้น (Solid Cream):", value=prof.get("default_bg_color", "#F5F2EB"), key="set_bg_color")
    s_hl_color = st.color_picker("สีกรอบไฟไฮไลต์นีออน (Active Lime):", value=prof.get("default_highlight_color", "#32CD32"), key="set_hl_color")

    st.markdown("##### 🎭 ตัวละครมาสคอตพิธีกรประจำเพจ (Mascot Host)")
    s_char_mode = st.radio(
        "รูปแบบตัวละครมาสคอตพิธีกร (Mascot):",
        options=["multi_pose", "builtin"],
        index=0 if prof.get("default_char_mode", "multi_pose") == "multi_pose" else 1,
        format_func=lambda x: {
            "multi_pose": "🎨 มาสคอตคัสตอม 8 รูป (4 ท่า x หุบปาก/อ้าปาก) — สำหรับคลิปเนียนระดับโปร",
            "builtin": "✨ มาสคอตระบบ VSIFY Host (ตัวเริ่มต้น)",
        }[x],
        key="set_char_mode",
    )

    if s_char_mode == "multi_pose":
        st.markdown("##### 📥 อัปโหลดรูปมาสคอตเต็มตัว 8 รูป (4 ท่าทาง x หุบปาก/อ้าปาก)")
        st.caption("💡 **วาดเห็นเต็มตัวตั้งแต่หัวจรดเท้าได้เลยครับ:** ระบบจัดวางให้เท้ายืนบนพื้นสตูดิโอ มีเงามิติที่พื้น และศีรษะอยู่ใต้ซับไตเติลพอดีเป๊ะ พร้อมตัดพื้นหลังโปร่งใสให้อัตโนมัติ")

        def _get_pose_img(key: str) -> str:
            val = prof.get(key, "")
            if val and Path(val).exists():
                return val
            fallback = ASSETS_DIR / "images" / f"{key}.png"
            if fallback.exists():
                return str(fallback)
            return ""

        # Quick 1-click Auto-Distributor for 1 or 2 images:
        with st.expander("⚡ มีรูปแค่ 1 รูป หรือ 2 รูป (หุบปาก/อ้าปาก)? กระจายใส่ครบ 8 ท่าในคลิกเดียว!", expanded=False):
            st.caption("ถ้าคุณเพิ่งสร้างรูปมาแค่ 1 รูป (รูปเดี่ยว) หรือ 2 รูป (หุบปาก/อ้าปาก) อัปโหลดตรงนี้ แล้วกดปุ่ม ระบบจะนำไปใช้กับทุกท่าทางให้อัตโนมัติทันที ไม่ต้องวาดแยก 8 รูปครับ!")
            up_q_cl = st.file_uploader("1. รูปหลัก / หุบปาก (เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_quick_cl")
            up_q_op = st.file_uploader("2. รูปอ้าปากพูด (ถ้ามี):", type=["png", "jpg", "jpeg"], key="up_quick_op")

            if st.button("🪄 กระจายรูปนี้ใส่ครบทั้ง 8 ท่าทางทันที", use_container_width=True, type="secondary"):
                if up_q_cl:
                    clean_cl = remove_fake_checkerboard_bg(Image.open(up_q_cl))
                    clean_op = remove_fake_checkerboard_bg(Image.open(up_q_op)) if up_q_op else clean_cl
                    for k, is_op in [
                        ("char_pose_think", False), ("char_pose_think_open", True),
                        ("char_pose_a", False), ("char_pose_a_open", True),
                        ("char_pose_b", False), ("char_pose_b_open", True),
                        ("char_pose_neutral", False), ("char_pose_neutral_open", True),
                    ]:
                        p = ASSETS_DIR / "images" / f"{k}.png"
                        im = clean_op if is_op else clean_cl
                        im.save(p, "PNG")
                        prof[k] = str(p)
                    prof["char_single_path"] = str(ASSETS_DIR / "images" / "char_pose_think.png")
                    prof["default_char_mode"] = "multi_pose"
                    save_channel_profile(prof)
                    st.session_state.channel_profile = prof
                    st.success("🎉 กระจายรูปใส่ครบทุกท่าเรียบร้อยแล้ว!")
                    st.rerun()
                else:
                    st.warning("กรุณาเลือกรูปหลัก (หุบปาก) ก่อนกดปุ่มครับ")

        # 1. ท่าคิด (Hook)
        with st.expander("🤔 ท่าที่ 1: ท่าคิด (ใช้ตอนเปิดคลิป Hook)", expanded=True):
            cur_t_cl = _get_pose_img("char_pose_think")
            if cur_t_cl and Path(cur_t_cl).exists():
                st.image(cur_t_cl, width=120, caption="1.1 ท่าคิด (หุบปาก)")
            up_t_cl = st.file_uploader("1.1 ท่าคิด — หุบปาก (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_t_cl")
            if up_t_cl:
                p_t_cl = ASSETS_DIR / "images" / "char_pose_think.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_t_cl))
                    clean_im.save(p_t_cl, "PNG")
                except Exception:
                    with open(p_t_cl, "wb") as f:
                        f.write(up_t_cl.getbuffer())
                prof["char_pose_think"] = str(p_t_cl)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่าคิด (หุบปาก) ถาวรแล้ว!")

            cur_t_op = _get_pose_img("char_pose_think_open")
            if cur_t_op and Path(cur_t_op).exists():
                st.image(cur_t_op, width=120, caption="1.2 ท่าคิด (อ้าปาก)")
            up_t_op = st.file_uploader("1.2 ท่าคิด — อ้าปากพูด (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_t_op")
            if up_t_op:
                p_t_op = ASSETS_DIR / "images" / "char_pose_think_open.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_t_op))
                    clean_im.save(p_t_op, "PNG")
                except Exception:
                    with open(p_t_op, "wb") as f:
                        f.write(up_t_op.getbuffer())
                prof["char_pose_think_open"] = str(p_t_op)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่าคิด (อ้าปาก) ถาวรแล้ว!")

        # 2. ท่าชี้ A (ซ้าย)
        with st.expander("👈 ท่าที่ 2: ท่าชี้สินค้า A (หันชี้ไปทางซ้าย)", expanded=True):
            cur_a_cl = _get_pose_img("char_pose_a")
            if cur_a_cl and Path(cur_a_cl).exists():
                st.image(cur_a_cl, width=120, caption="2.1 ชี้ A (หุบปาก)")
            up_a_cl = st.file_uploader("2.1 ท่าชี้ A — หุบปาก (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_a_cl")
            if up_a_cl:
                p_a_cl = ASSETS_DIR / "images" / "char_pose_a.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_a_cl))
                    clean_im.save(p_a_cl, "PNG")
                except Exception:
                    with open(p_a_cl, "wb") as f:
                        f.write(up_a_cl.getbuffer())
                prof["char_pose_a"] = str(p_a_cl)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่าชี้ A (หุบปาก) ถาวรแล้ว!")

            cur_a_op = _get_pose_img("char_pose_a_open")
            if cur_a_op and Path(cur_a_op).exists():
                st.image(cur_a_op, width=120, caption="2.2 ชี้ A (อ้าปาก)")
            up_a_op = st.file_uploader("2.2 ท่าชี้ A — อ้าปากพูด (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_a_op")
            if up_a_op:
                p_a_op = ASSETS_DIR / "images" / "char_pose_a_open.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_a_op))
                    clean_im.save(p_a_op, "PNG")
                except Exception:
                    with open(p_a_op, "wb") as f:
                        f.write(up_a_op.getbuffer())
                prof["char_pose_a_open"] = str(p_a_op)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่าชี้ A (อ้าปาก) ถาวรแล้ว!")

        # 3. ท่าชี้ B (ขวา)
        with st.expander("👉 ท่าที่ 3: ท่าชี้สินค้า B (หันชี้ไปทางขวา)", expanded=True):
            cur_b_cl = _get_pose_img("char_pose_b")
            if cur_b_cl and Path(cur_b_cl).exists():
                st.image(cur_b_cl, width=120, caption="3.1 ชี้ B (หุบปาก)")
            up_b_cl = st.file_uploader("3.1 ท่าชี้ B — หุบปาก (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_b_cl")
            if up_b_cl:
                p_b_cl = ASSETS_DIR / "images" / "char_pose_b.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_b_cl))
                    clean_im.save(p_b_cl, "PNG")
                except Exception:
                    with open(p_b_cl, "wb") as f:
                        f.write(up_b_cl.getbuffer())
                prof["char_pose_b"] = str(p_b_cl)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่าชี้ B (หุบปาก) ถาวรแล้ว!")

            cur_b_op = _get_pose_img("char_pose_b_open")
            if cur_b_op and Path(cur_b_op).exists():
                st.image(cur_b_op, width=120, caption="3.2 ชี้ B (อ้าปาก)")
            up_b_op = st.file_uploader("3.2 ท่าชี้ B — อ้าปากพูด (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_b_op")
            if up_b_op:
                p_b_op = ASSETS_DIR / "images" / "char_pose_b_open.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_b_op))
                    clean_im.save(p_b_op, "PNG")
                except Exception:
                    with open(p_b_op, "wb") as f:
                        f.write(up_b_op.getbuffer())
                prof["char_pose_b_open"] = str(p_b_op)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่าชี้ B (อ้าปาก) ถาวรแล้ว!")

        # 4. ท่ายิ้มสรุป (Conclusion)
        with st.expander("🎉 ท่าที่ 4: ท่ายิ้มสรุป (ใช้ตอนท้ายคลิป สรุปฟันธง)", expanded=True):
            cur_n_cl = _get_pose_img("char_pose_neutral")
            if cur_n_cl and Path(cur_n_cl).exists():
                st.image(cur_n_cl, width=120, caption="4.1 สรุป (หุบปาก)")
            up_n_cl = st.file_uploader("4.1 ท่ายิ้มสรุป — หุบปาก (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_n_cl")
            if up_n_cl:
                p_n_cl = ASSETS_DIR / "images" / "char_pose_neutral.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_n_cl))
                    clean_im.save(p_n_cl, "PNG")
                except Exception:
                    with open(p_n_cl, "wb") as f:
                        f.write(up_n_cl.getbuffer())
                prof["char_pose_neutral"] = str(p_n_cl)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่ายิ้มสรุป (หุบปาก) ถาวรแล้ว!")

            cur_n_op = _get_pose_img("char_pose_neutral_open")
            if cur_n_op and Path(cur_n_op).exists():
                st.image(cur_n_op, width=120, caption="4.2 สรุป (อ้าปาก)")
            up_n_op = st.file_uploader("4.2 ท่ายิ้มสรุป — อ้าปากพูด (PNG เต็มตัว):", type=["png", "jpg", "jpeg"], key="up_n_op")
            if up_n_op:
                p_n_op = ASSETS_DIR / "images" / "char_pose_neutral_open.png"
                try:
                    clean_im = remove_fake_checkerboard_bg(Image.open(up_n_op))
                    clean_im.save(p_n_op, "PNG")
                except Exception:
                    with open(p_n_op, "wb") as f:
                        f.write(up_n_op.getbuffer())
                prof["char_pose_neutral_open"] = str(p_n_op)
                prof["default_char_mode"] = "multi_pose"
                save_channel_profile(prof)
                st.session_state.channel_profile = prof
                st.success("✅ อัปโหลดและบันทึกท่ายิ้มสรุป (อ้าปาก) ถาวรแล้ว!")

        st.markdown("##### 💾 บันทึกการตั้งค่ามาสคอตถาวร")
        if st.button("💾 บันทึกรูปมาสคอตทั้ง 8 ท่าไว้ใช้ตลอดไป (Save All 8 Poses Permanently)", type="primary", use_container_width=True, key="btn_save_all_poses_perm"):
            prof["default_char_mode"] = "multi_pose"
            # Scan & ensure all 8 pose keys are strictly linked to the disk files
            for k in [
                "char_pose_think", "char_pose_think_open",
                "char_pose_a", "char_pose_a_open",
                "char_pose_b", "char_pose_b_open",
                "char_pose_neutral", "char_pose_neutral_open",
            ]:
                cur_p = prof.get(k, "")
                if not cur_p or not Path(cur_p).exists():
                    fallback_p = ASSETS_DIR / "images" / f"{k}.png"
                    if fallback_p.exists():
                        prof[k] = str(fallback_p)
            save_channel_profile(prof)
            st.session_state.channel_profile = prof
            st.toast("✅ บันทึกรูปมาสคอตทั้ง 8 ท่าไว้ใช้ตลอดไปเรียบร้อยแล้ว!")
            st.success("🎉 บันทึกรูปมาสคอตประจำเพจครบทั้ง 8 ท่าทางไว้ใช้ตลอดไปเรียบร้อยแล้ว! ข้อมูลจะถูกจดจำไว้ถาวร ไม่ต้องอัปโหลดใหม่อีกต่อไปครับ")

    else:
        builtin_p = IMAGES_DIR / "character_host.png"
        if builtin_p.exists():
            st.image(str(builtin_p), width=150, caption="มาสคอตระบบ VSIFY Host (พร้อม 4 ท่าครบชุด)")

    st.divider()

    # SECTION 4: SHOPEE AUTO-AFFILIATE
    st.markdown("### 🛒 หมวดที่ 4: ระบบนายหน้า Shopee Auto-Affiliate")
    shp_cfg = load_shopee_config()
    s_shp_enable = st.toggle("เปิดระบบแปลงลิงก์ Shopee Affiliate อัตโนมัติ", value=bool(shp_cfg.get("enabled", True)), key="set_shp_en")
    s_shp_aff_id = st.text_input("Shopee Affiliate Username / Partner ID:", value=shp_cfg.get("affiliate_id", ""), placeholder="เช่น whyitworks_aff หรือ user ID ของคุณ", key="set_shp_id")
    s_shp_sub1 = st.text_input("Sub-Tracking ID (สำหรับวัดผล):", value=shp_cfg.get("sub_ids", ["VSIFY"])[0] if shp_cfg.get("sub_ids") else "VSIFY", key="set_shp_sub")
    s_shp_appid = st.text_input("Shopee Open API App ID (ถ้ามี):", value=shp_cfg.get("app_id", ""), placeholder="เช่น 18000000000", key="set_shp_appid")
    s_shp_secret = st.text_input("Shopee Open API Secret Key (ถ้ามี):", value=shp_cfg.get("secret", ""), type="password", key="set_shp_sec")
    st.caption("💡 หากไม่มี App ID/Secret ระบบจะใช้โหมด Universal Tracking Link ให้โดยอัตโนมัติ 100%")

    st.divider()

    # SECTION 5: SOCIAL APIS & GOOGLE DRIVE
    st.markdown("### 🚀 หมวดที่ 5: การเชื่อมต่อโซเชียลมีเดีย & Google Drive Sync")
    post_cfg = load_autopost_config()
    gd_cfg = load_gdrive_config()

    st.markdown("#### ☁️ Google Drive Sync")
    is_local, local_msg = is_local_gdrive_path()
    if is_local:
        st.success(f"🟢 **ตรวจพบ Google Drive ในเครื่อง:** {local_msg}\n\nทุกคลิปจะถูกซิงก์ขึ้น Google Drive บนมือถือของคุณอัตโนมัติ!")
    s_gd_enable = st.toggle("เปิดซิงก์ Google Drive อัตโนมัติ", value=bool(gd_cfg.get("enabled", True)), key="set_gd_en")
    s_gd_webhook = st.text_input("Google Apps Script Webhook URL (สำหรับคลาวด์):", value=gd_cfg.get("webhook_url", ""), key="set_gd_wh")

    st.markdown("#### 🔵 Facebook Page Reels")
    s_fb_enable = st.toggle("เปิดโพสต์ Facebook Reels อัตโนมัติ", value=bool(post_cfg.get("facebook_enabled", False)), key="set_fb_en")
    s_fb_pid = st.text_input("Facebook Page ID:", value=post_cfg.get("facebook_page_id", ""), placeholder="เช่น 108928374829102", key="set_fb_pid")
    s_fb_tok = st.text_input("Page Access Token:", value=post_cfg.get("facebook_access_token", ""), type="password", key="set_fb_tok")
    if st.button("🧪 ทดสอบการเชื่อมต่อ Facebook Page", key="set_btn_test_fb", use_container_width=True):
        post_cfg["facebook_page_id"] = s_fb_pid
        post_cfg["facebook_access_token"] = s_fb_tok
        save_autopost_config(post_cfg)
        ok, msg = test_facebook_connection()
        if ok:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")

    st.markdown("#### 🔴 YouTube Shorts")
    s_yt_enable = st.toggle("เปิดโพสต์ YouTube Shorts อัตโนมัติ", value=bool(post_cfg.get("youtube_enabled", False)), key="set_yt_en")
    s_yt_tok = st.text_input("YouTube OAuth Access Token:", value=post_cfg.get("youtube_access_token", ""), type="password", key="set_yt_tok")
    if st.button("🧪 ทดสอบการเชื่อมต่อ YouTube Data API", key="set_btn_test_yt", use_container_width=True):
        post_cfg["youtube_access_token"] = s_yt_tok
        save_autopost_config(post_cfg)
        ok, msg = test_youtube_connection()
        if ok:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")

    st.markdown("#### ⚫ TikTok Webhook (Buffer / Make.com)")
    s_wh_enable = st.toggle("เปิดใช้งาน Social Webhook", value=bool(post_cfg.get("webhook_enabled", False)), key="set_wh_en")
    s_wh_url = st.text_input("Social Webhook URL:", value=post_cfg.get("webhook_url", ""), key="set_wh_url")
    if st.button("🧪 ทดสอบส่ง Webhook จำลอง", key="set_btn_test_wh", use_container_width=True):
        post_cfg["webhook_url"] = s_wh_url
        save_autopost_config(post_cfg)
        ok, msg = test_webhook_connection()
        if ok:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")

    st.markdown("---")

    # Master Save Button
    if st.button("💾 บันทึกการตั้งค่าส่วนกลางทั้งหมด (Save All Global Settings)", type="primary", use_container_width=True):
        # Save Channel Profile
        prof["channel_name"] = s_name
        prof["tagline"] = s_tagline
        prof["watermark_text"] = s_wm_text
        prof["watermark_opacity"] = s_wm_opac
        prof["default_outro_cta"] = s_outro
        prof["default_voice"] = v_def_key
        prof["default_emotion"] = v_def_emo
        prof["default_rate"] = s_def_rate
        prof["default_pitch"] = s_def_pitch
        prof["default_enable_bgm"] = s_def_bgm
        prof["default_bgm_vol"] = s_def_bgm_vol
        prof["default_enable_sfx"] = s_def_sfx
        prof["default_anim_style"] = s_anim_style
        prof["default_bg_color"] = s_bg_color
        prof["default_highlight_color"] = s_hl_color
        prof["default_char_mode"] = s_char_mode
        prof["default_image_mode"] = s_img_mode
        prof["default_art_style"] = s_art_style
        prof["default_subtitle_style"] = s_sub_style
        prof["default_subtitle_anim"] = s_sub_anim
        save_channel_profile(prof)
        st.session_state.channel_profile = prof

        # Save Shopee Config
        shp_cfg["enabled"] = s_shp_enable
        shp_cfg["affiliate_id"] = s_shp_aff_id
        shp_cfg["sub_ids"] = [s_shp_sub1]
        shp_cfg["app_id"] = s_shp_appid
        shp_cfg["secret"] = s_shp_secret
        save_shopee_config(shp_cfg)

        # Save Social Auto-Post Config
        post_cfg["facebook_enabled"] = s_fb_enable
        post_cfg["facebook_page_id"] = s_fb_pid
        post_cfg["facebook_access_token"] = s_fb_tok
        post_cfg["youtube_enabled"] = s_yt_enable
        post_cfg["youtube_access_token"] = s_yt_tok
        post_cfg["webhook_enabled"] = s_wh_enable
        post_cfg["webhook_url"] = s_wh_url
        save_autopost_config(post_cfg)

        # Save Google Drive Config
        gd_cfg["enabled"] = s_gd_enable
        gd_cfg["webhook_url"] = s_gd_webhook
        save_gdrive_config(gd_cfg)

        st.toast("✅ บันทึกการตั้งค่าส่วนกลางทั้งหมดเรียบร้อยแล้ว!")
        st.success("🎉 บันทึกการตั้งค่าสำเร็จ! ทุกคลิปใหม่จะใช้การตั้งค่านี้โดยอัตโนมัติ")
        st.rerun()
