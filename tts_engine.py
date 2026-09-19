"""
TTS Engine Module for Automated Short-Form Comparison Videos.
Supports:
1. Microsoft Edge Neural TTS (th-TH-NiwatNeural, th-TH-PremwadeeNeural) - ultra-realistic, natural breathing & pitch.
2. Google Cloud TTS (Neural2/WaveNet Thai)
3. gTTS (free fallback)
Includes BGM and transition SFX audio mixing.
"""

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import re
import sys
import edge_tts
from gtts import gTTS
from moviepy import AudioFileClip, CompositeAudioClip
import moviepy.audio.fx as afx

from config import AUDIO_DIR, TEMP_DIR, TTS_SILENCE_GAP

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class SegmentTimeline:
    segment_id: str
    text: str
    start_time: float
    end_time: float
    duration: float
    highlight_target: str  # "none", "A", or "B"
    audio_path: str
    round_label: str = ""


def preprocess_thai_pacing(text: str) -> str:
    """
    Intelligently formats text for Neural TTS (Edge-TTS Niwat/Premwadee):
    1. Inserts whitespace between Thai characters and English words or numbers
       to prevent acoustic model confusion, slurred speech, and mispronunciation.
    2. Inserts natural micro-pauses (commas, ellipses) around contrast connectors,
       questions, and exclamations for human-like breathing and intonation.
    3. Normalizes common unit abbreviations for crystal-clear spoken Thai.
    """
    if not text:
        return text
    t = text.strip()

    # 1. Separate Thai characters and English words
    t = re.sub(r"([ก-๙])([A-Za-z])", r"\1 \2", t)
    t = re.sub(r"([A-Za-z])([ก-๙])", r"\1 \2", t)

    # 2. Separate Thai characters and Numbers
    t = re.sub(r"([ก-๙])([0-9])", r"\1 \2", t)
    t = re.sub(r"([0-9])([ก-๙])", r"\1 \2", t)

    # 3. Spoken Unit Normalization
    t = re.sub(r"\bHz\b", " เฮิรตซ์", t, flags=re.IGNORECASE)
    t = re.sub(r"\bGB\b", " กิ๊ก", t, flags=re.IGNORECASE)
    t = re.sub(r"\bTB\b", " เทราไบต์", t, flags=re.IGNORECASE)
    t = re.sub(r"%", " เปอร์เซ็นต์", t)

    # 4. Natural breathing & rhetorical pacing
    t = re.sub(r"([!?])\s*", r"\1 ... ", t)
    t = re.sub(r"(:)\s*", r"\1, ", t)

    # Natural breathing pause before contrast conjunctions and rhetorical hooks
    connectors = [
        "ในขณะที่", "ขณะเดียวกัน", "ในทางกลับกัน", "ข้อดีก็คือ", "ข้อดีคือ",
        "ข้อเสียคือ", "จุดเด่นคือ", "ข้อจำกัดคือ", "สำหรับ", "นอกจากนี้",
        "โดยรวมแล้ว", "สรุปก็คือ", "แต่ว่า", "แต่ทว่า", "แต่", "ส่วน",
        "อย่าเพิ่งซื้อ", "มาดูกันเลย", "แล้วคุณล่ะ", "ฟันธงได้เลยว่า"
    ]
    for c in connectors:
        t = re.sub(rf"(?<![,...])\s+({re.escape(c)})", r", \1", t)

    t = re.sub(r",\s*,", ",", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def split_into_spoken_sentences(text: str, max_chars: int = 58) -> List[str]:
    """
    Intelligently splits a Thai script segment into bite-sized spoken sentences
    (30-55 characters) for sentence-by-sentence subtitle presentation and dynamic pacing.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
    results = []

    for line in raw_lines:
        # 1. Split on sentence terminators: !, ?, or newline
        chunks = [c.strip() for c in re.split(r"(?<=[!?])\s*", line) if c.strip()]
        for c in chunks:
            if len(c) <= max_chars:
                results.append(c)
                continue

            # 2. Split after polite particles with trailing space or punctuation
            sub_chunks = [sc.strip() for sc in re.split(r"(?<=[ครับค่ะนะ][!.,\s])\s*", c) if sc.strip()]
            if len(sub_chunks) > 1:
                for sc in sub_chunks:
                    if len(sc) <= max_chars:
                        results.append(sc)
                    else:
                        parts = [p.strip() for p in re.split(r"\s+(?=(?:แต่ถ้า|แต่ว่า|แต่|ในขณะที่|ส่วน|คอมเมนต์|พิกัด))", sc) if p.strip()]
                        results.extend(parts)
                continue

            # 3. Split before natural conjunctions or contrast markers
            parts = [p.strip() for p in re.split(r"\s+(?=(?:แต่ถ้า|แต่ว่า|ในขณะที่|ส่วน|คอมเมนต์บอก|พิกัดของแท้))", c) if p.strip()]
            if len(parts) > 1:
                results.extend(parts)
            else:
                # 4. Fallback: split near middle space if still long
                words = c.split(" ")
                if len(words) > 1:
                    mid = len(words) // 2
                    results.append(" ".join(words[:mid]))
                    results.append(" ".join(words[mid:]))
                else:
                    results.append(c)

    return [r for r in results if r]


class TTSEngine:
    """Manages multi-segment audio generation, measurement, and master track assembly with BGM/SFX."""

    VOICE_PRESETS = {
        "edge_senior_male": {
            "engine": "edge",
            "voice": "th-TH-NiwatNeural",
            "rate": "-5%",
            "pitch": "-8Hz",
            "desc": "🧔‍♂️ เสียงชายสุขุม/มีอายุ (ทุ้มลึก นุ่มนวล สไตล์ผู้ใหญ่ น่าเชื่อถือ)",
        },
        "edge_elder_doc": {
            "engine": "edge",
            "voice": "th-TH-NiwatNeural",
            "rate": "-8%",
            "pitch": "-14Hz",
            "desc": "👴 เสียงอาจารย์/ผู้เชี่ยวชาญอาวุโส (ทุ้มต่ำ ใจเย็น มีน้ำหนักคำ)",
        },
        "edge_story_male": {
            "engine": "edge",
            "voice": "th-TH-NiwatNeural",
            "rate": "-2%",
            "pitch": "-5Hz",
            "desc": "🎙️ เสียงเล่าเรื่องสารคดี (ทุ้มนุ่ม ลุ่มลึก น่าติดตาม)",
        },
        "edge_niwat": {
            "engine": "edge",
            "voice": "th-TH-NiwatNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
            "desc": "👦 นิวัฒน์ มาตรฐาน (ชายวัยทำงาน - ธรรมชาติ ฟังสบาย)",
        },
        "edge_energetic_male": {
            "engine": "edge",
            "voice": "th-TH-NiwatNeural",
            "rate": "+10%",
            "pitch": "+2Hz",
            "desc": "⚡ นิวัฒน์ ไวรัลวัยรุ่น (กระฉับกระเฉง ตื่นเต้น ไวรัล TikTok)",
        },
        "edge_mature_female": {
            "engine": "edge",
            "voice": "th-TH-PremwadeeNeural",
            "rate": "-4%",
            "pitch": "-5Hz",
            "desc": "👩 เปรมวดี ผู้ใหญ่/ภูมิฐาน (นุ่มนวล มั่นใจ ชัดถ้อยชัดคำ)",
        },
        "edge_premwadee": {
            "engine": "edge",
            "voice": "th-TH-PremwadeeNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
            "desc": "👧 เปรมวดี มาตรฐาน (หญิงสดใส เป็นมิตร)",
        },
        "gcloud_neural": {"engine": "gcloud", "voice": "th-TH-Neural2-C", "desc": "🌟 Google Cloud Neural2-C (สตูดิโอ)"},
        "gtts_thai": {"engine": "gtts", "voice": "th", "desc": "🤖 Google Translate TTS (ฟรี พื้นฐาน)"},
    }

    EMOTION_PRESETS = {
        "viral": {
            "name": "⚡ ตื่นเต้น ไวรัล กระฉับกระเฉง (Viral & Energetic)",
            "rate": "+10%",
            "pitch": "+2Hz",
            "desc": "เพิ่มความเร็วเล็กน้อย ยกโทนเสียงสูงขึ้น กระตุ้นความสนใจ เหมาะกับ Reels/TikTok/Shorts",
        },
        "story": {
            "name": "🎙️ เล่าเรื่อง นุ่มลึก น่าเชื่อถือ (Storytelling & Deep)",
            "rate": "+0%",
            "pitch": "-2Hz",
            "desc": "จังหวะสุขุม นุ่มลึก มีน้ำหนักคำ เหมาะกับบทวิเคราะห์ สเปก และความจริงทางวิทย์",
        },
        "casual": {
            "name": "☕ สบายๆ เป็นกันเอง ป้ายยา (Casual & Friendly)",
            "rate": "+5%",
            "pitch": "+1Hz",
            "desc": "น้ำเสียงฟังสบายเหมือนเพื่อนเล่าให้ฟัง เข้าถึงง่าย ชวนคุยและปักหมุดพิกัด",
        },
        "fast": {
            "name": "🚀 เข้าประเด็น ด่วนจี๋ สไตล์ TikTok (Fast Paced)",
            "rate": "+15%",
            "pitch": "+0Hz",
            "desc": "เร็ว คม สั้นไว ไม่เสียเวลา เหมาะกับโหมดกระชับ 30-40 วินาที",
        },
    }

    def __init__(
        self,
        voice_key: str = "edge_niwat",
        silence_gap: float = TTS_SILENCE_GAP,
        speech_rate: str = "+0%",
        speech_pitch: str = "+0Hz",
    ):
        self.voice_key = voice_key if voice_key in self.VOICE_PRESETS else "edge_niwat"
        self.silence_gap = silence_gap
        self.speech_rate = speech_rate
        self.speech_pitch = speech_pitch
        self._gcloud_available = self._check_google_cloud_tts()

    def _check_google_cloud_tts(self) -> bool:
        """Check if Google Cloud TTS credentials are configured."""
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if cred_path and Path(cred_path).exists():
            try:
                from google.cloud import texttospeech
                _ = texttospeech.TextToSpeechClient()
                return True
            except Exception:
                return False
        return False

    def synthesize_segment(self, text: str, output_path: Path) -> Path:
        """Synthesizes a single segment of speech."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        preset = self.VOICE_PRESETS.get(self.voice_key, self.VOICE_PRESETS["edge_niwat"])
        engine_type = preset["engine"]

        if engine_type == "edge":
            try:
                asyncio.run(self._synthesize_edge_tts(text, preset["voice"], output_path))
                return output_path
            except Exception as e:
                print(f"[TTS] Edge-TTS warning ({e}), falling back to gTTS...")

        elif engine_type == "gcloud" and self._gcloud_available:
            try:
                self._synthesize_gcloud(text, output_path)
                return output_path
            except Exception as e:
                print(f"[TTS] Google Cloud warning ({e}), falling back to Edge/gTTS...")

        # Secondary fallback: try Edge Niwat, then gTTS
        try:
            asyncio.run(self._synthesize_edge_tts(text, "th-TH-NiwatNeural", output_path))
            return output_path
        except Exception:
            self._synthesize_gtts(text, output_path)
            return output_path

    async def _synthesize_edge_tts(self, text: str, voice: str, output_path: Path):
        """Generate high-fidelity audio using Microsoft Edge Neural TTS."""
        preset = self.VOICE_PRESETS.get(self.voice_key, {})
        rate = self.speech_rate if self.speech_rate not in ("+0%", "0%", "") else preset.get("rate", "+0%")
        pitch = self.speech_pitch if self.speech_pitch not in ("+0Hz", "0Hz", "") else preset.get("pitch", "+0Hz")
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        await communicate.save(str(output_path))

    def _synthesize_gtts(self, text: str, output_path: Path):
        """Generate audio using Google Translate TTS (free fallback)."""
        tts = gTTS(text=text, lang="th", slow=False)
        tts.save(str(output_path))

    def _synthesize_gcloud(self, text: str, output_path: Path):
        """Generate high-fidelity audio using Google Cloud Neural2/WaveNet Thai."""
        from google.cloud import texttospeech

        client = texttospeech.TextToSpeechClient()
        s_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="th-TH",
            name="th-TH-Neural2-C",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.05,
        )
        response = client.synthesize_speech(
            input=s_input, voice=voice, audio_config=audio_config
        )
        with open(output_path, "wb") as out:
            out.write(response.audio_content)

    def build_timeline(
        self,
        script_data: Dict[str, Any],
        output_master_audio: Optional[Path] = None,
        include_bgm: bool = True,
        bgm_volume: float = 0.12,
        include_sfx: bool = True,
        **kwargs,
    ) -> Tuple[List[SegmentTimeline], Path, float]:
        """
        Takes script data, generates audio per segment with edge-tts neural voice,
        computes exact timeline, injects transition SFX, mixes BGM, and outputs master audio.
        Supports aliases: output_audio_path, enable_bgm, enable_sfx.
        """
        if output_master_audio is None and "output_audio_path" in kwargs:
            output_master_audio = kwargs["output_audio_path"]
        if "enable_bgm" in kwargs:
            include_bgm = kwargs["enable_bgm"]
        if "enable_sfx" in kwargs:
            include_sfx = kwargs["enable_sfx"]
        # Dynamic segments support (Multi-Round 60-90s or Classic 30s)
        if "segments" in script_data and isinstance(script_data["segments"], list) and len(script_data["segments"]) > 0:
            raw_segments_meta = script_data["segments"]
        else:
            raw_segments_meta = [
                {"id": "hook", "text": script_data.get("hook", ""), "highlight": "none", "round_label": "🔥 เปิดประเด็น"},
                {"id": "item_a", "text": script_data.get("item_a", ""), "highlight": "A", "round_label": f"📦 {script_data.get('name_a', 'ไอเทม A')}"},
                {"id": "item_b", "text": script_data.get("item_b", ""), "highlight": "B", "round_label": f"📦 {script_data.get('name_b', 'ไอเทม B')}"},
                {"id": "conclusion", "text": script_data.get("conclusion", ""), "highlight": "none", "round_label": "🏁 สรุปฟันธง"},
            ]

        # Expand multi-sentence segments into synchronized bite-sized sub-segments
        segments_meta = []
        for seg in raw_segments_meta:
            seg_text = seg.get("text", "").strip()
            if not seg_text:
                continue
            sub_sentences = split_into_spoken_sentences(seg_text)
            if len(sub_sentences) <= 1:
                segments_meta.append(seg)
            else:
                for s_idx, s_text in enumerate(sub_sentences):
                    new_seg = dict(seg)
                    new_seg["id"] = f"{seg.get('id', 'seg')}_{s_idx+1}"
                    new_seg["text"] = s_text
                    segments_meta.append(new_seg)

        if output_master_audio is None:
            output_master_audio = AUDIO_DIR / "master_audio.mp3"

        timeline: List[SegmentTimeline] = []
        current_time = 0.0
        audio_clips = []
        speech_timed_clips = []

        print(f"[TTS] Synthesizing speech with voice: {self.voice_key} ({len(segments_meta)} segments)...")
        for idx, seg in enumerate(segments_meta):
            seg_id = seg.get("id", f"seg_{idx}")
            text = seg.get("text", "").strip()
            if not text:
                continue

            # Smart pacing preprocessor for natural breathing pauses in neural TTS
            paced_text = preprocess_thai_pacing(text)
            seg_path = TEMP_DIR / f"tts_{self.voice_key}_{seg_id}.mp3"
            self.synthesize_segment(paced_text, seg_path)

            clip = AudioFileClip(str(seg_path))
            duration = clip.duration

            start_t = round(current_time, 3)
            end_t = round(current_time + duration, 3)

            timeline.append(
                SegmentTimeline(
                    segment_id=seg_id,
                    text=text,  # Keep clean text for subtitles
                    start_time=start_t,
                    end_time=end_t,
                    duration=duration,
                    highlight_target=seg.get("highlight", "none"),
                    audio_path=str(seg_path),
                    round_label=seg.get("round_label", ""),
                )
            )

            speech_timed_clips.append(clip.with_start(start_t))
            audio_clips.append(clip)
            current_time = end_t + self.silence_gap

        total_speech_duration = current_time

        # Master layer list for CompositeAudioClip
        all_layers = list(speech_timed_clips)

        # Transition SFX on every round switch
        sfx_clips = []
        if include_sfx:
            pop_sfx_path = AUDIO_DIR / "sfx_pop.wav"
            whoosh_sfx_path = AUDIO_DIR / "sfx_whoosh.wav"

            if pop_sfx_path.exists():
                last_target = "none"
                for seg in timeline:
                    if seg.highlight_target in ["A", "B"] and seg.highlight_target != last_target:
                        # Trigger pop SFX at the exact timestamp of switching to A or B
                        sfx_c = AudioFileClip(str(pop_sfx_path)).with_start(seg.start_time)
                        sfx_clips.append(sfx_c)
                        all_layers.append(sfx_c)
                    last_target = seg.highlight_target

        # Background Music (BGM) loop with subtle ducking and smooth fade in/out
        bgm_clip = None
        if include_bgm:
            bgm_path = AUDIO_DIR / "bgm_lofi.wav"
            if bgm_path.exists():
                raw_bgm = AudioFileClip(str(bgm_path))
                # Loop or trim to total_speech_duration
                if raw_bgm.duration < total_speech_duration:
                    loops = int(total_speech_duration / raw_bgm.duration) + 1
                    repeated = [raw_bgm.with_start(i * raw_bgm.duration) for i in range(loops)]
                    bgm_composite = CompositeAudioClip(repeated).subclipped(0, total_speech_duration)
                else:
                    bgm_composite = raw_bgm.subclipped(0, total_speech_duration)

                # Apply ducking volume and smooth fade in/out
                try:
                    fade_in_d = min(0.6, total_speech_duration / 4)
                    fade_out_d = min(1.0, total_speech_duration / 4)
                    bgm_composite = bgm_composite.with_effects([
                        afx.AudioFadeIn(fade_in_d),
                        afx.AudioFadeOut(fade_out_d)
                    ])
                except Exception:
                    pass

                bgm_clip = bgm_composite.with_volume_scaled(bgm_volume)
                all_layers.insert(0, bgm_clip)

        master_composite = CompositeAudioClip(all_layers)
        master_composite.write_audiofile(
            str(output_master_audio),
            fps=44100,
            nbytes=2,
            codec="libmp3lame",
            logger=None,
        )

        final_duration = master_composite.duration
        master_composite.close()
        for c in audio_clips:
            c.close()
        for c in sfx_clips:
            c.close()
        if bgm_clip:
            bgm_clip.close()

        print(f"[TTS] Master audio mixed: {output_master_audio} (Duration: {final_duration:.2f}s)")
        return timeline, output_master_audio, final_duration


if __name__ == "__main__":
    sample_script = {
        "hook": "สายกาแฟห้ามพลาด! ดริปเองกับแคปซูล แบบไหนตอบโจทย์ชีวิตคุณมากกว่ากัน?",
        "item_a": "กาแฟดริป ได้กลิ่นหอมกรุ่นแบบสโลว์ไลฟ์ ดึงรสชาติเมล็ดกาแฟแท้ๆ ออกมาได้ชัดเจน",
        "item_b": "กาแฟแคปซูล ตอบโจทย์ความเร็วในชั่วโมงเร่งด่วน กดปุ่มเดียวได้รสชาติเข้มข้นคงที่",
        "conclusion": "ชอบตัวไหน คอมเมนต์บอกกันหน่อยนะ พิกัดของแท้ราคาโปร แปะไว้ในคอมเมนต์แรกแล้วครับ",
    }
    engine = TTSEngine(voice_key="edge_niwat")
    timeline, master_path, duration = engine.build_timeline(sample_script)
    for seg in timeline:
        print(f"[{seg.start_time:.2f}s -> {seg.end_time:.2f}s] Highlight: {seg.highlight_target:4} | {seg.text[:35]}...")
