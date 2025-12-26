"""
ListingSpark AI - MILLION DOLLAR Video Tour Generator
Enterprise-grade video production with AI-powered automation
Version 2.0 - Production Ready
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import subprocess
from concurrent.futures import ThreadPoolExecutor
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS FOR TYPE SAFETY (Professional Software = Strong Typing)
# ============================================================================

class VideoQuality(str, Enum):
    """Video quality presets with pricing tiers"""
    BASIC = "720p"          # Free tier
    STANDARD = "1080p"      # $29/mo
    PRO = "4k"              # $99/mo
    ULTRA = "8k"            # $299/mo


class VideoFormat(str, Enum):
    """Social media optimized formats"""
    LANDSCAPE = "landscape"      # YouTube, website (16:9)
    SQUARE = "square"            # Instagram feed (1:1)
    VERTICAL = "vertical"        # TikTok, Reels, Stories (9:16)
    CINEMATIC = "cinematic"      # Ultra-wide (21:9)


class VoiceStyle(str, Enum):
    """Professional voice personas"""
    PROFESSIONAL_FEMALE = "professional_female"
    PROFESSIONAL_MALE = "professional_male"
    LUXURY_BRITISH = "luxury_british"
    FRIENDLY_FEMALE = "friendly_female"
    ENERGETIC_MALE = "energetic_male"
    SOPHISTICATED_FEMALE = "sophisticated_female"


class MusicMood(str, Enum):
    """Background music moods"""
    UPBEAT = "upbeat"
    LUXURY = "luxury"
    CALM = "calm"
    MODERN = "modern"
    CINEMATIC = "cinematic"


# ============================================================================
# ENHANCED CONFIGURATION CLASSES
# ============================================================================

@dataclass
class BrandingConfig:
    """Agent/Agency branding configuration with white-label support"""
    logo_path: Optional[str] = None
    agent_name: str = ""
    agency_name: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    license_number: str = ""
    brand_color: str = "#1E40AF"
    secondary_color: str = "#10B981"
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.8
    custom_intro_video: Optional[str] = None
    custom_outro_video: Optional[str] = None
    social_media: Dict[str, str] = None
    
    def __post_init__(self):
        if self.social_media is None:
            self.social_media = {}


@dataclass
class VideoConfig:
    """Video generation configuration with analytics tracking"""
    resolution: VideoQuality = VideoQuality.STANDARD
    fps: int = 30
    format: VideoFormat = VideoFormat.LANDSCAPE
    voice_style: VoiceStyle = VoiceStyle.PROFESSIONAL_FEMALE
    voice_speed: float = 1.0
    music_mood: MusicMood = MusicMood.UPBEAT
    music_volume: float = 0.15
    transition_style: str = "crossfade"
    transition_duration: float = 0.5
    include_captions: bool = True
    caption_style: str = "modern"
    include_property_stats: bool = True
    include_neighborhood_info: bool = True
    include_market_stats: bool = False
    auto_enhance_images: bool = True
    generate_thumbnails: bool = True
    export_vertical_version: bool = False
    export_square_version: bool = False
    add_background_music: bool = True
    voice_over_enabled: bool = True
    enable_ai_scene_detection: bool = True
    generate_srt_file: bool = False


@dataclass
class AnalyticsConfig:
    """Track video generation for business intelligence"""
    property_id: str
    agent_id: str
    generation_timestamp: str
    processing_time_seconds: float = 0.0
    video_duration_seconds: float = 0.0
    file_size_mb: float = 0.0
    quality_preset: str = ""
    features_used: List[str] = None
    cost_credits: int = 0
    
    def __post_init__(self):
        if self.features_used is None:
            self.features_used = []


# ============================================================================
# PREMIUM VOICE ENGINE WITH FALLBACK LOGIC
# ============================================================================

class PremiumVoiceEngine:
    """Multi-provider TTS with intelligent fallback and caching"""

    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.cache_dir = Path("voice_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.voices = {
            VoiceStyle.PROFESSIONAL_FEMALE: {
                "elevenlabs": "EXAVITQu4vr4xnSDxMaL",
                "openai": "nova",
                "edge": "en-US-AriaNeural",
                "description": "Warm, professional female - perfect for residential"
            },
            VoiceStyle.PROFESSIONAL_MALE: {
                "elevenlabs": "VR6AewLTigWG4xSOukaG",
                "openai": "onyx",
                "edge": "en-US-GuyNeural",
                "description": "Deep, authoritative - ideal for commercial"
            },
            VoiceStyle.LUXURY_BRITISH: {
                "elevenlabs": "ThT5KcBeYPX3keUQqHPh",
                "openai": "shimmer",
                "edge": "en-GB-SoniaNeural",
                "description": "Sophisticated British - luxury properties"
            },
            VoiceStyle.FRIENDLY_FEMALE: {
                "elevenlabs": "21m00Tcm4TlvDq8ikWAM",
                "openai": "alloy",
                "edge": "en-US-JennyNeural",
                "description": "Approachable and warm - family homes"
            },
            VoiceStyle.ENERGETIC_MALE: {
                "elevenlabs": "pNInz6obpgDQGcFmaJgB",
                "openai": "echo",
                "edge": "en-US-ChristopherNeural",
                "description": "Energetic and engaging - starter homes"
            },
            VoiceStyle.SOPHISTICATED_FEMALE: {
                "elevenlabs": "MF3mGyEYCl7XYWbV9V6O",
                "openai": "nova",
                "edge": "en-US-MichelleNeural",
                "description": "Elegant sophistication - high-end estates"
            }
        }

    def _get_cache_key(self, text: str, voice_id: str) -> str:
        """Generate cache key for voice files"""
        content = f"{text}:{voice_id}"
        return hashlib.md5(content.encode()).hexdigest()

    async def generate_speech(
        self,
        text: str,
        voice_style: VoiceStyle,
        output_file: Path,
        speed: float = 1.0
    ) -> Path:
        """Generate speech with intelligent provider selection and caching"""
        voice_config = self.voices[voice_style]
        
        cache_key = self._get_cache_key(text, voice_style.value)
        cached_file = self.cache_dir / f"{cache_key}.mp3"
        if cached_file.exists():
            logger.info(f"Using cached voice for: {text[:50]}...")
            output_file.write_bytes(cached_file.read_bytes())
            return output_file

        if self.elevenlabs_key:
            try:
                result = await self._generate_elevenlabs(
                    text, voice_config["elevenlabs"], output_file, speed
                )
                cached_file.write_bytes(result.read_bytes())
                return result
            except Exception as e:
                logger.warning(f"ElevenLabs failed: {e}, trying OpenAI...")

        if self.openai_key:
            try:
                result = await self._generate_openai(
                    text, voice_config["openai"], output_file, speed
                )
                cached_file.write_bytes(result.read_bytes())
                return result
            except Exception as e:
                logger.warning(f"OpenAI TTS failed: {e}, falling back to Edge...")

        result = await self._generate_edge(
            text, voice_config["edge"], output_file, speed
        )
        cached_file.write_bytes(result.read_bytes())
        return result

    async def _generate_elevenlabs(
        self, text: str, voice_id: str, output_file: Path, speed: float
    ) -> Path:
        """ElevenLabs TTS - Premium quality"""
        import aiohttp

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2",
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
                    
                    if speed != 1.0:
                        self._adjust_audio_speed(output_file, speed)
                    
                    return output_file
                else:
                    raise Exception(f"ElevenLabs API error: {response.status}")

    async def _generate_openai(
        self, text: str, voice: str, output_file: Path, speed: float
    ) -> Path:
        """OpenAI TTS - Good quality, cost-effective"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.openai_key)
        
        response = await client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=text,
            speed=speed
        )
        
        output_file.write_bytes(response.content)
        return output_file

    async def _generate_edge(
        self, text: str, voice: str, output_file: Path, speed: float
    ) -> Path:
        """Edge TTS - Free fallback"""
        import edge_tts
        
        rate = f"{int((speed - 1.0) * 100)}%"
        
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(str(output_file))
        return output_file

    def _adjust_audio_speed(self, audio_file: Path, speed: float) -> None:
        """Adjust audio playback speed using ffmpeg"""
        temp_file = audio_file.with_suffix('.temp.mp3')
        cmd = [
            'ffmpeg', '-y', '-i', str(audio_file),
            '-filter:a', f'atempo={speed}',
            str(temp_file)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        temp_file.replace(audio_file)


# ============================================================================
# AI-POWERED SCRIPT GENERATION
# ============================================================================

class AIScriptGenerator:
    """Generate compelling narration scripts using AI"""
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    async def generate_script(
        self,
        property_data: dict,
        rooms: List[dict],
        style: str = "professional",
        target_duration: int = 60,
        include_stats: bool = True
    ) -> dict:
        """Generate AI-optimized narration script"""
        
        if self.openai_key:
            return await self._generate_with_openai(
                property_data, rooms, style, target_duration, include_stats
            )
        elif self.anthropic_key:
            return await self._generate_with_claude(
                property_data, rooms, style, target_duration, include_stats
            )
        else:
            return self._generate_template_script(property_data, rooms, style)
    
    async def _generate_with_openai(
        self, property_data, rooms, style, target_duration, include_stats
    ) -> dict:
        """Generate script using GPT-4"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=self.openai_key)
        
        style_prompts = {
            "professional": "professional, informative, highlighting features and ROI",
            "luxury": "sophisticated, elegant, emphasizing exclusivity and prestige",
            "family-friendly": "warm, welcoming, focusing on lifestyle and community",
            "investment": "data-driven, focusing on value, location, and growth potential",
            "modern": "contemporary, trendy language for young professionals"
        }
        
        intro_time = 5
        outro_time = 5
        room_time = (target_duration - intro_time - outro_time) / max(len(rooms), 1)
        
        prompt = f"""You are an elite real estate video marketing expert. Create a compelling video tour narration script.

PROPERTY DETAILS:
Title: {property_data.get('title', 'Stunning Property')}
Address: {property_data.get('address', '')}
Price: ${property_data.get('price', 'Contact for pricing')}
Type: {property_data.get('property_type', 'Residential')}
Specs: {property_data.get('bedrooms', 0)} Beds | {property_data.get('bathrooms', 0)} Baths | {property_data.get('square_feet', 0)} SqFt
Features: {', '.join(property_data.get('features', []))}

ROOMS ({len(rooms)} spaces):
{json.dumps([{{'name': r.get('space_name', 'Room'), 'type': r.get('space_type', ''), 'description': r.get('description', '')}} for r in rooms], indent=2)}

STYLE: {style_prompts.get(style, style_prompts['professional'])}
TARGET: {target_duration} seconds total

Return ONLY valid JSON:
{{
  "intro": "5-8 second hook",
  "rooms": [{{"room_name": "name", "narration": "15-20 seconds", "key_features": ["feature1"]}}],
  "outro": "5-8 second CTA",
  "estimated_duration_seconds": {target_duration},
  "hook_appeal": "what makes this irresistible",
  "target_buyer_persona": "who this speaks to"
}}"""

        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.85,
            max_tokens=2000
        )
        
        script = json.loads(response.choices[0].message.content)
        script['generated_by'] = 'openai-gpt4'
        script['generation_timestamp'] = datetime.utcnow().isoformat()
        
        return script
    
    def _generate_template_script(self, property_data, rooms, style) -> dict:
        """Fallback template-based script generation"""
        intro = f"Welcome to this exceptional {property_data.get('property_type', 'property')} at {property_data.get('address', 'a prime location')}. "
        intro += f"Priced at ${property_data.get('price', 'contact for pricing')}, this home offers {property_data.get('bedrooms', 0)} bedrooms and {property_data.get('bathrooms', 0)} bathrooms."
        
        room_narrations = []
        for room in rooms:
            narration = f"The {room.get('space_name', 'room')} features {room.get('description', 'excellent finishes')}."
            room_narrations.append({
                "room_name": room.get('space_name', 'Room'),
                "narration": narration,
                "key_features": [room.get('space_type', '')]
            })
        
        outro = f"Contact us today to schedule your private showing."
        
        return {
            "intro": intro,
            "rooms": room_narrations,
            "outro": outro,
            "estimated_duration_seconds": 45,
            "generated_by": "template",
            "generation_timestamp": datetime.utcnow().isoformat()
        }


# ============================================================================
# VIDEO EFFECTS & COMPOSITION ENGINE
# ============================================================================

class VideoEffectsEngine:
    """Professional video effects, transitions, and composition"""
    
    @staticmethod
    def create_title_card(
        property_data: dict,
        branding: BrandingConfig,
        output_file: Path,
        duration: int = 3
    ) -> Path:
        """Create stunning opening title card"""
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        
        width, height = 1920, 1080
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        color1 = tuple(int(branding.brand_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        color2 = tuple(int(branding.secondary_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
        
        img = img.filter(ImageFilter.GaussianBlur(radius=2))
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            title_font = price_font = info_font = ImageFont.load_default()
        
        title = property_data.get('title', property_data.get('address', 'Exclusive Property'))
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = bbox[2] - bbox[0]
        title_x = (width - title_width) // 2
        title_y = 400
        
        draw.text((title_x + 2, title_y + 2), title, fill=(0, 0, 0, 128), font=title_font)
        draw.text((title_x, title_y), title, fill=(255, 255, 255), font=title_font)
        
        price = f"${property_data.get('price', 'Call for Pricing')}"
        bbox = draw.textbbox((0, 0), price, font=price_font)
        price_width = bbox[2] - bbox[0]
        price_x = (width - price_width) // 2
        price_y = 520
        draw.text((price_x + 2, price_y + 2), price, fill=(0, 0, 0, 128), font=price_font)
        draw.text((price_x, price_y), price, fill=(100, 255, 100), font=price_font)
        
        specs = f"{property_data.get('bedrooms', 0)} Beds  |  {property_data.get('bathrooms', 0)} Baths  |  {property_data.get('square_feet', 0):,} SqFt"
        bbox = draw.textbbox((0, 0), specs, font=info_font)
        specs_width = bbox[2] - bbox[0]
        specs_x = (width - specs_width) // 2
        specs_y = 620
        draw.text((specs_x, specs_y), specs, fill=(220, 220, 220), font=info_font)
        
        if branding.agent_name:
            brand_text = f"Presented by {branding.agent_name}"
            if branding.agency_name:
                brand_text += f"  •  {branding.agency_name}"
            bbox = draw.textbbox((0, 0), brand_text, font=info_font)
            brand_width = bbox[2] - bbox[0]
            brand_x = (width - brand_width) // 2
            draw.text((brand_x, 950), brand_text, fill=(180, 180, 180), font=info_font)
        
        img.save(output_file, quality=95)
        return output_file
    
    @staticmethod
    def create_contact_card(
        branding: BrandingConfig,
        output_file: Path,
        duration: int = 5
    ) -> Path:
        """Create compelling CTA end card"""
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = 1920, 1080
        
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        color1 = (20, 30, 50)
        color2 = (40, 50, 70)
        
        for y in range(height):
            ratio = y / height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            draw.rectangle([(0, y), (width, y+1)], fill=(r, g, b))
        
        try:
            cta_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 70)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 45)
        except:
            cta_font = info_font = ImageFont.load_default()
        
        cta = "Schedule Your Private Showing"
        bbox = draw.textbbox((0, 0), cta, font=cta_font)
        cta_width = bbox[2] - bbox[0]
        cta_x = (width - cta_width) // 2
        draw.text((cta_x, 250), cta, fill=(255, 255, 255), font=cta_font)
        
        y_pos = 450
        contact_items = [
            ("👤", branding.agent_name),
            ("📱", branding.phone),
            ("✉️", branding.email),
            ("🌐", branding.website)
        ]
        
        for icon, text in contact_items:
            if text:
                full_text = f"{icon}  {text}"
                bbox = draw.textbbox((0, 0), full_text, font=info_font)
                text_width = bbox[2] - bbox[0]
                text_x = (width - text_width) // 2
                draw.text((text_x, y_pos), full_text, fill=(200, 220, 255), font=info_font)
                y_pos += 80
        
        img.save(output_file, quality=95)
        return output_file
    
    @staticmethod
    async def compile_final_video(
        work_dir: Path,
        segments: List[Dict[str, Any]],
        background_music: Optional[Path],
        output_file: Path,
        config: VideoConfig
    ) -> Path:
        """Compile all video segments into final production"""
        
        concat_file = work_dir / 'concat.txt'
        with open(concat_file, 'w') as f:
            for segment in segments:
                f.write(f"file '{segment['video']}'\n")
                if 'duration' in segment:
                    f.write(f"duration {segment['duration']}\n")
        
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file)]
        
        filter_complex = []
        if config.add_background_music and background_music and background_music.exists():
            cmd.extend(['-i', str(background_music)])
            filter_complex.append(f'[1:a]volume={config.music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2')
        
        if filter_complex:
            cmd.extend(['-filter_complex', ';'.join(filter_complex)])
        
        cmd.extend([
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-r', str(config.fps),
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            str(output_file)
        ])
        
        logger.info(f"Compiling final video...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Video compilation failed: {result.stderr}")
        
        return output_file


# ============================================================================
# MAIN VIDEO GENERATOR CLASS
# ============================================================================

class ProfessionalVideoTourGenerator:
    """Million-dollar video tour generator"""
    
    def __init__(self):
        self.output_dir = Path("video_tours")
        self.output_dir.mkdir(exist_ok=True)
        
        self.music_dir = Path("music_library")
        self.music_dir.mkdir(exist_ok=True)
        
        self.cache_dir = Path("video_cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        self.voice_engine = PremiumVoiceEngine()
        self.script_generator = AIScriptGenerator()
        self.effects_engine = VideoEffectsEngine()
    
    async def generate_tour_video(
        self,
        property_id: str,
        property_data: dict,
        rooms: List[dict],
        config: VideoConfig,
        branding: BrandingConfig,
        callback_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate complete professional video tour"""
        start_time = datetime.now()
        
        try:
            logger.info(f"🎬 Starting video generation for property: {property_id}")
            
            work_dir = self.output_dir / property_id
            work_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("📝 Generating AI-powered script...")
            script = await self.script_generator.generate_script(
                property_data, rooms, "professional", 60, config.include_property_stats
            )
            
            logger.info("🎙️ Generating voice narrations...")
            audio_files = await self._generate_all_audio(script, config, work_dir)
            
            logger.info("🎨 Creating visual assets...")
            title_card = self.effects_engine.create_title_card(
                property_data, branding, work_dir / "title.png"
            )
            contact_card = self.effects_engine.create_contact_card(
                branding, work_dir / "contact.png"
            )
            
            logger.info("🎞️ Compiling video segments...")
            segments = await self._create_video_segments(
                rooms, audio_files, work_dir, config
            )
            
            segments.insert(0, {'video': str(title_card), 'duration': 3})
            segments.append({'video': str(contact_card), 'duration': 5})
            
            logger.info("🎵 Final compilation...")
            background_music = self._get_background_music(config.music_mood)
            final_video = work_dir / "final_tour.mp4"
            
            await self.effects_engine.compile_final_video(
                work_dir, segments, background_music, final_video, config
            )
            
            if branding.logo_path:
                logger.info("🏷️ Adding branding...")
                branded_video = work_dir / "final_branded.mp4"
                await self._add_watermark(final_video, branding, branded_video)
                final_video = branded_video
            
            processing_time = (datetime.now() - start_time).total_seconds()
            file_size = final_video.stat().st_size / (1024 * 1024)
            
            result = {
                "success": True,
                "video_url": f"/video_tours/{property_id}/final_tour.mp4",
                "video_path": str(final_video),
                "script": script,
                "duration_seconds": script.get('estimated_duration_seconds', 0),
                "file_size_mb": file_size,
                "processing_time_seconds": processing_time,
                "generated_at": start_time.isoformat()
            }
            
            logger.info(f"✅ Video generation complete! Time: {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Video generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "property_id": property_id,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_all_audio(
        self, script: dict, config: VideoConfig, work_dir: Path
    ) -> List[Path]:
        """Generate all audio narrations"""
        audio_files = []
        
        intro_file = work_dir / "audio_intro.mp3"
        await self.voice_engine.generate_speech(
            script['intro'], config.voice_style, intro_file, config.voice_speed
        )
        audio_files.append(intro_file)
        
        for i, room in enumerate(script['rooms']):
            room_file = work_dir / f"audio_room_{i}.mp3"
            await self.voice_engine.generate_speech(
                room['narration'], config.voice_style, room_file, config.voice_speed
            )
            audio_files.append(room_file)
        
        outro_file = work_dir / "audio_outro.mp3"
        await self.voice_engine.generate_speech(
            script['outro'], config.voice_style, outro_file, config.voice_speed
        )
        audio_files.append(outro_file)
        
        return audio_files
    
    async def _create_video_segments(
        self, rooms: List[dict], audio_files: List[Path], work_dir: Path, config: VideoConfig
    ) -> List[Dict[str, Any]]:
        """Create video segments from room images and audio"""
        segments = []
        
        for i, (room, audio) in enumerate(zip(rooms, audio_files[1:-1])):
            duration = self._get_audio_duration(audio)
            
            image_path = room.get('image_url') or room.get('photo_url')
            if not image_path:
                continue
            
            video_file = work_dir / f"segment_{i}.mp4"
            await self._create_video_from_image(
                image_path, audio, video_file, duration, config
            )
            
            segments.append({
                'video': str(video_file),
                'duration': duration,
                'room_name': room.get('space_name', f'Room {i+1}')
            })
        
        return segments
    
    async def _create_video_from_image(
        self, image_path: str, audio_path: Path, output_path: Path, 
        duration: float, config: VideoConfig
    ) -> None:
        """Create a video segment from a single image with audio"""
        if image_path.startswith('http'):
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(image_path) as resp:
                    image_data = await resp.read()
                    temp_image = output_path.parent / f"temp_img_{output_path.stem}.jpg"
                    temp_image.write_bytes(image_data)
                    image_path = str(temp_image)
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1',
            '-i', image_path,
            '-i', str(audio_path),
            '-filter_complex',
            f'[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z=\'min(zoom+0.0015,1.5)\':d={int(duration * config.fps)}:s=1920x1080:fps={config.fps}[v]',
            '-map', '[v]',
            '-map', '1:a',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            '-shortest',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _get_audio_duration(self, audio_file: Path) -> float:
        """Get audio file duration in seconds"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_file)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    
    def _get_background_music(self, mood: MusicMood) -> Optional[Path]:
        """Get background music for the specified mood"""
        music_map = {
            MusicMood.UPBEAT: "upbeat_background.mp3",
            MusicMood.LUXURY: "luxury_ambient.mp3",
            MusicMood.CALM: "calm_piano.mp3",
            MusicMood.MODERN: "modern_electronic.mp3",
            MusicMood.CINEMATIC: "cinematic_orchestral.mp3"
        }
        
        music_file = self.music_dir / music_map.get(mood, "upbeat_background.mp3")
        return music_file if music_file.exists() else None
    
    async def _add_watermark(
        self, video_file: Path, branding: BrandingConfig, output_file: Path
    ) -> Path:
        """Add logo watermark to video"""
        if not branding.logo_path or not Path(branding.logo_path).exists():
            output_file.write_bytes(video_file.read_bytes())
            return output_file
        
        positions = {
            "top-left": "10:10",
            "top-right": "W-w-10:10",
            "bottom-left": "10:H-h-10",
            "bottom-right": "W-w-10:H-h-10"
        }
        
        position = positions.get(branding.watermark_position, "W-w-10:H-h-10")
        
        cmd = [
            'ffmpeg', '-y',
            '-i', str(video_file),
            '-i', branding.logo_path,
            '-filter_complex',
            f'[1:v]scale=120:-1,format=rgba,colorchannelmixer=aa={branding.watermark_opacity}[logo];'
            f'[0:v][logo]overlay={position}:format=auto',
            '-codec:a', 'copy',
            str(output_file)
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        return output_file


# ============================================================================
# GLOBAL INSTANCE & EXPORTS
# ============================================================================

premium_video_generator = ProfessionalVideoTourGenerator()


async def generate_property_video(
    property_id: str,
    property_data: dict,
    rooms: List[dict],
    agent_branding: dict,
    video_settings: dict = None
) -> dict:
    """
    Simplified interface for generating videos
    
    Usage:
        result = await generate_property_video(
            property_id="prop_123",
            property_data={...},
            rooms=[...],
            agent_branding={...}
        )
    """
    
    branding = BrandingConfig(**agent_branding)
    config = VideoConfig(**video_settings) if video_settings else VideoConfig()
    
    return await premium_video_generator.generate_tour_video(
        property_id, property_data, rooms, config, branding
    )
