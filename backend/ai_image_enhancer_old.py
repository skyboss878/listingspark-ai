"""
AI Image Enhancer for ListingSpark AI
Enhances property images using AI
"""

import os
import logging
from pathlib import Path
from typing import Optional
from PIL import Image, ImageEnhance
import openai

logger = logging.getLogger(__name__)


class AIImageEnhancer:
    """AI-powered image enhancement service"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
            self.enabled = True
            logger.info("✅ AI Image Enhancer initialized")
        else:
            self.enabled = False
            logger.warning("⚠️ OpenAI API key not found - image enhancement disabled")
    
    async def enhance(
        self,
        input_path: str,
        output_dir: str,
        enhance_lighting: bool = True,
        enhance_colors: bool = True,
        remove_clutter: bool = False
    ) -> Optional[str]:
        """Enhance a single image"""
        
        try:
            # Load image
            img = Image.open(input_path)
            
            # Basic enhancements using PIL
            if enhance_lighting:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(1.1)  # Slight brightness increase
            
            if enhance_colors:
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.2)  # Boost colors
                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.1)  # Slight contrast boost
            
            # Save enhanced image
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            filename = Path(input_path).name
            output_file = output_path / f"enhanced_{filename}"
            
            img.save(str(output_file), quality=95, optimize=True)
            logger.info(f"✅ Enhanced image saved to: {output_file}")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ Failed to enhance image {input_path}: {e}")
            return input_path  # Return original on failure
    
    async def batch_enhance(
        self,
        input_paths: list,
        output_dir: str
    ) -> list:
        """Enhance multiple images"""
        
        enhanced_paths = []
        
        for input_path in input_paths:
            enhanced = await self.enhance(input_path, output_dir)
            if enhanced:
                enhanced_paths.append(enhanced)
        
        return enhanced_paths
