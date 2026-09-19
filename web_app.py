"""
Streamlit Web Application for Automated Short-Form Comparison Video Generation (9:16 Vertical).
Features a 4-Step Professional Production Studio:
1. Deep Research & Input Specification
2. Script Review Studio & AI Rewriter
3. Voice, Audio (BGM/SFX), Visual & Animation Customization
4. Video Rendering, Live Preview & Affiliate Management
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
    page_title="Shorts Studio - 9:16 Comparison Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import (
    ASSETS_DIR,
    IMAGES_DIR,
    SCRIPTS_DIR,
    OUTPUT_DIR,
    AUDIO_DIR,
    COLOR_BG_CREAM,
    COLOR_HIGHLIGHT_LIME,
    load_channel_profile,
    save_channel_profile,
    DEFAULT_CHANNEL_PROFILE,
)
from ai_script_generator import (
    AIScriptGenerator,
    get_random_idea,
    FRAMEWORK_PRESETS,
    DURATION_MODES,
    CATEGORIES,
    generate_social_caption,
)
from tts_engine import TTSEngine
from video_builder import VideoBuilder
from pipeline import hex_to_rgb
from image_fetcher import auto_fetch_or_create_image
from content_history import load_history, add_history_entry, delete_history_entry
from scheduler_daemon import (
    ensure_scheduler_running,
    load_autopilot_config,
    save_autopilot_config,
    run_autopilot_cycle,
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

    /* iOS Segmented Control Tabs */
    div[data-baseweb="tab-list"] {
        background-color: #E5E5EA !important;
        border-radius: 14px !important;
        padding: 4px !important;
        gap: 4px !important;
        border: none !important;
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
        background-color: rgba(255, 255, 255, 0.5) !important;
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
        <div class="ios-badge"> iOS Studio Edition • Automated 9:16 Pipeline</div>
        <h1 style="margin: 0; font-size: 27px; font-weight: 700; letter-spacing: -0.02em;">⚡ Why It Works — Short-Form Video Studio</h1>
        <p style="margin: 6px 0 0 0; color: #AEAEB2; font-size: 14.5px; line-height: 1.45;">
            สตูดิโอสร้างวิดีโอเปรียบเทียบ A vs B อัตโนมัติ: AI Deep Research, เสียง Neural เหมือนคนจริง, Dynamic Highlight & ตัวชี้, แคปชั่นไวรัล และระบบ Auto-Pilot ผลิตคลิป 24 ชั่วโมง
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar: Network & Sharing Info
with st.sidebar:
    st.header("🌐 การเชื่อมต่อ & การใช้งาน")
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

            **สำหรับคนอื่นในวง Wi-Fi เดียวกัน:**  
            `http://{local_ip}:8501`
            """
        )
        st.info(
            "💡 **แชร์ข้ามเน็ตฟรี:** `npx localtunnel --port 8501`"
        )
    st.divider()
    # Auto-Pilot Status Widget in Sidebar
    auto_cfg = load_autopilot_config()
    st.markdown("### ⏰ สถานะ Auto-Pilot 24 ชม.")
    if auto_cfg.get("enabled"):
        next_ts = auto_cfg.get("next_run_timestamp", 0)
        remaining_m = max(0, int((next_ts - time.time()) / 60)) if next_ts > 0 else 0
        rem_str = f"ในอีก {remaining_m // 60} ชม. {remaining_m % 60} นาที" if remaining_m >= 60 else f"ในอีก {remaining_m} นาที"
        st.success(f"🟢 **ทำงานอยู่** (ทุก {auto_cfg.get('interval_hours')} ชม.)\n\n⏱️ คลิปถัดไป: {rem_str}")
    else:
        st.info("⚪ **ปิดอยู่** (ตั้งเวลาที่แท็บ 5 ได้ตลอดเวลา)")

    st.divider()
    st.markdown("### 🏢 โปรไฟล์เพจ & ลายน้ำกันก๊อป")
    if "channel_profile" not in st.session_state:
        st.session_state.channel_profile = load_channel_profile()

    prof = st.session_state.channel_profile
    with st.expander("⚙️ ตั้งค่าลายน้ำ & ลิงก์ Affiliate ประจำเพจ", expanded=False):
        p_name = st.text_input("ชื่อเพจ / ช่อง:", value=prof.get("channel_name", "Why It Works"))
        p_wm = st.text_input("ข้อความลายน้ำ:", value=prof.get("watermark_text", "@WhyItWorks"))
        p_opac = st.slider("ความชัดลายน้ำ (Opacity):", min_value=0.2, max_value=1.0, value=float(prof.get("watermark_opacity", 0.75)), step=0.05)
        p_outro = st.text_area("บทส่งท้ายประจำเพจ (Default Outro CTA):", value=prof.get("default_outro_cta", "ถ้าอยากได้ความรู้เปรียบเทียบสนุกๆ แบบนี้ อย่าลืมกดติดตามเพจ Why It Works ไว้นะครับ!"), height=70)
        p_aff_a = st.text_input("🔗 ลิงก์ Affiliate เริ่มต้น A (Default Aff A):", value=prof.get("default_affiliate_a", "https://shopee.co.th"))
        p_aff_b = st.text_input("🔗 ลิงก์ Affiliate เริ่มต้น B (Default Aff B):", value=prof.get("default_affiliate_b", "https://shopee.co.th"))
        p_logo = st.file_uploader("โลโก้เพจ (PNG พื้นใส):", type=["png"], key="side_channel_logo")

        if st.button("💾 บันทึกโปรไฟล์เพจ", use_container_width=True):
            prof["channel_name"] = p_name
            prof["watermark_text"] = p_wm
            prof["watermark_opacity"] = p_opac
            prof["default_outro_cta"] = p_outro
            prof["default_affiliate_a"] = p_aff_a
            prof["default_affiliate_b"] = p_aff_b
            if p_logo:
                save_logo_p = ASSETS_DIR / "images" / "channel_logo.png"
                with open(save_logo_p, "wb") as f:
                    f.write(p_logo.getbuffer())
                prof["logo_path"] = str(save_logo_p)
            save_channel_profile(prof)
            st.session_state.channel_profile = prof
            st.toast("✅ บันทึกโปรไฟล์เพจและลิงก์ Affiliate เรียบร้อยแล้ว!")

    st.divider()
    st.markdown("### 📚 คลังประวัติคลิปที่สร้าง")
    history_items = load_history()
    with st.expander(f"🎬 ประวัติคลิปย้อนหลัง ({len(history_items)} คลิป)", expanded=False):
        if not history_items:
            st.caption("ยังไม่มีประวัติการสร้างคลิปในระบบ")
        else:
            for item in history_items[:8]:
                st.markdown(f"**📌 {item.get('topic', 'ไม่มีหัวข้อ')}**")
                st.caption(f"⏱️ {item.get('date_str', '')} | {item.get('duration_seconds', 0)} วินาที")
                v_p = item.get("video_path")
                if v_p and Path(v_p).exists():
                    with open(v_p, "rb") as vf:
                        st.download_button(
                            "⬇️ โหลดวิดีโอ MP4",
                            data=vf,
                            file_name=Path(v_p).name,
                            mime="video/mp4",
                            key=f"dl_hist_{item.get('id')}",
                            use_container_width=True,
                        )
                st.divider()

    st.divider()
    st.markdown("### 🛠️ เครื่องมือในระบบ")
    st.caption("• AI Model: Google Gemini (Deep Research)\n• Voice: Microsoft Edge Neural Thai / Google Cloud\n• Audio: Mixed with Lo-Fi BGM & Pop SFX\n• Video: 1080x1920 30FPS H.264")

# Initialize Session State
if "script_data" not in st.session_state:
    st.session_state.script_data = {
        "topic": "กาแฟดริป VS กาแฟแคปซูล",
        "name_a": "กาแฟดริป",
        "name_b": "กาแฟแคปซูล",
        "mode": "multi_round",
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
    # Initialize initial segments list
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

# Tabs Navigation
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. 🔍 ป้อนข้อมูล & ค้นหาเจาะลึก",
    "2. 📝 ตรวจบท & สั่งรีไรท์",
    "3. 🎨 ตั้งค่าเสียง, BGM & ภาพ",
    "4. 🎬 เรนเดอร์ & พรีวิวคลิป",
    "5. ⏰ Auto-Pilot ผลิตอัตโนมัติ 24 ชม.",
    "6. 🚀 ออโต้โพสต์ & Google Drive",
])

# -------------------------------------------------------------
# TAB 1: INPUT & DEEP RESEARCH
# -------------------------------------------------------------
with tab1:
    # Viral Idea Helper Banner
    num_fw = len(FRAMEWORK_PRESETS)
    st.markdown(
        f"""
        <div style="background: rgba(50, 205, 50, 0.08); border: 1px solid rgba(50, 205, 50, 0.3); border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="font-weight: 700; font-size: 16px; color: #1F1F1F; margin-bottom: 4px;">💡 คิดไม่ออก? สุ่มหัวข้อไวรัลยอดฮิตในคลิกเดียว (คัดสรร {num_fw} กรอบเนื้อหา & 10 หมวดหมู่)</div>
            <div style="font-size: 13px; color: #555;">ดึงหัวข้อคู่เปรียบเทียบและการจับคู่เคมีลงตัว พร้อมสเปก กลุ่มเป้าหมาย และกรอบความคิดไวรัลมาเติมให้ทันที</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_cat, col_fw_filter, col_rnd = st.columns([2, 3, 2])
    with col_cat:
        cat_options = ["ทั้งหมด (สุ่มทุกหมวด)"] + CATEGORIES
        selected_cat = st.selectbox(
            "📂 หมวดหมู่สินค้า",
            cat_options,
            index=0,
            label_visibility="collapsed",
        )
    with col_fw_filter:
        fw_filter_options = [("all", f"🎯 สุ่มทุกแนวทาง ({num_fw} Frameworks)")] + [
            (k, FRAMEWORK_PRESETS[k]["name"]) for k in FRAMEWORK_PRESETS
        ]
        selected_fw_filter = st.selectbox(
            "🎯 แนวทางเนื้อหา",
            options=[x[0] for x in fw_filter_options],
            format_func=lambda x: dict(fw_filter_options).get(x, x),
            index=0,
            label_visibility="collapsed",
        )
    with col_rnd:
        if st.button("🎲 สุ่มหัวข้อไวรัลทันที", use_container_width=True):
            template = get_random_idea(category=selected_cat, framework=selected_fw_filter)
            st.session_state.input_topic = template["topic"]
            st.session_state.input_name_a = template["name_a"]
            st.session_state.input_name_b = template["name_b"]
            st.session_state.input_details_a = template.get("details_a", "")
            st.session_state.input_details_b = template.get("details_b", "")
            st.session_state.input_target = template.get("target_audience", "")
            st.session_state.input_angles = template.get("key_angles", "")
            st.session_state.input_aff_a = template.get("affiliate_link_a", "")
            st.session_state.input_aff_b = template.get("affiliate_link_b", "")
            if "framework" in template:
                st.session_state.input_framework = template["framework"]
            st.session_state.script_version += 1
            st.toast(f"สุ่มได้หัวข้อ: {template['topic']} สำเร็จ!")
            st.rerun()

    st.divider()
    st.subheader("กำหนดหัวข้อและบริบทเพื่อให้ AI วิเคราะห์เจาะลึก")
    st.caption("ยิ่งใส่รายละเอียดเยอะ AI จะยิ่งค้นหาและเปรียบเทียบจุดเด่นจุดด้อยได้ลึกซึ้งและไม่ซ้ำซาก")

    col1, col2 = st.columns(2)
    with col1:
        in_topic = st.text_input("📌 หัวข้อเปรียบเทียบ (Topic)", key="input_topic")
        in_name_a = st.text_input("📦 ชื่อสินค้า / สิ่งที่เปรียบเทียบ A", key="input_name_a")
        in_details_a = st.text_area("📝 ข้อมูล/สเปก/จุดเด่นของ A (มีหรือไม่ก็ได้)", key="input_details_a", placeholder="เช่น เมล็ดกาแฟคั่วบด สุนทรียภาพ กลิ่นหอม คุมอุณหภูมิเอง...", height=85)
    with col2:
        in_target = st.text_input("🎯 กลุ่มเป้าหมายคนดู", key="input_target", placeholder="เช่น วัยทำงาน, นักเรียนงบน้อย, สายกาแฟจริงจัง, คนรักสุขภาพ...")
        in_name_b = st.text_input("📦 ชื่อสินค้า / สิ่งที่เปรียบเทียบ B", key="input_name_b")
        in_details_b = st.text_area("📝 ข้อมูล/สเปก/จุดเด่นของ B (มีหรือไม่ก็ได้)", key="input_details_b", placeholder="เช่น ชงใน 30 วินาที ได้มาตรฐาน รวดเร็ว ไม่เลอะเทอะ เครื่องกะทัดรัด...", height=85)

    st.markdown("#### 🔗 ลิงก์ Affiliate สำหรับให้ AI วางในคอมเมนต์ปักหมุด")
    col_aff1, col_aff2 = st.columns(2)
    with col_aff1:
        aff_a = st.text_input("พิกัด Affiliate สินค้า A", key="input_aff_a", placeholder="https://shopee.co.th/link_a")
    with col_aff2:
        aff_b = st.text_input("พิกัด Affiliate สินค้า B", key="input_aff_b", placeholder="https://shopee.co.th/link_b")

    in_angles = st.text_input("💡 มุมมองที่ต้องการเน้นเปรียบเทียบเป็นพิเศษ", key="input_angles", placeholder="เช่น ความคุ้มค่าในระยะยาว, ความยากง่ายในการใช้งาน, ความทนทาน...")

    st.markdown("#### 🎯 รูปแบบวิดีโอ & กรอบมุมมองไวรัล (Framing & Mode)")
    col_mode, col_fw = st.columns([1, 1], gap="medium")
    with col_mode:
        duration_keys = list(DURATION_MODES.keys())
        def_idx = duration_keys.index("deep_3round") if "deep_3round" in duration_keys else 0
        selected_mode = st.selectbox(
            "⏱️ รูปแบบความยาว & ความลึกเนื้อหา:",
            options=duration_keys,
            index=def_idx,
            format_func=lambda k: DURATION_MODES[k]["name"],
            help="เลือกระดับความยาวและจำนวนยกตามความเหมาะสมของข้อมูลที่หาได้",
        )
        st.caption(f"💡 {DURATION_MODES[selected_mode]['desc']}")
    with col_fw:
        fw_keys = list(FRAMEWORK_PRESETS.keys())
        cur_fw = st.session_state.get("input_framework", "persona")
        cur_idx = fw_keys.index(cur_fw) if cur_fw in fw_keys else 0
        selected_fw = st.selectbox(
            "🎯 กรอบมุมมองการจับคู่ (Viral Framework):",
            options=fw_keys,
            index=cur_idx,
            format_func=lambda k: FRAMEWORK_PRESETS[k]["name"],
            help="เลือกแนวทางที่จะให้ AI เน้น เพื่อสร้างเนื้อหาให้เข้ากับจิตวิทยาคนดูบน Reels/TikTok/Shorts",
        )
        st.session_state.input_framework = selected_fw
        st.info(f"💡 **แนวทาง:** {FRAMEWORK_PRESETS[selected_fw]['desc']}")

    auto_fetch_enabled = st.checkbox("📸 ค้นหา/สร้างรูปภาพสินค้า A & B อัตโนมัติ (ไม่ต้องเสียเวลาหาเซฟรูปเอง)", value=True)

    c_btn1, c_btn2 = st.columns([1, 1], gap="medium")
    with c_btn1:
        if st.button("🚀 สั่ง Gemini ร่างบท (เข้าสู่ห้องตรวจบท)", type="secondary", use_container_width=True):
            with st.spinner("🤖 Gemini กำลังทำ Deep Research วิเคราะห์สเปก จุดแข็ง จุดด้อย และร่างบทตาม Framework..."):
                try:
                    gen = AIScriptGenerator()
                    new_data = gen.generate_script(
                        topic=in_topic,
                        name_a=in_name_a,
                        name_b=in_name_b,
                        details_a=in_details_a,
                        details_b=in_details_b,
                        target_audience=in_target,
                        key_angles=in_angles,
                        affiliate_link_a=aff_a,
                        affiliate_link_b=aff_b,
                        script_mode=selected_mode,
                        channel_outro_cta=st.session_state.channel_profile.get("default_outro_cta", ""),
                        framework=selected_fw,
                    )
                    st.session_state.script_data = new_data
                    st.session_state.script_version += 1
                    st.success("✅ ทำการวิเคราะห์และสร้างบทเรียบร้อยแล้ว! คลิกไปที่แท็บ '2. ตรวจบท & สั่งรีไรท์' ได้เลยครับ")
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการเรียก AI: {e}")

    with c_btn2:
        if st.button("⚡ 1-Click Viral Auto-Pilot (คลิกเดียวจบครบวงจร)", type="primary", use_container_width=True):
            status_box = st.status("⚡ กำลังรันโหมด Auto-Pilot สร้างคลิปครบวงจร...", expanded=True)
            with status_box:
                try:
                    # 1. AI Research & Script
                    st.write("🤖 1/4: Gemini กำลังทำ Deep Research & เขียนบทตาม Framework...")
                    gen = AIScriptGenerator()
                    new_data = gen.generate_script(
                        topic=in_topic,
                        name_a=in_name_a,
                        name_b=in_name_b,
                        details_a=in_details_a,
                        details_b=in_details_b,
                        target_audience=in_target,
                        key_angles=in_angles,
                        affiliate_link_a=aff_a,
                        affiliate_link_b=aff_b,
                        script_mode=selected_mode,
                        channel_outro_cta=st.session_state.channel_profile.get("default_outro_cta", ""),
                        framework=selected_fw,
                    )
                    st.session_state.script_data = new_data
                    st.session_state.script_version += 1

                    # 2. Auto-fetch or generate images
                    st.write(f"📸 2/4: กำลังค้นหารูปภาพอัตโนมัติสำหรับ '{in_name_a}' และ '{in_name_b}'...")
                    t_now = int(time.time())
                    img_a_path = ASSETS_DIR / "images" / f"auto_a_{t_now}.png"
                    img_b_path = ASSETS_DIR / "images" / f"auto_b_{t_now}.png"
                    auto_fetch_or_create_image(in_name_a, img_a_path, is_item_b=False, allow_web_search=auto_fetch_enabled)
                    auto_fetch_or_create_image(in_name_b, img_b_path, is_item_b=True, allow_web_search=auto_fetch_enabled)

                    # 3. Synthesize Voice
                    st.write("🎙️ 3/4: สังเคราะห์เสียงพากย์ Edge Neural + มิกซ์ Lo-Fi BGM & SFX...")
                    tts = TTSEngine(voice_key="edge_niwat", speech_rate="+10%", speech_pitch="+2Hz")
                    output_mp4 = OUTPUT_DIR / f"shorts_autopilot_{t_now}.mp4"
                    master_audio_path = output_mp4.parent / f"{output_mp4.stem}_audio.mp3"
                    timeline, audio_file, total_duration = tts.build_timeline(
                        script_data=st.session_state.script_data,
                        output_master_audio=master_audio_path,
                        include_bgm=True,
                        bgm_volume=0.12,
                        include_sfx=True,
                    )

                    # 4. Render Video
                    st.write(f"🎬 4/4: กำลังเรนเดอร์วิดีโอ 1080x1920 (ความยาว {total_duration:.1f} วินาที)...")
                    builder = VideoBuilder(
                        bg_color=hex_to_rgb("#F5F2EB"),
                        highlight_color=hex_to_rgb("#32CD32"),
                        animation_style="pointer_and_border",
                    )
                    prof = st.session_state.channel_profile
                    wm_text = prof.get("watermark_text", "@WhyItWorks")
                    wm_opac = float(prof.get("watermark_opacity", 0.75))
                    saved_logo = prof.get("logo_path", "")
                    wm_logo = Path(saved_logo) if saved_logo and Path(saved_logo).exists() else None

                    final_video = builder.build_video(
                        image_a_path=img_a_path,
                        image_b_path=img_b_path,
                        character_path=IMAGES_DIR / "character_host.png",
                        topic=new_data.get("topic"),
                        name_a=new_data.get("name_a"),
                        name_b=new_data.get("name_b"),
                        timeline=timeline,
                        master_audio_path=audio_file,
                        output_video_path=output_mp4,
                        watermark_logo_path=wm_logo,
                        watermark_text=wm_text,
                        watermark_opacity=wm_opac,
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
                    status_box.update(label=f"🎉 Auto-Pilot สำเร็จ! สร้างคลิปเสร็จสมบูรณ์ใน {total_duration:.1f} วินาที", state="complete")
                    st.success("✅ คลิปวิดีโอถูกสร้างเรียบร้อยแล้ว! เลื่อนไปดูหรือกดที่แท็บ '4. เรนเดอร์ & พรีวิวคลิป' ได้เลยครับ")
                except Exception as e:
                    status_box.update(label=f"เกิดข้อผิดพลาด: {e}", state="error")
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# -------------------------------------------------------------
# TAB 2: SCRIPT STUDIO & REWRITER
# -------------------------------------------------------------
with tab2:
    st.subheader("📝 Script Review & Rewrite Studio")
    st.caption("อ่านบทที่ AI คิดมา ตรวจสอบความถูกต้อง สั่ง AI รีไรท์เฉพาะจุด หรือแก้คำด้วยตัวเองได้อิสระ")

    # Framework badge
    active_fw = st.session_state.script_data.get("framework", st.session_state.get("input_framework", "persona"))
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

    # Research Factsheet
    summary_text = st.session_state.script_data.get("research_summary", "")
    if summary_text:
        with st.expander("📊 สรุปข้อมูลเจาะลึกจาก AI (Research Fact Sheet)", expanded=True):
            st.info(summary_text)

    col_script, col_rewrite = st.columns([3, 2], gap="large")

    is_multi = (
        st.session_state.script_data.get("mode") in DURATION_MODES
        or st.session_state.script_data.get("mode") == "multi_round"
        or "round_1_a" in st.session_state.script_data
    )

    v = st.session_state.get("script_version", 1)

    with col_script:
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
            s_hook = st.text_area("🎯 Hook (เปิดประเด็นชวนสงสัย)", value=st.session_state.script_data.get("hook", ""), height=65, key=f"inp_hook_v{v}")

            round_data = {}
            for r in range(1, num_rounds + 1):
                r_title_key = f"round_{r}_title"
                r_title_val = st.session_state.script_data.get(r_title_key, f"มิติที่ {r}")
                st.markdown(f"##### 🥊 ยกที่ {r}: {r_title_val}")
                col_ra, col_rb = st.columns(2)
                with col_ra:
                    s_ra = st.text_area(f"🟢 A: {st.session_state.script_data.get('name_a', 'A')}", value=st.session_state.script_data.get(f"round_{r}_a", ""), height=75, key=f"inp_r{r}_a_v{v}")
                with col_rb:
                    s_rb = st.text_area(f"🔵 B: {st.session_state.script_data.get('name_b', 'B')}", value=st.session_state.script_data.get(f"round_{r}_b", ""), height=75, key=f"inp_r{r}_b_v{v}")
                round_data[r] = {
                    "title": r_title_val,
                    "a": s_ra,
                    "b": s_rb,
                }

            s_conclusion = st.text_area("🏁 สรุปฟันธง + Affiliate CTA ปักหมุด", value=st.session_state.script_data.get("conclusion", ""), height=75, key=f"inp_conc_v{v}")
            if st.button("🔄 ใส่บทส่งท้ายประจำเพจ", key=f"btn_outro_multi_v{v}", help="นำประโยคปิดท้ายที่ตั้งไว้ในโปรไฟล์เพจมาต่อท้ายข้อความสรุปทันที"):
                cur_outro = st.session_state.channel_profile.get("default_outro_cta", "")
                if cur_outro and cur_outro not in st.session_state.script_data.get("conclusion", ""):
                    st.session_state.script_data["conclusion"] = (st.session_state.script_data.get("conclusion", "").strip() + " " + cur_outro).strip()
                    st.session_state.script_version += 1
                    st.rerun()
            s_comment = st.text_area("📌 พิกัด Affiliate ปักหมุดคอมเมนต์แรก", value=st.session_state.script_data.get("affiliate_comment", ""), height=100, key=f"inp_aff_v{v}")

            # Sync and package
            st.session_state.script_data["hook"] = s_hook
            st.session_state.script_data["num_rounds"] = num_rounds
            for r, d in round_data.items():
                st.session_state.script_data[f"round_{r}_a"] = d["a"]
                st.session_state.script_data[f"round_{r}_b"] = d["b"]
            st.session_state.script_data["conclusion"] = s_conclusion
            st.session_state.script_data["affiliate_comment"] = s_comment

            # Build segments dynamically
            new_segments = [
                {"id": "hook", "text": s_hook, "highlight": "none", "round_label": "🔥 เปิดประเด็น"}
            ]
            for r in range(1, num_rounds + 1):
                r_title = round_data[r]["title"]
                if round_data[r]["a"]:
                    new_segments.append({"id": f"round_{r}_a", "text": round_data[r]["a"], "highlight": "A", "round_label": f"🥊 {r_title}"})
                if round_data[r]["b"]:
                    new_segments.append({"id": f"round_{r}_b", "text": round_data[r]["b"], "highlight": "B", "round_label": f"🥊 {r_title}"})
            new_segments.append({"id": "conclusion", "text": s_conclusion, "highlight": "none", "round_label": "🏁 สรุปฟันธง"})
            st.session_state.script_data["segments"] = new_segments
        else:
            st.markdown("#### ✍️ บทพากย์ 4 ท่อน (แก้ไขได้โดยตรง)")
            s_hook = st.text_area("🎯 ท่อนที่ 1: Hook (เปิดประเด็นชวนสงสัย)", value=st.session_state.script_data.get("hook", ""), height=70, key=f"inp_hook_v{v}")
            s_item_a = st.text_area(f"🟢 ท่อนที่ 2: จุดเด่น {st.session_state.script_data.get('name_a', 'Item A')}", value=st.session_state.script_data.get("item_a", ""), height=90, key=f"inp_item_a_v{v}")
            s_item_b = st.text_area(f"🔵 ท่อนที่ 3: จุดเด่น {st.session_state.script_data.get('name_b', 'Item B')}", value=st.session_state.script_data.get("item_b", ""), height=90, key=f"inp_item_b_v{v}")
            s_conclusion = st.text_area("🏁 ท่อนที่ 4: สรุปฟันธง + Affiliate CTA", value=st.session_state.script_data.get("conclusion", ""), height=90, key=f"inp_conc_v{v}")
            s_comment = st.text_area("📌 ข้อความสำหรับปักหมุดคอมเมนต์แรก", value=st.session_state.script_data.get("affiliate_comment", ""), height=120, key=f"inp_aff_v{v}")

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

    with col_rewrite:
        st.markdown("#### 🔄 สั่ง AI ปรับแก้ / รีไรท์ใหม่")
        st.caption("หากยังไม่ถูกใจ สั่งให้ AI ปรับสไตล์คำได้ทันที")
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
            "คำสั่งปรับแก้เพิ่มเติม (เช่น 'ขอยก 2 ให้เห็นความเร็วชัดขึ้น', 'ย่อให้กระชับขึ้น'):",
            placeholder="เช่น ขอให้เน้นประเด็นเรื่องราคาให้ชัดเจนขึ้น และใช้คำสแลงวัยรุ่น...",
            height=110,
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
                    st.success("รีไรท์สำเร็จแล้ว!")
                    st.rerun()
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

# -------------------------------------------------------------
# TAB 3: VOICE, BGM, SFX & VISUALS
# -------------------------------------------------------------
with tab3:
    st.subheader("🎨 ปรับแต่งเสียงพากย์, เพลงประกอบ และงานภาพ")

    c_voice, c_visual = st.columns(2, gap="large")

    with c_voice:
        st.markdown("#### 🎙️ การตั้งค่าเสียงพากย์ (Voice Engine)")
        voice_choice = st.selectbox(
            "เลือกผู้บรรยายเสียงพากย์:",
            options=["edge_niwat", "edge_premwadee", "gcloud_neural", "gtts_thai"],
            format_func=lambda x: TTSEngine.VOICE_PRESETS[x]["desc"],
            index=0,
            help="เสียง Edge Neural ของ Microsoft ให้เสียงที่เป็นธรรมชาติที่สุด มีจังหวะหายใจและน้ำหนักคำเหมือนคนพูดจริงๆ ฟรี 100%",
        )

        emotion_keys = list(TTSEngine.EMOTION_PRESETS.keys())
        emotion_choice = st.selectbox(
            "🎭 อารมณ์และจังหวะเสียงพากย์ (Voice Mood & Pace):",
            options=emotion_keys,
            format_func=lambda k: TTSEngine.EMOTION_PRESETS[k]["name"],
            index=0,
            help="ปรับโทนเสียง อารมณ์ และจังหวะเว้นวรรคให้เหมาะกับคลิปไวรัล",
        )
        st.caption(f"💡 {TTSEngine.EMOTION_PRESETS[emotion_choice]['desc']}")

        preset_rate = TTSEngine.EMOTION_PRESETS[emotion_choice]["rate"]
        preset_pitch = TTSEngine.EMOTION_PRESETS[emotion_choice]["pitch"]

        rate_options = ["-10%", "-5%", "+0%", "+5%", "+10%", "+15%", "+20%"]
        pitch_options = ["-5Hz", "-2Hz", "+0Hz", "+1Hz", "+2Hz", "+5Hz"]

        def_rate_idx = rate_options.index(preset_rate) if preset_rate in rate_options else 2
        def_pitch_idx = pitch_options.index(preset_pitch) if preset_pitch in pitch_options else 2

        c_rate, c_pitch = st.columns(2)
        with c_rate:
            voice_rate = st.select_slider(
                "ความเร็วเสียง (Rate):",
                options=rate_options,
                value=rate_options[def_rate_idx],
                key=f"slider_rate_{emotion_choice}",
            )
        with c_pitch:
            voice_pitch = st.select_slider(
                "ระดับโทนเสียง (Pitch):",
                options=pitch_options,
                value=pitch_options[def_pitch_idx],
                key=f"slider_pitch_{emotion_choice}",
            )

        st.markdown("#### 🎵 เสียงประกอบ (BGM & SFX)")
        enable_bgm = st.toggle("เปิดเพลงคลอเบาๆ ด้านหลัง (Lo-Fi BGM)", value=True)
        bgm_vol = st.slider("ระดับความดัง BGM:", min_value=0.05, max_value=0.30, value=0.12, step=0.01) if enable_bgm else 0.0
        enable_sfx = st.toggle("เปิดเสียง Effect (Pop / Whoosh) ตอนสลับกรอบชี้", value=True)

    with c_visual:
        st.markdown("#### 🖼️ สีและภาพพื้นหลัง (Background)")
        bg_mode = st.radio(
            "เลือกรูปแบบพื้นหลัง:",
            options=["color", "custom_image"],
            format_func=lambda x: "🎨 สีมินิมอล (Solid Cream / Custom Color)" if x == "color" else "📸 อัปโหลดภาพพื้นหลังเอง (Custom Image 9:16)",
            index=0,
            horizontal=True,
        )

        bg_color = "#F5F2EB"
        up_bg = None

        if bg_mode == "color":
            c_bg1, c_bg2 = st.columns(2)
            with c_bg1:
                bg_color = st.color_picker("สีพื้นหลัง (Background)", "#F5F2EB")
            with c_bg2:
                highlight_color = st.color_picker("สีกรอบไฟไฮไลต์ (Active Lime)", "#32CD32")
        else:
            c_bg1, c_bg2 = st.columns(2)
            with c_bg1:
                up_bg = st.file_uploader("อัปโหลดภาพพื้นหลัง 9:16 (PNG/JPG)", type=["png", "jpg", "jpeg"], key="uploader_bg")
            with c_bg2:
                highlight_color = st.color_picker("สีกรอบไฟไฮไลต์ (Active Lime)", "#32CD32")

        st.markdown("#### 🛡️ ลายน้ำป้องกันการก๊อปปี้คลิป (Anti-Theft Watermark)")
        enable_watermark = st.toggle("เปิดใช้งานลายน้ำเพจ (ย้ายตำแหน่งปลอดภัยตามยกอัตโนมัติ ไม่ทับจอ)", value=True)

        st.markdown("#### 🎯 รูปแบบ Animation การชี้")
        anim_style = st.selectbox(
            "เลือกเอฟเฟกต์ตอนพูดถึงไอเทม:",
            options=["pointer_and_border", "border_only"],
            format_func=lambda x: "ตัวชี้ลอยสลับไปมา + กรอบไฟนีออน (แนะนำ)" if x == "pointer_and_border" else "กรอบไฟนีออนอย่างเดียว",
        )

        st.markdown("#### 📤 รูปภาพสินค้า A & B")
        col_up_a, col_up_b = st.columns(2)
        with col_up_a:
            up_a = st.file_uploader("รูปสินค้า A (1:1 สี่เหลี่ยมจัตุรัส)", type=["png", "jpg", "jpeg"], key="uploader_a")
        with col_up_b:
            up_b = st.file_uploader("รูปสินค้า B (1:1 สี่เหลี่ยมจัตุรัส)", type=["png", "jpg", "jpeg"], key="uploader_b")

        st.markdown("#### 🧍‍♂️ ตัวละครผู้บรรยาย (Mascot Avatar & Animation)")
        char_mode = st.radio(
            "เลือกรูปแบบตัวละครผู้บรรยาย:",
            options=["builtin", "single_upload", "multi_pose"],
            format_func=lambda x: {
                "builtin": "✨ มาสคอตระบบ (ครบ 4 ท่า: จับคางคิด, ชี้ A, ชี้ B, สรุป + ขยับปากพูดอัตโนมัติ)",
                "single_upload": "🖼️ อัปโหลดรูปเดียว (ระบบสลับชี้ซ้าย-ขวา & ขยับตัวพูดให้อัตโนมัติ)",
                "multi_pose": "🎨 อัปโหลดแยก 4 ท่าทาง (คิดตาม, ชี้ A, ชี้ B, สรุปฟันธง)",
            }[x],
            index=0,
            help="ระบบจะเปลี่ยนท่าทางและขยับปากพูดให้ตรงกับจังหวะเสียงพากย์ของแต่ละยกโดยอัตโนมัติ",
        )

        up_char = None
        up_think = None
        up_pt_a = None
        up_pt_b = None
        up_neutral = None

        if char_mode == "single_upload":
            up_char = st.file_uploader("อัปโหลดรูปตัวละคร PNG พื้นใส (รูปเดียวใช้ได้ทั้งคลิป):", type=["png"], key="uploader_char_single")
            st.caption("💡 แนะนำ: หันหน้าตรงหรือชี้ไปทางซ้าย ระบบจะ Flip กลับด้านเวลาชี้สินค้า B ให้เองอัตโนมัติ พร้อมอนิเมชั่นขยับตัวตามจังหวะพูด!")
        elif char_mode == "multi_pose":
            st.caption("💡 อัปโหลดภาพ PNG พื้นใสแยกตามแต่ละจังหวะอารมณ์:")
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                up_think = st.file_uploader("1. ท่าจับคางคิด (Hook / ช่วงเปิด):", type=["png"], key="up_pose_think")
                up_pt_a = st.file_uploader("2. ท่ายกมือชี้ช่อง A (ทางซ้าย):", type=["png"], key="up_pose_a")
            with col_p2:
                up_pt_b = st.file_uploader("3. ท่ายกมือชี้ช่อง B (ทางขวา):", type=["png"], key="up_pose_b")
                up_neutral = st.file_uploader("4. ท่ายิ้มมั่นใจ / สรุปคลิป (Conclusion):", type=["png"], key="up_pose_neutral")

# -------------------------------------------------------------
# TAB 4: RENDER & PREVIEW
# -------------------------------------------------------------
with tab4:
    st.subheader("🎬 สร้างวิดีโอ 1080x1920 และรับชมตัวอย่าง")

    st.markdown(
        f"""
        **สรุปข้อมูลที่จะสร้าง:**  
        • **หัวข้อ:** {st.session_state.script_data.get('topic')}  
        • **สินค้า A:** {st.session_state.script_data.get('name_a')}  
        • **สินค้า B:** {st.session_state.script_data.get('name_b')}  
        • **เสียงพากย์:** {TTSEngine.VOICE_PRESETS[voice_choice]['desc']}  
        • **BGM / SFX:** {'เปิดใช้งาน' if enable_bgm else 'ปิด'} / {'เปิดใช้งาน' if enable_sfx else 'ปิด'}  
        • **พื้นหลัง:** {'ภาพอัปโหลดเอง' if bg_mode == 'custom_image' and up_bg else 'สีมินิมอล'}  
        • **ลายน้ำกันก๊อป:** {'เปิดใช้งาน (ย้ายจุดตามยก)' if enable_watermark else 'ปิด'}  
        • **ตัวละครผู้บรรยาย:** {'มาสคอตระบบ (4 ท่า + ขยับปาก)' if char_mode == 'builtin' else ('รูปเดี่ยวออโต้ฟลิป' if char_mode == 'single_upload' else 'แยก 4 ท่า')}
        """
    )

    if st.button("🎥 สั่งเรนเดอร์คลิปวิดีโอ 1080x1920 ทันที", type="primary", use_container_width=True):
        # Determine image paths
        path_a = IMAGES_DIR / "item_a_drip.png"
        path_b = IMAGES_DIR / "item_b_capsule.png"
        path_char = IMAGES_DIR / "character_host.png"
        path_custom_bg = None
        char_poses_dict = None

        if bg_mode == "custom_image" and up_bg:
            path_custom_bg = ASSETS_DIR / "images" / f"up_bg_{int(time.time())}.png"
            with open(path_custom_bg, "wb") as f:
                f.write(up_bg.getbuffer())

        t_now = int(time.time())
        if up_a:
            path_a = ASSETS_DIR / "images" / f"up_a_{t_now}.png"
            with open(path_a, "wb") as f:
                f.write(up_a.getbuffer())
        else:
            name_a_val = st.session_state.script_data.get("name_a", "A")
            path_a = auto_fetch_or_create_image(name_a_val, ASSETS_DIR / "images" / f"auto_a_{t_now}.png", is_item_b=False)

        if up_b:
            path_b = ASSETS_DIR / "images" / f"up_b_{t_now}.png"
            with open(path_b, "wb") as f:
                f.write(up_b.getbuffer())
        else:
            name_b_val = st.session_state.script_data.get("name_b", "B")
            path_b = auto_fetch_or_create_image(name_b_val, ASSETS_DIR / "images" / f"auto_b_{t_now}.png", is_item_b=True)

        if char_mode == "single_upload" and up_char:
            path_char = ASSETS_DIR / "images" / f"up_char_{int(time.time())}.png"
            with open(path_char, "wb") as f:
                f.write(up_char.getbuffer())
        elif char_mode == "multi_pose":
            char_poses_dict = {}
            t_stamp = int(time.time())
            if up_think:
                p_th = ASSETS_DIR / "images" / f"up_think_{t_stamp}.png"
                with open(p_th, "wb") as f:
                    f.write(up_think.getbuffer())
                char_poses_dict["thinking"] = p_th
            if up_pt_a:
                p_a = ASSETS_DIR / "images" / f"up_pt_a_{t_stamp}.png"
                with open(p_a, "wb") as f:
                    f.write(up_pt_a.getbuffer())
                char_poses_dict["point_a"] = p_a
            if up_pt_b:
                p_b = ASSETS_DIR / "images" / f"up_pt_b_{t_stamp}.png"
                with open(p_b, "wb") as f:
                    f.write(up_pt_b.getbuffer())
                char_poses_dict["point_b"] = p_b
            if up_neutral:
                p_ne = ASSETS_DIR / "images" / f"up_neu_{t_stamp}.png"
                with open(p_ne, "wb") as f:
                    f.write(up_neutral.getbuffer())
                char_poses_dict["neutral"] = p_ne

        # Setup watermark
        wm_logo = None
        wm_text = None
        wm_opac = 0.75

        if enable_watermark:
            prof = st.session_state.channel_profile
            wm_text = prof.get("watermark_text", "@WhyItWorks")
            wm_opac = float(prof.get("watermark_opacity", 0.75))
            saved_logo = prof.get("logo_path", "")
            if saved_logo and Path(saved_logo).exists():
                wm_logo = Path(saved_logo)

        output_mp4 = OUTPUT_DIR / f"shorts_{int(time.time())}.mp4"

        progress_box = st.status("🎬 เริ่มกระบวนการสร้างวิดีโอ...", expanded=True)
        with progress_box:
            st.write(f"🎙️ กำลังสังเคราะห์เสียงพากย์ Neural ({voice_choice}) และมิกซ์ BGM/SFX...")
            tts = TTSEngine(
                voice_key=voice_choice,
                speech_rate=voice_rate,
                speech_pitch=voice_pitch,
            )
            master_audio_path = output_mp4.parent / f"{output_mp4.stem}_audio.mp3"
            timeline, audio_file, total_duration = tts.build_timeline(
                script_data=st.session_state.script_data,
                output_master_audio=master_audio_path,
                include_bgm=enable_bgm,
                bgm_volume=bgm_vol,
                include_sfx=enable_sfx,
            )

            st.write(f"🎨 กำลังเรนเดอร์ Dynamic Animation, พื้นหลัง, ลายน้ำกันก๊อป และซับไตเติล (ความยาว {total_duration:.1f} วินาที)...")
            bg_rgb = hex_to_rgb(bg_color)
            hl_rgb = hex_to_rgb(highlight_color)
            builder = VideoBuilder(
                bg_color=bg_rgb,
                highlight_color=hl_rgb,
                animation_style=anim_style,
            )

            start_t = time.time()
            final_video = builder.build_video(
                image_a_path=path_a,
                image_b_path=path_b,
                character_path=path_char,
                topic=st.session_state.script_data.get("topic"),
                name_a=st.session_state.script_data.get("name_a"),
                name_b=st.session_state.script_data.get("name_b"),
                timeline=timeline,
                master_audio_path=audio_file,
                output_video_path=output_mp4,
                custom_bg_path=path_custom_bg,
                character_poses=char_poses_dict,
                watermark_logo_path=wm_logo,
                watermark_text=wm_text,
                watermark_opacity=wm_opac,
            )
            elapsed = time.time() - start_t
            progress_box.update(label=f"✅ เรนเดอร์วิดีโอ 1080x1920 สำเร็จสมบูรณ์ใน {elapsed:.1f} วินาที!", state="complete")
            st.session_state.rendered_video_path = str(final_video)

            # Record in content history
            c_path = output_mp4.parent / f"{output_mp4.stem}_cover.jpg"
            add_history_entry(
                topic=st.session_state.script_data.get("topic", ""),
                name_a=st.session_state.script_data.get("name_a", "A"),
                name_b=st.session_state.script_data.get("name_b", "B"),
                video_path=str(final_video),
                cover_path=str(c_path) if c_path.exists() else None,
                social_caption=st.session_state.script_data.get("social_caption", ""),
                hashtags=st.session_state.script_data.get("hashtags", ""),
                affiliate_comment=st.session_state.script_data.get("affiliate_comment", ""),
                framework=st.session_state.script_data.get("framework", "persona"),
                duration_mode=st.session_state.script_data.get("mode", "deep_3round"),
                duration_seconds=total_duration,
            )

    # Display Results if available
    if st.session_state.rendered_video_path and Path(st.session_state.rendered_video_path).exists():
        v_path = Path(st.session_state.rendered_video_path)
        cover_path = v_path.parent / f"{v_path.stem}_cover.jpg"

        st.success("🎉 คลิปวิดีโอของคุณพร้อมนำไปโพสต์แล้ว!")
        c_video, c_details = st.columns([1, 1], gap="large")

        with c_video:
            st.video(str(v_path))
            with open(v_path, "rb") as f:
                st.download_button(
                    "⬇️ ดาวน์โหลดวิดีโอ MP4 (1080x1920)",
                    data=f,
                    file_name=v_path.name,
                    mime="video/mp4",
                    use_container_width=True,
                )

        with c_details:
            if cover_path.exists():
                st.image(str(cover_path), caption="ภาพปกคลิปอัตโนมัติ (Cover Thumbnail)", use_container_width=True)
                with open(cover_path, "rb") as f:
                    st.download_button(
                        "⬇️ ดาวน์โหลดภาพปกคลิป",
                        data=f,
                        file_name=cover_path.name,
                        mime="image/jpeg",
                        use_container_width=True,
                    )

            st.markdown("#### 📱 แคปชั่น & แฮชแท็กสำหรับโพสต์ลงโซเชียล (Copy ได้ทันที):")
            social_cap = st.session_state.script_data.get("social_caption") or generate_social_caption(st.session_state.script_data)["social_caption"]
            st.code(social_cap, language="text")

            st.markdown("#### 📌 ข้อความสำหรับปักหมุดคอมเมนต์แรก (Auto-Pin Comment):")
            st.code(st.session_state.script_data.get("affiliate_comment", ""), language="text")

# -------------------------------------------------------------
# TAB 5: AUTOPILOT 24/7 AUTONOMOUS SCHEDULER
# -------------------------------------------------------------
with tab5:
    st.subheader("⏰ Auto-Pilot 24 Hours — ผลิตคลิปอัตโนมัติตามเวลา")
    st.caption("ระบบทำงานในพื้นหลังตลอด 24 ชั่วโมง สุ่มหัวข้อไวรัล ค้นภาพ สังเคราะห์เสียง Neural ตัดต่อวิดีโอ 9:16 แคปชั่น แฮชแท็ก และปักหมุด Affiliate เตรียมพร้อมนำไปโพสต์ได้ทันที")

    auto_cfg = load_autopilot_config()
    prof = st.session_state.channel_profile

    # Top Status Cards (iOS Style)
    col_st1, col_st2, col_st3 = st.columns([1, 1, 1])
    with col_st1:
        is_active = auto_cfg.get("enabled", False)
        badge_color = "#34C759" if is_active else "#8E8E93"
        badge_title = "🟢 เปิดทำงาน (Active)" if is_active else "⚪ ปิดทำงาน (Paused)"
        st.markdown(
            f"""
            <div class="ios-card" style="border-left: 5px solid {badge_color};">
                <div style="font-size: 13px; color: #8E8E93; font-weight: 600;">สถานะระบบ Auto-Pilot</div>
                <div style="font-size: 19px; font-weight: 700; color: {badge_color}; margin-top: 4px;">{badge_title}</div>
                <div style="font-size: 12px; color: #636366; margin-top: 5px;">Worker Daemon: {'🟢 ออนไลน์' if is_scheduler_alive() else '🟡 กำลังเตรียมพร้อม'}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_st2:
        next_ts = auto_cfg.get("next_run_timestamp", 0)
        if is_active and next_ts > 0:
            diff_m = max(0, int((next_ts - time.time()) / 60))
            if diff_m >= 60:
                timer_txt = f"ในอีก {diff_m // 60} ชม. {diff_m % 60} นาที"
            else:
                timer_txt = f"ในอีก {diff_m} นาที"
            scheduled_clock = time.strftime("%H:%M น.", time.localtime(next_ts))
        else:
            timer_txt = "—"
            scheduled_clock = "ยังไม่ได้เปิดใช้งาน"

        st.markdown(
            f"""
            <div class="ios-card" style="border-left: 5px solid #007AFF;">
                <div style="font-size: 13px; color: #8E8E93; font-weight: 600;">รอบการผลิตคลิปถัดไป</div>
                <div style="font-size: 19px; font-weight: 700; color: #007AFF; margin-top: 4px;">{timer_txt}</div>
                <div style="font-size: 12px; color: #636366; margin-top: 5px;">เวลาประมาณ {scheduled_clock}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_st3:
        total_gen = auto_cfg.get("total_generated", 0)
        last_topic_str = auto_cfg.get("last_topic") or "ยังไม่มีคลิป"
        st.markdown(
            f"""
            <div class="ios-card" style="border-left: 5px solid #FF9500;">
                <div style="font-size: 13px; color: #8E8E93; font-weight: 600;">ยอดผลิตสะสม</div>
                <div style="font-size: 19px; font-weight: 700; color: #FF9500; margin-top: 4px;">{total_gen} คลิป</div>
                <div style="font-size: 12px; color: #636366; margin-top: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">ล่าสุด: {last_topic_str}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("#### ⚙️ ตั้งค่าความถี่ & เงื่อนไขการผลิต (Schedule Configuration)")
    c_form1, c_form2 = st.columns(2, gap="large")

    with c_form1:
        auto_toggle = st.toggle("🚀 เปิดใช้งานระบบผลิตอัตโนมัติตามเวลา (Auto-Pilot)", value=bool(auto_cfg.get("enabled", False)))

        interval_choices = [1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 24.0]
        cur_int = float(auto_cfg.get("interval_hours", 3.0))
        int_idx = interval_choices.index(cur_int) if cur_int in interval_choices else 2
        selected_interval = st.selectbox(
            "⏱️ สร้างคลิปใหม่ทุกๆ:",
            options=interval_choices,
            index=int_idx,
            format_func=lambda h: f"ทุก {int(h) if h.is_integer() else h} ชั่วโมง ({int(24/h)} คลิปต่อวัน)",
            help="กำหนดระยะเวลาที่จะให้ระบบตื่นขึ้นมาสร้างคลิปใหม่ เช่น ทุก 3 ชั่วโมง",
        )

        all_cats = ["ทั้งหมด (สุ่มทุกหมวด)"] + CATEGORIES
        cur_cat = auto_cfg.get("target_category", "ทั้งหมด (สุ่มทุกหมวด)")
        cat_idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
        selected_cat = st.selectbox(
            "📂 หมวดหมู่สินค้าเป้าหมาย:",
            options=all_cats,
            index=cat_idx,
            help="ระบบจะสุ่มหัวข้อจากหมวดนี้ หรือเลือก 'ทั้งหมด' เพื่อให้คอนเทนต์หลากหลาย",
        )

        fw_list = ["all"] + list(FRAMEWORK_PRESETS.keys())
        cur_fw = auto_cfg.get("target_framework", "all")
        fw_idx = fw_list.index(cur_fw) if cur_fw in fw_list else 0
        selected_fw = st.selectbox(
            "🎯 กรอบแนวทาง Framework ไวรัล:",
            options=fw_list,
            index=fw_idx,
            format_func=lambda k: f"สุ่มทุกแนวทาง ({len(FRAMEWORK_PRESETS)} Frameworks)" if k == "all" else FRAMEWORK_PRESETS[k]["name"],
            help="เลือกแนวทางจิตวิทยาการเปรียบเทียบ",
        )

    with c_form2:
        dur_list = list(DURATION_MODES.keys())
        cur_dur = auto_cfg.get("target_duration_mode", "standard_3round")
        dur_idx = dur_list.index(cur_dur) if cur_dur in dur_list else 1
        selected_dur = st.selectbox(
            "⏱️ รูปแบบความยาวคลิป:",
            options=dur_list,
            index=dur_idx,
            format_func=lambda k: DURATION_MODES[k]["name"],
        )

        auto_img_fetch = st.checkbox("📸 ค้นหาและบันทึกภาพสินค้าจากเว็บฟรีอัตโนมัติ", value=bool(auto_cfg.get("auto_search_images", True)))

        st.markdown("##### 🔗 พิกัด Affiliate สำรองเริ่มต้น (Default Affiliate Links)")
        st.caption("ระบบจะนำลิงก์นี้ไปใส่ในแคปชั่นและปักหมุดคอมเมนต์แรกอัตโนมัติ สำหรับทุกคลิปที่สร้างโดยระบบออโต้")
        def_aff_a = st.text_input("ลิงก์ Affiliate สินค้า A เริ่มต้น:", value=auto_cfg.get("default_affiliate_a", prof.get("default_affiliate_a", "https://shopee.co.th")))
        def_aff_b = st.text_input("ลิงก์ Affiliate สินค้า B เริ่มต้น:", value=auto_cfg.get("default_affiliate_b", prof.get("default_affiliate_b", "https://shopee.co.th")))

    c_btn_save, c_btn_run = st.columns([1, 1], gap="medium")
    with c_btn_save:
        if st.button("💾 บันทึกการตั้งค่า Auto-Pilot", type="secondary", use_container_width=True):
            auto_cfg["enabled"] = auto_toggle
            auto_cfg["interval_hours"] = float(selected_interval)
            auto_cfg["target_category"] = selected_cat
            auto_cfg["target_framework"] = selected_fw
            auto_cfg["target_duration_mode"] = selected_dur
            auto_cfg["auto_search_images"] = auto_img_fetch
            auto_cfg["default_affiliate_a"] = def_aff_a
            auto_cfg["default_affiliate_b"] = def_aff_b
            if auto_toggle and auto_cfg.get("next_run_timestamp", 0) <= time.time():
                auto_cfg["next_run_timestamp"] = int(time.time() + float(selected_interval) * 3600)
            save_autopilot_config(auto_cfg)
            st.toast("✅ บันทึกการตั้งค่า Auto-Pilot สำเร็จแล้ว!")
            st.rerun()

    with c_btn_run:
        if st.button("⚡ ทดสอบสร้างอัตโนมัติ 1 คลิปทันที (Run 1 Clip Now)", type="primary", use_container_width=True):
            auto_cfg["interval_hours"] = float(selected_interval)
            auto_cfg["target_category"] = selected_cat
            auto_cfg["target_framework"] = selected_fw
            auto_cfg["target_duration_mode"] = selected_dur
            auto_cfg["auto_search_images"] = auto_img_fetch
            auto_cfg["default_affiliate_a"] = def_aff_a
            auto_cfg["default_affiliate_b"] = def_aff_b
            save_autopilot_config(auto_cfg)

            with st.spinner("🤖 กำลังรันกระบวนการผลิตคลิปอัตโนมัติครบวงจร (Research -> Script -> Audio -> Video 1080x1920 -> Social Caption)..."):
                ok, res_msg = run_autopilot_cycle(is_manual=True)
                if ok:
                    st.success(f"🎉 {res_msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {res_msg}")

    # Activity Feed / Logs
    st.divider()
    st.markdown("#### 📜 บันทึกกิจกรรมระบบอัตโนมัติ (Activity Feed & Logs)")
    logs = auto_cfg.get("history_log", [])
    if not logs:
        st.caption("ยังไม่มีบันทึกกิจกรรมในระบบ")
    else:
        st.text_area("Live Production Activity", value="\n".join(logs), height=180, disabled=True)

# -------------------------------------------------------------
# TAB 6: GOOGLE DRIVE SYNC & MULTI-PLATFORM AUTO-POST
# -------------------------------------------------------------
with tab6:
    st.subheader("🚀 Cloud Sync & Multi-Platform Auto-Post — ซิงก์ Google Drive & โพสต์อัตโนมัติ")
    st.caption("เชื่อมต่อระบบเข้ากับ Google Drive และเครือข่ายโซเชียลมีเดีย (Facebook Page Reels, YouTube Shorts, TikTok Webhook) เพื่อให้ระบบนำคลิปที่สร้างเสร็จไปซิงก์และโพสต์ให้อัตโนมัติ")

    gd_cfg = load_gdrive_config()
    post_cfg = load_autopost_config()

    # Part 1: Google Drive Synchronization Card
    st.markdown(
        """
        <div class="ios-card">
            <div style="font-size: 17px; font-weight: 700; color: #1C1C1E; margin-bottom: 6px;">
                ☁️ 1. ระบบซิงก์ Google Drive (Google Drive Auto-Sync)
            </div>
            <div style="font-size: 13.5px; color: #636366; line-height: 1.4;">
                นำคลิปวิดีโอ MP4, ภาพหน้าปก และแคปชั่นไปเก็บไว้ใน Google Drive ทันทีที่ผลิตเสร็จ สะดวกสำหรับเปิดดูในมือถือหรือสำรองข้อมูล
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    is_local, local_msg = is_local_gdrive_path()
    if is_local:
        st.success(f"🟢 **ตรวจพบ Google Drive for Desktop ในเครื่อง:** {local_msg}\n\nทุกคลิปที่บันทึกใน `output/` จะถูก Sync ขึ้น Google Drive บนมือถือและคลาวด์ของคุณอัตโนมัติอยู่แล้วครับ!")
    else:
        st.info("ℹ️ กำลังรันบน Cloud หรือโฟลเดอร์ภายนอก สามารถตั้งค่า Webhook ด้านล่างเพื่อให้ระบบอัปโหลดเข้า Drive ได้โดยตรง")

    c_gd1, c_gd2 = st.columns(2, gap="large")
    with c_gd1:
        gd_enable = st.toggle("เปิดระบบซิงก์ Google Drive อัตโนมัติ", value=bool(gd_cfg.get("enabled", True)))
        gd_mode_options = [("auto", "อัตโนมัติ (Auto Detect)"), ("local", "Google Drive for Desktop ในเครื่อง"), ("webhook", "Webhook / Google Apps Script (สำหรับ Cloud 24h)")]
        cur_gd_mode = gd_cfg.get("sync_mode", "auto")
        gd_mode_idx = [x[0] for x in gd_mode_options].index(cur_gd_mode) if cur_gd_mode in [x[0] for x in gd_mode_options] else 0
        gd_mode = st.selectbox(
            "เลือกรูปแบบการซิงก์:",
            options=[x[0] for x in gd_mode_options],
            index=gd_mode_idx,
            format_func=lambda k: dict(gd_mode_options).get(k, k),
        )

    with c_gd2:
        gd_webhook = st.text_input("Webhook URL (Google Apps Script / Make.com):", value=gd_cfg.get("webhook_url", ""), placeholder="https://script.google.com/macros/s/.../exec")
        gd_folder_id = st.text_input("Google Drive Folder ID (ไม่บังคับ):", value=gd_cfg.get("folder_id", ""), placeholder="เช่น 1A2b3C4d5E6f...")

    c_gdb1, c_gdb2 = st.columns(2, gap="medium")
    with c_gdb1:
        if st.button("🧪 ทดสอบการเชื่อมต่อ Google Drive", type="secondary", use_container_width=True):
            gd_cfg["enabled"] = gd_enable
            gd_cfg["sync_mode"] = gd_mode
            gd_cfg["webhook_url"] = gd_webhook
            gd_cfg["folder_id"] = gd_folder_id
            save_gdrive_config(gd_cfg)
            ok, msg = test_gdrive_connection()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")
    with c_gdb2:
        if st.button("💾 บันทึกการตั้งค่า Google Drive", type="secondary", use_container_width=True):
            gd_cfg["enabled"] = gd_enable
            gd_cfg["sync_mode"] = gd_mode
            gd_cfg["webhook_url"] = gd_webhook
            gd_cfg["folder_id"] = gd_folder_id
            save_gdrive_config(gd_cfg)
            st.toast("✅ บันทึกการตั้งค่า Google Drive สำเร็จ!")

    st.divider()

    # Part 2: Multi-Platform Auto-Post Card
    st.markdown(
        """
        <div class="ios-card">
            <div style="font-size: 17px; font-weight: 700; color: #1C1C1E; margin-bottom: 6px;">
                🚀 2. ระบบ Auto-Post โซเชียลมีเดีย (Facebook Page, YouTube Shorts, TikTok)
            </div>
            <div style="font-size: 13.5px; color: #636366; line-height: 1.4;">
                สั่งให้ระบบนำคลิปที่ตัดต่อเสร็จพร้อมแคปชั่นและแฮชแท็ก ไปเผยแพร่บนโซเชียลมีเดียทันที ทุกแพลตฟอร์มมีระบบ Fail-safe แยกอิสระ หากไม่เปิดใช้งานระบบจะเซฟคลิปเก็บไว้ตามปกติ
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Accordions for each platform
    with st.expander("🔵 Facebook Page Reels + ปักหมุด Affiliate อัตโนมัติ", expanded=False):
        fb_enable = st.toggle("เปิดใช้งานโพสต์ Facebook Reels อัตโนมัติ", value=bool(post_cfg.get("facebook_enabled", False)), key="tog_fb")
        fb_page_id = st.text_input("Facebook Page ID:", value=post_cfg.get("facebook_page_id", ""), placeholder="เช่น 108928374829102", key="inp_fb_pid")
        fb_token = st.text_input("Page Access Token (Long-lived Token):", value=post_cfg.get("facebook_access_token", ""), type="password", key="inp_fb_tok")
        fb_comm = st.checkbox("📌 ปักหมุดลิงก์ Affiliate ในคอมเมนต์แรกทันทีหลังคลิปโพสต์เสร็จ (แนะนำ)", value=bool(post_cfg.get("facebook_auto_comment", True)), key="chk_fb_comm")

        if st.button("🧪 ทดสอบการเชื่อมต่อ Facebook Page", key="btn_test_fb"):
            post_cfg["facebook_page_id"] = fb_page_id
            post_cfg["facebook_access_token"] = fb_token
            save_autopost_config(post_cfg)
            ok, msg = test_facebook_connection()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

    with st.expander("🔴 YouTube Shorts (YouTube Data API v3)", expanded=False):
        yt_enable = st.toggle("เปิดใช้งานโพสต์ YouTube Shorts อัตโนมัติ", value=bool(post_cfg.get("youtube_enabled", False)), key="tog_yt")
        yt_token = st.text_input("YouTube OAuth 2.0 Access Token:", value=post_cfg.get("youtube_access_token", ""), type="password", key="inp_yt_tok")
        yt_priv_options = [("unlisted", "Unlisted (ไม่เป็นสาธารณะ เพื่อตรวจดูก่อน)"), ("public", "Public (สาธารณะทันที)"), ("private", "Private (ส่วนตัว)")]
        cur_yt_priv = post_cfg.get("youtube_privacy_status", "unlisted")
        priv_idx = [x[0] for x in yt_priv_options].index(cur_yt_priv) if cur_yt_priv in [x[0] for x in yt_priv_options] else 0
        yt_privacy = st.selectbox("สถานะการเผยแพร่คลิป:", options=[x[0] for x in yt_priv_options], index=priv_idx, format_func=lambda k: dict(yt_priv_options).get(k, k), key="sel_yt_priv")

        if st.button("🧪 ทดสอบการเชื่อมต่อ YouTube Data API", key="btn_test_yt"):
            post_cfg["youtube_access_token"] = yt_token
            save_autopost_config(post_cfg)
            ok, msg = test_youtube_connection()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

    with st.expander("⚫ TikTok & Multi-Platform Webhook (Buffer / Make.com / Zapier)", expanded=False):
        wh_enable = st.toggle("เปิดใช้งาน Webhook ส่งคลิปไป TikTok / โซเชียลอื่นๆ", value=bool(post_cfg.get("webhook_enabled", False)), key="tog_wh")
        wh_url = st.text_input("Social Webhook URL:", value=post_cfg.get("webhook_url", ""), placeholder="https://hook.eu1.make.com/... หรือ https://api.bufferapp.com/...", key="inp_wh_url")
        wh_secret = st.text_input("Webhook Secret Header (ถ้ามี):", value=post_cfg.get("webhook_secret", ""), type="password", key="inp_wh_sec")

        if st.button("🧪 ทดสอบยิง Webhook จำลอง", key="btn_test_wh"):
            post_cfg["webhook_url"] = wh_url
            post_cfg["webhook_secret"] = wh_secret
            save_autopost_config(post_cfg)
            ok, msg = test_webhook_connection()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

    # Action buttons for social settings
    c_pbtn1, c_pbtn2 = st.columns([1, 1], gap="medium")
    with c_pbtn1:
        if st.button("💾 บันทึกการตั้งค่า Auto-Post ทั้งหมด", type="secondary", use_container_width=True):
            post_cfg["facebook_enabled"] = fb_enable
            post_cfg["facebook_page_id"] = fb_page_id
            post_cfg["facebook_access_token"] = fb_token
            post_cfg["facebook_auto_comment"] = fb_comm
            post_cfg["youtube_enabled"] = yt_enable
            post_cfg["youtube_access_token"] = yt_token
            post_cfg["youtube_privacy_status"] = yt_privacy
            post_cfg["webhook_enabled"] = wh_enable
            post_cfg["webhook_url"] = wh_url
            post_cfg["webhook_secret"] = wh_secret
            save_autopost_config(post_cfg)
            st.toast("✅ บันทึกการตั้งค่าโซเชียลทั้งหมดเรียบร้อยแล้ว!")
            st.rerun()

    with c_pbtn2:
        if st.button("🚀 ทดสอบส่งคลิปล่าสุดโพสต์ลงโซเชียลทันที (Publish Latest)", type="primary", use_container_width=True):
            # Find latest generated video
            out_videos = sorted(OUTPUT_DIR.glob("shorts_*.mp4"), key=os.path.getmtime, reverse=True)
            if not out_videos:
                st.warning("ยังไม่มีไฟล์วิดีโอในโฟลเดอร์ output/ กรุณาสร้างคลิปก่อน 1 คลิปครับ")
            else:
                latest_vid = out_videos[0]
                latest_meta = latest_vid.parent / f"{latest_vid.stem}_meta.json"
                latest_cover = latest_vid.parent / f"{latest_vid.stem}_cover.jpg"

                with st.spinner(f"🚀 กำลังส่งคลิป '{latest_vid.name}' ไปยังโซเชียลแพลตฟอร์มที่เปิดใช้งาน..."):
                    results = publish_to_all_enabled(
                        video_path=str(latest_vid),
                        cover_path=str(latest_cover) if latest_cover.exists() else None,
                        meta_path=str(latest_meta) if latest_meta.exists() else None,
                    )
                    if not results:
                        st.info("ℹ️ ยังไม่ได้เปิดใช้งานแพลตฟอร์มใดๆ (กรุณาเปิดใช้งานและกรอก Token ก่อนครับ)")
                    else:
                        for p_name, (p_ok, p_msg) in results.items():
                            if p_ok:
                                st.success(f"[{p_name.upper()}] ✅ {p_msg}")
                            else:
                                st.error(f"[{p_name.upper()}] ❌ {p_msg}")

    # Logs section
    st.divider()
    st.markdown("#### 📜 ประวัติการส่งโพสต์โซเชียล (Live Auto-Post Logs)")
    p_logs = post_cfg.get("post_log", [])
    if not p_logs:
        st.caption("ยังไม่มีประวัติการส่งโพสต์ในระบบ")
    else:
        st.text_area("Social Post Activity", value="\n".join(p_logs), height=180, disabled=True)


