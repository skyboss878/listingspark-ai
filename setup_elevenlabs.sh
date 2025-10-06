#!/bin/bash

# Complete ElevenLabs Voice Integration Deployment Script
# This script sets up professional AI voice narration for ListingSpark

set -e  # Exit on error

echo "=========================================="
echo "ElevenLabs Voice Integration Setup"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ]; then
    echo -e "${RED}Error: Please run this script from the listingspark-ai root directory${NC}"
    exit 1
fi

cd backend

# Step 1: Install dependencies
echo -e "\n${YELLOW}Step 1: Installing required Python packages...${NC}"
pip install httpx python-dotenv || {
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
}
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 2: Create elevenlabs_voice.py
echo -e "\n${YELLOW}Step 2: Creating ElevenLabs voice engine...${NC}"

cat > elevenlabs_voice.py << 'VOICEFILE'
import os
import logging
import httpx
from pathlib import Path
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class ElevenLabsVoiceEngine:
    """Professional voice narration using ElevenLabs API"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.enabled = os.getenv("ELEVENLABS_ENABLED", "false").lower() == "true"
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Professional voices for real estate
        self.voices = {
            "professional_female": {
                "id": os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"),
                "name": "Rachel",
                "description": "Warm, professional female voice - perfect for luxury listings"
            },
            "professional_male": {
                "id": "TxGEqnHWrfWFTfGW9XjX",
                "name": "Josh",
                "description": "Confident, authoritative male voice - great for commercial properties"
            },
            "friendly_female": {
                "id": "EXAVITQu4vr4xnSDxMaL",
                "name": "Bella",
                "description": "Friendly, conversational - ideal for family homes"
            },
            "luxury_male": {
                "id": "pNInz6obpgDQGcFmaJgB",
                "name": "Adam",
                "description": "Deep, sophisticated - perfect for high-end estates"
            }
        }
        
        if self.enabled and not self.api_key:
            logger.warning("ElevenLabs enabled but no API key found")
            self.enabled = False
    
    async def generate_narration(
        self,
        text: str,
        voice_id: str = "professional_female",
        output_path: Optional[Path] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> Optional[Path]:
        """Generate professional voice narration"""
        if not self.enabled:
            logger.info("ElevenLabs disabled, skipping narration")
            return None
        
        try:
            voice_config = self.voices.get(voice_id, self.voices["professional_female"])
            actual_voice_id = voice_config["id"]
            
            if output_path is None:
                output_path = Path(f"narration_{voice_id}.mp3")
            
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            url = f"{self.base_url}/text-to-speech/{actual_voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            logger.info(f"Generating narration with voice: {voice_config['name']}")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=data)
                
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Narration saved to: {output_path}")
                    return output_path
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            return None
    
    async def check_quota(self) -> Dict:
        """Check remaining character quota"""
        if not self.enabled:
            return {"quota_remaining": 0, "quota_limit": 0}
        
        try:
            url = f"{self.base_url}/user"
            headers = {"xi-api-key": self.api_key}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "quota_remaining": user_data.get('character_count', 0),
                        "quota_limit": user_data.get('character_limit', 0)
                    }
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
        
        return {"quota_remaining": 0, "quota_limit": 0}

# Initialize global instance
elevenlabs_engine = ElevenLabsVoiceEngine()
VOICEFILE

echo -e "${GREEN}✓ ElevenLabs voice engine created${NC}"

# Step 3: Update .env file
echo -e "\n${YELLOW}Step 3: Updating environment configuration...${NC}"

# Check if ElevenLabs config already exists
if grep -q "ELEVENLABS_API_KEY" .env; then
    echo -e "${YELLOW}ElevenLabs configuration already exists in .env${NC}"
else
    cat >> .env << 'ENVFILE'

# =============================================================================
# ELEVENLABS VOICE NARRATION
# =============================================================================
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_ENABLED=false

# Set ELEVENLABS_ENABLED=true after adding your API key
# Get your key from: https://elevenlabs.io/app/settings/api-keys
ENVFILE
    echo -e "${GREEN}✓ ElevenLabs configuration added to .env${NC}"
    echo -e "${YELLOW}⚠ Don't forget to add your actual API key!${NC}"
fi

# Step 4: Add server.py integration check
echo -e "\n${YELLOW}Step 4: Checking server.py integration...${NC}"

if grep -q "from elevenlabs_voice import elevenlabs_engine" server.py; then
    echo -e "${GREEN}✓ ElevenLabs already integrated in server.py${NC}"
else
    echo -e "${YELLOW}⚠ You need to manually add ElevenLabs endpoints to server.py${NC}"
    echo -e "Add this import at the top:"
    echo -e "${GREEN}from elevenlabs_voice import elevenlabs_engine${NC}"
    echo ""
    echo -e "Then add these endpoints (see artifact for full code)"
fi

# Step 5: Test installation
echo -e "\n${YELLOW}Step 5: Testing ElevenLabs integration...${NC}"

python << 'PYTEST'
import sys
sys.path.insert(0, '.')

try:
    from elevenlabs_voice import elevenlabs_engine
    print("✓ ElevenLabs module imported successfully")
    print(f"✓ Enabled: {elevenlabs_engine.enabled}")
    print(f"✓ Available voices: {len(elevenlabs_engine.voices)}")
    for key, voice in elevenlabs_engine.voices.items():
        print(f"  - {key}: {voice['name']} - {voice['description']}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
PYTEST

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ ElevenLabs integration test passed${NC}"
else
    echo -e "${RED}✗ Integration test failed${NC}"
    exit 1
fi

# Step 6: Commit changes
echo -e "\n${YELLOW}Step 6: Git operations...${NC}"
cd ..

git add backend/elevenlabs_voice.py
git add backend/.env 2>/dev/null || true

echo -e "${GREEN}✓ Files staged for commit${NC}"

# Final instructions
echo -e "\n=========================================="
echo -e "${GREEN}ElevenLabs Integration Complete!${NC}"
echo -e "=========================================="
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Get your ElevenLabs API key:"
echo "   → https://elevenlabs.io/app/settings/api-keys"
echo ""
echo "2. Update backend/.env with your key:"
echo "   ${GREEN}nano backend/.env${NC}"
echo "   Set: ELEVENLABS_API_KEY=your_actual_key"
echo "   Set: ELEVENLABS_ENABLED=true"
echo ""
echo "3. Add endpoints to server.py (see artifact)"
echo ""
echo "4. Commit and deploy:"
echo "   ${GREEN}git commit -m 'Add ElevenLabs voice narration'${NC}"
echo "   ${GREEN}git push origin main${NC}"
echo ""
echo "5. Add env vars to Render dashboard:"
echo "   → ELEVENLABS_API_KEY"
echo "   → ELEVENLABS_ENABLED=true"
echo ""
echo -e "${GREEN}Available Voice Options:${NC}"
echo "  • professional_female (Rachel) - Luxury listings"
echo "  • professional_male (Josh) - Commercial properties"
echo "  • friendly_female (Bella) - Family homes"
echo "  • luxury_male (Adam) - High-end estates"
echo ""
echo -e "${YELLOW}Pricing:${NC}"
echo "  • Free: 10,000 chars/month (~8 tours)"
echo "  • Creator: $22/month - 100,000 chars (recommended)"
echo ""
echo "=========================================="
