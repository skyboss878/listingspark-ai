"""
Video Tour Generation Module
Creates narrated video tours from 360° images with music
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class VideoTourGenerator:
    """Generate narrated video tours from property rooms"""
    
    def __init__(self):
        self.output_dir = Path("video_tours")
        self.output_dir.mkdir(exist_ok=True)
        self.music_dir = Path("music_library")
        self.music_dir.mkdir(exist_ok=True)
    
    async def generate_narration_script(self, property_data: dict, rooms: List[dict]) -> str:
        """Generate AI narration script for the tour"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        prompt = f"""Create an engaging, professional real estate video tour narration script.

Property: {property_data['title']}
Address: {property_data['address']}
Price: ${property_data['price']}
Type: {property_data['property_type']}
Bedrooms: {property_data['bedrooms']}
Bathrooms: {property_data['bathrooms']}
Square Feet: {property_data['square_feet']}

Rooms in order:
{json.dumps([{'name': r['space_name'], 'type': r['space_type'], 'category': r['space_category']} for r in rooms], indent=2)}

Create a warm, professional narration that:
- Opens with an inviting introduction
- Smoothly transitions between rooms
- Highlights unique features
- Uses descriptive, appealing language
- Ends with a call-to-action
- Is about 15-20 seconds per room

Format as JSON: {{"intro": "...", "rooms": [{{"room_name": "...", "narration": "..."}}], "outro": "..."}}"""

        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def text_to_speech(self, text: str, output_file: Path) -> Path:
        """Convert text to speech audio file"""
        # Using edge-tts (free Microsoft TTS)
        import edge_tts
        
        voice = "en-US-AriaNeural"  # Professional female voice
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_file))
        
        return output_file
    
    async def create_video_from_images(
        self,
        images: List[Path],
        audio_files: List[Path],
        music_file: Optional[Path],
        output_file: Path
    ) -> Path:
        """Combine images, narration, and music into video"""
        import subprocess
        
        # This requires FFmpeg installed
        # Create video segments for each room
        segments = []
        
        for i, (img, audio) in enumerate(zip(images, audio_files)):
            segment_file = output_file.parent / f"segment_{i}.mp4"
            
            # Get audio duration
            duration_cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(audio)
            ]
            duration = float(subprocess.check_output(duration_cmd).decode().strip())
            
            # Create video segment with pan/zoom effect
            cmd = [
                'ffmpeg', '-y',
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
        
        # Concatenate segments
        concat_file = output_file.parent / "concat.txt"
        with open(concat_file, 'w') as f:
            for seg in segments:
                f.write(f"file '{seg.name}'\n")
        
        # Combine all segments
        temp_output = output_file.parent / "temp_video.mp4"
        concat_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(temp_output)
        ]
        subprocess.run(concat_cmd, check=True, capture_output=True)
        
        # Add background music if provided
        if music_file and music_file.exists():
            music_cmd = [
                'ffmpeg', '-y',
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
        
        # Cleanup
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
            
            # Step 1: Generate narration script
            script_json = await self.generate_narration_script(property_data, rooms)
            script = json.loads(script_json)
            
            # Step 2: Create audio files for each room
            audio_dir = self.output_dir / property_id / "audio"
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            audio_files = []
            
            # Intro
            intro_audio = audio_dir / "intro.mp3"
            await self.text_to_speech(script['intro'], intro_audio)
            audio_files.append(intro_audio)
            
            # Room narrations
            for room_script in script['rooms']:
                room_audio = audio_dir / f"{room_script['room_name']}.mp3"
                await self.text_to_speech(room_script['narration'], room_audio)
                audio_files.append(room_audio)
            
            # Outro
            outro_audio = audio_dir / "outro.mp3"
            await self.text_to_speech(script['outro'], outro_audio)
            audio_files.append(outro_audio)
            
            # Step 3: Get room images
            images = []
            # Add a title card image first
            # Then add room images
            for room in rooms:
                if room.get('image_360_url'):
                    # Convert URL to file path
                    img_path = Path(room['image_360_url'].replace('/tours/', 'tours/'))
                    if img_path.exists():
                        images.append(img_path)
            
            # Step 4: Select music
            music_file = self.music_dir / f"{music_track}.mp3"
            if not music_file.exists():
                music_file = None  # No music if file doesn't exist
            
            # Step 5: Create video
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
