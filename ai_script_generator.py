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
