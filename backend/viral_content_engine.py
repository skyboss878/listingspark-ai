"""
Real360 AI - Viral Content Engine
Automatically generates viral-ready social media content from property tours
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class SocialPlatform:
    INSTAGRAM_REELS = "instagram_reels"
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    FACEBOOK = "facebook"
    INSTAGRAM_FEED = "instagram_feed"
    LINKEDIN = "linkedin"


class ViralContentEngine:
    """Engine for generating viral social media content"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None
        
        if self.api_key and OPENAI_AVAILABLE:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.enabled = True
            logger.info("✅ Viral Content Engine initialized")
        else:
            self.enabled = False
            logger.warning("⚠️ Viral Content Engine disabled")
    
    async def generate_viral_caption(
        self,
        property_details: Dict[str, Any],
        tone: str = "excited",
        platform: str = SocialPlatform.INSTAGRAM_REELS
    ) -> Dict[str, Any]:
        """Generate viral caption with emotional hooks"""
        
        if not self.enabled:
            return self._fallback_caption(property_details, platform)
        
        try:
            prompt = f"""Create a VIRAL social media caption for this property listing:

Property Details:
- Address: {property_details.get('address')}
- Price: ${property_details.get('price', 0):,}
- Bedrooms: {property_details.get('bedrooms')}
- Bathrooms: {property_details.get('bathrooms')}
- Square Feet: {property_details.get('square_feet'):,}
- Features: {', '.join(property_details.get('features', [])[:5])}

Platform: {platform}
Tone: {tone} and persuasive

Create a caption that:
1. Starts with an attention-grabbing hook
2. Uses emotional language and storytelling
3. Highlights the "can't miss" factor
4. Includes strategic emojis
5. Ends with a strong call-to-action
6. Is optimized for {platform}

Provide JSON with:
- hook: Opening line (eye-catching)
- body: Main caption (2-3 sentences)
- cta: Call to action
- full_caption: Complete caption with emojis
- hashtags: 10-15 trending relevant hashtags
- best_post_time: Optimal posting time
- engagement_tips: Tips to boost engagement"""

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a viral real estate social media expert who creates content that gets massive engagement."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Viral caption generation error: {e}")
            return self._fallback_caption(property_details, platform)
    
    def _fallback_caption(self, property_details: Dict[str, Any], platform: str) -> Dict[str, Any]:
        """Fallback viral caption when AI unavailable"""
        
        price = property_details.get('price', 0)
        bedrooms = property_details.get('bedrooms', 0)
        city = property_details.get('city', 'this area')
        
        captions = {
            SocialPlatform.INSTAGRAM_REELS: {
                'hook': '🚨 STOP SCROLLING! This is THE ONE! 🏠✨',
                'body': f'Imagine waking up in this STUNNING {bedrooms}-bedroom dream home in {city}! Every room tells a story of luxury and comfort. Priced at ${price:,} - this is your chance to own paradise! 🌟',
                'cta': '👉 DM me NOW for a private showing before it\'s gone! Link in bio! 📩',
                'full_caption': f'🚨 STOP SCROLLING! This is THE ONE! 🏠✨\n\nImagine waking up in this STUNNING {bedrooms}-bedroom dream home in {city}! Every room tells a story of luxury and comfort. Priced at ${price:,} - this is your chance to own paradise! 🌟\n\n👉 DM me NOW for a private showing before it\'s gone! Link in bio! 📩',
                'hashtags': ['#DreamHome', '#RealEstate', '#HouseHunting', '#NewListing', '#HomeTour', f'#{city}Homes', '#RealEstateAgent', '#PropertyTour', '#LuxuryHomes', '#HomeGoals'],
                'best_post_time': '7-9 PM (peak engagement time)',
                'engagement_tips': 'Post during evening hours, use trending audio, ask viewers to save/share'
            },
            SocialPlatform.TIKTOK: {
                'hook': 'POV: You just found your DREAM HOME 😍🏠',
                'body': f'{bedrooms} bedrooms of pure perfection in {city}! Every corner is Instagram-worthy! ${price:,} for THIS?! 🤯',
                'cta': 'Comment "MINE" if you want a private tour! 👇',
                'full_caption': f'POV: You just found your DREAM HOME 😍🏠\n\n{bedrooms} bedrooms of pure perfection in {city}! Every corner is Instagram-worthy! ${price:,} for THIS?! 🤯\n\nComment "MINE" if you want a private tour! 👇',
                'hashtags': ['#realestate', '#hometour', '#dreamhome', '#housetok', '#realestatetiktok', f'#{city.lower()}', '#property', '#newhome', '#homegoals', '#foryou'],
                'best_post_time': '12-2 PM or 7-9 PM',
                'engagement_tips': 'Use trending sounds, create suspense with transitions, engage in comments'
            },
            SocialPlatform.YOUTUBE_SHORTS: {
                'hook': 'Wait until you see inside! 🤩',
                'body': f'Full tour of this {bedrooms}-bed, {property_details.get("bathrooms")}-bath beauty in {city}! The kitchen will blow your mind! 🏠',
                'cta': 'Subscribe for more amazing property tours! 🔔',
                'full_caption': f'Wait until you see inside! 🤩\n\nFull tour of this {bedrooms}-bed, {property_details.get("bathrooms")}-bath beauty in {city}! The kitchen will blow your mind! 🏠\n\nSubscribe for more amazing property tours! 🔔',
                'hashtags': ['#shorts', '#realestate', '#hometour', '#propertytour', '#dreamhome', f'#{city}realestate', '#luxuryhome', '#realestateagent'],
                'best_post_time': '3-5 PM (after-school hours)',
                'engagement_tips': 'Hook within first 2 seconds, use text overlays, end with clear CTA'
            }
        }
        
        return captions.get(platform, captions[SocialPlatform.INSTAGRAM_REELS])
    
    async def generate_platform_strategy(
        self,
        property_details: Dict[str, Any],
        tour_duration: int = 60
    ) -> Dict[str, Any]:
        """Generate complete multi-platform posting strategy"""
        
        strategy = {
            'property_id': property_details.get('id'),
            'platforms': [],
            'posting_schedule': [],
            'content_variations': [],
            'engagement_goals': {}
        }
        
        # Analyze property type and price to determine best platforms
        price = property_details.get('price', 0)
        
        platforms_priority = []
        
        # High-energy platforms for all properties
        if tour_duration <= 60:
            platforms_priority.extend([
                {
                    'platform': SocialPlatform.INSTAGRAM_REELS,
                    'priority': 'HIGH',
                    'reason': 'Best reach and engagement',
                    'format': '9:16 vertical, 15-60s',
                    'expected_reach': '5,000-50,000 views'
                },
                {
                    'platform': SocialPlatform.TIKTOK,
                    'priority': 'HIGH',
                    'reason': 'Viral potential',
                    'format': '9:16 vertical, 15-60s',
                    'expected_reach': '10,000-100,000+ views'
                }
            ])
        
        # YouTube Shorts for all
        platforms_priority.append({
            'platform': SocialPlatform.YOUTUBE_SHORTS,
            'priority': 'MEDIUM',
            'reason': 'Long-term discovery',
            'format': '9:16 vertical, up to 60s',
            'expected_reach': '2,000-20,000 views'
        })
        
        # Facebook for higher-end properties
        if price > 500000:
            platforms_priority.append({
                'platform': SocialPlatform.FACEBOOK,
                'priority': 'MEDIUM',
                'reason': 'Homebuyer demographic',
                'format': '1:1 or 4:5, any duration',
                'expected_reach': '1,000-10,000 views'
            })
        
        # LinkedIn for luxury properties
        if price > 1000000:
            platforms_priority.append({
                'platform': SocialPlatform.LINKEDIN,
                'priority': 'LOW',
                'reason': 'High-net-worth audience',
                'format': '16:9 or 1:1, professional',
                'expected_reach': '500-5,000 views'
            })
        
        strategy['platforms'] = platforms_priority
        
        # Create posting schedule
        strategy['posting_schedule'] = [
            {
                'day': 'Day 1',
                'time': '7:00 PM',
                'platform': SocialPlatform.INSTAGRAM_REELS,
                'caption_tone': 'excited',
                'notes': 'Post during peak engagement time'
            },
            {
                'day': 'Day 1',
                'time': '8:00 PM',
                'platform': SocialPlatform.TIKTOK,
                'caption_tone': 'energetic',
                'notes': 'Use trending sound, slightly different hook than Instagram'
            },
            {
                'day': 'Day 2',
                'time': '12:00 PM',
                'platform': SocialPlatform.YOUTUBE_SHORTS,
                'caption_tone': 'informative',
                'notes': 'Lunchtime browsing audience'
            },
            {
                'day': 'Day 2',
                'time': '6:00 PM',
                'platform': SocialPlatform.FACEBOOK,
                'caption_tone': 'professional',
                'notes': 'Evening family browsing time'
            }
        ]
        
        # Engagement goals
        strategy['engagement_goals'] = {
            'total_views_target': '20,000+',
            'engagement_rate_target': '5-10%',
            'saves_target': '500+',
            'shares_target': '200+',
            'comments_target': '100+',
            'leads_target': '10-20 inquiries'
        }
        
        return strategy
    
    async def generate_viral_clips(
        self,
        full_tour_path: str,
        viral_moments: List[Dict[str, Any]],
        property_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate multiple short viral clips from full tour"""
        
        clips = []
        
        for i, moment in enumerate(viral_moments):
            clip_data = {
                'clip_id': f"clip_{i+1}",
                'source_video': full_tour_path,
                'start_time': moment.get('timestamp_start', 0),
                'end_time': moment.get('timestamp_end', 15),
                'duration': moment.get('duration', 15),
                'room_focus': moment.get('room'),
                'suggested_caption': moment.get('caption'),
                'hashtags': moment.get('suggested_hashtags', []),
                'platforms': moment.get('best_platforms', []),
                'cta': moment.get('cta'),
                'effects': {
                    'music': 'upbeat_trending',
                    'text_overlays': [
                        {'text': f"${property_details.get('price', 0):,}", 'timestamp': 2, 'position': 'top'},
                        {'text': moment.get('caption', ''), 'timestamp': 5, 'position': 'bottom'}
                    ],
                    'transitions': 'smooth_fade',
                    'filters': 'bright_and_vibrant'
                },
                'auto_schedule': {
                    'enabled': True,
                    'preferred_time': '7:00 PM',
                    'wait_for_wifi': True
                }
            }
            
            clips.append(clip_data)
        
        return clips
    
    def get_trending_hashtags(self, category: str = 'real_estate') -> List[str]:
        """Get current trending hashtags"""
        
        trending = {
            'real_estate': [
                '#RealEstate', '#DreamHome', '#HouseHunting', '#NewListing',
                '#HomeTour', '#RealEstateAgent', '#PropertyTour', '#LuxuryHomes',
                '#HomeGoals', '#RealEstateLife', '#HomeSweetHome', '#Realtor',
                '#HouseForSale', '#OpenHouse', '#RealEstateInvesting'
            ],
            'luxury': [
                '#LuxuryRealEstate', '#LuxuryHomes', '#LuxuryLiving', '#MansionTour',
                '#MillionDollarListing', '#LuxuryProperty', '#HighEndRealEstate',
                '#DreamHouse', '#LuxuryLifestyle', '#ModernLuxury'
            ],
            'modern': [
                '#ModernHome', '#ContemporaryDesign', '#ModernArchitecture',
                '#MinimalistHome', '#CleanDesign', '#ModernLiving'
            ]
        }
        
        return trending.get(category, trending['real_estate'])


# Global instance
_viral_engine = None

def get_viral_engine() -> ViralContentEngine:
    """Get or create Viral Content Engine instance"""
    global _viral_engine
    if _viral_engine is None:
        _viral_engine = ViralContentEngine()
    return _viral_engine
