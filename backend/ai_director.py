"""
Real360 AI Director Mode
AI-powered cinematography director for real estate tours
Guides realtors through optimal camera movements and selling moments
"""

import os
import logging
from typing import Dict, List, Optional, Any
from enum import Enum
import json

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class RoomType(str, Enum):
    ENTRANCE = "entrance"
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    DINING_ROOM = "dining_room"
    BEDROOM = "bedroom"
    BATHROOM = "bathroom"
    OUTDOOR = "outdoor"
    GARAGE = "garage"
    OFFICE = "office"
    BASEMENT = "basement"


class CameraAngle(str, Enum):
    WIDE_SHOT = "wide_shot"
    MEDIUM_SHOT = "medium_shot"
    DETAIL_SHOT = "detail_shot"
    PAN_LEFT = "pan_left"
    PAN_RIGHT = "pan_right"
    TILT_UP = "tilt_up"
    TILT_DOWN = "tilt_down"
    DOLLY_IN = "dolly_in"
    DOLLY_OUT = "dolly_out"


class ViralMomentType(str, Enum):
    REVEAL = "reveal"
    TRANSITION = "transition"
    FEATURE_HIGHLIGHT = "feature_highlight"
    LIFESTYLE_MOMENT = "lifestyle_moment"
    DRAMATIC_VIEW = "dramatic_view"


class AIDirector:
    """AI Director for guided real estate tour filming"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key and OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.enabled = True
            logger.info("✅ AI Director Mode initialized")
        else:
            self.enabled = False
            logger.warning("⚠️ AI Director Mode disabled - OpenAI not available")
    
    async def generate_shot_guidance(
        self,
        room_type: RoomType,
        property_details: Dict[str, Any],
        current_position: str = "entrance"
    ) -> Dict[str, Any]:
        """Generate real-time shot guidance for the realtor"""
        
        if not self.enabled:
            return self._fallback_guidance(room_type)
        
        try:
            prompt = f"""You are a professional real estate cinematographer guiding a realtor through filming a property tour.

Property Details:
- Type: {property_details.get('property_type', 'single_family')}
- Price: ${property_details.get('price', 0):,}
- Bedrooms: {property_details.get('bedrooms', 0)}
- Features: {', '.join(property_details.get('features', []))}

Current Room: {room_type}
Current Position: {current_position}

Provide guidance in JSON format with:
1. camera_angle: Best angle to use (wide_shot, medium_shot, detail_shot, pan, tilt, dolly)
2. verbal_direction: Concise, friendly instruction (max 2 sentences)
3. key_features: List of 3 features to highlight in this room
4. movement_speed: slow/medium/fast
5. duration_seconds: How long to film this shot (5-15 seconds)
6. next_move: Where to move camera next
7. is_viral_moment: true/false - is this a potential viral clip?
8. viral_caption: If viral moment, suggest a caption

Keep directions natural and encouraging like a helpful cinematographer on set."""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert real estate cinematographer providing shot-by-shot guidance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            guidance = json.loads(response.choices[0].message.content)
            return guidance
            
        except Exception as e:
            logger.error(f"AI Director error: {e}")
            return self._fallback_guidance(room_type)
    
    def _fallback_guidance(self, room_type: RoomType) -> Dict[str, Any]:
        """Fallback guidance when AI is not available"""
        
        guidance_map = {
            RoomType.ENTRANCE: {
                "camera_angle": "wide_shot",
                "verbal_direction": "Start with a wide shot from the entrance. Pan slowly from left to right to capture the full space and natural light.",
                "key_features": ["Front door design", "Entry flooring", "Natural lighting"],
                "movement_speed": "slow",
                "duration_seconds": 8,
                "next_move": "living_room",
                "is_viral_moment": True,
                "viral_caption": "First impressions matter! 🏠✨ Watch this stunning entrance reveal."
            },
            RoomType.KITCHEN: {
                "camera_angle": "detail_shot",
                "verbal_direction": "Focus on the kitchen island first. Then pan to appliances and countertops. Make it feel inviting and functional.",
                "key_features": ["Kitchen island", "Stainless appliances", "Granite countertops"],
                "movement_speed": "medium",
                "duration_seconds": 12,
                "next_move": "dining_room",
                "is_viral_moment": True,
                "viral_caption": "Chef's dream kitchen! 👨‍🍳 Everything you need in one perfect space."
            },
            RoomType.LIVING_ROOM: {
                "camera_angle": "wide_shot",
                "verbal_direction": "Capture the entire living area. Highlight windows, ceiling height, and flow. Move slowly to show spaciousness.",
                "key_features": ["Open floor plan", "Natural light", "Ceiling height"],
                "movement_speed": "slow",
                "duration_seconds": 10,
                "next_move": "kitchen",
                "is_viral_moment": True,
                "viral_caption": "Space to live, laugh, and love! ❤️ Look at this living room!"
            },
            RoomType.BEDROOM: {
                "camera_angle": "medium_shot",
                "verbal_direction": "Start at the doorway showing the bed placement. Then highlight closet space and windows. Keep it peaceful and inviting.",
                "key_features": ["Room size", "Closet space", "Window views"],
                "movement_speed": "medium",
                "duration_seconds": 8,
                "next_move": "bathroom",
                "is_viral_moment": False,
                "viral_caption": ""
            },
            RoomType.BATHROOM: {
                "camera_angle": "detail_shot",
                "verbal_direction": "Showcase the vanity, then the shower/tub, and finally the fixtures. Keep movements smooth and highlight luxury features.",
                "key_features": ["Vanity", "Shower/tub", "Tile work"],
                "movement_speed": "slow",
                "duration_seconds": 7,
                "next_move": "next_bedroom",
                "is_viral_moment": False,
                "viral_caption": ""
            },
            RoomType.OUTDOOR: {
                "camera_angle": "wide_shot",
                "verbal_direction": "Start with the backyard view. Pan across the space showing the full outdoor area. Capture lifestyle potential!",
                "key_features": ["Yard size", "Outdoor features", "Privacy"],
                "movement_speed": "slow",
                "duration_seconds": 10,
                "next_move": "conclusion",
                "is_viral_moment": True,
                "viral_caption": "Your private outdoor paradise! 🌳☀️ Perfect for entertaining!"
            }
        }
        
        return guidance_map.get(room_type, guidance_map[RoomType.ENTRANCE])
    
    async def generate_viral_moments(
        self,
        tour_data: Dict[str, Any],
        all_shots: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify and extract viral moment clips from the full tour"""
        
        viral_moments = []
        
        for i, shot in enumerate(all_shots):
            if shot.get('is_viral_moment'):
                viral_moments.append({
                    'clip_id': f"viral_{i}",
                    'timestamp_start': shot.get('timestamp_start', 0),
                    'timestamp_end': shot.get('timestamp_end', 15),
                    'duration': shot.get('duration_seconds', 15),
                    'room': shot.get('room_type'),
                    'caption': shot.get('viral_caption'),
                    'suggested_hashtags': self._generate_hashtags(shot, tour_data),
                    'best_platforms': self._suggest_platforms(shot),
                    'cta': self._generate_cta(tour_data)
                })
        
        return viral_moments
    
    def _generate_hashtags(self, shot: Dict[str, Any], tour_data: Dict[str, Any]) -> List[str]:
        """Generate trending hashtags for the shot"""
        
        base_tags = ['#RealEstate', '#DreamHome', '#HouseHunting', '#NewListing']
        
        # Add room-specific tags
        room = shot.get('room_type', '')
        if 'kitchen' in room.lower():
            base_tags.extend(['#KitchenGoals', '#ModernKitchen', '#HomeDesign'])
        elif 'living' in room.lower():
            base_tags.extend(['#LivingRoom', '#HomeInspiration', '#InteriorDesign'])
        elif 'outdoor' in room.lower():
            base_tags.extend(['#BackyardGoals', '#OutdoorLiving', '#HomeExterior'])
        
        # Add price-based tags
        price = tour_data.get('price', 0)
        if price > 1000000:
            base_tags.extend(['#LuxuryRealEstate', '#LuxuryHomes'])
        
        # Add location tags
        city = tour_data.get('city', '').replace(' ', '')
        if city:
            base_tags.append(f'#{city}Homes')
        
        return base_tags[:10]
    
    def _suggest_platforms(self, shot: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest best platforms for this viral moment"""
        
        duration = shot.get('duration_seconds', 15)
        
        platforms = []
        
        # Instagram Reels (15-90 seconds)
        if 15 <= duration <= 90:
            platforms.append({
                'platform': 'Instagram Reels',
                'format': '9:16 vertical',
                'max_duration': '90s',
                'priority': 'high'
            })
        
        # TikTok (15-60 seconds)
        if 15 <= duration <= 60:
            platforms.append({
                'platform': 'TikTok',
                'format': '9:16 vertical',
                'max_duration': '60s',
                'priority': 'high'
            })
        
        # YouTube Shorts (up to 60 seconds)
        if duration <= 60:
            platforms.append({
                'platform': 'YouTube Shorts',
                'format': '9:16 vertical',
                'max_duration': '60s',
                'priority': 'medium'
            })
        
        # Facebook/Instagram Feed
        platforms.append({
            'platform': 'Facebook/Instagram Feed',
            'format': '4:5 or 1:1',
            'max_duration': '2min',
            'priority': 'medium'
        })
        
        return platforms
    
    def _generate_cta(self, tour_data: Dict[str, Any]) -> str:
        """Generate call-to-action for the viral clip"""
        
        ctas = [
            "DM me for a private showing! 📩",
            "Link in bio to schedule your tour! 🏠",
            "Don't miss this one! Book your showing today! ✨",
            "Save this before it's gone! 💫",
            "Tag someone who needs to see this! 👇",
            "Your dream home is waiting! Contact me now! 📞"
        ]
        
        import random
        return random.choice(ctas)
    
    async def generate_tour_script(
        self,
        property_details: Dict[str, Any],
        rooms: List[str]
    ) -> Dict[str, Any]:
        """Generate complete tour script with timing and dialogue"""
        
        script = {
            'property_id': property_details.get('id'),
            'total_duration': 0,
            'shots': [],
            'viral_moments': [],
            'music_suggestions': [],
            'opening_hook': '',
            'closing_cta': ''
        }
        
        # Generate opening hook
        price = property_details.get('price', 0)
        bedrooms = property_details.get('bedrooms', 0)
        script['opening_hook'] = f"Welcome to this stunning {bedrooms}-bedroom home! Let me show you why this is THE one you've been waiting for! 🏠✨"
        
        # Generate shot sequence for each room
        for room in rooms:
            room_guidance = await self.generate_shot_guidance(
                RoomType(room),
                property_details
            )
            script['shots'].append(room_guidance)
            script['total_duration'] += room_guidance.get('duration_seconds', 10)
        
        # Add closing
        script['closing_cta'] = "Ready to make this your home? Contact me today to schedule your private showing! Don't let this opportunity slip away! 🔑"
        
        # Suggest background music
        script['music_suggestions'] = [
            {'track': 'Upbeat Modern Pop', 'mood': 'energetic', 'platforms': ['Instagram', 'TikTok']},
            {'track': 'Ambient Luxury', 'mood': 'elegant', 'platforms': ['YouTube', 'Facebook']},
            {'track': 'Cinematic Orchestral', 'mood': 'dramatic', 'platforms': ['YouTube']}
        ]
        
        return script


# Global instance
_ai_director = None

def get_ai_director() -> AIDirector:
    """Get or create AI Director instance"""
    global _ai_director
    if _ai_director is None:
        _ai_director = AIDirector()
    return _ai_director
