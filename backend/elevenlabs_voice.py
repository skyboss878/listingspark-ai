"""
ElevenLabs Voice Narration Module for ListingSpark AI
Generates professional voice narration for virtual tours.

Uses the modern ElevenLabs SDK (v1.x/v2.x) - client.text_to_speech.convert()
rather than the removed v0.x client.generate() method.
"""

import os
import logging
from pathlib import Path
from typing import Optional

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False

logger = logging.getLogger(__name__)

DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # ElevenLabs' default professional female voice

# Friendly names the app uses map to real ElevenLabs voice IDs
VOICE_NAME_MAP = {
    "professional_female": "EXAVITQu4vr4xnSDxMaL",
    "professional_male": "VR6AewLTigWG4xSOukaG",
    "friendly_female": "21m00Tcm4TlvDq8ikWAM",
    "energetic_male": "pNInz6obpgDQGcFmaJgB",
}


class ElevenLabsVoice:
    """ElevenLabs voice narration service"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.client = None

        if self.api_key and ELEVENLABS_AVAILABLE:
            try:
                self.client = ElevenLabs(api_key=self.api_key)
                self.enabled = True
                logger.info("✅ ElevenLabs voice initialized")
            except Exception as e:
                self.enabled = False
                logger.warning(f"⚠️ ElevenLabs initialization failed: {e}")
        else:
            self.enabled = False
            logger.warning("⚠️ ElevenLabs not available - voice narration disabled")

    def _resolve_voice_id(self, voice_id: Optional[str]) -> str:
        """Accepts either a friendly name (professional_female) or a raw ElevenLabs voice ID."""
        if not voice_id:
            return os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
        return VOICE_NAME_MAP.get(voice_id, voice_id)

    async def generate_speech(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """Generate speech audio and return raw MP3 bytes (for direct HTTP responses)."""
        if not self.enabled or not self.client:
            raise RuntimeError("Voice narration is disabled - ElevenLabs not configured")

        resolved_voice_id = self._resolve_voice_id(voice_id)

        audio_stream = self.client.text_to_speech.convert(
            voice_id=resolved_voice_id,
            text=text,
            model_id=os.getenv("VOICE_MODEL", "eleven_turbo_v2"),
            output_format="mp3_44100_128",
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.5,
                use_speaker_boost=True,
            ),
        )
        return b"".join(chunk for chunk in audio_stream)

    async def generate_narration(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """Generate voice narration from text and optionally save to a file. Returns the file path."""
        if not self.enabled or not self.client:
            logger.warning("Voice narration is disabled")
            return None

        try:
            audio_bytes = await self.generate_speech(text, voice_id)

            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
                logger.info(f"✅ Voice narration saved to: {output_path}")
                return str(output_file)

            return audio_bytes
        except Exception as e:
            logger.error(f"❌ Failed to generate voice narration: {e}")
            return None

    def get_available_voices(self):
        """Get list of available voices"""
        if not self.enabled or not self.client:
            return []
        try:
            response = self.client.voices.get_all()
            return [{"voice_id": v.voice_id, "name": v.name} for v in response.voices]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []

    @property
    def voices(self):
        """Alias so routes that reference .voices (instead of calling get_available_voices()) still work."""
        return self.get_available_voices()


# Create a singleton instance
elevenlabs_engine = None

def get_elevenlabs_engine():
    """Get or create ElevenLabs engine instance"""
    global elevenlabs_engine
    if elevenlabs_engine is None:
        elevenlabs_engine = ElevenLabsVoice()
    return elevenlabs_engine
