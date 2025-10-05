import os
import logging
import httpx
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ElevenLabsVoiceEngine:
    """Professional voice narration using ElevenLabs API"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.enabled = os.getenv("ELEVENLABS_ENABLED", "false").lower() == "true"
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Professional voices for real estate
        self.voices = {
            "professional_female": {
                "id": os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
                "name": "Rachel",
                "description": "Warm, professional female voice - perfect for luxury listings"
            },
            "professional_male": {
                "id": "TxGEqnHWrfWFTfGW9XjX",
                "name": "Josh",
                "description": "Confident, authoritative male voice - great for commercial properties"
            },
            "friendly_female": {
                "id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella",
                "description": "Friendly, conversational - ideal for family homes"
            },
            "luxury_male": {
                "id": "pNInz6obpgDQGcFmaJgB",
                "name": "Adam",
                "description": "Deep, sophisticated - perfect for high-end estates"
            }
        }
        
        if self.enabled and not self.api_key:
            logger.warning("ElevenLabs enabled but no API key found")
            self.enabled = False
    
    async def generate_narration(
        self,
        text: str,
        voice_id: str = "professional_female",
        output_path: Optional[Path] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> Optional[Path]:
        """Generate professional voice narration"""
        if not self.enabled:
            logger.info("ElevenLabs disabled, skipping narration")
            return None
        
        try:
            voice_config = self.voices.get(voice_id, self.voices["professional_female"])
            actual_voice_id = voice_config["id"]
            
            if output_path is None:
                output_path = Path(f"narration_{voice_id}.mp3")
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            url = f"{self.base_url}/text-to-speech/{actual_voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            logger.info(f"Generating narration with voice: {voice_config['name']}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Narration saved to: {output_path}")
                    return output_path
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            return None
    
    async def check_quota(self) -> Dict:
        """Check remaining character quota"""
        if not self.enabled:
            return {"quota_remaining": 0, "quota_limit": 0}
        
        try:
            url = f"{self.base_url}/user"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "quota_remaining": user_data.get('character_count', 0),
                        "quota_limit": user_data.get('character_limit', 0)
                    }
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
        
        return {"quota_remaining": 0, "quota_limit": 0}

# Initialize global instance
elevenlabs_engine = ElevenLabsVoiceEngine()
