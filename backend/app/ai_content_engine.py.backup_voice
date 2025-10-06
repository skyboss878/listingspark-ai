"""
AI Content Engine for Viral Real Estate Content
Uses OpenAI GPT-4 Turbo for generating platform-optimized social media content
"""

import os
import logging
import asyncio
import re
from typing import Dict, List, Optional
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class ViralContentEngine:
    """Generate viral social media content using OpenAI GPT-4"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if self.api_key and self.api_key != 'demo-key-for-testing':
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            logger.warning("OpenAI API key not configured. AI content generation disabled.")
    
    async def generate_viral_content(self, property_data: Dict, platform: str, content_type: str = "caption") -> Dict:
        """Generate viral content for specific social media platforms"""
        
        if not self.enabled:
            return self._generate_fallback_content(property_data, platform, content_type)
        
        try:
            prompt = self._create_platform_prompt(property_data, platform, content_type)
            
            response = await self.client.chat.completions.create(
            model="gpt-4o",
                messages=[
                    {"role": "system", "content": self._get_system_prompt(platform, content_type)},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.85,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            content_text = response.choices[0].message.content
            return self._parse_ai_response(content_text, platform, content_type, property_data)
            
        except Exception as e:
            logger.error(f"Error generating AI content: {e}")
            return self._generate_fallback_content(property_data, platform, content_type)
    
    def _get_system_prompt(self, platform: str, content_type: str) -> str:
        """Get system prompt based on platform and content type"""
        
        base_prompt = """You are a viral real estate social media expert who creates engaging, high-converting content that stops scrollers and generates massive engagement. You understand platform algorithms, trending formats, and psychology of viral content."""
        
        platform_prompts = {
            "instagram": """Focus on:
- Visual storytelling and aspirational language
- 3-5 key highlights in first sentence
- Emoji usage (2-3 relevant ones)
- Call-to-action that encourages saves/shares
- 20-30 strategic hashtags mixing popular and niche
- Engaging question at the end""",
            
            "tiktok": """Focus on:
- Hook in first 3 words that creates curiosity
- Conversational, energetic tone
- Pattern interrupts and unexpected reveals
- Trending audio/format suggestions
- 5-8 viral hashtags
- Challenge or trend integration ideas""",
            
            "facebook": """Focus on:
- Storytelling that evokes emotion
- Longer, detailed narrative
- Community engagement prompts
- Local area highlights
- 8-12 relevant hashtags
- Questions that spark conversations""",
            
            "twitter": """Focus on:
- Punchy, attention-grabbing opening
- Maximum impact in limited characters
- Thread-worthy insights
- 3-5 targeted hashtags
- Engagement-driving hooks"""
        }
        
        return f"{base_prompt}\n\n{platform_prompts.get(platform, '')}"
    
    def _create_platform_prompt(self, property_data: Dict, platform: str, content_type: str) -> str:
        """Create detailed prompt for AI generation"""
        
        tour_info = ""
        if property_data.get('has_tour'):
            tour_info = """
🎯 SPECIAL FEATURE: This property has an INTERACTIVE 360° VIRTUAL TOUR!
This is a HUGE selling point - emphasize that viewers can:
- Explore every room from home
- Experience the space like they're there
- Take a virtual walkthrough anytime
- See every detail in 360 degrees

Make the virtual tour a major highlight in the content!"""
        
        return f"""Create viral {platform} {content_type} for this property:

📍 PROPERTY DETAILS:
Title: {property_data.get('title', 'Stunning Property')}
Address: {property_data.get('address', 'Prime Location')}
Price: {property_data.get('price', 'Contact for pricing')}
Type: {property_data.get('property_type', 'Residential')}
Bedrooms: {property_data.get('bedrooms', 'N/A')}
Bathrooms: {property_data.get('bathrooms', 'N/A')}
Square Feet: {property_data.get('square_feet', 'N/A')}
Description: {property_data.get('description', 'Amazing property with great features')}
Features: {', '.join(property_data.get('features', []))}
{tour_info}

🎯 OBJECTIVE:
Create content that:
1. Stops the scroll immediately
2. Creates FOMO (fear of missing out)
3. Encourages shares, saves, and comments
4. Highlights the virtual tour if available
5. Uses platform-specific viral strategies

Make it authentic, exciting, and irresistible!"""
    
    def _parse_ai_response(self, response: str, platform: str, content_type: str, property_data: Dict) -> Dict:
        """Parse and structure AI-generated content"""
        
        hashtags = re.findall(r'#[\w]+', response)
        viral_score = self._calculate_viral_score(response, hashtags, property_data)
        
        content_lines = response.split('\n')
        clean_content = '\n'.join([line for line in content_lines if not line.strip().startswith(('Note:', 'Remember:', 'Tip:'))])
        
        return {
            'platform': platform,
            'content_type': content_type,
            'content': clean_content.strip(),
            'hashtags': hashtags[:30],
            'viral_score': viral_score,
            'has_tour_mention': property_data.get('has_tour', False),
            'word_count': len(clean_content.split()),
            'char_count': len(clean_content),
            'ai_generated': True
        }
    
    def _calculate_viral_score(self, content: str, hashtags: List[str], property_data: Dict) -> int:
        """Calculate viral potential score (0-100)"""
        
        score = 50
        
        hashtag_count = len(hashtags)
        if 10 <= hashtag_count <= 25:
            score += 10
        elif hashtag_count > 0:
            score += 5
        
        word_count = len(content.split())
        if 50 <= word_count <= 150:
            score += 8
        elif 30 <= word_count <= 200:
            score += 5
        
        emoji_count = len(re.findall(r'[^\w\s,]', content))
        if 3 <= emoji_count <= 8:
            score += 7
        
        if '?' in content:
            score += 5
        
        cta_keywords = ['link in bio', 'dm', 'contact', 'book', 'schedule', 'visit']
        if any(keyword in content.lower() for keyword in cta_keywords):
            score += 5
        
        if property_data.get('has_tour'):
            score += 15
            if any(term in content.lower() for term in ['360', 'virtual', 'tour', 'explore']):
                score += 5
        
        first_words = ' '.join(content.split()[:10]).lower()
        hook_words = ['imagine', 'stop', 'wait', 'omg', 'wow', 'just', 'this']
        if any(word in first_words for word in hook_words):
            score += 5
        
        return min(score, 100)
    
    def _generate_fallback_content(self, property_data: Dict, platform: str, content_type: str) -> Dict:
        """Generate fallback content when AI is unavailable"""
        
        tour_section = ""
        if property_data.get('has_tour'):
            tour_section = """

🔄 INTERACTIVE 360° VIRTUAL TOUR AVAILABLE!
👉 Explore every room from anywhere
👉 Experience the space like you're there
👉 See every detail in immersive 360°

No need to wait for a showing - take the tour NOW! 🏠✨"""
        
        templates = {
            'instagram': f"""🏠✨ YOUR DREAM HOME AWAITS ✨

📍 {property_data.get('address', 'Prime Location')}
💰 {property_data.get('price', 'Incredible Value')}
🛏️ {property_data.get('bedrooms', 'Multiple')} Bed | 🛁 {property_data.get('bathrooms', 'Multiple')} Bath
📐 {property_data.get('square_feet', 'Spacious')} sq ft

{property_data.get('description', 'This stunning property offers everything you need for luxury living!')}{tour_section}

This won't last long! 🔥

#RealEstate #DreamHome #HomeForSale #LuxuryRealEstate #PropertyListing #NewListing #HouseHunting #RealEstateAgent #HomeSweetHome #PropertyForSale #RealEstateInvesting #ModernHome #LuxuryProperty #VirtualTour #360Tour #RealEstateLife #PropertyGoals #HomeGoals #InstaHome #RealEstateMarketing""",
            
            'tiktok': f"""STOP SCROLLING! 🛑

This {property_data.get('property_type', 'property')} is UNREAL 😍

📍 {property_data.get('address', 'Amazing Location')}
💵 {property_data.get('price', "You Won't Believe")}
{property_data.get('description', "Everything you've been dreaming of!")}{tour_section}
Who's ready to move in? 🙋‍♀️

#RealEstateTikTok #HouseTour #DreamHome #PropertyTour #RealEstate #NewListing #VirtualTour #360Home #HouseTok""",
            
            'facebook': f"""🏡 JUST LISTED - Don't Miss This One! 🏡

Looking for your perfect home? This might be THE ONE!

🌟 Location: {property_data.get('address', 'Prime Area')}
🌟 Price: {property_data.get('price', 'Great Value')}
🌟 Details: {property_data.get('bedrooms', 'Multiple')} bedrooms, {property_data.get('bathrooms', 'Multiple')} bathrooms

{property_data.get('description', 'This incredible property has everything you need and more!')}{tour_section}

Interested? Let's talk! Drop a comment or send us a message.

What's your favorite feature? 👇

#RealEstate #HomeForSale #Property #NewListing #DreamHome #VirtualTour #360PropertyTour #HomeBuying #RealEstateAgent #PropertyListing""",
            
            'twitter': f"""🚨 JUST LISTED 🚨

{property_data.get('title', 'Stunning Property')}
📍 {property_data.get('address', 'Prime Location')}
💰 {property_data.get('price', 'Amazing Value')}

{property_data.get('description', 'Incredible opportunity!')[:100]}...

{'🔄 360° Virtual Tour Available!' if property_data.get('has_tour') else ''}

#RealEstate #Property #HomeForSale #VirtualTour"""
        }
        
        content = templates.get(platform, templates['instagram'])
        hashtags = re.findall(r'#[\w]+', content)
        viral_score = 75 if property_data.get('has_tour') else 65
        
        return {
            'platform': platform,
            'content_type': content_type,
            'content': content,
            'hashtags': hashtags,
            'viral_score': viral_score,
            'has_tour_mention': property_data.get('has_tour', False),
            'word_count': len(content.split()),
            'char_count': len(content),
            'ai_generated': False
        }
    
    async def generate_batch_content(self, property_data: Dict, platforms: List[str] = None) -> Dict[str, Dict]:
        """Generate content for multiple platforms simultaneously"""
        
        if platforms is None:
            platforms = ['instagram', 'tiktok', 'facebook', 'twitter']
        
        tasks = [self.generate_viral_content(property_data, platform) for platform in platforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        content_dict = {}
        for platform, result in zip(platforms, results):
            if isinstance(result, Exception):
                logger.error(f"Error generating content for {platform}: {result}")
                content_dict[platform] = self._generate_fallback_content(property_data, platform, "caption")
            else:
                content_dict[platform] = result
        
        return content_dict
    
    async def optimize_content(self, content: str, platform: str, optimization_goal: str = "engagement") -> Dict:
        """Optimize existing content for better performance"""
        
        if not self.enabled:
            return {'optimized': False, 'original': content, 'message': 'AI optimization not available'}
        
        try:
            prompt = f"""Optimize this {platform} content for maximum {optimization_goal}:

ORIGINAL CONTENT:
{content}

INSTRUCTIONS:
1. Maintain the core message
2. Improve hook and engagement
3. Optimize hashtag strategy
4. Add compelling CTA
5. Enhance readability

Provide ONLY the optimized content, no explanations."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a social media optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.7
            )
            
            optimized_content = response.choices[0].message.content.strip()
            
            return {
                'optimized': True,
                'original': content,
                'optimized_content': optimized_content,
                'platform': platform,
                'optimization_goal': optimization_goal
            }
            
        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return {'optimized': False, 'original': content, 'error': str(e)}
