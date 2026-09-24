"""
Video Tour Generation Module
Creates narrated video tours from 360 images with music.

Uses:
- Claude (Opus) for narration script writing
- ElevenLabs for text-to-speech (via elevenlabs_voice.py)
- imageio_ffmpeg's bundled ffmpeg binary for video assembly (works on any
  host, including Render, without a system ffmpeg install)
- mutagen for audio duration (avoids needing ffprobe separately)
"""

import os
import logging
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Optional
import json

import imageio_ffmpeg
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()


class VideoTourGenerator:
    """Generate narrated video tours from property rooms"""

    def __init__(self):
        self.output_dir = Path("video_tours")
        self.output_dir.mkdir(exist_ok=True)
        self.music_dir = Path("music_library")
        self.music_dir.mkdir(exist_ok=True)

    async def generate_narration_script(self, property_data: dict, rooms: List[dict]) -> str:
        """Generate AI narration script for the tour using Claude Opus"""
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise RuntimeError("ANTHROPIC_API_KEY not configured - cannot generate narration script")

        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=anthropic_key)

        prompt = f"""Create an engaging, professional real estate video tour narration script. Respond with ONLY valid JSON, no markdown fences, no preamble.

Property: {property_data.get('title', property_data.get('address', 'this property'))}
Address: {property_data.get('address', '')}
Price: ${property_data.get('price', 0):,.0f}
Type: {property_data.get('property_type', 'home')}
Bedrooms: {property_data.get('bedrooms', 0)}
Bathrooms: {property_data.get('bathrooms', 0)}
Square Feet: {property_data.get('square_feet', 0)}

Rooms in order:
{json.dumps([{'name': r.get('space_name', 'Room'), 'type': r.get('space_type', ''), 'category': r.get('space_category', '')} for r in rooms], indent=2)}

Create a warm, professional narration that:
- Opens with an inviting introduction
- Smoothly transitions between rooms
- Highlights unique features
- Uses descriptive, appealing language
- Ends with a call-to-action
- Is about 15-20 seconds per room when spoken aloud

Return JSON with exactly this shape:
{{"intro": "...", "rooms": [{{"room_name": "...", "narration": "..."}}], "outro": "..."}}"""

        response = await client.messages.create(
            model="claude-opus-5-5",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text.strip()
        raw_text = re.sub(r'^```json\s*|```$', '', raw_text, flags=re.MULTILINE).strip()
        return raw_text

    async def text_to_speech(self, text: str, output_file: Path) -> Path:
        """Convert text to speech audio file using ElevenLabs"""
        from elevenlabs_voice import get_elevenlabs_engine

        engine = get_elevenlabs_engine()
        if not engine.enabled:
            raise RuntimeError("ElevenLabs voice narration is not configured")

        audio_bytes = await engine.generate_speech(text, "professional_female")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "wb") as f:
            f.write(audio_bytes)
        return output_file

    def _get_audio_duration(self, audio_file: Path) -> float:
        """Get audio duration in seconds without needing ffprobe"""
        return MP3(str(audio_file)).info.length

    async def create_video_from_images(
        self,
        images: List[Path],
        audio_files: List[Path],
        music_file: Optional[Path],
        output_file: Path
    ) -> Path:
        """Combine images, narration, and music into video"""
        import subprocess

        segments = []

        for i, (img, audio) in enumerate(zip(images, audio_files)):
            segment_file = output_file.parent / f"segment_{i}.mp4"
            duration = self._get_audio_duration(audio)

            cmd = [
                FFMPEG_BINARY, '-y',
                '-loop', '1', '-i', str(img),
                '-i', str(audio),
                '-filter_complex',
                f'[0:v]scale=1920:1080,zoompan=z=\'min(zoom+0.0015,1.5)\':d={int(duration * 30)}:s=1920x1080[v]',
                '-map', '[v]', '-map', '1:a',
                '-c:v', 'libx264', '-c:a', 'aac',
                '-shortest', '-t', str(duration),
                str(segment_file)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            segments.append(segment_file)

        concat_file = output_file.parent / "concat.txt"
        with open(concat_file, 'w') as f:
            for seg in segments:
                f.write(f"file '{seg.name}'\n")

        temp_output = output_file.parent / "temp_video.mp4"
        concat_cmd = [
            FFMPEG_BINARY, '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(temp_output)
        ]
        subprocess.run(concat_cmd, check=True, capture_output=True)

        if music_file and music_file.exists():
            music_cmd = [
                FFMPEG_BINARY, '-y',
                '-i', str(temp_output),
                '-i', str(music_file),
                '-filter_complex',
                '[1:a]volume=0.3[music];[0:a][music]amix=inputs=2:duration=first[a]',
                '-map', '0:v', '-map', '[a]',
                '-c:v', 'copy', '-c:a', 'aac',
                str(output_file)
            ]
            subprocess.run(music_cmd, check=True, capture_output=True)
            temp_output.unlink()
        else:
            temp_output.rename(output_file)

        for seg in segments:
            seg.unlink()
        concat_file.unlink()

        return output_file

    async def generate_tour_video(
        self,
        property_id: str,
        property_data: dict,
        rooms: List[dict],
        music_track: Optional[str] = "upbeat"
    ) -> Dict:
        """Main method to generate complete video tour"""
        try:
            logger.info(f"Generating video tour for property {property_id}")

            script_json = await self.generate_narration_script(property_data, rooms)
            script = json.loads(script_json)

            audio_dir = self.output_dir / property_id / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)

            audio_files = []

            intro_audio = audio_dir / "intro.mp3"
            await self.text_to_speech(script['intro'], intro_audio)
            audio_files.append(intro_audio)

            for room_script in script['rooms']:
                room_audio = audio_dir / f"{room_script['room_name']}.mp3"
                await self.text_to_speech(room_script['narration'], room_audio)
                audio_files.append(room_audio)

            outro_audio = audio_dir / "outro.mp3"
            await self.text_to_speech(script['outro'], outro_audio)
            audio_files.append(outro_audio)

            images = []
            for room in rooms:
                if room.get('image_360_url'):
                    img_path = Path(room['image_360_url'].replace('/tours/', 'tours/'))
                    if img_path.exists():
                        images.append(img_path)

            music_file = self.music_dir / f"{music_track}.mp3"
            if not music_file.exists():
                music_file = None

            output_file = self.output_dir / property_id / "tour_video.mp4"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            video_path = await self.create_video_from_images(
                images,
                audio_files,
                music_file,
                output_file
            )

            logger.info(f"Video tour completed: {video_path}")

            return {
                "success": True,
                "video_url": f"/video_tours/{property_id}/tour_video.mp4",
                "video_path": str(video_path),
                "script": script
            }

        except Exception as e:
            logger.error(f"Video generation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
video_generator = VideoTourGenerator()
