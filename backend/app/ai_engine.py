"""
Production-Ready AI Content Generation Engine
Uses OpenAI GPT-4 for viral real estate content creation
"""
import os
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import json
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIContentEngine:
    """Advanced AI-powered content generation for real estate listings"""
    
    PLATFORM_CONFIGS = {
        "instagram": {
            "max_length": 2200,
            "hashtags": (15, 30),
            "tone": "visual, aspirational, lifestyle-focused",
            "emoji_density": "high"
        },
        "tiktok": {
            "max_length": 300,
            "hashtags": (5, 10),
            "tone": "energetic, trendy, authentic",
            "emoji_density": "moderate"
        },
        "facebook": {
            "max_length": 5000,
            "hashtags": (3, 8),
            "tone": "informative, community-focused, detailed",
            "emoji_density": "low"
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if self.api_key and self.api_key != 'demo-key-for-testing':
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("OpenAI API key not configured. Using demo content.")
    
    async def generate_viral_content(
        self,
        property_data: Dict,
        platform: str,
        include_tour_cta: bool = False
    ) -> Dict:
        """Generate platform-optimized viral content"""
        try:
            if not self.enabled:
                return self._generate_demo_content(property_data, platform, include_tour_cta)
            
            config = self.PLATFORM_CONFIGS.get(platform, self.PLATFORM_CONFIGS["instagram"])
            
            tour_emphasis = ""
            if include_tour_cta:
                tour_emphasis = "\n\nCRITICAL: This property has an INTERACTIVE 360° VIRTUAL TOUR! Make this a major selling point."
            
            prompt = f"""Create viral {platform} content for this property:

Title: {property_data.get('title')}
Address: {property_data.get('address')}
Price: {property_data.get('price')}
Type: {property_data.get('property_type')}
Beds/Baths: {property_data.get('bedrooms')}/{property_data.get('bathrooms')}
Size: {property_data.get('square_feet')} sq ft
Description: {property_data.get('description')}
Features: {', '.join(property_data.get('features', []))}{tour_emphasis}

Create engaging content with {config['hashtags'][0]}-{config['hashtags'][1]} hashtags. Tone: {config['tone']}."""

            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": f"You are a viral real estate marketing expert for {platform}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            import re
            hashtags = re.findall(r'#\w+', content)
            
            viral_score = 50 + len(hashtags) * 3 + len(content.split()) // 15
            if include_tour_cta:
                viral_score += 15
            viral_score = min(viral_score, 100)
            
            return {
                "platform": platform,
                "content": content,
                "hashtags": hashtags[:30],
                "viral_score": viral_score,
                "ai_generated": True
            }
            
        except Exception as e:
            logger.error(f"AI generation error: {e}")
            return self._generate_demo_content(property_data, platform, include_tour_cta)
    
    def _generate_demo_content(
        self,
        property_data: Dict,
        platform: str,
        include_tour_cta: bool
    ) -> Dict:
        """Fallback demo content when API is not available"""
        has_tour = include_tour_cta or property_data.get('has_tour', False)
        tour_text = "\n\nVIRTUAL 360° TOUR AVAILABLE!\nExplore every room interactively!" if has_tour else ""
        
        title = property_data.get('title', 'Stunning Property')
        
        if platform == "tiktok":
            content = f"""POV: You found your DREAM HOME

{title}
{property_data.get('price')}
{property_data.get('bedrooms')}BR | {property_data.get('bathrooms')}BA{tour_text}

Tag someone who needs to see this!

#RealEstate #DreamHome #HouseTour #PropertyTour #NewListing"""
        
        elif platform == "facebook":
            content = f"""JUST LISTED: {title}

Location: {property_data.get('address')}
Price: {property_data.get('price')}
Bedrooms: {property_data.get('bedrooms')}
Bathrooms: {property_data.get('bathrooms')}
Square Footage: {property_data.get('square_feet')}

{property_data.get('description', 'Beautiful property with amazing features!')}{tour_text}

Contact us today to schedule a viewing!

#RealEstate #JustListed #HomeForSale #PropertyForSale"""
        
        else:  # Instagram default
            content = f"""{title.upper()}

{property_data.get('address')}
{property_data.get('price')}
{property_data.get('bedrooms')} beds | {property_data.get('bathrooms')} baths

{property_data.get('description', 'Beautiful property')}{tour_text}

Don't miss this opportunity!

#RealEstate #DreamHome #Property #HomeForSale #VirtualTour #NewListing #{platform.title()}Ready #LuxuryLiving"""
        
        return {
            "platform": platform,
            "content": content,
            "hashtags": ['#RealEstate', '#DreamHome', '#Property', '#HomeForSale'],
            "viral_score": 85 if has_tour else 70,
            "ai_generated": False
        }
