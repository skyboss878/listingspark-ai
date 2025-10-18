"""
ElevenLabs Voice Narration Module for ListingSpark AI
Generates professional voice narration for virtual tours
"""

import os
import logging
from pathlib import Path
from typing import Optional
from elevenlabs import generate, save, set_api_key, Voice, VoiceSettings

logger = logging.getLogger(__name__)


class ElevenLabsVoice:
    """ElevenLabs voice narration service"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if self.api_key:
            set_api_key(self.api_key)
            self.enabled = True
            logger.info("✅ ElevenLabs voice initialized")
        else:
            self.enabled = False
            logger.warning("⚠️ ElevenLabs API key not found - voice narration disabled")
    
    async def generate_narration(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None,
        model: str = "eleven_monolingual_v1"
    ) -> Optional[str]:
        """Generate voice narration from text"""
        
        if not self.enabled:
            logger.warning("Voice narration is disabled (no API key)")
            return None
        
        try:
            # Use default voice if not specified
            voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
            
            # Generate audio
            audio = generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.5,
                        use_speaker_boost=True
                    )
                ),
                model=model
            )
            
            # Save to file if output path provided
            if output_path:
                output_file = Path(output_path)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                save(audio, str(output_file))
                logger.info(f"✅ Voice narration saved to: {output_path}")
                return str(output_file)
            
            return audio
            
        except Exception as e:
            logger.error(f"❌ Failed to generate voice narration: {e}")
            return None
    
    def get_available_voices(self):
        """Get list of available voices"""
        if not self.enabled:
            return []
        
        try:
            from elevenlabs import voices
            return voices()
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []


# Create a singleton instance
elevenlabs_engine = None

def get_elevenlabs_engine():
    """Get or create ElevenLabs engine instance"""
    global elevenlabs_engine
    if elevenlabs_engine is None:
        elevenlabs_engine = ElevenLabsVoice()
    return elevenlabs_engine
