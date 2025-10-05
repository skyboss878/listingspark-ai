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
                "id": os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),  # Rachel
                "name": "Rachel",
                "description": "Warm, professional female voice - perfect for luxury listings"
            },
            "professional_male": {
                "id": "TxGEqnHWrfWFTfGW9XjX",  # Josh
                "name": "Josh",
                "description": "Confident, authoritative male voice - great for commercial properties"
            },
            "friendly_female": {
                "id": "EXAVITQu4vr4xnSDxMaL",  # Bella
                "name": "Bella",
                "description": "Friendly, conversational - ideal for family homes"
            },
            "luxury_male": {
                "id": "pNInz6obpgDQGcFmaJgB",  # Adam
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
        similarity_boost: float = 0.75,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> Optional[Path]:
        """
        Generate professional voice narration
        
        Args:
            text: Script to narrate
            voice_id: Voice preset key (e.g., 'professional_female')
            output_path: Where to save the audio file
            stability: Voice stability (0-1). Higher = more consistent
            similarity_boost: Voice clarity (0-1). Higher = clearer
            style: Style exaggeration (0-1). 0 = neutral, 1 = expressive
            use_speaker_boost: Enhance clarity and remove background noise
        
        Returns:
            Path to generated audio file or None if failed
        """
        if not self.enabled:
            logger.info("ElevenLabs disabled, skipping narration")
            return None
        
        try:
            # Get voice ID from preset
            voice_config = self.voices.get(voice_id)
            if not voice_config:
                logger.warning(f"Unknown voice preset: {voice_id}, using default")
                voice_config = self.voices["professional_female"]
            
            actual_voice_id = voice_config["id"]
            
            # Prepare output path
            if output_path is None:
                output_path = Path(f"narration_{voice_id}.mp3")
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # API request
            url = f"{self.base_url}/text-to-speech/{actual_voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",  # Best quality model
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost
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
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return None
        
        except Exception as e:
            logger.error(f"Error generating narration: {e}", exc_info=True)
            return None
    
    async def generate_tour_narration(
        self,
        property_data: Dict,
        rooms: List[Dict],
        voice_id: str = "professional_female",
        output_dir: Path = None
    ) -> Dict[str, Path]:
        """
        Generate narration for entire property tour
        
        Args:
            property_data: Property information
            rooms: List of rooms to narrate
            voice_id: Voice preset to use
            output_dir: Directory to save audio files
        
        Returns:
            Dictionary mapping room names to audio file paths
        """
        if output_dir is None:
            output_dir = Path("tours") / property_data['id'] / "audio"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        narrations = {}
        
        # Generate intro narration
        intro_script = self._generate_intro_script(property_data)
        intro_path = output_dir / "intro.mp3"
        intro_audio = await self.generate_narration(
            intro_script,
            voice_id=voice_id,
            output_path=intro_path
        )
        if intro_audio:
            narrations['intro'] = intro_audio
        
        # Generate room-by-room narration
        for room in rooms:
            room_script = self._generate_room_script(room, property_data)
            room_name = room['space_name'].replace(" ", "_").lower()
            room_path = output_dir / f"{room_name}.mp3"
            
            room_audio = await self.generate_narration(
                room_script,
                voice_id=voice_id,
                output_path=room_path
            )
            
            if room_audio:
                narrations[room['space_name']] = room_audio
        
        # Generate outro narration
        outro_script = self._generate_outro_script(property_data)
        outro_path = output_dir / "outro.mp3"
        outro_audio = await self.generate_narration(
            outro_script,
            voice_id=voice_id,
            output_path=outro_path
        )
        if outro_audio:
            narrations['outro'] = outro_audio
        
        logger.info(f"Generated {len(narrations)} narration files for property tour")
        return narrations
    
    def _generate_intro_script(self, property_data: Dict) -> str:
        """Generate engaging intro script"""
        title = property_data.get('title', 'this property')
        price = property_data.get('price', '')
        address = property_data.get('address', '')
        bedrooms = property_data.get('bedrooms', '')
        bathrooms = property_data.get('bathrooms', '')
        sqft = property_data.get('square_feet', '')
        
        script = f"Welcome to {title}. "
        
        if price:
            script += f"Priced at {price}, "
        
        script += f"this stunning property is located at {address}. "
        
        if bedrooms and bathrooms:
            script += f"Featuring {bedrooms} bedrooms and {bathrooms} bathrooms"
            if sqft:
                script += f", with {sqft} square feet of living space"
            script += ". "
        
        script += "Let's take a tour and explore what makes this property special."
        
        return script
    
    def _generate_room_script(self, room: Dict, property_data: Dict) -> str:
        """Generate room-specific narration script"""
        space_name = room['space_name']
        space_type = room['space_type']
        description = room.get('description', '')
        sqft = room.get('square_feet')
        
        # Start with room introduction
        script = f"Here we have the {space_name}. "
        
        # Add description if available
        if description:
            script += f"{description} "
        
        # Add size if available
        if sqft:
            script += f"This space offers {sqft} square feet. "
        
        # Add context-specific details based on room type
        room_insights = {
            "Kitchen": "Notice the quality appliances and ample counter space, perfect for preparing meals and entertaining.",
            "Master Bedroom": "This spacious retreat provides a peaceful sanctuary with plenty of natural light.",
            "Living Room": "The open layout creates an inviting atmosphere, ideal for relaxation and gathering with family.",
            "Bathroom": "Featuring modern fixtures and elegant finishes throughout.",
            "Dining Room": "A perfect space for hosting dinner parties and creating memories with loved ones."
        }
        
        # Add generic insight if specific one exists
        for room_keyword, insight in room_insights.items():
            if room_keyword.lower() in space_name.lower() or room_keyword.lower() in space_type.lower():
                script += f"{insight} "
                break
        
        return script.strip()
    
    def _generate_outro_script(self, property_data: Dict) -> str:
        """Generate compelling outro script"""
        title = property_data.get('title', 'this property')
        
        script = f"Thank you for touring {title}. "
        script += "This property offers an exceptional opportunity for those seeking quality and comfort. "
        script += "For more information or to schedule an in-person showing, please contact us. "
        script += "We look forward to helping you find your dream home."
        
        return script
    
    async def get_available_voices(self) -> List[Dict]:
        """Get list of all available voices from ElevenLabs"""
        if not self.enabled:
            return list(self.voices.values())
        
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    voices_data = response.json()
                    return voices_data.get('voices', [])
                else:
                    logger.error(f"Failed to fetch voices: {response.status_code}")
                    return list(self.voices.values())
        
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return list(self.voices.values())
    
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


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # Test single narration
        test_text = "Welcome to this beautiful 3-bedroom home located in the heart of downtown."
        
        audio_path = await elevenlabs_engine.generate_narration(
            text=test_text,
            voice_id="professional_female",
            output_path=Path("test_narration.mp3")
        )
        
        if audio_path:
            print(f"✓ Narration generated: {audio_path}")
        else:
            print("✗ Narration failed")
        
        # Check quota
        quota = await elevenlabs_engine.check_quota()
        print(f"Quota: {quota['quota_remaining']} / {quota['quota_limit']} characters")
    
    asyncio.run(test())
