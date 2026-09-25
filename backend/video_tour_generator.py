"""
Video Tour Generation Module
Creates narrated video tours from property images with music.

Matches the calling convention used by server.py's TourGenerationService:
  VideoTourGenerator(images=..., output_dir=..., style=..., enable_360=...,
                      camera_speed=..., fps=..., resolution=...)
  await tour_gen.generate(music_track=..., narration_file=...)

Uses imageio_ffmpeg's bundled ffmpeg binary (works on Render without a
system ffmpeg install) and mutagen for audio duration (avoids ffprobe).
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

import imageio_ffmpeg
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

FFMPEG_BINARY = imageio_ffmpeg.get_ffmpeg_exe()


class VideoTourGenerator:
    """Assembles property images (+ optional narration/music) into a video tour."""

    def __init__(
        self,
        images: List[str],
        output_dir: str,
        style: str = "cinematic",
        enable_360: bool = True,
        camera_speed: float = 1.5,
        fps: int = 30,
        resolution: str = "1920x1080",
    ):
        self.images = images or []
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.style = style
        self.enable_360 = enable_360
        self.camera_speed = camera_speed
        self.fps = fps
        self.resolution = resolution

    def _resolve_image_path(self, image_ref: str) -> Optional[Path]:
        """Listing images are stored as URLs like /uploads/xyz.jpg, which map
        to a local file at uploads/xyz.jpg relative to the server's cwd."""
        candidate = Path(image_ref.lstrip("/"))
        if candidate.exists():
            return candidate
        return None

    async def generate(
        self,
        music_track: Optional[str] = None,
        narration_file: Optional[str] = None,
    ) -> str:
        """Build the tour video. Returns the path to the finished mp4."""
        valid_images = [p for p in (self._resolve_image_path(img) for img in self.images) if p]
        if not valid_images:
            raise RuntimeError("No valid, existing images found to build the tour video from")

        if narration_file and Path(narration_file).exists():
            total_duration = MP3(str(narration_file)).info.length
        else:
            total_duration = 5.0 * len(valid_images)
        per_image_duration = max(total_duration / len(valid_images), 2.0)

        zoom_target = 1.5 if self.enable_360 else 1.1
        zoom_step = 0.0015 * self.camera_speed

        segments = []
        for i, img in enumerate(valid_images):
            segment_file = self.output_dir / f"segment_{i}.mp4"
            cmd = [
                FFMPEG_BINARY, "-y",
                "-loop", "1", "-i", str(img),
                "-t", str(per_image_duration),
                "-vf",
                f"scale={self.resolution.replace('x', ':')}:force_original_aspect_ratio=increase,"
                f"crop={self.resolution.replace('x', ':')},"
                f"zoompan=z='min(zoom+{zoom_step},{zoom_target})':d={int(per_image_duration * self.fps)}:s={self.resolution}",
                "-c:v", "libx264", "-r", str(self.fps), "-pix_fmt", "yuv420p",
                str(segment_file),
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            segments.append(segment_file)

        concat_file = self.output_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for seg in segments:
                f.write(f"file '{seg.name}'\n")

        silent_video = self.output_dir / "silent_video.mp4"
        subprocess.run(
            [FFMPEG_BINARY, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(silent_video)],
            check=True, capture_output=True,
        )

        output_file = self.output_dir / "tour_video.mp4"

        if narration_file and Path(narration_file).exists():
            music_file = None
            if music_track:
                candidate = Path("music_library") / f"{music_track}.mp3"
                if candidate.exists():
                    music_file = candidate

            if music_file:
                cmd = [
                    FFMPEG_BINARY, "-y",
                    "-i", str(silent_video), "-i", str(narration_file), "-i", str(music_file),
                    "-filter_complex", "[2:a]volume=0.25[bg];[1:a][bg]amix=inputs=2:duration=first[a]",
                    "-map", "0:v", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac", "-shortest",
                    str(output_file),
                ]
            else:
                cmd = [
                    FFMPEG_BINARY, "-y",
                    "-i", str(silent_video), "-i", str(narration_file),
                    "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-shortest",
                    str(output_file),
                ]
            subprocess.run(cmd, check=True, capture_output=True)
        else:
            silent_video.rename(output_file)

        for seg in segments:
            seg.unlink(missing_ok=True)
        concat_file.unlink(missing_ok=True)
        if silent_video.exists() and silent_video != output_file:
            silent_video.unlink(missing_ok=True)

        return str(output_file)


# Global instance (kept for any code that imports it directly)
video_generator = None
