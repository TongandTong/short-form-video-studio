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
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={self.api_key}"
        )
        self.fallback_endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={self.api_key}"
        )

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
    ) -> Dict[str, Any]:
        """
        Deep-researches comparison points and writes a 4-part short-form script in Thai.
        """
        prompt = f"""
คุณเป็น Senior Short-Form Video Producer และ Product Analyst มืออาชีพ เชี่ยวชาญการทำคลิปแนวตั้ง 9:16 (Reels/TikTok/Shorts) สไตล์ "Side-by-Side Comparison: A vs B" ที่คนดูจนจบและกดคลิกดูสินค้า

โจทย์เปรียบเทียบ:
- หัวข้อ: {topic}
- ไอเทม A: {name_a} (ข้อมูลเบื้องต้น: {details_a or 'ทั่วไป'})
- ไอเทม B: {name_b} (ข้อมูลเบื้องต้น: {details_b or 'ทั่วไป'})
- กลุ่มเป้าหมายคนดู: {target_audience or 'บุคคลทั่วไป / ผู้บริโภคที่กำลังตัดสินใจซื้อ'}
- จุดที่อยากเน้นเปรียบเทียบ: {key_angles or 'ความคุ้มค่า สเปกการใช้งานจริง และความสะดวก'}
- โทนอารมณ์: {tone} (น่าสนใจ มีน้ำหนักคำ ชวนฟัง กระชับ ไม่เวิ่นเว้อ)

ภารกิจของคุณ:
1. ทำ Deep Comparative Research วิเคราะห์เจาะลึก 4 มิติสำคัญ:
   - จุดแข็งเด่นชัด (Key Strengths)
   - จุดสังเกตหรือสิ่งที่ต้องยอมรับ (Trade-offs / ข้อจำกัด)
   - ความคุ้มค่าและราคาจริงในไทย
   - ฟันธง: ใครเหมาะกับ A และใครเหมาะกับ B
2. เขียนบทพากย์วิดีโอ 4 ท่อน (สั้น กระชับ สำหรับอ่านพากย์ 20-30 วินาที):
   - hook: ประโยคเปิดคลิป 1 ประโยค ยิงคำถามหรือประเด็นตรงจุด ชวนสงสัยให้อยู่ดูต่อ
   - item_a: เจาะจุดเด่นของ {name_a} ให้เห็นภาพชัดเจน ทำไมต้องตัวนี้ (1-2 ประโยคกระชับ)
   - item_b: เจาะจุดเด่นของ {name_b} ให้เห็นความต่าง ทำไมต้องตัวนี้ (1-2 ประโยคกระชับ)
   - conclusion: สรุปฟันธง พร้อมประโยค Call-To-Action (CTA) สไตล์ Affiliate แบบเนียนๆ ชวนคนดูโหวต และบอกว่าพิกัดของแท้อยู่ในคอมเมนต์แรกแล้ว
3. affiliate_comment: ข้อความสำหรับปักหมุดคอมเมนต์แรกใต้คลิป รวบรวมพิกัด {name_a} และ {name_b} จัดวางสวยงามพร้อมอีโมจิ

สำคัญมาก:
- ห้ามใส่เครื่องหมาย Enter หรือขึ้นบรรทัดใหม่จริงในค่า JSON string เด็ดขาด ให้ใช้ \\n เท่านั้น
- ตอบเป็น JSON block เท่านั้นในโครงสร้างนี้:

{{
  "topic": "{topic}",
  "name_a": "{name_a}",
  "name_b": "{name_b}",
  "research_summary": "สรุปข้อมูลเจาะลึก 4 มิติสั้นๆ เพื่อให้ผู้อ่านเข้าใจภาพรวม...",
  "hook": "ประโยคเปิดคลิป...",
  "item_a": "ประโยคอธิบายไอเทม A...",
  "item_b": "ประโยคอธิบายไอเทม B...",
  "conclusion": "ประโยคสรุปฟันธงและ CTA เนียนๆ...",
  "affiliate_comment": "📍 พิกัดของแท้ราคาโปร:\\n👉 {name_a}: [ลิงก์ A]\\n👉 {name_b}: [ลิงก์ B]\\n(โหวตกันในคอมเมนต์ได้เลยครับ)"
}}
"""
        return self._call_gemini(prompt, affiliate_link_a, affiliate_link_b, topic, name_a, name_b)

    def rewrite_script(
        self,
        current_script: Dict[str, Any],
        instruction: str,
        tone: str = "engaging",
    ) -> Dict[str, Any]:
        """
        Rewrites or polishes an existing script according to user's feedback.
        """
        prompt = f"""
คุณเป็น Senior Video Script Doctor มีบทเปรียบเทียบเดิมดังนี้:
หัวข้อ: {current_script.get('topic', '')}
สินค้า A: {current_script.get('name_a', '')}
สินค้า B: {current_script.get('name_b', '')}

บทเดิม:
- Hook: {current_script.get('hook', '')}
- Item A: {current_script.get('item_a', '')}
- Item B: {current_script.get('item_b', '')}
- Conclusion: {current_script.get('conclusion', '')}

คำสั่งปรับแก้จากผู้ใช้ (Instruction):
"{instruction}"
โทนที่ต้องการ: {tone}

โปรดรีไรท์บทใหม่ทั้ง 4 ท่อนให้ตรงตามคำสั่ง ปรับคำให้คมขึ้น น่าฟังขึ้น และจบด้วย CTA เนียนๆ เช่นเดิม
สำคัญ: ห้ามมี Enter จริงใน JSON string ให้ใช้ \\n เท่านั้น ตอบเฉพาะ JSON:

{{
  "topic": "{current_script.get('topic', '')}",
  "name_a": "{current_script.get('name_a', '')}",
  "name_b": "{current_script.get('name_b', '')}",
  "research_summary": "{current_script.get('research_summary', 'ปรับปรุงบทตามคำสั่งผู้ใช้')}",
  "hook": "บทเปิดใหม่...",
  "item_a": "บท A ใหม่...",
  "item_b": "บท B ใหม่...",
  "conclusion": "บทสรุปใหม่...",
  "affiliate_comment": "{current_script.get('affiliate_comment', '')}"
}}
"""
        return self._call_gemini(
            prompt,
            affiliate_link_a="",
            affiliate_link_b="",
            topic=current_script.get("topic", ""),
            name_a=current_script.get("name_a", ""),
            name_b=current_script.get("name_b", ""),
        )

    def _call_gemini(
        self,
        prompt: str,
        affiliate_link_a: str,
        affiliate_link_b: str,
        topic: str,
        name_a: str,
        name_b: str,
    ) -> Dict[str, Any]:
        """Helper to call Gemini REST API and parse response."""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.95,
                "maxOutputTokens": 2048,
                "responseMimeType": "application/json",
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        for url in [self.endpoint, self.fallback_endpoint]:
            try:
                response = requests.post(
                    url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=35,
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

        # Fallback template
        return {
            "topic": topic,
            "name_a": name_a,
            "name_b": name_b,
            "research_summary": f"เปรียบเทียบ {name_a} ด้านความยืดหยุ่นและการควบคุม กับ {name_b} ด้านความรวดเร็วและมาตรฐานสม่ำเสมอ",
            "hook": f"สองตัวนี้เลือกอะไรดี? มาดูความต่างระหว่าง {name_a} กับ {name_b} กันครับ!",
            "item_a": f"{name_a} โดดเด่นด้วยฟังก์ชันที่ครบครัน เหมาะกับคนที่ชอบความคุ้มค่าและปรับแต่งได้ตามใจ",
            "item_b": f"ส่วน {name_b} ตอบโจทย์เรื่องความง่าย รวดเร็ว และได้มาตรฐานคุณภาพที่คงที่ทุกครั้ง",
            "conclusion": "แล้วคุณล่ะชอบตัวไหนมากกว่ากัน? พิกัดราคาพิเศษของทั้งสองตัว ปักหมุดไว้ในคอมเมนต์เรียบร้อยแล้วครับ!",
            "affiliate_comment": f"📍 พิกัดของแท้ราคาโปร:\n👉 {name_a}: {affiliate_link_a or '[ใส่ลิงก์ A]'}\n👉 {name_b}: {affiliate_link_b or '[ใส่ลิงก์ B]'}\nโหวตกันในคอมเมนต์ได้เลยน้า!",
        }

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

        if "hook" in data and "item_a" in data:
            return data

        sanitized = re.sub(r"[\r\n]+", "\\n", clean)
        return json.loads(sanitized)


# Curated High-Retention Trending Comparison Library
TRENDING_COMPARISON_TEMPLATES = [
    # 📱 Gadget & Tech
    {
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "iPad Air VS iPad Pro",
        "name_a": "iPad Air",
        "name_b": "iPad Pro",
        "details_a": "ชิปแรง ประสิทธิภาพเกินพอ น้ำหนักเบา ราคาคุ้มค่าสำหรับเรียนและทำงานทั่วไป",
        "details_b": "หน้าจอ Tandem OLED 120Hz ProMotion กล้องดีกว่า ลำโพง 4 ตัว เหมาะกับครีเอเตอร์มืออาชีพ",
        "target_audience": "นักศึกษา คนทำงาน และสายกราฟิกที่กำลังตัดสินใจซื้อไอแพด",
        "key_angles": "ความคุ้มค่าของสเปกเทียบกับส่วนต่างราคาหลักหมื่น",
        "affiliate_link_a": "https://shopee.co.th/ipad_air_official",
        "affiliate_link_b": "https://shopee.co.th/ipad_pro_official",
    },
    {
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "หูฟังไร้สาย Earbuds VS หูฟัง In-Ear",
        "name_a": "หูฟังทรง Earbuds",
        "name_b": "หูฟังทรง In-Ear",
        "details_a": "แปะหูใส่สบาย ไม่อุดอู้ ได้ยินเสียงรอบข้าง ปลอดภัยเวลาเดินข้างนอก",
        "details_b": "จุกยางซีลหู ตัดเสียงรบกวนเงียบสนิท (ANC) เบสแน่นเต็มมิติ ฟังเพลงโฟกัสสุดๆ",
        "target_audience": "คนทำงานออฟฟิศ นักเรียน และสายเดินทางที่ใช้หูฟังทุกวัน",
        "key_angles": "ความสบายในการสวมใส่ทั้งวัน เทียบกับประสิทธิภาพการตัดเสียงรบกวน",
        "affiliate_link_a": "https://shopee.co.th/earbuds_sample",
        "affiliate_link_b": "https://shopee.co.th/inear_sample",
    },
    {
        "category": "📱 ไอที & แกดเจ็ต",
        "topic": "เมาส์เพื่อสุขภาพ (Ergonomic) VS เมาส์ทั่วไป",
        "name_a": "เมาส์ทรง Ergonomic",
        "name_b": "เมาส์ธรรมดาทั่วไป",
        "details_a": "ทรงแนวตั้ง 57 องศา ลดการบิดของกระดูกข้อมือ ป้องกันออฟฟิศซินโดรมระยะยาว",
        "details_b": "รูปทรงคุ้นมือ น้ำหนักเบา ควบคุมง่าย พกพาสะดวก ราคาเข้าถึงง่าย",
        "target_audience": "พนักงานออฟฟิศ โปรแกรมเมอร์ และคนที่ใช้คอมพิวเตอร์เกินวันละ 6 ชั่วโมง",
        "key_angles": "การแก้ปัญหาปวดข้อมือเรื้อรัง เทียบกับความเคยชินและความคล่องตัว",
        "affiliate_link_a": "https://shopee.co.th/ergo_mouse_promo",
        "affiliate_link_b": "https://shopee.co.th/normal_mouse_promo",
    },
    # ☕ Food & Drinks
    {
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "กาแฟดริป VS กาแฟแคปซูล",
        "name_a": "กาแฟดริป",
        "name_b": "กาแฟแคปซูล",
        "details_a": "กลิ่นอโรม่าหอมกรุ่น สุนทรียภาพ ได้รสสัมผัสเมล็ดแท้ ละเมียดละไม",
        "details_b": "สะดวกเร็วใน 1 นาที รสชาติคงที่มาตรฐานทุกแก้ว ล้างทำความสะอาดง่าย",
        "target_audience": "คนรักกาแฟ คนทำงานเช้าที่ต้องการคาเฟอีนคุณภาพ",
        "key_angles": "ความสุนทรีย์ในการชง เทียบกับความสะดวกรวดเร็วในชั่วโมงเร่งด่วน",
        "affiliate_link_a": "https://shopee.co.th/sample_drip",
        "affiliate_link_b": "https://shopee.co.th/sample_capsule",
    },
    {
        "category": "☕ เครื่องดื่ม & อาหาร",
        "topic": "ชาเขียวมัทฉะแท้ VS กาแฟดำอเมริกาโน่",
        "name_a": "มัทฉะแท้เกรดพิธีการ",
        "name_b": "กาแฟดำอเมริกาโน่",
        "details_a": "มี L-Theanine ให้สมาธิต่อเนื่อง ไม่ใจสั่น คุมหิว สารต้านอนุมูลอิสระ EGCG สูง",
        "details_b": "กระตุ้นความตื่นตัวทันที เพิ่มการเผาผลาญ 0 แคลอรี่ ชงง่ายหาซื้อง่าย",
        "target_audience": "สายรักสุขภาพ คนคุมน้ำหนัก และวัยทำงานที่อยากโฟกัสงาน",
        "key_angles": "พลังงานที่นิ่งต่อเนื่องแบบมัทฉะ เทียบกับความตื่นตัวเร็วแบบกาแฟดำ",
        "affiliate_link_a": "https://shopee.co.th/ceremonial_matcha",
        "affiliate_link_b": "https://shopee.co.th/specialty_coffee_beans",
    },
    # 🏠 Home & Living
    {
        "category": "🏠 ของใช้ในบ้าน & ครัว",
        "topic": "หม้อทอดไร้น้ำมัน VS เตาอบลมร้อน",
        "name_a": "หม้อทอดไร้น้ำมัน (Air Fryer)",
        "name_b": "เตาอบลมร้อน (Convection Oven)",
        "details_a": "ร้อนไว อาหารกรอบเร็ว รีดน้ำมันได้ดี เหมาะกับเมนูด่วน 1-2 คน ขนาดกะทัดรัด",
        "details_b": "ความจุเยอะ ทำอาหารได้พร้อมกันหลายอย่าง ทำเบเกอรี่และย่างไก่ทั้งตัวได้สม่ำเสมอ",
        "target_audience": "คนอยู่คอนโด แม่บ้าน และคนที่ชอบทำอาหารคลีนทานเองที่บ้าน",
        "key_angles": "ความสะดวกรวดเร็วในการทำมื้อด่วน เทียบกับความหลากหลายและความจุ",
        "affiliate_link_a": "https://shopee.co.th/airfryer_deal",
        "affiliate_link_b": "https://shopee.co.th/oven_deal",
    },
    {
        "category": "🏠 ของใช้ในบ้าน & ครัว",
        "topic": "เครื่องดูดฝุ่นไร้สาย VS หุ่นยนต์ดูดฝุ่น",
        "name_a": "เครื่องดูดฝุ่นไร้สาย",
        "name_b": "หุ่นยนต์ดูดฝุ่นถูพื้น",
        "details_a": "แรงดูดทรงพลัง ดูดได้ทุกที่ ทั้งโซฟา ซอกตู้ ผ้าม่าน ในรถ จัดการจุดเลอะได้ทันที",
        "details_b": "ทำงานอัตโนมัติทุกวันตามเวลาที่ตั้งไว้ ไม่ต้องเปลืองแรง เก็บฝุ่นละเอียดตอนไม่อยู่ห้อง",
        "target_audience": "คนทำงานไม่มีเวลา คนเลี้ยงสัตว์ และคนรักความสะอาดในบ้าน",
        "key_angles": "ความคล่องตัวจัดการซอกหลืบ เทียบกับการประหยัดแรงและเวลาแบบอัตโนมัติ",
        "affiliate_link_a": "https://shopee.co.th/cordless_vacuum",
        "affiliate_link_b": "https://shopee.co.th/robot_vacuum",
    },
    # 💄 Health & Beauty
    {
        "category": "💄 สุขภาพ & บิวตี้",
        "topic": "เวย์โปรตีน Concentrate VS เวย์โปรตีน Isolate",
        "name_a": "เวย์ Concentrate (WPC)",
        "name_b": "เวย์ Isolate (WPI)",
        "details_a": "โปรตีน 70-80% ราคาคุ้มค่า รสชาติอร่อยกลมกล่อม เหมาะกับคนสร้างกล้ามทั่วไป",
        "details_b": "โปรตีน 90%+ แลคโตสและไขมันเกือบศูนย์ ย่อยง่าย คนแพ้นมทานได้ ลีนไว",
        "target_audience": "คนออกกำลังกาย เล่นเวท และคนที่อยากเสริมโปรตีนให้ถึงในแต่ละวัน",
        "key_angles": "ความคุ้มค่าคุ้มราคา เทียบกับความบริสุทธิ์ของโปรตีนและคนที่มีอาการแพ้นม",
        "affiliate_link_a": "https://shopee.co.th/whey_concentrate",
        "affiliate_link_b": "https://shopee.co.th/whey_isolate",
    },
    {
        "category": "💄 สุขภาพ & บิวตี้",
        "topic": "คุชชั่นเกาหลี (Cushion) VS รองพื้นเนื้อแมตต์ (Foundation)",
        "name_a": "คุชชั่น (Cushion)",
        "name_b": "รองพื้นเนื้อแมตต์ (Foundation)",
        "details_a": "ให้งานผิวฉ่ำโกลว์ดูเป็นธรรมชาติ พกพาง่าย ตบเติมระหว่างวันได้สะดวกรวดเร็ว",
        "details_b": "การปกปิดระดับ Full Coverage คุมมันยาวนานทั้งวัน ไม่เยิ้มแม้เจออากาศร้อนชื้น",
        "target_audience": "สาวๆ และคนที่แต่งหน้าทำงานหรือไปเรียนในทุกๆ วัน",
        "key_angles": "งานผิวสบายๆ เป็นธรรมชาติพกพาง่าย เทียบกับความติดทนคุมมันขั้นสุด",
        "affiliate_link_a": "https://shopee.co.th/cushion_glow",
        "affiliate_link_b": "https://shopee.co.th/matte_foundation",
    }
]


def get_random_idea(category: Optional[str] = None) -> Dict[str, str]:
    """Returns a random high-retention comparison idea template."""
    import random
    pool = TRENDING_COMPARISON_TEMPLATES
    if category and category != "ทั้งหมด (สุ่มทุกหมวด)":
        filtered = [item for item in pool if item["category"] == category]
        if filtered:
            pool = filtered
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
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))
