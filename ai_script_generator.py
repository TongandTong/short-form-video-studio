"""
AI Script Generator using Google Gemini API.
Features:
- Deep Research Comparison across 4 critical pillars (Specs, Trade-offs, Value, User Profile)
- Contextual input support (user notes, target audience, specific focus angles)
- Rewrite Studio (allows users to ask AI to rewrite/polish with specific instructions & tones)
- Pinned Affiliate comment generator with high-conversion CTAs.
"""

import json
import os
import re
import sys
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

from config import TEMP_DIR

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


FRAMEWORK_PRESETS: Dict[str, Dict[str, str]] = {
    "persona": {
        "id": "persona",
        "name": "👤 Persona-based (ใครเหมาะกับอะไร)",
        "desc": "จัดกลุ่มตามผู้ใช้ เช่น มือใหม่ vs มือโปร หรือ คนตื่นสาย vs สายชิล",
        "hook_guide": "กระตุกเตือนว่า 'อย่าเพิ่งซื้อถ้ายังไม่รู้ว่าคุณเป็นคนประเภทไหน!'",
        "r1_focus": "สไตล์การใช้งาน & ไลฟ์สไตล์ผู้ใช้",
        "r2_focus": "ทักษะ ความเร่งรีบ & การปรับแต่ง",
        "r3_focus": "ความคุ้มค่าตามระดับการใช้งานจริง",
        "conclusion_guide": "ฟันธงชัดเจนว่าคนแบบไหนเหมาะกับ A และคนแบบไหนเหมาะกับ B",
    },
    "crossover": {
        "id": "crossover",
        "name": "🔀 Cross-over (จับคู่ข้ามหมวด)",
        "desc": "เทียบสิ่งที่ไม่น่าเข้ากันแต่คนสงสัย เช่น กาแฟสด vs ชามัทฉะ (การตื่นตัว & โฟกัส)",
        "hook_guide": "เปิดด้วยประเด็นน่าสงสัยว่า 2 สิ่งนี้ดูคนละเรื่อง แต่ถ้าต้องการผลลัพธ์นี้ ตัวไหนชนะขาด?",
        "r1_focus": "กลไกการทำงาน & ผลลัพธ์ที่ได้ทันที",
        "r2_focus": "ผลข้างเคียง & ความนิ่งต่อเนื่องตลอดวัน",
        "r3_focus": "ความสะดวกและความง่ายในชีวิตประจำวัน",
        "conclusion_guide": "ชี้ชัดว่าสำหรับเป้าหมายนี้ ตัวไหนตอบโจทย์ตรงจุดกว่ากัน",
    },
    "cost_value": {
        "id": "cost_value",
        "name": "💰 Cost vs Value (คำนวณต้นทุนจริง)",
        "desc": "ซูมเรื่องเงิน เวลา และจุดคุ้มทุน เช่น ชงเอง vs ซื้อร้าน สิ้นปีเหลือเงินกี่บาท",
        "hook_guide": "เปิดด้วยตัวเลขเงินที่ประหยัดได้ต่อปี ชวนสะดุ้งกระตุกต่อมอยากรู้",
        "r1_focus": "ต้นทุนก้อนแรก & ค่าอุปกรณ์เริ่มต้น",
        "r2_focus": "ค่าใช้จ่ายรายวัน & เวลาที่ต้องเสียไป",
        "r3_focus": "จุดคุ้มทุน (Breakeven) & ยอดเงินเก็บใน 1 ปี",
        "conclusion_guide": "คำนวณจุดคุ้มทุนเป็นตัวเลขชัดเจน และบอกว่าใครจะคุ้มเงินที่สุด",
    },
    "blind_test": {
        "id": "blind_test",
        "name": "🙈 Blind Test / Experiment (ทดลองจริง)",
        "desc": "คนทั่วไปแยกออกจริงไหม เช่น ของหลักร้อย vs หลักพัน หรือสูตรทางเลือก vs สูตรแท้",
        "hook_guide": "ถ้าปิดตาชิม/ลองโดยไม่ดูป้ายราคา คนทั่วไปจะแยกออกจริงไหม ผลลัพธ์น่าตกใจมาก!",
        "r1_focus": "สัมผัสแรก รสชาติ หรือความรู้สึกภายนอก",
        "r2_focus": "ประสิทธิภาพการใช้งานจริงแบบไม่มองแบรนด์",
        "r3_focus": "ความคุ้มค่าเทียบกับราคาที่จ่ายเพิ่ม",
        "conclusion_guide": "เฉลยผลทดสอบจริงว่าคุ้มที่จะจ่ายแพงกว่าไหม หรือตัวถูกก็เหลือเฟือ",
    },
    "scenario_budget": {
        "id": "scenario_budget",
        "name": "🎯 Scenario / Budget (จำกัดเงื่อนไข)",
        "desc": "จำกัดงบหรือพื้นที่ เช่น งบ 1,000 บาท ซื้อแบบไหนจบสุด หรืออยู่คอนโดเลือกตัวไหน",
        "hook_guide": "เปิดด้วยเพดานงบประมาณหรือเงื่อนไขจำกัด เลือกทางไหนเจ็บตัวน้อยสุดและจบจริง",
        "r1_focus": "สิ่งที่ได้จริงในงบประมาณจำกัดนี้",
        "r2_focus": "ข้อจำกัดที่ต้องยอมรับ (Trade-offs)",
        "r3_focus": "ความทนทานและความคุ้มค่าในระยะยาว",
        "conclusion_guide": "สรุปทางเลือกที่ดีที่สุดที่จบในงบหรือเงื่อนไขนั้นๆ",
    },
    "price_tier": {
        "id": "price_tier",
        "name": "🏷️ Price Tier (แพง vs ถูก)",
        "desc": "ของหลักร้อยที่ฟังก์ชันและสเปกเทียบชั้นหลักหมื่น สู้ไหวจริงไหม",
        "hook_guide": "ราคาต่างกันหลายเท่าตัว! ของหลักร้อยจะท้าชนของหลักหมื่นได้จริงเหรอ?",
        "r1_focus": "ฟังก์ชันหลักที่ทำได้เทียบเท่าตัวแพง",
        "r2_focus": "จุดต่างของวัสดุ ดีเทล และความพรีเมียม",
        "r3_focus": "ความทนทานและประสบการณ์การใช้งานระยะยาว",
        "conclusion_guide": "ฟันธงว่าส่วนต่างราคาคุ้มค่าที่จะจ่ายเพิ่มหรือไม่",
    },
    "old_vs_modern": {
        "id": "old_vs_modern",
        "name": "⏳ Old School vs Modern (เก่า vs ใหม่)",
        "desc": "เสน่ห์งานคราฟต์คลาสสิกดั้งเดิม vs นวัตกรรมเครื่องอัตโนมัติความเร็วสูง",
        "hook_guide": "ยุคนี้ยังต้องเหนื่อยทำมืออยู่ไหม หรือเครื่องออโต้จะเข้ามาแทนที่ 100% แล้ว?",
        "r1_focus": "เสน่ห์ความสุนทรีย์ & การคราฟต์ด้วยตัวเอง",
        "r2_focus": "ความเร็ว ความง่าย & ความสม่ำเสมอได้มาตรฐาน",
        "r3_focus": "การดูแลรักษา ล้างทำความสะอาด & ความจุกจิก",
        "conclusion_guide": "ฟันธงว่าคนดูเหมาะกับสายดื่มด่ำความคลาสสิก หรือสายเน้นชีวิตง่าย",
    },
    "myth_vs_reality": {
        "id": "myth_vs_reality",
        "name": "💡 Myth vs Reality (ความเชื่อ vs ความจริง)",
        "desc": "วิทยาศาสตร์หักล้างความเชื่อผิดๆ เช่น คั่วเข้ม vs คั่วอ่อน ใครคาเฟอีนแรงกว่ากัน",
        "hook_guide": "คุณกำลังเข้าใจผิดอยู่หรือเปล่า? ความจริงระหว่าง 2 สิ่งนี้ที่คน 90% ยังเชื่อผิดๆ!",
        "r1_focus": "ความเชื่อยอดฮิตที่คนมักเข้าใจผิด",
        "r2_focus": "ข้อเท็จจริงทางวิทยาศาสตร์ที่พิสูจน์แล้ว",
        "r3_focus": "ผลลัพธ์จริงและการนำไปใช้งานให้ถูกต้อง",
        "conclusion_guide": "หักล้างความเชื่อเดิมและฟันธงวิธีเลือกที่ถูกต้องตามหลักการ",
    },
    "local_vs_import": {
        "id": "local_vs_import",
        "name": "🇹🇭 Local vs Import (ของไทย vs ของนอก)",
        "desc": "ลบอคติ เมล็ดไทยเกรดประกวด vs เมล็ดนอกยอดฮิต เทียบหมัดต่อหมัด",
        "hook_guide": "อย่าเพิ่งดูถูกของไทย! ลองเทียบตัวท็อปบ้านเรา กับตัวดังนำเข้า ใครจะอยู่ใครจะไป?",
        "r1_focus": "คุณภาพวัตถุดิบ & รสสัมผัสเนื้อแท้",
        "r2_focus": "ความสดใหม่ ความเข้ากันได้กับคนไทย & ภาษีนำเข้า",
        "r3_focus": "ความคุ้มค่าคุ้มราคาเมื่อเทียบกันตรงๆ",
        "conclusion_guide": "ชี้ชัดจุดที่ของไทยทำได้เหนือกว่า และจุดเด่นเฉพาะตัวของสินค้านอก",
    },
    "hype_vs_standard": {
        "id": "hype_vs_standard",
        "name": "🔥 Hype vs Standard (ทริกไวรัล vs สูตรมาตรฐาน)",
        "desc": "ทริกลัดหรือสูตรแปลกบนโซเชียล เทียบกับวิธีมาตรฐานที่มือโปรใช้จริง",
        "hook_guide": "ทริกไวรัลในโซเชียลที่คนแห่ทำตาม เวิร์กจริงหรือแค่หลอกตา? มาทดลองเทียบกับวิธีจริง!",
        "r1_focus": "ความแปลกใหม่ & สิ่งที่ทริกไวรัลเคลมไว้",
        "r2_focus": "ผลลัพธ์จริงเมื่อทดสอบเทียบกับสูตรมาตรฐาน",
        "r3_focus": "ความสม่ำเสมอและความคุ้มค่าในการทำซ้ำ",
        "conclusion_guide": "ฟันธงว่าสูตรไวรัลคุ้มค่าที่จะลองไหม หรือวิธีมาตรฐานคือคำตอบที่ดีที่สุด",
    },
    "country_matchup": {
        "id": "country_matchup",
        "name": "🌍 Country Matchup (ศึกสองชาติ / ศักยภาพประเทศ)",
        "desc": "เทียบศักยภาพระดับชาติ กองทัพ เศรษฐกิจ การศึกษา ด้วยสถิติและดัชนีระดับโลกอย่างเป็นกลาง",
        "hook_guide": "เปิดด้วยประเด็นเทียบหมัดต่อหมัดระหว่าง 2 ชาติเพื่อนบ้านหรือมหาอำนาจ สถิติจริงใครเหนือกว่ากัน?",
        "r1_focus": "แสนยานุภาพกองทัพ งบประมาณ & กำลังพล (Military Power & Defense)",
        "r2_focus": "พลังเศรษฐกิจ ขนาด GDP & อุตสาหกรรมหลัก (Economy & GDP per Capita)",
        "r3_focus": "ระบบการศึกษา คุณภาพชีวิต & ดัชนีทุนมนุษย์ (Education & Human Development Index)",
        "conclusion_guide": "สรุปจุดแข็งของแต่ละประเทศและมุมมองการเติบโตอย่างเป็นกลาง ไร้อคติดราม่า",
    },
    "era_timeline": {
        "id": "era_timeline",
        "name": "⏳ Era Timeline (ข้ามยุคสมัย อดีต vs ปัจจุบัน)",
        "desc": "เทียบการเปลี่ยนแปลงข้ามกาลเวลา ยุค 90s vs ปัจจุบัน, ยุคก่อน vs ยุคนี้, เจนเก่า vs เจนใหม่",
        "hook_guide": "ย้อนวันวานเทียบปัจจุบัน! 20-30 ปีผ่านไป สิ่งนี้เปลี่ยนไปขนาดไหน คนยุคนี้จะเชื่อไหม?",
        "r1_focus": "วิถีชีวิต ความคลาสสิก & ข้อจำกัดในอดีต (Past Lifestyle & Nostalgia)",
        "r2_focus": "ความสะดวกสบาย นวัตกรรม & การเปลี่ยนแปลงปัจจุบัน (Modern Efficiency & Tech)",
        "r3_focus": "สิ่งที่ได้มาเทียบกับเสน่ห์ที่หายไป (What We Gained vs What We Lost)",
        "conclusion_guide": "ฟันธงว่าคุณคิดถึงเสน่ห์ยุคก่อน หรือชอบความง่ายของยุคนี้มากกว่ากัน ชวนคนดูแชร์ความทรงจำ",
    },
    "perfect_pairing": {
        "id": "perfect_pairing",
        "name": "🤝 Perfect Pairing (จับคู่ของที่เข้ากัน: A + B เคมีลงตัว)",
        "desc": "วิเคราะห์ทำไม 2 สิ่งนี้อยู่ด้วยกันแล้วปัง เช่น กาแฟ+มะพร้าว, หมูสามชั้น+กิมจิ, อุปกรณ์คู่ใจ",
        "hook_guide": "เคยสงสัยไหมว่าทำไม 2 สิ่งนี้พอกินหรือใช้คู่กันแล้วเข้ากันอย่างเหลือเชื่อ? ความลับทางวิทยาศาสตร์อยู่ตรงนี้!",
        "r1_focus": "กลไกเคมี รสสัมผัส หรือฟังก์ชันที่เสริมกัน (Chemical & Flavor Synergy)",
        "r2_focus": "ผลลัพธ์ทวีคูณ (1+1 มากกว่า 2) ทั้งประโยชน์และประสบการณ์ (Boosted Benefits)",
        "r3_focus": "สัดส่วนทองคำ & ทริกการจับคู่ให้ฟินที่สุด (Golden Ratio & Best Practice)",
        "conclusion_guide": "ฟันธงเหตุผลที่ 2 สิ่งนี้คือคู่แท้ที่ต้องลอง และแนะนำให้คนดูลองทำตาม",
    },
}


DURATION_MODES: Dict[str, Dict[str, Any]] = {
    "short_1round": {
        "id": "short_1round",
        "rounds": 1,
        "name": "⚡ กระชับ สั้นไว (1 ยก: ~30-40s)",
        "desc": "เปิด Hook ไว ชี้หมัดเด็ดจุดต่างของ A vs B จบด้วยสรุปฟันธง เหมาะกับคนดูรีบ",
    },
    "medium_2round": {
        "id": "medium_2round",
        "rounds": 2,
        "name": "⚖️ ความยาวมาตรฐาน (2 ยก: ~45-60s)",
        "desc": "ยกที่ 1 การใช้งานจริง สวนกลับด้วยยกที่ 2 ความคุ้มค่า/ราคา ความยาวกำลังดี",
    },
    "deep_3round": {
        "id": "deep_3round",
        "rounds": 3,
        "name": "🔥 เจาะลึกมัลติราวด์ (3 ยก: ~75-90s)",
        "desc": "เปรียบเทียบสลับไปมา 3 มิติครบครัน คุณภาพ ความสะดวก และราคา ข้อมูลลึกซึ้ง",
    },
    "multi_battle_3round": {
        "id": "multi_battle_3round",
        "rounds": 3,
        "name": "🎡 แบทเทิล 3 คู่ย่อยใน 1 คลิป (Carousel Battle: ~60-80s)",
        "desc": "1 คลิปเปรียบเทียบ 3 คู่ย่อยสลับเปลี่ยนรูปและชื่อตามยก เช่น กาแฟดำ: ยก 1 ส้ม vs มะพร้าว, ยก 2 นม vs อัลมอนด์, ยก 3 โทนิค vs น้ำผึ้งมะนาว",
    },
    "master_4round": {
        "id": "master_4round",
        "rounds": 4,
        "name": "👑 เอ็กซ์ตรีมครบมิติ (4 ยก: ~100-120s)",
        "desc": "เจาะลึก 4 ยกสุดเข้มข้น เพิ่มมิติความทนทานและประสบการณ์ระยะยาว คอนเทนต์ระดับพรีเมียม",
    },
}


def generate_social_caption(data: Dict[str, Any]) -> Dict[str, str]:
    """Generates an engaging, high-CTR social media caption and trending hashtags."""
    topic = data.get("topic", "")
    name_a = data.get("name_a", "A")
    name_b = data.get("name_b", "B")
    hook = data.get("hook", "")
    fw = data.get("framework", "persona")
    is_pairing = fw == "perfect_pairing"

    clean_a = re.sub(r"[^\w\u0E00-\u0E7F]", "", name_a)
    clean_b = re.sub(r"[^\w\u0E00-\u0E7F]", "", name_b)

    if is_pairing:
        caption_lines = [
            f"✨ ทำไม {name_a} + {name_b} ถึงเป็นคู่แท้ที่ต้องลองสักครั้งในชีวิต! 🤝",
            f"หลายคนอาจจะยังไม่รู้ว่าความเข้ากันทางเคมีและรสชาติมันลงตัวขนาดไหน...",
            "👇 ใครเคยลองสูตรนี้แล้วบ้าง คอมเมนต์บอกหน่อยว่าฟินจริงไหม!",
        ]
        tags = [
            "#WhyItWorks",
            "#คู่แท้",
            "#สูตรเด็ด",
            f"#{clean_a}" if clean_a else "",
            f"#{clean_b}" if clean_b else "",
            "#สาระน่ารู้",
            "#TikTokสายความรู้",
            "#เรื่องนี้ต้องรู้",
        ]
    else:
        caption_lines = [
            f"🥊 {topic} เลือกตัวไหนดีกว่ากันแน่? สรุปจบในคลิปเดียว!",
            f"{hook[:90]}..." if hook else f"เทียบหมัดต่อหมัดระหว่าง {name_a} กับ {name_b} แบบเจาะลึก",
            "💬 คุณอยู่ทีมไหน? โหวตกันในคอมเมนต์เลย! (พิกัดปักหมุดไว้ในคอมเมนต์แรกแล้วครับ)",
        ]
        tags = [
            "#WhyItWorks",
            "#เปรียบเทียบ",
            f"#{clean_a}" if clean_a else "",
            f"#{clean_b}" if clean_b else "",
            "#รู้หรือไม่",
            "#สาระน่ารู้",
            "#ของมันต้องมี",
            "#TikTokสายความรู้",
            "#เทรนด์วันนี้",
        ]

    caption_text = "\n".join(caption_lines)
    tags_clean = [t for t in tags if t and t != "#"]
    tags_text = " ".join(tags_clean)
    return {
        "social_caption": f"{caption_text}\n\n{tags_text}",
        "hashtags": tags_text,
    }


def extract_names_from_topic(topic: str) -> tuple[str, str]:
    """Extracts Item A and Item B from a comparison topic string."""
    if not topic:
        return "", ""
    delimiters = [" VS ", " vs ", " Vs ", " v ", " V ", " กับ ", " หรือ ", " vs. ", " VS. ", " / "]
    for d in delimiters:
        if d in topic:
            parts = topic.split(d, 1)
            a = re.sub(r"^[0-9\.\s\-\:\#\*\U00010000-\U0010ffff]+", "", parts[0]).strip()
            b = re.sub(r"^[0-9\.\s\-\:\#\*\U00010000-\U0010ffff]+", "", parts[1]).strip()
            if a and b:
                return a, b
    return "", ""


class AIScriptGenerator:
    """Generates deep, fact-based Thai comparison scripts using Gemini."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                    self.api_key = st.secrets["GEMINI_API_KEY"]
            except Exception:
                pass

        if not self.api_key:
            raise ValueError(
                "Gemini API Key is missing! Set GEMINI_API_KEY in .env or pass it to AIScriptGenerator."
            )
        # Multi-tiered model hierarchy:
        # 1. Gemini Flash Latest & 2.5 Flash - State-of-the-art fast intelligence & reliable quota
        # 2. Gemini 3.5 Flash & 3-Flash-Preview - Cutting edge reasoning
        # 3. Gemini 3.1 Pro Preview - Flagship deep reasoning fallback
        self.endpoints = [
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-lite-latest:generateContent?key={self.api_key}",
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key={self.api_key}",
        ]
        self.endpoint = self.endpoints[0]
        self.fallback_endpoint = self.endpoints[1]
        self.secondary_fallback = self.endpoints[4]

    def generate_script(
        self,
        topic: str,
        name_a: str,
        name_b: str,
        details_a: str = "",
        details_b: str = "",
        target_audience: str = "",
        key_angles: str = "",
        affiliate_link_a: str = "",
        affiliate_link_b: str = "",
        tone: str = "engaging",
        script_mode: str = "deep_3round",
        channel_outro_cta: str = "",
        framework: str = "persona",
    ) -> Dict[str, Any]:
        """
        Deep-researches comparison points and writes a short-form script in Thai.
        Supports:
        - 10 Viral Comparison Frameworks (Persona, Crossover, Cost vs Value, Blind Test, etc.)
        - 4 Duration & Depth Modes: short_1round, medium_2round, deep_3round, master_4round.
        """
        fw = FRAMEWORK_PRESETS.get(framework, FRAMEWORK_PRESETS["persona"])
        outro_prompt_hint = f"\n- ข้อความส่งท้ายประจำเพจที่ต้องสอดแทรกไว้ใน conclusion: '{channel_outro_cta}'" if channel_outro_cta else ""

        # Safeguard: if name_a/b are empty or mismatched coffee defaults when topic is different
        if (name_a == "กาแฟดริป" and "กาแฟ" not in topic) or not name_a or not name_b:
            parsed_a, parsed_b = extract_names_from_topic(topic)
            if parsed_a and parsed_b:
                name_a, name_b = parsed_a, parsed_b

        # Map script_mode to standardized depth
        if script_mode in ("classic", "short_1round"):
            active_mode = "short_1round"
            num_rounds = 1
        elif script_mode == "medium_2round":
            active_mode = "medium_2round"
            num_rounds = 2
        elif script_mode in ("multi_round", "deep_3round"):
            active_mode = "deep_3round"
            num_rounds = 3
        elif script_mode == "multi_battle_3round":
            active_mode = "multi_battle_3round"
            num_rounds = 3
        elif script_mode == "master_4round":
            active_mode = "master_4round"
            num_rounds = 4
        else:
            active_mode = "deep_3round"
            num_rounds = 3

        round_focus_map = {
            1: fw.get("r1_focus", "คุณภาพ & การใช้งานจริง"),
            2: fw.get("r2_focus", "ความสะดวก & ความคุ้มค่า"),
            3: fw.get("r3_focus", "ความคุ้มค่า & ราคาต่อการใช้งาน"),
            4: "ความทนทาน & ประสบการณ์ระยะยาว (Durability & Long-term Value)",
        }

        framework_directive = f"""
กรอบการเล่าเรื่องเชิงกลยุทธ์ (Content Framework):
- หมวดหมู่: {fw['name']}
- แนวคิดหลัก: {fw['desc']}
- ทิศทาง Hook: {fw['hook_guide']}
- โฟกัสยกที่ 1: {round_focus_map[1]}
- โฟกัสยกที่ 2: {round_focus_map[2]}
- โฟกัสยกที่ 3: {round_focus_map[3]}
- โฟกัสยกที่ 4: {round_focus_map[4]}
- ทิศทางสรุปฟันธง: {fw['conclusion_guide']}
"""

        is_pairing = fw.get("id") == "perfect_pairing"
        is_multi_battle = active_mode == "multi_battle_3round"
        round_prompts = []
        json_fields = []
        for r in range(1, num_rounds + 1):
            f_title = round_focus_map.get(r, f"มิติที่ {r}")
            if is_multi_battle:
                round_prompts.append(
                    f"{r}. ยกที่ {r} (คู่แบทเทิลย่อยที่ {r}):\n"
                    f"   - round_{r}_title: หัวข้อยกที่ {r}\n"
                    f"   - round_{r}_name_a: ชื่อไอเทม A ประจำยกนี้ (เช่น กาแฟ+ส้มยูซุ)\n"
                    f"   - round_{r}_name_b: ชื่อไอเทม B ประจำยกนี้ (เช่น กาแฟ+น้ำมะพร้าว)\n"
                    f"   - round_{r}_a: จุดเด่นของไอเทม A ในคู่นี้ (1-2 ประโยคกระชับ ชัดเจน)\n"
                    f"   - round_{r}_b: สวนกลับด้วยจุดเด่นของไอเทม B ในคู่นี้ (1-2 ประโยคกระชับ)"
                )
                json_fields.append(
                    f'  "round_{r}_title": "{f_title}",\n'
                    f'  "round_{r}_name_a": "ชื่อไอเทม A ประจำยก {r}",\n'
                    f'  "round_{r}_name_b": "ชื่อไอเทม B ประจำยก {r}",\n'
                    f'  "round_{r}_a": "...",\n'
                    f'  "round_{r}_b": "..."'
                )
            elif is_pairing:
                round_prompts.append(
                    f"{r}. ยกที่ {r} ({f_title}):\n"
                    f"   - round_{r}_title: ตั้งชื่อยกที่ {r} สั้นๆ (ให้สอดคล้องกับ {f_title})\n"
                    f"   - round_{r}_a: บทบาท/รสสัมผัส/คุณสมบัติเด่นของ {name_a} ในมิตินี้ (1-2 ประโยคกระชับ)\n"
                    f"   - round_{r}_b: บทบาทของ {name_b} ที่เข้ามาเสริม/ตัดเลี่ยน/ทำงานร่วมกันจนลงตัว (1-2 ประโยคกระชับ)"
                )
                json_fields.append(f'  "round_{r}_title": "{f_title}",\n  "round_{r}_a": "...",\n  "round_{r}_b": "..."')
            else:
                round_prompts.append(
                    f"{r}. ยกที่ {r} ({f_title}):\n"
                    f"   - round_{r}_title: ตั้งชื่อยกที่ {r} สั้นๆ (ให้สอดคล้องกับ {f_title})\n"
                    f"   - round_{r}_a: ข้อมูล/จุดเด่นด้านนี้ของ {name_a} (1-2 ประโยคกระชับ ชัดเจน มีน้ำหนัก)\n"
                    f"   - round_{r}_b: สวนกลับด้วยข้อมูล/จุดต่างด้านนี้ของ {name_b} (1-2 ประโยคกระชับ)"
                )
                json_fields.append(f'  "round_{r}_title": "{f_title}",\n  "round_{r}_a": "...",\n  "round_{r}_b": "..."')

        rounds_instruction_str = "\n".join(round_prompts)
        json_rounds_str = ",\n".join(json_fields)

        producer_role = (
            f"คุณเป็น Senior Short-Form Video Producer มืออาชีพ เชี่ยวชาญการทำคลิปวิเคราะห์การจับคู่ที่ลงตัว (Synergy Pairing: ทำไม A + B ถึงเข้ากันขั้นสุด) สไตล์ Reels/TikTok/Shorts ความยาวจำนวน {num_rounds} ยก ที่คนดูเกาะติดหน้าจอจนจบ"
            if is_pairing
            else f"คุณเป็น Senior Short-Form Video Producer มืออาชีพ เชี่ยวชาญการทำคลิปเปรียบเทียบแบบสลับชี้ A vs B สไตล์ Reels/TikTok/Shorts ความยาวจำนวน {num_rounds} ยก ที่คนดูเกาะติดหน้าจอจนจบ"
        )

        prompt = f"""
{producer_role}

โจทย์เปรียบเทียบ:
- หัวข้อ: {topic}
- ไอเทม A: {name_a} (ข้อมูล/สเปก: {details_a or 'ทั่วไป'})
- ไอเทม B: {name_b} (ข้อมูล/สเปก: {details_b or 'ทั่วไป'})
- กลุ่มเป้าหมายคนดู: {target_audience or 'บุคคลทั่วไป / ผู้บริโภคที่กำลังตัดสินใจซื้อ'}
- จุดเน้นพิเศษ: {key_angles or 'เปรียบเทียบรอบด้านทั้งประสิทธิภาพ ความสะดวก และราคา'}
- โทนอารมณ์: {tone} (น่าสนใจ มีน้ำหนักคำ ชวนฟัง กระชับ มีพลัง ไม่เวิ่นเว้อ)
{framework_directive}

ภารกิจของคุณ:
ร่างบทพากย์วิดีโอเปรียบเทียบสลับไปมาจำนวน {num_rounds} ยก สลับชี้ A ➜ B ตามกรอบ Framework ข้างต้น:
- hook: ประโยคเปิดคลิป 1 ประโยค ยิงคำถามคมๆ หรือประเด็นชวนสะดุ้งตามแนวทาง Framework ให้อยู่ดูต่อ
{rounds_instruction_str}
- conclusion: สรุปฟันธงตามแนวทาง {fw['conclusion_guide']} พร้อม CTA สไตล์ Affiliate เนียนๆ ชวนคนดูโหวต และบอกว่าพิกัดของแท้อยู่ในคอมเมนต์แรก{outro_prompt_hint}
- affiliate_comment: ข้อความสำหรับปักหมุดคอมเมนต์แรก รวบรวมพิกัด {name_a} และ {name_b} พร้อมอีโมจิ

สำคัญมาก:
- ห้ามใส่เครื่องหมาย Enter จริงในค่า JSON string เด็ดขาด ให้ใช้ \\n เท่านั้น
- ตอบเป็น JSON block เท่านั้นในโครงสร้างนี้:

{{
  "topic": "{topic}",
  "name_a": "{name_a}",
  "name_b": "{name_b}",
  "mode": "{active_mode}",
  "num_rounds": {num_rounds},
  "research_summary": "สรุปข้อมูลเจาะลึก {num_rounds} ยกสั้นๆ ตามกรอบ {fw['name']}...",
  "hook": "ประโยคเปิดคลิปตามกรอบ...",
{json_rounds_str},
  "conclusion": "ประโยคสรุปฟันธงและ CTA...",
  "affiliate_comment": "📍 พิกัดของแท้ราคาโปร:\\n👉 {name_a}: [ลิงก์ A]\\n👉 {name_b}: [ลิงก์ B]\\n(โหวตกันในคอมเมนต์ได้เลยครับ)"
}}
"""
        raw_res = self._call_gemini(
            prompt,
            affiliate_link_a,
            affiliate_link_b,
            topic,
            name_a,
            name_b,
            num_rounds=num_rounds,
            round_focus_map=round_focus_map,
            active_mode=active_mode,
        )
        return self._package_script_data(raw_res, active_mode, name_a, name_b, framework)

    def _package_script_data(
        self,
        data: Dict[str, Any],
        mode: str,
        name_a: str,
        name_b: str,
        framework: str = "persona",
    ) -> Dict[str, Any]:
        """Constructs the canonical segments timeline structure for TTS and Video engines."""
        fw = FRAMEWORK_PRESETS.get(framework, FRAMEWORK_PRESETS["persona"])
        data["framework"] = framework
        data["framework_name"] = fw["name"]

        # Determine num_rounds
        if mode in ("classic", "short_1round"):
            num_rounds = 1
            active_mode = "short_1round"
        elif mode == "medium_2round":
            num_rounds = 2
            active_mode = "medium_2round"
        elif mode in ("multi_round", "deep_3round"):
            num_rounds = 3
            active_mode = "deep_3round"
        elif mode == "multi_battle_3round":
            num_rounds = 3
            active_mode = "multi_battle_3round"
        elif mode == "master_4round":
            num_rounds = 4
            active_mode = "master_4round"
        else:
            if "round_4_a" in data:
                num_rounds = 4
                active_mode = "master_4round"
            elif "round_3_a" in data:
                num_rounds = 3
                active_mode = "deep_3round"
            elif "round_2_a" in data:
                num_rounds = 2
                active_mode = "medium_2round"
            else:
                num_rounds = 1
                active_mode = "short_1round"

        data["mode"] = active_mode
        data["num_rounds"] = num_rounds

        segments = [
            {"id": "hook", "text": data.get("hook", ""), "highlight": "none", "round_label": "🔥 เปิดประเด็น"}
        ]

        rounds_data = []
        for r in range(1, num_rounds + 1):
            r_title = data.get(f"round_{r}_title") or f"ยกที่ {r}"
            r_a = data.get(f"round_{r}_a") or (data.get("item_a", "") if r == 1 else "")
            r_b = data.get(f"round_{r}_b") or (data.get("item_b", "") if r == 1 else "")
            r_name_a = data.get(f"round_{r}_name_a") or name_a
            r_name_b = data.get(f"round_{r}_name_b") or name_b

            data[f"round_{r}_a"] = r_a
            data[f"round_{r}_b"] = r_b
            data[f"round_{r}_title"] = r_title
            data[f"round_{r}_name_a"] = r_name_a
            data[f"round_{r}_name_b"] = r_name_b

            rounds_data.append({
                "round": r,
                "title": r_title,
                "name_a": r_name_a,
                "name_b": r_name_b,
                "text_a": r_a,
                "text_b": r_b,
            })

            if r_a:
                segments.append({
                    "id": f"round_{r}_a",
                    "text": r_a,
                    "highlight": "A",
                    "round_label": f"🥊 {r_title}",
                    "round_number": r,
                    "name_a": r_name_a,
                    "name_b": r_name_b,
                })
            if r_b:
                segments.append({
                    "id": f"round_{r}_b",
                    "text": r_b,
                    "highlight": "B",
                    "round_label": f"🥊 {r_title}",
                    "round_number": r,
                    "name_a": r_name_a,
                    "name_b": r_name_b,
                })

        conclusion_text = data.get("conclusion", "")
        segments.append({
            "id": "conclusion",
            "text": conclusion_text,
            "highlight": "none",
            "round_label": "🏁 สรุปฟันธง",
        })

        data["segments"] = segments
        data["rounds"] = rounds_data
        data["rounds_data"] = rounds_data
        data.setdefault("item_a", data.get("round_1_a", ""))
        data.setdefault("item_b", data.get("round_1_b", ""))

        social_info = generate_social_caption(data)
        data["social_caption"] = data.get("social_caption") or social_info["social_caption"]
        data["hashtags"] = data.get("hashtags") or social_info["hashtags"]
        return data

    def rewrite_script(
        self,
        current_script: Dict[str, Any],
        instruction: str,
        tone: str = "engaging",
    ) -> Dict[str, Any]:
        """
        Rewrites or polishes an existing script according to user's feedback.
        Dynamically preserves the number of rounds in current_script.
        """
        topic = current_script.get("topic", "")
        name_a = current_script.get("name_a", "")
        name_b = current_script.get("name_b", "")
        mode = current_script.get("mode", "deep_3round")
        num_rounds = current_script.get("num_rounds", 3)
        fw = current_script.get("framework", "persona")

        round_snippets = []
        json_fields = []
        for r in range(1, num_rounds + 1):
            rt = current_script.get(f"round_{r}_title", f"ยกที่ {r}")
            ra = current_script.get(f"round_{r}_a", "")
            rb = current_script.get(f"round_{r}_b", "")
            round_snippets.append(f"- ยกที่ {r} ({rt}):\n  - A: {ra}\n  - B: {rb}")
            json_fields.append(f'  "round_{r}_title": "{rt}",\n  "round_{r}_a": "...",\n  "round_{r}_b": "..."')

        rounds_text = "\n".join(round_snippets)
        json_rounds_str = ",\n".join(json_fields)

        prompt = f"""
คุณเป็น Senior Video Script Doctor มีบทเปรียบเทียบเดิม ({num_rounds} ยก) ดังนี้:
หัวข้อ: {topic}
สินค้า A: {name_a}
สินค้า B: {name_b}

บทเดิม:
- Hook: {current_script.get('hook', '')}
{rounds_text}
- สรุป: {current_script.get('conclusion', '')}

คำสั่งปรับแก้จากผู้ใช้ (Instruction):
"{instruction}"
โทนที่ต้องการ: {tone}

โปรดรีไรท์บทใหม่ทั้ง {num_rounds} ยกให้คมขึ้น น่าฟังขึ้น ไหลลื่น ตอบโจทย์คำสั่งผู้ใช้
สำคัญ: ห้ามใส่ Enter จริงใน JSON string ให้ใช้ \\n เท่านั้น ตอบเฉพาะ JSON block รูปแบบเดิม:
{{
  "topic": "{topic}",
  "name_a": "{name_a}",
  "name_b": "{name_b}",
  "mode": "{mode}",
  "num_rounds": {num_rounds},
  "research_summary": "{current_script.get('research_summary', 'ปรับปรุงตามคำสั่ง')}",
  "hook": "...",
{json_rounds_str},
  "conclusion": "...",
  "affiliate_comment": "{current_script.get('affiliate_comment', '')}"
}}
"""
        raw_res = self._call_gemini(
            prompt,
            "",
            "",
            topic,
            name_a,
            name_b,
            num_rounds=num_rounds,
            active_mode=mode,
        )
        return self._package_script_data(raw_res, mode, name_a, name_b, framework=fw)

    def _call_gemini(
        self,
        prompt: str,
        affiliate_link_a: str,
        affiliate_link_b: str,
        topic: str,
        name_a: str,
        name_b: str,
        num_rounds: int = 3,
        round_focus_map: Optional[Dict[int, str]] = None,
        active_mode: str = "deep_3round",
    ) -> Dict[str, Any]:
        """Helper to call Gemini REST API and parse response with multi-tier fallback."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 2500,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        for url in self.endpoints:
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=15,
                )
                if response.status_code == 200:
                    data = response.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    text_parts = [p["text"] for p in parts if "text" in p and not p.get("thought")]
                    raw_text = "".join(text_parts).strip()
                    if not raw_text:
                        continue
                    parsed = self._clean_and_parse_json(raw_text)

                    # Inject affiliate links
                    comment = parsed.get("affiliate_comment", "")
                    if affiliate_link_a:
                        comment = comment.replace("[ลิงก์ A]", affiliate_link_a)
                    if affiliate_link_b:
                        comment = comment.replace("[ลิงก์ B]", affiliate_link_b)
                    parsed["affiliate_comment"] = comment
                    return parsed
            except Exception as e:
                print(f"[AI] Call warning on {url}: {e}")

        # Complete fallback template with all rounds populated
        fb = {
            "topic": topic,
            "name_a": name_a,
            "name_b": name_b,
            "mode": active_mode,
            "num_rounds": num_rounds,
            "research_summary": f"เปรียบเทียบ {name_a} ด้านความยืดหยุ่นและการควบคุม กับ {name_b} ด้านความรวดเร็วและมาตรฐานสม่ำเสมอ",
            "hook": f"สองตัวนี้เลือกอะไรดี? มาดูความต่างระหว่าง {name_a} กับ {name_b} กันครับ!",
            "item_a": f"{name_a} โดดเด่นด้วยฟังก์ชันที่ครบครัน เหมาะกับคนที่ชอบความคุ้มค่าและปรับแต่งได้ตามใจ",
            "item_b": f"ส่วน {name_b} ตอบโจทย์เรื่องความง่าย รวดเร็ว และได้มาตรฐานคุณภาพที่คงที่ทุกครั้ง",
            "conclusion": "แล้วคุณล่ะชอบตัวไหนมากกว่ากัน? พิกัดราคาพิเศษของทั้งสองตัว ปักหมุดไว้ในคอมเมนต์เรียบร้อยแล้วครับ!",
            "affiliate_comment": f"📍 พิกัดของแท้ราคาโปร:\n👉 {name_a}: {affiliate_link_a or '[ใส่ลิงก์ A]'}\n👉 {name_b}: {affiliate_link_b or '[ใส่ลิงก์ B]'}\nโหวตกันในคอมเมนต์ได้เลยน้า!",
        }
        rf_map = round_focus_map or {
            1: "คุณภาพ & การใช้งานจริง",
            2: "ความสะดวก & ความคุ้มค่า",
            3: "ความคุ้มค่า & ราคาต่อการใช้งาน",
            4: "ความทนทาน & ประสบการณ์ระยะยาว",
        }
        for r in range(1, num_rounds + 1):
            f_title = rf_map.get(r, f"มิติที่ {r}")
            fb[f"round_{r}_title"] = f_title
            fb[f"round_{r}_a"] = f"{name_a} ในมิติ {f_title} ตอบโจทย์การใช้งานจริงและมีฟังก์ชันครบครัน"
            fb[f"round_{r}_b"] = f"ส่วน {name_b} ในด้าน {f_title} เน้นความสะดวก รวดเร็ว และได้ผลลัพธ์ที่สม่ำเสมอ"
        return fb

    def _clean_and_parse_json(self, text: str) -> Dict[str, Any]:
        """Strip markdown code fence if present and parse JSON with fallbacks."""
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        elif clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        try:
            return json.loads(clean)
        except Exception:
            pass

        # Regex key-value extraction fallback
        data = {}
        fields = [
            "topic",
            "name_a",
            "name_b",
            "research_summary",
            "hook",
            "round_1_title",
            "round_1_a",
            "round_1_b",
            "round_2_title",
            "round_2_a",
            "round_2_b",
            "round_3_title",
            "round_3_a",
            "round_3_b",
            "round_4_title",
            "round_4_a",
            "round_4_b",
            "item_a",
            "item_b",
            "conclusion",
            "affiliate_comment",
        ]
        for field in fields:
            pattern = rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*?)"\s*(?:,|\}})'
            m = re.search(pattern, clean, re.DOTALL)
            if m:
                val = m.group(1).replace('\\"', '"').replace("\\n", "\n")
                data[field] = val

        if "hook" in data and ("item_a" in data or "round_1_a" in data):
            return data

        sanitized = re.sub(r"[\r\n]+", "\\n", clean)
        return json.loads(sanitized)

    def generate_fresh_topic_idea(
        self,
        category: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Uses Gemini to invent a brand new, trending, highly viral comparison topic on demand."""
        cat_hint = f"ในหมวดหมู่: {category}" if category and category != "ทั้งหมด (สุ่มทุกหมวด)" else "เลือกหมวดหมู่ที่เป็นกระแสไวรัลในไทย (ของกิน, เครื่องดื่ม, แกดเจ็ต, ของใช้, สุขภาพ, การเงิน)"
        fw_hint = f"ใช้กรอบจิตวิทยา: {framework}" if framework and framework != "all" else "เลือกกรอบจิตวิทยาที่น่าสนใจ (เช่น persona, budget_vs_luxury, crossover, perfect_pairing, science_myth)"

        prompt = f"""คุณคือ Senior Viral Content Strategist ของช่องวิดีโอสั้น 'แตกต่างกันอย่างไร / Why It Works'
โปรดคิดหัวข้อเปรียบเทียบ (VS / Pairing) ที่สดใหม่ แปลกใหม่ ชวนสงสัย และมีโอกาสเป็นไวรัลสูงมาก 1 หัวข้อ
เงื่อนไข:
- {cat_hint}
- {fw_hint}
- ต้องเป็นของ 2 สิ่งที่คนไทยรู้จักดี เคยสงสัย หรือกำลังถกเถียงกันในชีวิตประจำวัน
- ชื่อไอเทม A และ B ต้องชัดเจน เป็นรูปธรรม จับต้องได้ ไม่ใช่นามธรรม

ตอบกลับเป็น JSON Schema นี้เท่านั้น:
{{
  "framework": "{framework if framework and framework != 'all' else 'persona'}",
  "category": "{category if category and category != 'ทั้งหมด (สุ่มทุกหมวด)' else '☕ เครื่องดื่ม & อาหาร'}",
  "topic": "ชื่อหัวข้อคลิปที่ดึงดูด น่าคลิกดู (เช่น กาแฟส้ม VS กาแฟมะพร้าว หรือ ทำไมกินสิ่งนี้คู่กันแล้วดี)",
  "name_a": "ชื่อไอเทม A พร้อมคำขยายสั้นๆ",
  "name_b": "ชื่อไอเทม B พร้อมคำขยายสั้นๆ",
  "details_a": "จุดเด่น รสชาติ หรือสเปกของ A (1-2 ประโยค)",
  "details_b": "จุดเด่น รสชาติ หรือสเปกของ B (1-2 ประโยค)",
  "target_audience": "กลุ่มคนที่สนใจประเด็นนี้",
  "key_angles": "มิติเปรียบเทียบหลักที่ทำให้คนดูต้องหยุดดูจนจบ",
  "affiliate_link_a": "https://shopee.co.th",
  "affiliate_link_b": "https://shopee.co.th"
}}"""

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.88,
                "topP": 0.95,
                "maxOutputTokens": 800,
                "responseMimeType": "application/json",
            },
        }

        for url in self.endpoints:
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=18,
                )
                if response.status_code == 200:
                    data = response.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    raw_text = "".join([p.get("text", "") for p in parts if not p.get("thought")]).strip()
                    if raw_text:
                        parsed = self._clean_and_parse_json(raw_text)
                        if parsed.get("topic") and parsed.get("name_a") and parsed.get("name_b"):
                            return parsed
            except Exception as e:
                print(f"[AI] Fresh topic call error on {url}: {e}")

        # Fallback to random template
        return get_random_idea(category=category, framework=framework, use_ai=False)


# Curated High-Retention Trending Comparison Library across 8 Categories & 10 Frameworks
TRENDING_COMPARISON_TEMPLATES = [
    # 👤 Persona-based
    {
        "framework": "persona",
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "iPad Air VS iPad Pro (ใครเหมาะกับตัวไหน)",
        "name_a": "iPad Air",
        "name_b": "iPad Pro",
        "details_a": "ชิปแรง น้ำหนักเบา ราคาคุ้มค่า เหมาะสำหรับเรียน จดโน้ต และทำงานทั่วไป",
        "details_b": "หน้าจอ Tandem OLED 120Hz ProMotion กล้องคู่ ลำโพง 4 ตัว เหมาะกับครีเอเตอร์มืออาชีพ",
        "target_audience": "นักศึกษา คนทำงาน และสายกราฟิกที่กำลังตัดสินใจซื้อไอแพด",
        "key_angles": "ความคุ้มค่าของสเปกเทียบกับพฤติกรรมการใช้งานจริงของแต่ละคน",
        "affiliate_link_a": "https://shopee.co.th/ipad_air_official",
        "affiliate_link_b": "https://shopee.co.th/ipad_pro_official",
    },
    {
        "framework": "persona",
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "หูฟังทรง Earbuds VS หูฟัง In-Ear",
        "name_a": "หูฟังทรง Earbuds",
        "name_b": "หูฟังทรง In-Ear",
        "details_a": "แปะหูใส่สบายทั้งวัน ไม่อุดอู้ ได้ยินเสียงรอบข้าง ปลอดภัยเวลาเดินข้างนอก",
        "details_b": "จุกยางซีลหู ตัดเสียงรบกวนเงียบสนิท (ANC) เบสแน่น เหมาะกับคนชอบโลกส่วนตัว",
        "target_audience": "คนทำงานออฟฟิศ นักเรียน และสายเดินทางที่ใช้หูฟังทุกวัน",
        "key_angles": "ความสบายไม่อึดอัด เทียบกับสมาธิและการตัดเสียงรบกวนขั้นสุด",
        "affiliate_link_a": "https://shopee.co.th/earbuds_sample",
        "affiliate_link_b": "https://shopee.co.th/inear_sample",
    },

    # 🔀 Cross-over
    {
        "framework": "crossover",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "ชาเขียวมัทฉะแท้ VS กาแฟดำอเมริกาโน่",
        "name_a": "มัทฉะแท้เกรดพิธีการ",
        "name_b": "กาแฟดำอเมริกาโน่",
        "details_a": "มี L-Theanine ให้สมาธิต่อเนื่อง ไม่ใจสั่น คุมหิว สารต้านอนุมูลอิสระ EGCG สูง",
        "details_b": "กระตุ้นความตื่นตัวทันที เพิ่มอัตราการเผาผลาญ 0 แคลอรี่ ชงง่ายหาซื้อง่าย",
        "target_audience": "สายรักสุขภาพ คนคุมน้ำหนัก และวัยทำงานที่ต้องการโฟกัสทำงานทั้งวัน",
        "key_angles": "พลังงานที่นิ่งต่อเนื่องยาวนาน เทียบกับความตื่นตัวฉับพลัน",
        "affiliate_link_a": "https://shopee.co.th/ceremonial_matcha",
        "affiliate_link_b": "https://shopee.co.th/specialty_coffee_beans",
    },
    {
        "framework": "crossover",
        "category": "💄 สุขภาพ & บิวตี้",
        "topic": "เวย์โปรตีนเชค VS ไข่ต้ม 5 ฟอง",
        "name_a": "เวย์โปรตีนชงดื่ม",
        "name_b": "ไข่ต้ม CP / ตลาดสด",
        "details_a": "ได้โปรตีน 25-30 กรัมใน 1 สกู๊ป ดื่มง่ายใน 30 วินาที ดูดซึมไว เหมาะหลังเล่นเวททันที",
        "details_b": "อาหารธรรมชาติ 100% มีวิตามิน แร่ธาตุ ไขมันดี อิ่มท้องนาน ต้นทุนประหยัดมาก",
        "target_audience": "คนเริ่มออกกำลังกาย สร้างกล้ามเนื้อ และคนคุมอาหาร",
        "key_angles": "ความสะดวกสะดวกรวดเร็ว เทียบกับคุณค่าอาหารธรรมชาติและต้นทุนต่อวัน",
        "affiliate_link_a": "https://shopee.co.th/whey_protein",
        "affiliate_link_b": "https://shopee.co.th/boiled_eggs",
    },

    # 💰 Cost vs Value
    {
        "framework": "cost_value",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "ชงกาแฟกินเองที่บ้าน VS ซื้อกาแฟสดร้านดังทุกวัน",
        "name_a": "ชงดื่มเองที่บ้าน",
        "name_b": "ซื้อกาแฟสดร้านดัง",
        "details_a": "ต้นทุนเมล็ดเกรดพรีเมียมแก้วละ 15-25 บาท ค่าอุปกรณ์คืนทุนใน 3 เดือนแรก",
        "details_b": "แก้วละ 65-150 บาท ปีนึงจ่าย 25,000-50,000 บาท แลกกับไม่ต้องล้าง ไม่ต้องชงเอง",
        "target_audience": "คนทำงานออฟฟิศที่ติดกาแฟทุกเช้า และอยากวางแผนการเงินเก็บเงินแสน",
        "key_angles": "คำนวณเงินเหลือเก็บใน 1 ปี และจุดคุ้มทุนค่าอุปกรณ์",
        "affiliate_link_a": "https://shopee.co.th/home_coffee_maker",
        "affiliate_link_b": "https://shopee.co.th/coffee_shop_card",
    },
    {
        "framework": "cost_value",
        "category": "🚗 ยานยนต์ & การเดินทาง",
        "topic": "รถยนต์ไฟฟ้า (EV) VS รถยนต์น้ำมัน (คำนวณ 5 ปี)",
        "name_a": "รถยนต์ไฟฟ้า (EV)",
        "name_b": "รถยนต์น้ำมัน (ICE)",
        "details_a": "ค่าไฟกิโลเมตรละ 0.6-0.9 บาท เช็กระยะถูก แต่มีค่าเบี้ยประกันและเสื่อมราคาแบตเตอรี่",
        "details_b": "ค่าน้ำมันกิโลเมตรละ 2.5-3.5 บาท ซ่อมบำรุงมีช่างทั่วไป อะไหล่หาง่าย เติมไวใน 3 นาที",
        "target_audience": "คนที่กำลังจะออกรถคันใหม่ หรือขับรถวันละเกิน 50 กิโลเมตร",
        "key_angles": "ส่วนต่างค่าพลังงาน 5 ปีเทียบกับค่าเบี้ยประกันและราคาขายต่อ",
        "affiliate_link_a": "https://shopee.co.th/ev_charger",
        "affiliate_link_b": "https://shopee.co.th/car_accessories",
    },

    # 🚗 ยานยนต์ & การเดินทาง (New Category)
    {
        "framework": "persona",
        "category": "🚗 ยานยนต์ & การเดินทาง",
        "topic": "ยางรถยนต์นุ่มเงียบ (Comfort) VS ยางรถยนต์สปอร์ตหนึบ (Sport)",
        "name_a": "ยางสายนุ่มเงียบ (Comfort)",
        "name_b": "ยางสายสปอร์ตหนึบ (Sport Performance)",
        "details_a": "ร่องยางละเอียด ซับแรงสะเทือนดีเยี่ยม เสียงในห้องโดยสารเงียบ เหมาะขับในเมืองทางเรียบ",
        "details_b": "แก้มยางแน่น รีดน้ำไว เข้าโค้งคม เบรกสั้น มั่นใจในความเร็วสูงและถนนเปียก",
        "target_audience": "คนมีรถยนต์ที่กำลังจะเปลี่ยนยางชุดใหม่ตามระยะ",
        "key_angles": "ความนุ่มนวลสบายหู เทียบกับความปลอดภัยและสมรรถนะการควบคุม",
        "affiliate_link_a": "https://shopee.co.th/comfort_tires",
        "affiliate_link_b": "https://shopee.co.th/sport_tires",
    },

    # 💼 การเงิน & ไลฟ์สไตล์ (New Category)
    {
        "framework": "cost_value",
        "category": "💼 การเงิน & ไลฟ์สไตล์",
        "topic": "รูดผ่อน 0% 10 เดือน VS จ่ายเงินสดเต็มจำนวน",
        "name_a": "รูดผ่อน 0% 10 เดือน",
        "name_b": "จ่ายสดเต็มจำนวน",
        "details_a": "เงินก้อนยังอยู่ในบัญชีดอกเบี้ยสูง/กองทุน ได้แต้มสะสมและแคชแบ็กบัตรเครดิต",
        "details_b": "จบหนี้ทันที ไม่สร้างภาระผูกพัน ไม่เสี่ยงต่อการใช้จ่ายเกินตัว สบายใจไร้กังวล",
        "target_audience": "วัยทำงาน และคนที่กำลังวางแผนซื้อของชิ้นใหญ่หลักหมื่น",
        "key_angles": "ผลตอบแทนจากการหมุนเงิน เทียบกับวินัยทางการเงินและความสบายใจ",
        "affiliate_link_a": "https://shopee.co.th/credit_card_deal",
        "affiliate_link_b": "https://shopee.co.th/savings_app",
    },
    {
        "framework": "scenario_budget",
        "category": "💼 การเงิน & ไลฟ์สไตล์",
        "topic": "คอนโดติดรถไฟฟ้า VS บ้านเดี่ยวชานเมือง (งบ 3-4 ล้าน)",
        "name_a": "คอนโดติดแนวรถไฟฟ้า",
        "name_b": "บ้านเดี่ยว/ทาวน์โฮมชานเมือง",
        "details_a": "ประหยัดเวลาเดินทางวันละ 2 ชั่วโมง ใกล้แหล่งงาน ปล่อยเช่าง่าย คุมค่าเดินทางได้",
        "details_b": "ได้พื้นที่ใช้สอย 3-4 เท่า มีสวน มีที่จอดรถส่วนตัว เลี้ยงสัตว์ได้ เหมาะกับครอบครัว",
        "target_audience": "คนทำงานรุ่นใหม่และคู่รักที่กำลังเริ่มต้นซื้ออสังหาริมทรัพย์ชิ้นแรก",
        "key_angles": "ต้นทุนเวลาและค่าเดินทาง เทียบกับพื้นที่ใช้สอยและความสุขของครอบครัว",
        "affiliate_link_a": "https://shopee.co.th/condo_decor",
        "affiliate_link_b": "https://shopee.co.th/home_garden",
    },

    # 🎮 เกมมิ่ง & สตรีมมิ่ง (New Category)
    {
        "framework": "price_tier",
        "category": "🎮 เกมมิ่ง & สตรีมมิ่ง",
        "topic": "จอคอม IPS 180Hz VS จอเกมมิ่ง OLED 240Hz",
        "name_a": "จอ IPS 180Hz (หลักพัน)",
        "name_b": "จอ OLED 240Hz (หลักหมื่น)",
        "details_a": "ราคาจับต้องได้ง่าย สีสันตรง ไม่ต้องกังวลเรื่องจอเบิร์นอิน ตอบสนองลื่นไหลเพียงพอ",
        "details_b": "Contrast อนันต์ สีดำสนิท Response Time 0.03ms ไร้โกสต์ ภาพสวยสมจริงระดับเทพ",
        "target_audience": "เกมเมอร์ สายอีสปอร์ต และคนที่กำลังจัดโต๊ะคอมใหม่",
        "key_angles": "ความคุ้มค่าของจอราคาประหยัด เทียบกับมิติภาพและรีเฟรชเรทระดับสุดยอด",
        "affiliate_link_a": "https://shopee.co.th/ips_monitor",
        "affiliate_link_b": "https://shopee.co.th/oled_monitor",
    },

    # 🐾 สัตว์เลี้ยง & ของใช้หมาแมว (New Category)
    {
        "framework": "myth_vs_reality",
        "category": "🐾 สัตว์เลี้ยง & ของใช้หมาแมว",
        "topic": "อาหารแมวเกรด Holistic VS อาหารแมวตลาดทั่วไป",
        "name_a": "อาหารเกรด Holistic Grain-Free",
        "name_b": "อาหารแมวเกรด Commercial ทั่วไป",
        "details_a": "เนื้อสัตว์แท้ไม่มีเศษกระดูก โซเดียมต่ำ ลดความเสี่ยงโรคไตระยะยาว ขนแน่นเงางาม",
        "details_b": "ราคาประหยัด หาซื้อง่าย กลิ่นหอมกระตุ้นความอยากอาหารของน้องแมวได้ดี",
        "target_audience": "ทาสแมว และคนที่อยากดูแลสุขภาพสัตว์เลี้ยงระยะยาว",
        "key_angles": "ค่ายาค่ารักษาโรคไตในอนาคต เทียบกับส่วนต่างราคาค่าอาหารต่อเดือน",
        "affiliate_link_a": "https://shopee.co.th/holistic_cat_food",
        "affiliate_link_b": "https://shopee.co.th/daily_cat_food",
    },

    # 🙈 Blind Test / Experiment
    {
        "framework": "blind_test",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "กาแฟคั่วบด 100 บาท VS เมล็ด Geisha แก้วละ 250 บาท",
        "name_a": "เมล็ดคั่วบดหลักร้อย",
        "name_b": "เมล็ดประกวด Geisha หลักพัน",
        "details_a": "รสชาติเข้มข้น หอมมาตรฐาน ชงเติมนมหรือดื่มดำก็อร่อย คุ้มค่าเงิน",
        "details_b": "กลิ่นฟลอรัลดอกไม้สีขาว โทนซิตรัสซับซ้อน ได้คะแนน Cupping 88+ ลื่นคอสุดๆ",
        "target_audience": "คอกาแฟและคนที่สงสัยว่ากาแฟแพงๆ มีดีจริงหรือแค่อุปทานหมู่",
        "key_angles": "ถ้าปิดตาชิม คนทั่วไปแยกโน้ตดอกไม้กับกาแฟปกติออกจริงไหม",
        "affiliate_link_a": "https://shopee.co.th/daily_beans",
        "affiliate_link_b": "https://shopee.co.th/geisha_specialty",
    },

    # 🎯 Scenario / Budget
    {
        "framework": "scenario_budget",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "งบ 1,000 บาท: หม้อต้ม Moka Pot VS เซ็ตดริปเปอร์พร้อมตาชั่ง",
        "name_a": "หม้อต้ม Moka Pot สไตล์เข้ม",
        "name_b": "เซ็ตดริปเปอร์ V60 พร้อมตาชั่ง",
        "details_a": "สกัดกาแฟได้เข้มข้นคล้ายเอสเพรสโซ่ ชงเมนูนมอร่อย ทนทานใช้งานได้ตลอดชีพ",
        "details_b": "เรียนรู้ศาสตร์การสกัดได้ลึกซึ้ง ได้กาแฟใสหอมกรุ่น คุมรสชาติได้ละเอียดทุกหยด",
        "target_audience": "มือใหม่งบจำกัดที่อยากเริ่มทำกาแฟดื่มเองที่บ้านด้วยงบ 1,000 บาท",
        "key_angles": "ความครอบคลุมเมนู และความคุ้มค่าที่จะจบในงบ 1,000 บาท",
        "affiliate_link_a": "https://shopee.co.th/mokapot_set",
        "affiliate_link_b": "https://shopee.co.th/v60_drip_set",
    },

    # 🏷️ Price Tier
    {
        "framework": "price_tier",
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "ไมค์ไวร์เลสหลักร้อย VS ไมค์ไวร์เลสแบรนด์ดังหลักหมื่น",
        "name_a": "ไมค์ไร้สายหลักร้อย (Budget Wireless)",
        "name_b": "ไมค์สตูดิโอระดับหมื่น (Pro Wireless)",
        "details_a": "ใช้งานง่าย เสียบแล้วติดทันที ตัดเสียงรบกวนพอใช้ เหมาะกับมือใหม่เริ่มทำคลิป",
        "details_b": "มี Safety Track บันทึกเสียงสำรองในตัว ระยะส่ง 250 ม. คลื่น 2.4GHz เสถียรสูง",
        "target_audience": "ครีเอเตอร์ คนทำคลิป TikTok / Reels ที่กำลังเลือกซื้อไมค์ติดเสื้อ",
        "key_angles": "คุณภาพเสียงที่คนดูในมือถือฟังออกจริงไหม เทียบกับส่วนต่างราคา 10 เท่า",
        "affiliate_link_a": "https://shopee.co.th/budget_mic",
        "affiliate_link_b": "https://shopee.co.th/pro_mic",
    },

    # ⏳ Old School vs Modern
    {
        "framework": "old_vs_modern",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "กาแฟดริปมือสโลว์ไลฟ์ VS กาแฟแคปซูลทันใจ",
        "name_a": "กาแฟดริปมือ (Manual Drip)",
        "name_b": "กาแฟแคปซูล (Capsule Machine)",
        "details_a": "กลิ่นอโรม่าหอมกรุ่น สุนทรียภาพ ได้รสสัมผัสเมล็ดแท้ ละเมียดละไม ได้ควบคุมทุกขั้นตอน",
        "details_b": "สะดวกเร็วใน 1 นาที รสชาติคงที่มาตรฐานทุกแก้ว ล้างทำความสะอาดง่าย ไม่เลอะเทอะ",
        "target_audience": "คนรักกาแฟ และคนทำงานเช้าที่ต้องการคาเฟอีนคุณภาพ",
        "key_angles": "ความสุนทรีย์ในการชง เทียบกับความสะดวกรวดเร็วในชั่วโมงเร่งด่วน",
        "affiliate_link_a": "https://shopee.co.th/sample_drip",
        "affiliate_link_b": "https://shopee.co.th/sample_capsule",
    },

    # 💡 Myth vs Reality
    {
        "framework": "myth_vs_reality",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "กาแฟคั่วเข้ม VS กาแฟคั่วอ่อน (ใครคาเฟอีนแรงกว่า?)",
        "name_a": "กาแฟคั่วเข้ม (Dark Roast)",
        "name_b": "กาแฟคั่วอ่อน (Light Roast)",
        "details_a": "รสเข้ม ขม บอดี้หนัก มีกลิ่นสโมคกี้ แต่คาเฟอีนระเหิดไปตามความร้อนบางส่วน",
        "details_b": "รสเปรี้ยวผลไม้ บอดี้บาง แต่โมเลกุลคาเฟอีนคงอยู่ครบกว่าเมื่อเทียบตามน้ำหนักเมล็ด",
        "target_audience": "คนชอบดื่มกาแฟ และคนที่เข้าใจผิดว่ากาแฟขมแปลว่าคาเฟอีนเยอะ",
        "key_angles": "หลักการวิทยาศาสตร์เรื่องคาเฟอีนเทียบกับความรู้สึกขมที่ปลายลิ้น",
        "affiliate_link_a": "https://shopee.co.th/dark_roast_beans",
        "affiliate_link_b": "https://shopee.co.th/light_roast_beans",
    },

    # 🇹🇭 Local vs Import
    {
        "framework": "local_vs_import",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "เมล็ดไทยเกรดประกวดแม่จันใต้ VS เมล็ดนอก Ethiopia Yirgacheffe",
        "name_a": "เมล็ดไทยแม่จันใต้ (Thai Specialty)",
        "name_b": "เมล็ดเอธิโอเปีย (Ethiopia Yirgacheffe)",
        "details_a": "รสชาติดอกไม้ป่า หวานฉ่ำปลาย คั่วสดใหม่จากดอยในไทย ไม่ต้องผ่านภาษีนำเข้ามหาโหด",
        "details_b": "เอกลักษณ์ความหอมเบอร์กาม็อตและชามะลิระดับโลก แหล่งกำเนิดกาแฟที่คอกาแฟต้องลอง",
        "target_audience": "สายกาแฟ Specialty และคนที่อยากเปิดใจอุดหนุนเกษตรกรไทย",
        "key_angles": "ความสดใหม่และคุณภาพเทียบกับต้นทุนค่าขนส่งข้ามทวีป",
        "affiliate_link_a": "https://shopee.co.th/thai_specialty_coffee",
        "affiliate_link_b": "https://shopee.co.th/ethiopia_coffee_beans",
    },

    # 🔥 Hype vs Standard
    {
        "framework": "hype_vs_standard",
        "category": "🏠 ของใช้ในบ้าน & ครัว",
        "topic": "หม้อทอดไร้น้ำมัน VS เตาอบลมร้อนมาตรฐาน",
        "name_a": "หม้อทอดไร้น้ำมัน (Air Fryer)",
        "name_b": "เตาอบลมร้อน (Convection Oven)",
        "details_a": "ลมร้อนหมุนเวียนเร็ว อาหารกรอบไวใน 10 นาที รีดน้ำมันหยดทิ้ง เหมาะมื้อด่วน 1-2 คน",
        "details_b": "พื้นที่กว้าง ทำอาหารได้หลายอย่างพร้อมกัน ย่างไก่ทั้งตัว อบเบเกอรี่เนียนสม่ำเสมอ",
        "target_audience": "คนอยู่คอนโด แม่บ้าน และคนที่ชอบทำอาหารคลีนทานเองที่บ้าน",
        "key_angles": "กระแสทอดไร้น้ำมันที่คนฮิต เทียบกับความหลากหลายและคุ้มค่าของเตาอบจริง",
        "affiliate_link_a": "https://shopee.co.th/airfryer_deal",
        "affiliate_link_b": "https://shopee.co.th/oven_deal",
    },
    # 🌍 Country Matchup
    {
        "framework": "country_matchup",
        "category": "🌍 ภูมิรัฐศาสตร์ & ยุคสมัย",
        "topic": "ไทย VS กัมพูชา (เทียบศักยภาพ กองทัพ, เศรษฐกิจ, การศึกษา)",
        "name_a": "ประเทศไทย (Thailand)",
        "name_b": "ประเทศกัมพูชา (Cambodia)",
        "details_a": "อันดับ Global Firepower สูงกว่า งบประมาณกลาโหม 2 แสนล้าน ขนาด GDP 5 แสนล้านดอลลาร์ อุตสาหกรรมรถยนต์และการแพทย์ชั้นนำ",
        "details_b": "อัตราการเติบโตทางเศรษฐกิจ (GDP Growth) รวดเร็ว มีแรงดึงดูดการลงทุนจากจีน และค่าจ้างแรงงานที่แข่งขันได้",
        "target_audience": "คนที่สนใจสถานการณ์รอบบ้าน การเมืองระหว่างประเทศ และข้อเท็จจริงเชิงสถิติ",
        "key_angles": "สถิติอันดับกองทัพโลก ขนาดเศรษฐกิจ GDP ต่อหัว และดัชนีการศึกษาแบบเป็นกลาง",
        "affiliate_link_a": "https://shopee.co.th/world_atlas_book",
        "affiliate_link_b": "https://shopee.co.th/asean_history_book",
    },
    {
        "framework": "country_matchup",
        "category": "🌍 ภูมิรัฐศาสตร์ & ยุคสมัย",
        "topic": "ไทย VS เวียดนาม (ศึกแย่งชิงฐานการผลิตและ FDI)",
        "name_a": "ประเทศไทย (Thailand)",
        "name_b": "ประเทศเวียดนาม (Vietnam)",
        "details_a": "โครงสร้างพื้นฐานคมนาคมยอดเยี่ยม โลจิสติกส์เชื่อมต่อ EEC และซัพพลายเชนชิ้นส่วนยานยนต์ที่แข็งแกร่งที่สุดในอาเซียน",
        "details_b": "ประชากรวัยแรงงานมหาศาล ข้อตกลงการค้าเสรี (FTA) กับยุโรป-สหรัฐฯ และฐานผลิตอิเล็กทรอนิกส์/เซมิคอนดักเตอร์ระดับโลก",
        "target_audience": "วัยทำงาน นักลงทุน และคนที่ติดตามทิศทางเศรษฐกิจอาเซียน",
        "key_angles": "โครงสร้างพื้นฐาน กำลังคน ค่าแรง และการดึงดูดทุนต่างชาติ (FDI)",
        "affiliate_link_a": "https://shopee.co.th/investment_book_thai",
        "affiliate_link_b": "https://shopee.co.th/economy_trend_book",
    },

    # ⏳ Era Timeline
    {
        "framework": "era_timeline",
        "category": "🌍 ภูมิรัฐศาสตร์ & ยุคสมัย",
        "topic": "วิถีชีวิตไทยยุค 90s VS ยุคปัจจุบัน 2020s",
        "name_a": "ชีวิตยุค 90s (Slow Life & Analog)",
        "name_b": "ชีวิตยุค 2020s (Fast Pace & Digital)",
        "details_a": "โทรศัพท์บ้าน รอฟังเพลงจากวิทยุ ตู้เกม เพจเจอร์ ความสัมพันธ์แบบไม่เร่งรีบ มีเสน่ห์ความทรงจำ",
        "details_b": "สมาร์ตโฟน อินเทอร์เน็ต 5G สั่งอาหารส่งถึงหน้าบ้าน ทำงานแบบ Remote สบายกว่าแต่สมาธิสั้นลง",
        "target_audience": "วัยรุ่นยุค 90s คนเจน Y/Z และคนที่ชอบเรื่องราว Nostalgia ย้อนวันวาน",
        "key_angles": "เสน่ห์ความผูกพันในอดีต เทียบกับความสะดวกสบายขั้นสุดในยุคดิจิทัล",
        "affiliate_link_a": "https://shopee.co.th/retro_game_console",
        "affiliate_link_b": "https://shopee.co.th/smart_gadget_deal",
    },

    # 🤝 Perfect Pairing (จับคู่ของที่เข้ากัน)
    {
        "framework": "perfect_pairing",
        "category": "🤝 จับคู่ของที่เข้ากัน (Perfect Pairing)",
        "topic": "กาแฟดำ + น้ำมะพร้าว (ทำไมคู่นี้ถึงฮิตระเบิด)",
        "name_a": "กาแฟดำ (Black Coffee / Espresso)",
        "name_b": "น้ำมะพร้าวสด (Fresh Coconut Water)",
        "details_a": "ความเข้ม ขม หอมกรุ่นของกาแฟคั่ว และคาเฟอีนช่วยปลุกสมอง",
        "details_b": "ความหวานละมุนธรรมชาติ กลิ่นหอมนุ่ม และเกลือแร่โพแทสเซียมช่วยเติมความสดชื่น ตัดความขมของกาแฟได้กลมกล่อม",
        "target_audience": "สายสุขภาพ คอกาแฟ และคนที่อยากดื่มกาแฟสดชื่นแบบไม่ใส่น้ำตาลสังเคราะห์",
        "key_angles": "ความขมตัดความหวานธรรมชาติ กลไกคาเฟอีนเสริมเกลือแร่ ดื่มง่ายไม่อ้วน",
        "affiliate_link_a": "https://shopee.co.th/coffee_beans_deal",
        "affiliate_link_b": "https://shopee.co.th/coconut_water_100",
    },
    {
        "framework": "perfect_pairing",
        "category": "🤝 จับคู่ของที่เข้ากัน (Perfect Pairing)",
        "topic": "มัทฉะแท้ + นมข้าวโอ๊ต (Oat Milk Matcha Latte)",
        "name_a": "มัทฉะเกรดพิธีการ (Ceremonial Matcha)",
        "name_b": "นมข้าวโอ๊ต (Barista Oat Milk)",
        "details_a": "รสอูมามิแท้ กลิ่นหอมใบชาเข้มข้น และสาร L-Theanine ช่วยให้โฟกัสนิ่ง",
        "details_b": "เนื้อสัมผัสครีมมี่ รสมอลต์หวานธรรมชาติ ไม่กลบกลิ่นหญ้าและกลิ่นชาเขียวเหมือนนมวัว",
        "target_audience": "สายมัทฉะ คนแพ้นมวัว (Lactose Intolerance) และสายคาเฟ่",
        "key_angles": "การชูรสอูมามิของมัทฉะ ความครีมมี่ของนมโอ๊ตที่ไม่บดบังกลิ่นชา",
        "affiliate_link_a": "https://shopee.co.th/ceremonial_matcha",
        "affiliate_link_b": "https://shopee.co.th/oat_milk_barista",
    },
    {
        "framework": "perfect_pairing",
        "category": "🤝 จับคู่ของที่เข้ากัน (Perfect Pairing)",
        "topic": "หมูสามชั้นย่าง + กิมจิหมักสด (ทำไมกินคู่กันแล้วไม่เลี่ยน)",
        "name_a": "หมูสามชั้นย่างเกรียม (Grilled Pork Belly)",
        "name_b": "กิมจิผักกาดขาวหมักสด (Fresh Kimchi)",
        "details_a": "ความมัน ฉ่ำ กรอบนอกนุ่มใน รสเค็มมันเข้มข้นจากเนื้อและไขมัน",
        "details_b": "กรดแลคติกตามธรรมชาติ ความเปรี้ยวซ่า เผ็ดร้อน ช่วยตัดเลี่ยนไขมันทันที พร้อมโพรไบโอติกช่วยย่อย",
        "target_audience": "สายปิ้งย่าง สายอาหารเกาหลี และคนชอบกินของอร่อย",
        "key_angles": "กลไกกรดเปรี้ยวซ่าตัดเลี่ยนไขมัน ความลงตัวของรสสัมผัสและสุขภาพทางเดินอาหาร",
        "affiliate_link_a": "https://shopee.co.th/bbq_grill_pan",
        "affiliate_link_b": "https://shopee.co.th/korean_kimchi_fresh",
    },
    {
        "framework": "perfect_pairing",
        "category": "🤝 จับคู่ของที่เข้ากัน (Perfect Pairing)",
        "topic": "iPhone + Apple Watch (ทำไมใช้คู่กันแล้วตัดไม่ขาด)",
        "name_a": "iPhone (ศูนย์กลางการทำงานและประมวลผล)",
        "name_b": "Apple Watch (ส่วนขยายติดข้อมือตลอด 24 ชม.)",
        "details_a": "แอปพลิเคชัน กล้อง การเชื่อมต่อ และการจัดการข้อมูลหลัก",
        "details_b": "ตรวจจับการเต้นหัวใจ การนอนหลับ รับสายด่วน ปลดล็อกเครื่องอัตโนมัติ ไม่ต้องหยิบมือถือ",
        "target_audience": "สายเทคโนโลยี คนทำงาน และคนที่ใส่ใจสุขภาพ",
        "key_angles": "Ecosystem Synergy ความสะดวกสบายของการเชื่อมต่อที่ไร้รอยต่อ",
        "affiliate_link_a": "https://shopee.co.th/iphone_official",
        "affiliate_link_b": "https://shopee.co.th/apple_watch_official",
    },
    {
        "framework": "perfect_pairing",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "กาแฟช็อตเอสเปรสโซ + น้ำส้มสด (ทำไมเข้ากันอย่างลงตัว)",
        "name_a": "ช็อตเอสเปรสโซเข้มข้น (Espresso Shot)",
        "name_b": "น้ำส้มคั้นสดแท้ 100% (Fresh Orange Juice)",
        "details_a": "รสขมเข้ม บอดี้แน่น มีกลิ่นหอมอโรม่าคั่วบด",
        "details_b": "ความเปรี้ยวอมหวานจากกรดซิตริกธรรมชาติ ช่วยตัดความขมและชูรสฟรุตตี้ให้เด่นชัด",
        "target_audience": "คอกาแฟสายสดชื่น และคนที่เพิ่งเริ่มหัดดื่มกาแฟดำ",
        "key_angles": "Citrus & Coffee Synergy สัดส่วนความสดชื่นที่ไม่ต้องใส่น้ำตาลเพิ่ม",
        "affiliate_link_a": "https://shopee.co.th/coffee_beans",
        "affiliate_link_b": "https://shopee.co.th/orange_press",
    },
    {
        "framework": "persona",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "กาแฟ Cold Brew VS กาแฟ Iced Americano",
        "name_a": "กาแฟสกัดเย็น (Cold Brew)",
        "name_b": "อเมริกาโน่เย็น (Iced Americano)",
        "details_a": "แช่น้ำเย็น 12-18 ชม. กรดต่ำ รสนุ่มละมุน ไม่ระคายเคืองกระเพาะ ดื่มง่าย",
        "details_b": "สกัดด้วยน้ำร้อนแรงดันสูงแล้วเทลงน้ำแข็ง คาแรกเตอร์ชัด ขมเข้ม บอดี้แน่น",
        "target_audience": "คนทำงาน คอกาแฟ และคนที่มีปัญหากรดไหลย้อนหรือแสบท้อง",
        "key_angles": "ความเป็นกรดต่ำกับความนุ่มคอ เทียบกับความเข้มตื่นตัวฉับพลัน",
        "affiliate_link_a": "https://shopee.co.th/cold_brew_pot",
        "affiliate_link_b": "https://shopee.co.th/espresso_maker",
    },
    {
        "framework": "budget_vs_luxury",
        "category": "🏠 ของใช้ในบ้าน",
        "topic": "กระทะเหล็กหล่อ (Cast Iron) VS กระทะเคลือบหินอ่อน (Non-Stick)",
        "name_a": "กระทะเหล็กหล่อ (Cast Iron)",
        "name_b": "กระทะเคลือบหินอ่อน (Non-Stick)",
        "details_a": "กักเก็บความร้อนสูง ย่างสเต๊กเกรียมกรอบหอม ทนทานใช้ได้ชั่วลูกชั่วหลาน ยิ่งใช้ยิ่งลื่น",
        "details_b": "น้ำหนักเบา ไม่ต้องใช้น้ำมัน ทำความสะอาดง่าย แต่สารเคลือบมีอายุการใช้งาน 1-2 ปี",
        "target_audience": "สายทำอาหาร พ่อบ้านแม่บ้าน และคนรักสเต๊ก",
        "key_angles": "ความทนทานและการสะสมความร้อนระดับเชฟ เทียบกับความสะดวกล้างง่ายของมือใหม่",
        "affiliate_link_a": "https://shopee.co.th/cast_iron_pan",
        "affiliate_link_b": "https://shopee.co.th/nonstick_pan",
    },
    {
        "framework": "persona",
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "แปรงสีฟันไฟฟ้าโซนิค VS แปรงสีฟันขนนุ่มธรรมดา",
        "name_a": "แปรงสีฟันไฟฟ้าโซนิค (Sonic Toothbrush)",
        "name_b": "แปรงสีฟันขนนุ่มธรรมดา (Manual Toothbrush)",
        "details_a": "สั่น 30,000-40,000 ครั้ง/นาที กำจัดคราบพลัคได้ลึกกว่า 3 เท่า มีระบบจับเวลา 2 นาที",
        "details_b": "ราคาประหยัด ควบคุมน้ำหนักมือได้ตามใจ พกพาง่าย ไม่ต้องกังวลเรื่องชาร์จแบต",
        "target_audience": "คนที่รักสุขภาพฟัน คนจัดฟัน และคนอยากแก้ปัญหากลิ่นปากและหินปูน",
        "key_angles": "ประสิทธิภาพการขจัดคราบหินปูนและความสม่ำเสมอ เทียบกับความประหยัดและความคล่องตัว",
        "affiliate_link_a": "https://shopee.co.th/electric_toothbrush",
        "affiliate_link_b": "https://shopee.co.th/soft_toothbrush",
    },
    {
        "framework": "crossover",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "นมโอ๊ตบาริสต้า (Oat Milk) VS นมสดพาสเจอร์ไรส์ 100%",
        "name_a": "นมโอ๊ตบาริสต้า (Oat Milk Barista)",
        "name_b": "นมวัวพาสเจอร์ไรส์แท้ 100%",
        "details_a": "ไม่มีแลคโตส ใยอาหารเบต้ากลูแคนสูง รสมันนัวจากข้าวโอ๊ต เหมาะกับกาแฟคั่วกลาง-อ่อน",
        "details_b": "โปรตีนและแคลเซียมธรรมชาติสูง รสนมแท้กลมกล่อม ตีฟองครีมได้เนียนนุ่มและอยู่ตัวนาน",
        "target_audience": "คนแพ้นมวัว สายวีแกน และคนรักกาแฟลาเต้",
        "key_angles": "ความสบายท้องไร้แลคโตส เทียบกับสารอาหารโปรตีนและความมันนัวดั้งเดิม",
        "affiliate_link_a": "https://shopee.co.th/oat_milk",
        "affiliate_link_b": "https://shopee.co.th/fresh_milk",
    },
    {
        "framework": "persona",
        "category": "🏠 ของใช้ในบ้าน",
        "topic": "หุ่นยนต์ดูดฝุ่นถูพื้น VS เครื่องดูดฝุ่นไร้สายทรงพลัง",
        "name_a": "หุ่นยนต์ดูดฝุ่นอัตโนมัติ (Robot Vacuum)",
        "name_b": "เครื่องดูดฝุ่นไร้สาย (Cordless Vacuum)",
        "details_a": "ตั้งเวลาทำงานได้ทุกวัน หลบสิ่งกีดขวางด้วย LiDAR ดูดพร้อมถูและกลับแท่นชาร์จเอง",
        "details_b": "แรงดูดมหาศาล ดูดไรฝุ่นบนที่นอน ซอกโซฟา และผ้าม่านได้ทุกมุมห้อง สะอาดหมดจดทันใจ",
        "target_audience": "คนทำงานไม่มีเวลา คนเลี้ยงสัตว์ และคนรักความสะอาดแบบไร้ฝุ่น",
        "key_angles": "การประหยัดเวลาแบบอัตโนมัติ เทียบกับพลังการทำความสะอาดเฉพาะจุดที่ละเอียดกว่า",
        "affiliate_link_a": "https://shopee.co.th/robot_vacuum",
        "affiliate_link_b": "https://shopee.co.th/cordless_vacuum",
    },
    {
        "framework": "science_myth",
        "category": "💄 สุขภาพ & บิวตี้",
        "topic": "ครีมกันแดด Physical VS ครีมกันแดด Chemical",
        "name_a": "กันแดด Physical (แร่ธาตุสะท้อนแสง)",
        "name_b": "กันแดด Chemical (สารเคมีซับรังสี)",
        "details_a": "ใช้ Zinc Oxide / Titanium Dioxide เคลือบผิวสะท้อนรังสี UV ออก อ่อนโยน ไม่ระคายเคือง",
        "details_b": "เนื้อบางเบา ซึมไว ไม่วอก ไม่ขาวลอย เหมาะกับการทาก่อนแต่งหน้าและเล่นกีฬากลางแจ้ง",
        "target_audience": "คนผิวแพ้ง่าย เป็นสิว และคนที่ต้องเผชิญแดดเมืองไทยทุกวัน",
        "key_angles": "ความอ่อนโยนต่อผิวแพ้ง่าย เทียบกับความสบายผิวไม่เหนอะหนะ",
        "affiliate_link_a": "https://shopee.co.th/physical_sunscreen",
        "affiliate_link_b": "https://shopee.co.th/chemical_sunscreen",
    },
    {
        "framework": "budget_vs_luxury",
        "category": "🏠 ของใช้ในบ้าน",
        "topic": "หม้อหุงข้าวดิจิทัล (IH Smart Cooker) VS หม้อหุงข้าวไฟฟ้าธรรมดา",
        "name_a": "หม้อหุงข้าวดิจิทัลระบบแม่เหล็ก IH",
        "name_b": "หม้อหุงข้าวไฟฟ้าแผ่นความร้อนทั่วไป",
        "details_a": "ความร้อนกระจาย 360 องศา ข้าวสุกเรียงเม็ดนุ่มฟูสม่ำเสมอ คุมอุณหภูมิแม่นยำ หุงข้าวได้ทุกสายพันธุ์",
        "details_b": "ราคาหลักร้อย ใช้งานง่ายแค่กดสวิตช์เดียว ร้อนไว ประหยัดไฟ เหมาะกับหอพักและชีวิตง่ายๆ",
        "target_audience": "คนที่ให้ความสำคัญกับความอร่อยของข้าวสวย และครอบครัวยุคใหม่",
        "key_angles": "คุณภาพรสสัมผัสความฟูของเมล็ดข้าว เทียบกับความคุ้มค่าและใช้งานง่าย",
        "affiliate_link_a": "https://shopee.co.th/ih_rice_cooker",
        "affiliate_link_b": "https://shopee.co.th/basic_rice_cooker",
    },
    {
        "framework": "persona",
        "category": "💄 สุขภาพ & บิวตี้",
        "topic": "รองเท้าวิ่ง Max Cushion VS รองเท้าวิ่งทรง Barefoot",
        "name_a": "รองเท้าวิ่งพื้นหนานุ่ม (Max Cushion)",
        "name_b": "รองเท้าวิ่งมินิมอล (Barefoot Shoes)",
        "details_a": "โฟมหนานุ่ม ซับแรงกระแทกเข่าและข้อเท้าดีเยี่ยม วิ่งระยะไกลสบาย เหมาะกับคนน้ำหนักเยอะ",
        "details_b": "พื้นบางไร้ดรอป กระตุ้นการลงเท้าแบบธรรมชาติ เสริมสร้างกล้ามเนื้อฝ่าเท้าและเอ็นร้อยหวายให้แข็งแรง",
        "target_audience": "นักวิ่งทุกระดับ คนออกกำลังกาย และคนที่มีปัญหาปวดข้อเข่า",
        "key_angles": "การปกป้องลดแรงกระแทก เทียบกับการฝึกฝ่าเท้าตามสรีระธรรมชาติ",
        "affiliate_link_a": "https://shopee.co.th/max_cushion_shoes",
        "affiliate_link_b": "https://shopee.co.th/barefoot_shoes",
    },
    {
        "framework": "crossover",
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "ไข่ไก่สดฟาร์มเบอร์ 0 VS ไข่เป็ดไล่ทุ่ง",
        "name_a": "ไข่ไก่เบอร์ 0 สดพิเศษ",
        "name_b": "ไข่เป็ดไล่ทุ่งสด",
        "details_a": "ไข่ขาวโปรตีนแน่น คอเลสเตอรอลพอเหมาะ กลิ่นคาวน้อย เหมาะกับไข่ต้ม ไข่คน และอาหารทุกเมนู",
        "details_b": "ไข่แดงฟองโต สีส้มเข้มจัด มีไขมันดีและรสชาติมันนัวเข้มข้น เหมาะทำไข่ดาวกรอบและไข่พะโล้",
        "target_audience": "คนทำอาหาร สายฟิตเนส และคนรักไข่ดาวกรอบไข่แดงเยิ้ม",
        "key_angles": "ความเนียนละมุนของไข่ขาว เทียบกับความมันนัวเข้มข้นของไข่แดงเป็ด",
        "affiliate_link_a": "https://shopee.co.th/fresh_eggs",
        "affiliate_link_b": "https://shopee.co.th/duck_eggs",
    },
    {
        "framework": "persona",
        "category": "🏠 ของใช้ในบ้าน",
        "topic": "ที่นอนยางพาราแท้ 100% VS ที่นอนพ็อกเก็ตสปริง (Pocket Spring)",
        "name_a": "ที่นอนยางพาราแท้ 100%",
        "name_b": "ที่นอน Pocket Spring แยกอิสระ",
        "details_a": "รองรับสรีระกระดูกสันหลังตามน้ำหนัก ไม่สะสมไรฝุ่น ทนทานไม่ยุบตัวนาน 10-15 ปี",
        "details_b": "สปริงแยกจุด คนข้างๆ ขยับตัวไม่สะเทือน ระบายอากาศดี ไม่ร้อนหลัง นุ่มเด้งกำลังดี",
        "target_audience": "คนปวดหลัง ออฟฟิศซินโดรม และคนที่มีปัญหาเรื่องการนอนหลับ",
        "key_angles": "การพยุงแนวกระดูกลดอาการปวดเมื่อย เทียบกับการไม่สะเทือนคนข้างเคียงและการระบายความร้อน",
        "affiliate_link_a": "https://shopee.co.th/latex_mattress",
        "affiliate_link_b": "https://shopee.co.th/spring_mattress",
    },
]

CATEGORIES = list(dict.fromkeys(item["category"] for item in TRENDING_COMPARISON_TEMPLATES if "category" in item))


def get_random_idea(
    category: Optional[str] = None,
    framework: Optional[str] = None,
    use_ai: bool = False,
    seen_topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Returns a fresh high-retention comparison idea template or generates a fresh one via AI."""
    import random

    if use_ai:
        try:
            gen = AIScriptGenerator()
            return gen.generate_fresh_topic_idea(category=category, framework=framework)
        except Exception:
            pass

    pool = TRENDING_COMPARISON_TEMPLATES
    if category and category != "ทั้งหมด (สุ่มทุกหมวด)":
        filtered = [item for item in pool if item.get("category") == category]
        if filtered:
            pool = filtered
    if framework and framework != "all":
        filtered = [item for item in pool if item.get("framework") == framework]
        if filtered:
            pool = filtered

    # Avoid recently selected topics in this session
    if seen_topics:
        unseen = [item for item in pool if item.get("topic") not in seen_topics]
        if unseen:
            pool = unseen

    return random.choice(pool).copy()


if __name__ == "__main__":
    gen = AIScriptGenerator()
    res = gen.generate_script(
        topic="หูฟังไร้สาย VS หูฟังมีสาย",
        name_a="หูฟังไร้สาย (TWS)",
        name_b="หูฟังมีสาย (IEM)",
        details_a="เน้นตัดเสียงรบกวน พกพาง่าย แบต 6 ชม.",
        details_b="เน้นเสียงคมชัดระดับ Hi-Res ไม่ต้องชาร์จ ไม่ดีเลย์",
        key_angles="คุณภาพเสียงเทียบกับความคล่องตัว",
        target_audience="คนชอบฟังเพลงระหว่างเดินทางและทำงาน",
        framework="persona",
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
