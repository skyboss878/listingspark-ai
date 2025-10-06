import os
import logging
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import numpy as np
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AIImageEnhancer:
    """Professional real estate image enhancement"""
    
    def __init__(self):
        self.enabled = True
    
    def enhance_real_estate_photo(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        enhancement_level: str = "standard"
    ) -> Path:
        """Enhance a real estate photo with professional corrections"""
        try:
            img = Image.open(image_path)
            original_format = img.format or 'JPEG'
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Enhancement pipeline
            img = self._auto_levels(img)
            img = self._enhance_lighting(img, enhancement_level)
            img = self._enhance_colors(img, enhancement_level)
            img = self._sharpen(img, enhancement_level)
            img = self._remove_noise(img)
            
            if output_path is None:
                output_path = image_path.parent / f"{image_path.stem}_enhanced{image_path.suffix}"
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            img.save(output_path, format=original_format, quality=95, optimize=True)
            logger.info(f"Enhanced: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return image_path
    
    def _auto_levels(self, img: Image.Image) -> Image.Image:
        """Auto-adjust levels"""
        img_array = np.array(img, dtype=np.float32)
        
        for i in range(3):
            channel = img_array[:, :, i]
            p2, p98 = np.percentile(channel, (2, 98))
            
            if p98 > p2:
                channel = np.clip((channel - p2) * (255 / (p98 - p2)), 0, 255)
                img_array[:, :, i] = channel
        
        return Image.fromarray(img_array.astype(np.uint8))
    
    def _enhance_lighting(self, img: Image.Image, level: str) -> Image.Image:
        """Enhance brightness and contrast"""
        brightness_factors = {"light": 1.05, "standard": 1.1, "aggressive": 1.15}
        contrast_factors = {"light": 1.1, "standard": 1.15, "aggressive": 1.2}
        
        brightness = ImageEnhance.Brightness(img)
        img = brightness.enhance(brightness_factors[level])
        
        contrast = ImageEnhance.Contrast(img)
        img = contrast.enhance(contrast_factors[level])
        
        return img
    
    def _enhance_colors(self, img: Image.Image, level: str) -> Image.Image:
        """Boost color saturation for real estate"""
        saturation_factors = {"light": 1.1, "standard": 1.2, "aggressive": 1.3}
        
        color = ImageEnhance.Color(img)
        img = color.enhance(saturation_factors[level])
        
        return img
    
    def _sharpen(self, img: Image.Image, level: str) -> Image.Image:
        """Apply unsharp mask"""
        if level == "light":
            return img.filter(ImageFilter.UnsharpMask(radius=1, percent=100, threshold=3))
        elif level == "standard":
            return img.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=3))
        else:
            return img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
    
    def _remove_noise(self, img: Image.Image) -> Image.Image:
        """Subtle noise reduction"""
        return img.filter(ImageFilter.MedianFilter(size=3))
    
    def batch_enhance_property_photos(self, image_paths: list, output_dir: Path) -> list:
        """Enhance multiple photos at once"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        enhanced_paths = []
        for i, img_path in enumerate(image_paths):
            output_path = output_dir / f"enhanced_{i:03d}{Path(img_path).suffix}"
            enhanced = self.enhance_real_estate_photo(img_path, output_path)
            enhanced_paths.append(enhanced)
        
        return enhanced_paths

# Global instance
ai_enhancer = AIImageEnhancer()
