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
import sys
import edge_tts
from gtts import gTTS
from moviepy import AudioFileClip, CompositeAudioClip

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


class TTSEngine:
    """Manages multi-segment audio generation, measurement, and master track assembly with BGM/SFX."""

    VOICE_PRESETS = {
        "edge_niwat": {"engine": "edge", "voice": "th-TH-NiwatNeural", "desc": "นิวัฒน์ (ชาย - นุ่มลึก มีน้ำหนัก เว้นจังหวะธรรมชาติ)"},
        "edge_premwadee": {"engine": "edge", "voice": "th-TH-PremwadeeNeural", "desc": "เปรมวดี (หญิง - สดใส ชัดเจน เป็นธรรมชาติ)"},
        "gcloud_neural": {"engine": "gcloud", "voice": "th-TH-Neural2-C", "desc": "Google Cloud Neural2-C (สตูดิโอ)"},
        "gtts_thai": {"engine": "gtts", "voice": "th", "desc": "Google Translate TTS (พื้นฐาน ฟรี)"},
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
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=self.speech_rate,
            pitch=self.speech_pitch,
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
    ) -> Tuple[List[SegmentTimeline], Path, float]:
        """
        Takes script data, generates audio per segment with edge-tts neural voice,
        computes exact timeline, injects transition SFX, mixes BGM, and outputs master audio.
        """
        segments_meta = [
            {"id": "hook", "text": script_data.get("hook", ""), "highlight": "none"},
            {"id": "item_a", "text": script_data.get("item_a", ""), "highlight": "A"},
            {"id": "item_b", "text": script_data.get("item_b", ""), "highlight": "B"},
            {"id": "conclusion", "text": script_data.get("conclusion", ""), "highlight": "none"},
        ]

        if output_master_audio is None:
            output_master_audio = AUDIO_DIR / "master_audio.mp3"

        timeline: List[SegmentTimeline] = []
        current_time = 0.0
        audio_clips = []
        speech_timed_clips = []

        print(f"[TTS] Synthesizing speech with voice: {self.voice_key}...")
        for seg in segments_meta:
            seg_id = seg["id"]
            text = seg["text"].strip()
            if not text:
                continue

            seg_path = TEMP_DIR / f"tts_{self.voice_key}_{seg_id}.mp3"
            self.synthesize_segment(text, seg_path)

            clip = AudioFileClip(str(seg_path))
            duration = clip.duration

            start_t = round(current_time, 3)
            end_t = round(current_time + duration, 3)

            timeline.append(
                SegmentTimeline(
                    segment_id=seg_id,
                    text=text,
                    start_time=start_t,
                    end_time=end_t,
                    duration=duration,
                    highlight_target=seg["highlight"],
                    audio_path=str(seg_path),
                )
            )

            speech_timed_clips.append(clip.with_start(start_t))
            audio_clips.append(clip)
            current_time = end_t + self.silence_gap

        total_speech_duration = current_time

        # Master layer list for CompositeAudioClip
        all_layers = list(speech_timed_clips)

        # Transition SFX at keyframe moments
        sfx_clips = []
        if include_sfx:
            pop_sfx_path = AUDIO_DIR / "sfx_pop.wav"
            whoosh_sfx_path = AUDIO_DIR / "sfx_whoosh.wav"

            if pop_sfx_path.exists() and whoosh_sfx_path.exists():
                for seg in timeline:
                    if seg.highlight_target in ["A", "B"]:
                        # Trigger SFX right at the start of Item A or Item B
                        sfx_c = AudioFileClip(str(pop_sfx_path)).with_start(seg.start_time)
                        sfx_clips.append(sfx_c)
                        all_layers.append(sfx_c)

        # Background Music (BGM) loop at gentle volume
        bgm_clip = None
        if include_bgm:
            bgm_path = AUDIO_DIR / "bgm_lofi.wav"
            if bgm_path.exists():
                raw_bgm = AudioFileClip(str(bgm_path))
                # Loop or trim to total_speech_duration
                if raw_bgm.duration < total_speech_duration:
                    loops = int(total_speech_duration / raw_bgm.duration) + 1
                    # Repeat bgm
                    repeated = [raw_bgm.with_start(i * raw_bgm.duration) for i in range(loops)]
                    bgm_composite = CompositeAudioClip(repeated).subclipped(0, total_speech_duration)
                else:
                    bgm_composite = raw_bgm.subclipped(0, total_speech_duration)

                # Set subtle background volume
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
