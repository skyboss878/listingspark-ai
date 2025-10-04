"""
ListingSpark AI - Professional Video Tour Generator
Premium features that command professional pricing
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class BrandingConfig:
    """Agent/Agency branding configuration"""
    logo_path: Optional[str] = None
    agent_name: str = ""
    agency_name: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    license_number: str = ""
    brand_color: str = "#1E40AF"  # Hex color for overlays
    watermark_position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right


@dataclass
class VideoConfig:
    """Video generation configuration"""
    resolution: str = "1920x1080"  # 1080p, 4K available
    fps: int = 30
    format: str = "landscape"  # landscape, square, vertical
    quality: str = "high"  # low, medium, high, ultra
    voice_provider: str = "elevenlabs"  # edge-tts, elevenlabs
    voice_id: str = "professional_female"
    music_genre: str = "upbeat"
    music_volume: float = 0.2
    narration_speed: float = 1.0
    transition_style: str = "crossfade"  # crossfade, zoom, slide
    include_captions: bool = True
    include_property_stats: bool = True


class PremiumVoiceEngine:
    """Handle multiple TTS providers for premium quality"""
    
    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        
        # Professional voice options
        self.voices = {
            "professional_female": {
                "elevenlabs": "EXAVITQu4vr4xnSDxMaL",  # Bella - professional
                "edge": "en-US-AriaNeural",
                "description": "Warm, professional female voice"
            },
            "professional_male": {
                "elevenlabs": "VR6AewLTigWG4xSOukaG",  # Arnold - authoritative
                "edge": "en-US-GuyNeural",
                "description": "Deep, authoritative male voice"
            },
            "friendly_female": {
                "elevenlabs": "21m00Tcm4TlvDq8ikWAM",  # Rachel - friendly
                "edge": "en-US-JennyNeural",
                "description": "Friendly, approachable female"
            },
            "luxury_british": {
                "elevenlabs": "ThT5KcBeYPX3keUQqHPh",  # Dorothy - British accent
                "edge": "en-GB-SoniaNeural",
                "description": "Sophisticated British accent for luxury properties"
            }
        }
    
    async def generate_speech_elevenlabs(
        self,
        text: str,
        voice_id: str,
        output_file: Path
    ) -> Path:
        """Generate speech using ElevenLabs (premium quality)"""
        import aiohttp
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    output_file.write_bytes(audio_data)
                    return output_file
                else:
                    raise Exception(f"ElevenLabs API error: {response.status}")
    
    async def generate_speech_edge(
        self,
        text: str,
        voice: str,
        output_file: Path
    ) -> Path:
        """Generate speech using Edge TTS (free fallback)"""
        import edge_tts
        
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_file))
        return output_file
    
    async def generate_speech(
        self,
        text: str,
        voice_option: str,
        provider: str,
        output_file: Path
    ) -> Path:
        """Generate speech using configured provider"""
        voice_config = self.voices.get(voice_option, self.voices["professional_female"])
        
        if provider == "elevenlabs" and self.elevenlabs_key:
            return await self.generate_speech_elevenlabs(
                text,
                voice_config["elevenlabs"],
                output_file
            )
        else:
            return await self.generate_speech_edge(
                text,
                voice_config["edge"],
                output_file
            )


class VideoEffectsEngine:
    """Advanced video effects and transitions"""
    
    @staticmethod
    def create_title_card(
        property_data: dict,
        branding: BrandingConfig,
        output_file: Path,
        duration: int = 3
    ) -> Path:
        """Create professional opening title card"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create 1920x1080 image
        img = Image.new('RGB', (1920, 1080), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # Try to load custom fonts, fallback to default
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Add property title
        title = property_data['title']
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        draw.text(
            ((1920 - title_width) // 2, 400),
            title,
            fill=(255, 255, 255),
            font=title_font
        )
        
        # Add price
        price = f"${property_data['price']}"
        bbox = draw.textbbox((0, 0), price, font=subtitle_font)
        price_width = bbox[2] - bbox[0]
        draw.text(
            ((1920 - price_width) // 2, 520),
            price,
            fill=(100, 200, 100),
            font=subtitle_font
        )
        
        # Add specs
        specs = f"{property_data['bedrooms']} BD | {property_data['bathrooms']} BA | {property_data['square_feet']} SqFt"
        bbox = draw.textbbox((0, 0), specs, font=info_font)
        specs_width = bbox[2] - bbox[0]
        draw.text(
            ((1920 - specs_width) // 2, 600),
            specs,
            fill=(200, 200, 200),
            font=info_font
        )
        
        # Add branding at bottom
        if branding.agent_name:
            agent_text = f"Presented by {branding.agent_name}"
            if branding.agency_name:
                agent_text += f" | {branding.agency_name}"
            bbox = draw.textbbox((0, 0), agent_text, font=info_font)
            agent_width = bbox[2] - bbox[0]
            draw.text(
                ((1920 - agent_width) // 2, 950),
                agent_text,
                fill=(150, 150, 150),
                font=info_font
            )
        
        img.save(output_file)
        return output_file
    
    @staticmethod
    def create_contact_card(
        branding: BrandingConfig,
        output_file: Path,
        duration: int = 5
    ) -> Path:
        """Create ending contact/CTA card"""
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.new('RGB', (1920, 1080), color=(20, 30, 50))
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
        except:
            title_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # CTA text
        cta = "Schedule Your Private Showing"
        bbox = draw.textbbox((0, 0), cta, font=title_font)
        cta_width = bbox[2] - bbox[0]
        draw.text(
            ((1920 - cta_width) // 2, 300),
            cta,
            fill=(255, 255, 255),
            font=title_font
        )
        
        # Contact info
        y_pos = 450
        contact_items = [
            branding.agent_name,
            branding.phone,
            branding.email,
            branding.website
        ]
        
        for item in contact_items:
            if item:
                bbox = draw.textbbox((0, 0), item, font=info_font)
                item_width = bbox[2] - bbox[0]
                draw.text(
                    ((1920 - item_width) // 2, y_pos),
                    item,
                    fill=(200, 220, 255),
                    font=info_font
                )
                y_pos += 80
        
        img.save(output_file)
        return output_file
    
    @staticmethod
    async def add_watermark_and_branding(
        video_file: Path,
        branding: BrandingConfig,
        output_file: Path
    ) -> Path:
        """Add logo watermark and branding overlay"""
        import subprocess
        
        if not branding.logo_path or not Path(branding.logo_path).exists():
            # No logo, just copy
            output_file.write_bytes(video_file.read_bytes())
            return output_file
        
        # Position mapping
        positions = {
            "top-left": "10:10",
            "top-right": "main_w-overlay_w-10:10",
            "bottom-left": "10:main_h-overlay_h-10",
            "bottom-right": "main_w-overlay_w-10:main_h-overlay_h-10"
        }
        
        position = positions.get(branding.watermark_position, positions["bottom-right"])
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_file),
            '-i', branding.logo_path,
            '-filter_complex',
            f'[1:v]scale=150:-1[logo];[0:v][logo]overlay={position}:format=auto',
            '-codec:a', 'copy',
            str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_file


class ProfessionalVideoTourGenerator:
    """Premium video tour generation with all professional features"""
    
    def __init__(self):
        self.output_dir = Path("video_tours")
        self.output_dir.mkdir(exist_ok=True)
        self.music_dir = Path("music_library")
        self.music_dir.mkdir(exist_ok=True)
        self.voice_engine = PremiumVoiceEngine()
        self.effects_engine = VideoEffectsEngine()
    
    async def generate_premium_script(
        self,
        property_data: dict,
        rooms: List[dict],
        style: str = "professional"  # professional, luxury, family-friendly
    ) -> dict:
        """Generate AI-optimized narration script"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        style_prompts = {
            "professional": "professional, informative tone focusing on features and benefits",
            "luxury": "sophisticated, elegant language emphasizing luxury and exclusivity",
            "family-friendly": "warm, welcoming tone highlighting family living and community"
        }
        
        prompt = f"""You are a top real estate marketing copywriter. Create a compelling video tour narration script.

Property Details:
- Title: {property_data['title']}
- Address: {property_data['address']}
- Price: ${property_data['price']}
- Type: {property_data['property_type']}
- Beds: {property_data['bedrooms']} | Baths: {property_data['bathrooms']}
- Square Feet: {property_data['square_feet']}
- Features: {', '.join(property_data.get('features', []))}

Rooms ({len(rooms)} total):
{json.dumps([{'name': r['space_name'], 'type': r['space_type'], 'description': r.get('description', '')} for r in rooms], indent=2)}

Style: {style_prompts[style]}

Requirements:
1. INTRO (5-8 seconds): Hook viewers immediately with the property's best selling point
2. ROOM NARRATIONS (15-20 seconds each): 
   - Highlight unique features
   - Use sensory language (imagine, picture, feel)
   - Mention dimensions/details naturally
   - Smooth transitions between rooms
3. OUTRO (5-8 seconds): Strong call-to-action, create urgency

Make it engaging enough for social media while remaining professional.
Use natural, conversational language a person would actually say.

Return ONLY valid JSON in this exact format:
{{
  "intro": "string",
  "rooms": [
    {{"room_name": "string", "narration": "string"}}
  ],
  "outro": "string",
  "estimated_duration_seconds": number
}}"""

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.8
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_tour_video(
        self,
        property_id: str,
        property_data: dict,
        rooms: List[dict],
        config: VideoConfig,
        branding: BrandingConfig
    ) -> Dict:
        """Generate complete professional video tour"""
        try:
            logger.info(f"Starting premium video generation for {property_id}")
            
            # Step 1: Generate script
            script = await self.generate_premium_script(property_data, rooms)
            
            # Step 2: Create working directory
            work_dir = self.output_dir / property_id
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 3: Generate all audio
            audio_files = []
            
            # Intro audio
            intro_audio = work_dir / "audio_intro.mp3"
            await self.voice_engine.generate_speech(
                script['intro'],
                config.voice_id,
                config.voice_provider,
                intro_audio
            )
            audio_files.append(intro_audio)
            
            # Room narrations
            for i, room_narration in enumerate(script['rooms']):
                room_audio = work_dir / f"audio_room_{i}.mp3"
                await self.voice_engine.generate_speech(
                    room_narration['narration'],
                    config.voice_id,
                    config.voice_provider,
                    room_audio
                )
                audio_files.append(room_audio)
            
            # Outro audio
            outro_audio = work_dir / "audio_outro.mp3"
            await self.voice_engine.generate_speech(
                script['outro'],
                config.voice_id,
                config.voice_provider,
                outro_audio
            )
            audio_files.append(outro_audio)
            
            # Step 4: Create title and contact cards
            title_card = work_dir / "title_card.png"
            self.effects_engine.create_title_card(property_data, branding, title_card)
            
            contact_card = work_dir / "contact_card.png"
            self.effects_engine.create_contact_card(branding, contact_card)
            
            # Step 5: Compile video segments
            # ... (continued in next message)
            
            return {
                "success": True,
                "video_url": f"/video_tours/{property_id}/final_tour.mp4",
                "script": script,
                "duration": script.get('estimated_duration_seconds', 0)
            }
            
        except Exception as e:
            logger.error(f"Premium video generation failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}



# Global instance
premium_video_generator = ProfessionalVideoTourGenerator()
