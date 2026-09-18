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

from config import (
    ASSETS_DIR,
    IMAGES_DIR,
    SCRIPTS_DIR,
    OUTPUT_DIR,
    AUDIO_DIR,
    COLOR_BG_CREAM,
    COLOR_HIGHLIGHT_LIME,
)
from ai_script_generator import AIScriptGenerator
from tts_engine import TTSEngine
from video_builder import VideoBuilder
from pipeline import hex_to_rgb

# Page Configuration
st.set_page_config(
    page_title="Shorts Studio - 9:16 Comparison Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Header
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1E1E2F 0%, #2A2A40 100%); padding: 22px 28px; border-radius: 14px; margin-bottom: 24px; color: white;">
        <h1 style="margin: 0; font-size: 28px; font-weight: 700;">⚡ Automated Short-Form Video Studio (9:16)</h1>
        <p style="margin: 6px 0 0 0; color: #B0B0C0; font-size: 15px;">
            สร้างวิดีโอเปรียบเทียบ A vs B สไตล์ Reels/Shorts/TikTok ด้วย AI Deep Research, เสียง Neural เหมือนคนจริง, Dynamic Highlight & ตัวชี้ และระบบ Affiliate CTA ปักหมุด
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar: Network & Sharing Info
with st.sidebar:
    st.header("🌐 การแชร์ให้ผู้อื่นใช้งาน")
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
        "💡 **ถ้าต้องการให้คนที่อยู่นอกบ้านใช้งาน:**\n"
        "ใช้ฟรี Cloudflare Tunnel หรือ Localtunnel ได้ทันที:\n"
        "พิมพ์ใน Terminal: `npx localtunnel --port 8501`"
    )
    st.divider()
    st.markdown("### 🛠️ เครื่องมือในระบบ")
    st.caption("• AI Model: Google Gemini (Deep Research)\n• Voice: Microsoft Edge Neural Thai / Google Cloud\n• Audio: Mixed with Lo-Fi BGM & Pop SFX\n• Video: 1080x1920 30FPS H.264")

# Initialize Session State
if "script_data" not in st.session_state:
    st.session_state.script_data = {
        "topic": "กาแฟดริป VS กาแฟแคปซูล",
        "name_a": "กาแฟดริป",
        "name_b": "กาแฟแคปซูล",
        "research_summary": "เปรียบเทียบกาแฟดริปที่เน้นความสุนทรีย์ กลิ่นหอมอโรม่าชัดเจน กับกาแฟแคปซูลที่เน้นความสะดวกรวดเร็ว รสชาติมาตรฐานทุกแก้วใน 1 นาที",
        "hook": "สายกาแฟห้ามพลาด! ดริปเองกับแคปซูล แบบไหนตอบโจทย์ชีวิตคุณมากกว่ากัน?",
        "item_a": "กาแฟดริป ได้กลิ่นหอมกรุ่นแบบสโลว์ไลฟ์ ดึงรสชาติเมล็ดกาแฟแท้ๆ ออกมาได้ชัดเจน เหมาะกับสายสุนทรีย์มีเวลาละเมียดละไม",
        "item_b": "กาแฟแคปซูล ตอบโจทย์ความเร็วในชั่วโมงเร่งด่วน แค่กดปุ่มเดียวก็ได้รสชาติเข้มข้นคงที่ ได้มาตรฐานร้านหรูในสิบวินาที",
        "conclusion": "ชอบความหอมคลาสสิกเลือกดริป ชอบความง่ายทันใจเลือกแคปซูล คอมเมนต์บอกกันหน่อยนะ ส่วนพิกัดของแท้ราคาโปร แปะไว้ในคอมเมนต์แรกแล้วครับ",
        "affiliate_comment": "📍 พิกัดของแท้ราคาโปรโมชั่นพิเศษ:\n👉 กาแฟดริป: https://shopee.co.th/sample_drip\n👉 กาแฟแคปซูล: https://shopee.co.th/sample_capsule\n(ใครสนใจตัวไหน จิ้มดูพิกัดในลิงก์ได้เลยครับ)",
    }

if "rendered_video_path" not in st.session_state:
    st.session_state.rendered_video_path = None

# Tabs Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "1. 🔍 ป้อนข้อมูล & ค้นหาเจาะลึก",
    "2. 📝 ตรวจบท & สั่งรีไรท์",
    "3. 🎨 ตั้งค่าเสียง, BGM & ภาพ",
    "4. 🎬 เรนเดอร์ & พรีวิวคลิป",
])

# -------------------------------------------------------------
# TAB 1: INPUT & DEEP RESEARCH
# -------------------------------------------------------------
with tab1:
    st.subheader("กำหนดหัวข้อและบริบทเพื่อให้ AI วิเคราะห์เจาะลึก")
    st.caption("ยิ่งใส่รายละเอียดเยอะ AI จะยิ่งค้นหาและเปรียบเทียบจุดเด่นจุดด้อยได้ลึกซึ้งและไม่ซ้ำซาก")

    col1, col2 = st.columns(2)
    with col1:
        in_topic = st.text_input("📌 หัวข้อเปรียบเทียบ (Topic)", value=st.session_state.script_data.get("topic", "กาแฟดริป VS กาแฟแคปซูล"))
        in_name_a = st.text_input("📦 ชื่อสินค้า / สิ่งที่เปรียบเทียบ A", value=st.session_state.script_data.get("name_a", "กาแฟดริป"))
        in_details_a = st.text_area("📝 ข้อมูล/สเปก/จุดเด่นของ A (มีหรือไม่ก็ได้)", placeholder="เช่น เมล็ดกาแฟคั่วบด สุนทรียภาพ กลิ่นหอม คุมอุณหภูมิเอง...", height=85)
    with col2:
        in_target = st.text_input("🎯 กลุ่มเป้าหมายคนดู", placeholder="เช่น วัยทำงาน, นักเรียนงบน้อย, สายกาแฟจริงจัง, คนรักสุขภาพ...")
        in_name_b = st.text_input("📦 ชื่อสินค้า / สิ่งที่เปรียบเทียบ B", value=st.session_state.script_data.get("name_b", "กาแฟแคปซูล"))
        in_details_b = st.text_area("📝 ข้อมูล/สเปก/จุดเด่นของ B (มีหรือไม่ก็ได้)", placeholder="เช่น ชงใน 30 วินาที ได้มาตรฐาน รวดเร็ว ไม่เลอะเทอะ เครื่องกะทัดรัด...", height=85)

    st.markdown("#### 🔗 ลิงก์ Affiliate สำหรับให้ AI วางในคอมเมนต์ปักหมุด")
    col_aff1, col_aff2 = st.columns(2)
    with col_aff1:
        aff_a = st.text_input("พิกัด Affiliate สินค้า A", placeholder="https://shopee.co.th/link_a")
    with col_aff2:
        aff_b = st.text_input("พิกัด Affiliate สินค้า B", placeholder="https://shopee.co.th/link_b")

    in_angles = st.text_input("💡 มุมมองที่ต้องการเน้นเปรียบเทียบเป็นพิเศษ", placeholder="เช่น ความคุ้มค่าในระยะยาว, ความยากง่ายในการใช้งาน, ความทนทาน...")

    if st.button("🚀 สั่งให้ Gemini ทำ Deep Research & ร่างบทใหม่ทันที", type="primary", use_container_width=True):
        with st.spinner("🤖 Gemini กำลังทำ Deep Research วิเคราะห์สเปก จุดแข็ง จุดด้อย และร่างบท 4 ท่อน..."):
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
                )
                st.session_state.script_data = new_data
                st.success("✅ ทำการวิเคราะห์และสร้างบทเรียบร้อยแล้ว! คลิกไปที่แท็บ '2. ตรวจบท & สั่งรีไรท์' ได้เลยครับ")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเรียก AI: {e}")

# -------------------------------------------------------------
# TAB 2: SCRIPT STUDIO & REWRITER
# -------------------------------------------------------------
with tab2:
    st.subheader("📝 Script Review & Rewrite Studio")
    st.caption("อ่านบทที่ AI คิดมา ตรวจสอบความถูกต้อง สั่ง AI รีไรท์เฉพาะจุด หรือแก้คำด้วยตัวเองได้อิสระ")

    # Research Factsheet
    summary_text = st.session_state.script_data.get("research_summary", "")
    if summary_text:
        with st.expander("📊 สรุปข้อมูลเจาะลึก 4 มิติจาก AI (Research Fact Sheet)", expanded=True):
            st.info(summary_text)

    col_script, col_rewrite = st.columns([3, 2], gap="large")

    with col_script:
        st.markdown("#### ✍️ บทพากย์ 4 ท่อน (แก้ไขได้โดยตรง)")
        s_hook = st.text_area(
            "🎯 ท่อนที่ 1: Hook (เปิดประเด็นชวนสงสัย)",
            value=st.session_state.script_data.get("hook", ""),
            height=70,
        )
        s_item_a = st.text_area(
            f"🟢 ท่อนที่ 2: จุดเด่น {st.session_state.script_data.get('name_a', 'Item A')} (กรอบและตัวชี้ไปที่ A)",
            value=st.session_state.script_data.get("item_a", ""),
            height=90,
        )
        s_item_b = st.text_area(
            f"🟢 ท่อนที่ 3: จุดเด่น {st.session_state.script_data.get('name_b', 'Item B')} (กรอบและตัวชี้ไปที่ B)",
            value=st.session_state.script_data.get("item_b", ""),
            height=90,
        )
        s_conclusion = st.text_area(
            "🏁 ท่อนที่ 4: สรุปฟันธง + Affiliate CTA ชวนโหวตและดูคอมเมนต์",
            value=st.session_state.script_data.get("conclusion", ""),
            height=90,
        )
        s_comment = st.text_area(
            "📌 ข้อความสำหรับปักหมุดคอมเมนต์แรก (Affiliate Pinned Comment)",
            value=st.session_state.script_data.get("affiliate_comment", ""),
            height=120,
        )

        # Sync changes to session_state
        st.session_state.script_data["hook"] = s_hook
        st.session_state.script_data["item_a"] = s_item_a
        st.session_state.script_data["item_b"] = s_item_b
        st.session_state.script_data["conclusion"] = s_conclusion
        st.session_state.script_data["affiliate_comment"] = s_comment

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
            "คำสั่งปรับแก้เพิ่มเติม (เช่น 'ขอท่อนฮุคให้กระแทกใจกว่านี้', 'ย่อให้สั้นลง'):",
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

        c_rate, c_pitch = st.columns(2)
        with c_rate:
            voice_rate = st.select_slider(
                "ความเร็วเสียง (Rate):",
                options=["-10%", "+0%", "+5%", "+10%", "+15%"],
                value="+0%",
            )
        with c_pitch:
            voice_pitch = st.select_slider(
                "ระดับโทนเสียง (Pitch):",
                options=["-5Hz", "+0Hz", "+5Hz"],
                value="+0Hz",
            )

        st.markdown("#### 🎵 เสียงประกอบ (BGM & SFX)")
        enable_bgm = st.toggle("เปิดเพลงคลอเบาๆ ด้านหลัง (Lo-Fi BGM)", value=True)
        bgm_vol = st.slider("ระดับความดัง BGM:", min_value=0.05, max_value=0.30, value=0.12, step=0.01) if enable_bgm else 0.0
        enable_sfx = st.toggle("เปิดเสียง Effect (Pop / Whoosh) ตอนสลับกรอบชี้", value=True)

    with c_visual:
        st.markdown("#### 🖼️ สีและภาพพื้นหลัง")
        c_bg1, c_bg2 = st.columns(2)
        with c_bg1:
            bg_color = st.color_picker("สีพื้นหลัง (Background)", "#F5F2EB")
        with c_bg2:
            highlight_color = st.color_picker("สีกรอบไฟไฮไลต์ (Active Lime)", "#32CD32")

        st.markdown("#### 🎯 รูปแบบ Animation การชี้")
        anim_style = st.selectbox(
            "เลือกเอฟเฟกต์ตอนพูดถึงไอเทม:",
            options=["pointer_and_border", "border_only"],
            format_func=lambda x: "ตัวชี้ลอยสลับไปมา + กรอบไฟนีออน (แนะนำ)" if x == "pointer_and_border" else "กรอบไฟนีออนอย่างเดียว",
        )

        st.markdown("#### 📤 อัปโหลดรูปสินค้าและตัวละคร Avatar (Optional)")
        up_a = st.file_uploader("รูปสินค้า A (1:1 สี่เหลี่ยมจัตุรัส)", type=["png", "jpg", "jpeg"], key="uploader_a")
        up_b = st.file_uploader("รูปสินค้า B (1:1 สี่เหลี่ยมจัตุรัส)", type=["png", "jpg", "jpeg"], key="uploader_b")
        up_char = st.file_uploader("รูปตัวละคร Avatar ด้านล่าง (PNG พื้นใส)", type=["png"], key="uploader_char")

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
        """
    )

    if st.button("🎥 สั่งเรนเดอร์คลิปวิดีโอ 1080x1920 ทันที", type="primary", use_container_width=True):
        # Determine image paths
        path_a = IMAGES_DIR / "item_a_drip.png"
        path_b = IMAGES_DIR / "item_b_capsule.png"
        path_char = IMAGES_DIR / "character_host.png"

        if up_a:
            path_a = ASSETS_DIR / "images" / f"up_a_{int(time.time())}.png"
            with open(path_a, "wb") as f:
                f.write(up_a.getbuffer())

        if up_b:
            path_b = ASSETS_DIR / "images" / f"up_b_{int(time.time())}.png"
            with open(path_b, "wb") as f:
                f.write(up_b.getbuffer())

        if up_char:
            path_char = ASSETS_DIR / "images" / f"up_char_{int(time.time())}.png"
            with open(path_char, "wb") as f:
                f.write(up_char.getbuffer())

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

            st.write(f"🎨 กำลังเรนเดอร์ Dynamic Animation, กรอบไฟ, ตัวชี้ และซับไตเติล (ความยาว {total_duration:.1f} วินาที)...")
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
            )
            elapsed = time.time() - start_t
            progress_box.update(label=f"✅ เรนเดอร์วิดีโอ 1080x1920 สำเร็จสมบูรณ์ใน {elapsed:.1f} วินาที!", state="complete")
            st.session_state.rendered_video_path = str(final_video)

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

            st.markdown("#### 📋 ข้อความสำหรับปักหมุดคอมเมนต์แรก (Auto-Pin Comment):")
            st.code(st.session_state.script_data.get("affiliate_comment", ""), language="text")
