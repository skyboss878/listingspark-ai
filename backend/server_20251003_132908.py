from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware  
import os
import logging
import uuid
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import asyncio
import aiofiles
import sqlite3
import aiosqlite
import openai
from PIL import Image
import cv2
import numpy as np

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create directories
UPLOAD_DIR = ROOT_DIR / "uploads"
TOURS_DIR = ROOT_DIR / "tours"
UPLOAD_DIR.mkdir(exist_ok=True)
TOURS_DIR.mkdir(exist_ok=True)

# OpenAI configuration
openai.api_key = os.environ.get('OPENAI_API_KEY', 'demo-key-for-testing')

# Create the main app
app = FastAPI(title="ListingSpark AI", description="Transform boring property listings into viral social media gold")

# Mount static files for tours
app.mount("/tours", StaticFiles(directory=str(TOURS_DIR)), name="tours")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Database setup
DATABASE_PATH = "listingspark.db"

async def init_db():
    """Initialize SQLite database with tables"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                listings_created INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                total_shares INTEGER DEFAULT 0,
                viral_score_average REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Properties table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS properties (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                address TEXT NOT NULL,
                price TEXT NOT NULL,
                property_type TEXT NOT NULL,
                bedrooms INTEGER,
                bathrooms REAL,
                square_feet INTEGER,
                features TEXT,
                has_tour BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Virtual tours table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS virtual_tours (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                tour_name TEXT NOT NULL,
                tour_url TEXT NOT NULL,
                thumbnail_url TEXT,
                processing_status TEXT DEFAULT 'pending',
                tour_type TEXT DEFAULT '360_image',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        
        # Tour scenes table for multi-room tours
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tour_scenes (
                id TEXT PRIMARY KEY,
                tour_id TEXT NOT NULL,
                scene_name TEXT NOT NULL,
                image_url TEXT NOT NULL,
                scene_order INTEGER DEFAULT 0,
                hotspots TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tour_id) REFERENCES virtual_tours (id)
            )
        """)
        
        # Viral content table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS viral_content (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content TEXT NOT NULL,
                viral_score INTEGER NOT NULL,
                hashtags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        
        # Analytics table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                property_id TEXT PRIMARY KEY,
                views INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                engagement_rate REAL DEFAULT 0.0,
                viral_score INTEGER DEFAULT 0,
                tour_views INTEGER DEFAULT 0,
                trending_status TEXT DEFAULT 'normal',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        
        await db.commit()

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    plan: str = "free"
    listings_created: int = 0
    total_views: int = 0
    total_shares: int = 0
    viral_score_average: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str

class Property(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    description: str
    address: str
    price: str
    property_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    features: List[str] = []
    has_tour: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PropertyCreate(BaseModel):
    title: str
    description: str
    address: str
    price: str
    property_type: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    features: List[str] = []

class VirtualTour(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    tour_name: str
    tour_url: str
    thumbnail_url: Optional[str] = None
    processing_status: str = "pending"
    tour_type: str = "360_image"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TourScene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tour_id: str
    scene_name: str
    image_url: str
    scene_order: int = 0
    hotspots: List[Dict] = []

class ViralContent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    property_id: str
    platform: str
    content_type: str
    content: str
    viral_score: int
    hashtags: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

# 360 Image Processing
class Tour360Processor:
    @staticmethod
    def validate_360_image(image_path: str) -> bool:
        """Validate if image is suitable for 360 viewing"""
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                # Check if aspect ratio is 2:1 (typical for equirectangular 360 images)
                aspect_ratio = width / height
                return 1.8 <= aspect_ratio <= 2.2 and width >= 2048
        except:
            return False
    
    @staticmethod
    async def process_360_image(image_path: str, tour_id: str) -> dict:
        """Process uploaded 360 image"""
        try:
            # Create tour directory
            tour_dir = TOURS_DIR / tour_id
            tour_dir.mkdir(exist_ok=True)
            
            # Copy and optimize image
            processed_path = tour_dir / "360_image.jpg"
            
            # Resize and optimize for web viewing
            with Image.open(image_path) as img:
                # Resize if too large (max 4096x2048 for web)
                if img.width > 4096:
                    new_height = int(img.height * 4096 / img.width)
                    img = img.resize((4096, new_height), Image.Resampling.LANCZOS)
                
                # Save optimized version
                img.save(processed_path, "JPEG", quality=85, optimize=True)
            
            # Create thumbnail
            thumbnail_path = tour_dir / "thumbnail.jpg"
            with Image.open(processed_path) as img:
                img.thumbnail((400, 200))
                img.save(thumbnail_path, "JPEG", quality=80)
            
            return {
                "tour_url": f"/tours/{tour_id}/360_image.jpg",
                "thumbnail_url": f"/tours/{tour_id}/thumbnail.jpg",
                "status": "completed"
            }
        except Exception as e:
            logging.error(f"Error processing 360 image: {e}")
            return {"status": "failed", "error": str(e)}
    
    @staticmethod
    def create_tour_html(tour_id: str, scenes: List[dict]) -> str:
        """Generate A-Frame HTML for 360 tour"""
        scenes_html = ""
        for i, scene in enumerate(scenes):
            scenes_html += f"""
            <a-scene id="scene{i}" {'' if i == 0 else 'style="display: none;"'}>
                <a-sky src="#{scene['id']}" rotation="0 -130 0"></a-sky>
                <a-camera look-controls wasd-controls>
                    <a-cursor color="white" animation__click="property: scale; startEvents: click; from: 0.1 0.1 0.1; to: 1 1 1; dur: 150"></a-cursor>
                </a-camera>
            </a-scene>
            """
        
        assets_html = ""
        for scene in scenes:
            assets_html += f'<img id="{scene["id"]}" src="{scene["image_url"]}">\n'
        
        navigation_buttons = ""
        if len(scenes) > 1:
            for i, scene in enumerate(scenes):
                navigation_buttons += f"""
                <button onclick="showScene({i})" class="tour-nav-btn {'active' if i == 0 else ''}" id="btn{i}">
                    {scene['name']}
                </button>
                """
        
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://aframe.io/releases/1.4.0/aframe.min.js"></script>
    <title>360° Virtual Tour</title>
    <style>
        body {{ margin: 0; font-family: Arial, sans-serif; }}
        .tour-controls {{
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            display: flex;
            gap: 10px;
        }}
        .tour-nav-btn {{
            padding: 10px 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .tour-nav-btn:hover, .tour-nav-btn.active {{
            background: rgba(255,255,255,0.9);
            color: black;
        }}
        .tour-info {{
            position: fixed;
            top: 20px;
            left: 20px;
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 15px;
            border-radius: 8px;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="tour-info">
        <h3>Virtual Tour</h3>
        <p>Click and drag to look around. Use WASD to move.</p>
    </div>
    
    <a-scene embedded vr-mode-ui="enabled: true">
        <a-assets>
            {assets_html}
        </a-assets>
        
        {scenes_html}
    </a-scene>
    
    <div class="tour-controls">
        {navigation_buttons}
    </div>
    
    <script>
        function showScene(sceneIndex) {{
            // Hide all scenes
            for (let i = 0; i < {len(scenes)}; i++) {{
                const scene = document.getElementById('scene' + i);
                const btn = document.getElementById('btn' + i);
                if (scene) {{
                    scene.style.display = i === sceneIndex ? 'block' : 'none';
                }}
                if (btn) {{
                    btn.classList.toggle('active', i === sceneIndex);
                }}
            }}
        }}
    </script>
</body>
</html>
        """
        
        return html_template

# AI Content Engine
class ViralContentEngine:
    def __init__(self):
        self.openai_key = os.environ.get('OPENAI_API_KEY')
    
    async def generate_viral_content(self, property_data: dict, platform: str) -> dict:
        """Generate viral content for specific platforms"""
        try:
            if not self.openai_key or self.openai_key == 'demo-key-for-testing':
                return self._demo_content(property_data, platform)
            
            prompt = self._create_platform_prompt(property_data, platform)
            
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"You are a viral real estate content creator specializing in {platform}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            content_text = response.choices[0].message.content
            return self._parse_content_response(content_text, platform, property_data)
        except Exception as e:
            logging.error(f"Error generating viral content: {e}")
            return self._demo_content(property_data, platform)
    
    def _create_platform_prompt(self, property_data: dict, platform: str) -> str:
        tour_mention = "🏠 BONUS: Features interactive 360° virtual tour!" if property_data.get('has_tour') else ""
        
        return f"""Create engaging {platform} content for this property:
        
        Property: {property_data.get('title', 'Beautiful Property')}
        Address: {property_data.get('address', 'Prime Location')}
        Price: {property_data.get('price', 'Contact for pricing')}
        Description: {property_data.get('description', 'Amazing property')}
        {tour_mention}
        
        Create viral, engaging content with hashtags that highlights the virtual tour if available."""
    
    def _parse_content_response(self, response: str, platform: str, property_data: dict) -> dict:
        import re
        hashtags = re.findall(r'#[\w]+', response)
        viral_score = min(50 + len(hashtags) * 5 + len(response.split()) // 10, 100)
        
        # Boost viral score if has virtual tour
        if property_data.get('has_tour'):
            viral_score = min(viral_score + 15, 100)
        
        return {
            'platform': platform,
            'caption': response[:500],
            'hashtags': hashtags[:20],
            'viral_score': viral_score,
        }
    
    def _demo_content(self, property_data: dict, platform: str) -> dict:
        """Demo content when no API key is available"""
        tour_text = "\n\n🔄 INTERACTIVE 360° VIRTUAL TOUR AVAILABLE!\nExplore every corner from home! " if property_data.get('has_tour') else ""
        
        demo_content = f"""🏠✨ STUNNING {property_data.get('property_type', 'Property').upper()}! ✨

📍 {property_data.get('address', 'Prime Location')}
💰 {property_data.get('price', 'Amazing Value')}

{property_data.get('description', 'This incredible property offers everything you need!')}{tour_text}

Don't miss out on this amazing opportunity! 🔥

#RealEstate #DreamHome #Property #HomeForSale #VirtualTour #360Tour #{platform.title()}Ready #LuxuryLiving #PropertyListing #RealEstateAgent #NewListing #HomeSweetHome"""
        
        viral_score = 85 if property_data.get('has_tour') else 75
        
        return {
            'platform': platform,
            'caption': demo_content,
            'hashtags': ['#RealEstate', '#DreamHome', '#Property', '#HomeForSale', '#VirtualTour', '#360Tour'],
            'viral_score': viral_score,
        }

content_engine = ViralContentEngine()

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to ListingSpark AI with 360° Virtual Tours!"}

@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    user = User(**user_data.dict())
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "INSERT INTO users (id, email, name, plan, listings_created, total_views, total_shares, viral_score_average) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user.id, user.email, user.name, user.plan, user.listings_created, user.total_views, user.total_shares, user.viral_score_average)
        )
        await db.commit()
    
    return user

@api_router.post("/properties", response_model=Property)
async def create_property(property_data: PropertyCreate, user_id: str):
    """Create a new property listing"""
    property_obj = Property(user_id=user_id, **property_data.dict())
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        features_json = json.dumps(property_obj.features)
        await db.execute(
            """INSERT INTO properties (id, user_id, title, description, address, price, property_type, 
               bedrooms, bathrooms, square_feet, features, has_tour) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (property_obj.id, property_obj.user_id, property_obj.title, property_obj.description,
             property_obj.address, property_obj.price, property_obj.property_type,
             property_obj.bedrooms, property_obj.bathrooms, property_obj.square_feet, features_json, property_obj.has_tour)
        )
        
        # Update user's listing count
        await db.execute(
            "UPDATE users SET listings_created = listings_created + 1 WHERE id = ?",
            (user_id,)
        )
        await db.commit()
    
    return property_obj

@api_router.get("/properties/{user_id}")
async def get_user_properties(user_id: str):
    """Get all properties for a user"""  
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM properties WHERE user_id = ?", (user_id,)) as cursor:
            rows = await cursor.fetchall()
            properties = []
            for row in rows:
                features = json.loads(row[10]) if row[10] else []
                prop = {
                    'id': row[0], 'user_id': row[1], 'title': row[2], 'description': row[3],
                    'address': row[4], 'price': row[5], 'property_type': row[6],
                    'bedrooms': row[7], 'bathrooms': row[8], 'square_feet': row[9],
                    'features': features, 'has_tour': bool(row[11]), 'created_at': row[12]
                }
                properties.append(prop)
            return properties

@api_router.post("/properties/{property_id}/upload-360")
async def upload_360_image(
    property_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    scene_name: str = Form("Main Room")
):
    """Upload 360-degree image for virtual tour"""
    
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check if property exists
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT id FROM properties WHERE id = ?", (property_id,)) as cursor:
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Property not found")
    
    try:
        # Save uploaded file
        upload_path = UPLOAD_DIR / f"{uuid.uuid4()}_{file.filename}"
        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate 360 image
        if not Tour360Processor.validate_360_image(str(upload_path)):
            os.remove(upload_path)
            raise HTTPException(status_code=400, detail="Image must be 360-degree equirectangular format (2:1 aspect ratio)")
        
        # Create tour record
        tour_id = str(uuid.uuid4())
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                """INSERT INTO virtual_tours (id, property_id, tour_name, tour_url, processing_status, tour_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (tour_id, property_id, f"{scene_name} Tour", f"/tours/{tour_id}/tour.html", "processing", "360_image")
            )
            await db.commit()
        
        # Process image in background
        background_tasks.add_task(process_tour_background, tour_id, property_id, str(upload_path), scene_name)
        
        return {
            "message": "360° image uploaded successfully. Processing virtual tour...",
            "tour_id": tour_id,
            "status": "processing"
        }
        
    except Exception as e:
        if upload_path.exists():
            os.remove(upload_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

async def process_tour_background(tour_id: str, property_id: str, image_path: str, scene_name: str):
    """Background task to process 360 tour"""
    try:
        # Process the 360 image
        result = await Tour360Processor.process_360_image(image_path, tour_id)
        
        if result["status"] == "completed":
            # Create scene record
            scene_id = str(uuid.uuid4())
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute(
                    """INSERT INTO tour_scenes (id, tour_id, scene_name, image_url, scene_order)
                       VALUES (?, ?, ?, ?, ?)""",
                    (scene_id, tour_id, scene_name, result["tour_url"], 0)
                )
                
                # Get all scenes for this tour
                async with db.execute("SELECT * FROM tour_scenes WHERE tour_id = ? ORDER BY scene_order", (tour_id,)) as cursor:
                    scenes = await cursor.fetchall()
                
                scene_data = []
                for scene in scenes:
                    scene_data.append({
                        "id": f"scene_{scene[0]}",
                        "name": scene[2],
                        "image_url": scene[3]
                    })
                
                # Generate tour HTML
                tour_html = Tour360Processor.create_tour_html(tour_id, scene_data)
                tour_html_path = TOURS_DIR / tour_id / "tour.html"
                
                async with aiofiles.open(tour_html_path, 'w') as f:
                    await f.write(tour_html)
                
                # Update tour status
                await db.execute(
                    """UPDATE virtual_tours SET processing_status = ?, thumbnail_url = ?
                       WHERE id = ?""",
                    ("completed", result["thumbnail_url"], tour_id)
                )
                
                # Update property to indicate it has a tour
                await db.execute(
                    "UPDATE properties SET has_tour = 1 WHERE id = ?",
                    (property_id,)
                )
                
                await db.commit()
        
        # Clean up uploaded file
        if os.path.exists(image_path):
            os.remove(image_path)
            
    except Exception as e:
        logging.error(f"Error processing tour: {e}")
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE virtual_tours SET processing_status = ? WHERE id = ?",
                ("failed", tour_id)
            )
            await db.commit()

@api_router.get("/properties/{property_id}/tours")
async def get_property_tours(property_id: str):
    """Get all virtual tours for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM virtual_tours WHERE property_id = ?", (property_id,)) as cursor:
            tours = await cursor.fetchall()
            result = []
            for tour in tours:
                result.append({
                    'id': tour[0],
                    'property_id': tour[1], 
                    'tour_name': tour[2],
                    'tour_url': tour[3],
                    'thumbnail_url': tour[4],
                    'processing_status': tour[5],
                    'tour_type': tour[6],
                    'created_at': tour[7]
                })
            return result

@api_router.post("/properties/{property_id}/viral-content")
async def generate_property_viral_content(property_id: str):
    """Generate viral content for a property"""
    # Get property data
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Property not found")
            
            features = json.loads(row[10]) if row[10] else []
            property_data = {
                'id': row[0], 'title': row[2], 'description': row[3],
                'address': row[4], 'price': row[5], 'property_type': row[6],
                'features': features, 'has_tour': bool(row[11])
            }
    
    viral_contents = []
    platforms = ["instagram", "tiktok", "facebook"]
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for platform in platforms:
            content_data = await content_engine.generate_viral_content(property_data, platform)
            viral_content_id = str(uuid.uuid4())
            
            await db.execute(
                """INSERT INTO viral_content (id, property_id, platform, content_type, content, viral_score, hashtags)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (viral_content_id, property_id, platform, "caption", 
                 content_data['caption'], content_data['viral_score'], 
                 json.dumps(content_data['hashtags']))
            )
            
            viral_contents.append({
                'id': viral_content_id,
                'property_id': property_id,
                'platform': platform,
                'content': content_data['caption'],
                'viral_score': content_data['viral_score'],
                'hashtags': content_data['hashtags']
            })
        
        await db.commit()
    
    return {"message": "Viral content generated successfully", "content": viral_contents}

@api_router.get("/properties/{property_id}/viral-content")
async def get_property_viral_content(property_id: str):
    """Get all viral content for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM viral_content WHERE property_id = ?", (property_id,)) as cursor:
            rows = await cursor.fetchall()
            content = []
            for row in rows:
                hashtags = json.loads(row[6]) if row[6] else []
                content.append({
                    'id': row[0], 'property_id': row[1], 'platform': row[2],
                    'content_type': row[3], 'content': row[4], 'viral_score': row[5],
                    'hashtags': hashtags, 'created_at': row[7]
                })
            return content

@api_router.get("/properties/{property_id}/analytics")
async def get_property_analytics(property_id: str):
    """Get analytics for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM analytics WHERE property_id = ?", (property_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                # Create default analytics
                await db.execute(
                    "INSERT INTO analytics (property_id, views, shares, engagement_rate, viral_score, tour_views) VALUES (?, 0, 0, 0.0, 0, 0)",
                    (property_id,)
                )
                await db.commit()
                return {"property_id": property_id, "views": 0, "shares": 0, "engagement_rate": 0.0, "viral_score": 0, "tour_views": 0}
            
            return {
                "property_id": row[0], "views": row[1], "shares": row[2],
                "engagement_rate": row[3], "viral_score": row[4], "tour_views": row[5]
            }
@api_router.post("/tours/{tour_id}/view")
async def track_tour_view(tour_id: str):
    """Track virtual tour view"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get tour and property info
        async with db.execute("SELECT property_id FROM virtual_tours WHERE id = ?", (tour_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tour not found")
            
            property_id = row[0]
        
        # Update analytics
        await db.execute(
            """UPDATE analytics SET tour_views = tour_views + 1, views = views + 1, updated_at = CURRENT_TIMESTAMP
               WHERE property_id = ?""",
            (property_id,)
        )
        await db.commit()
        
        return {"message": "Tour view tracked"}

@api_router.get("/dashboard/{user_id}")
async def get_user_dashboard(user_id: str):
    """Get dashboard data for a user"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get user
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            user_row = await cursor.fetchone()
            if not user_row:
                raise HTTPException(status_code=404, detail="User not found")
        
        # Get properties with tour status
        async with db.execute("SELECT *, has_tour FROM properties WHERE user_id = ?", (user_id,)) as cursor:
            properties = await cursor.fetchall()
        
        # Get total analytics
        total_views = 0
        total_shares = 0
        total_tour_views = 0
        properties_with_tours = 0
        
        for prop in properties:
            if prop[11]:  # has_tour column
                properties_with_tours += 1
            
            async with db.execute("SELECT views, shares, tour_views FROM analytics WHERE property_id = ?", (prop[0],)) as cursor:
                analytics = await cursor.fetchone()
                if analytics:
                    total_views += analytics[0]
                    total_shares += analytics[1]
                    total_tour_views += analytics[2]
        
        return {
            "user": {
                "id": user_row[0], "email": user_row[1], "name": user_row[2],
                "plan": user_row[3], "listings_created": user_row[4]
            },
            "stats": {
                "total_properties": len(properties),
                "total_views": total_views,
                "total_shares": total_shares,
                "total_tour_views": total_tour_views,
                "properties_with_tours": properties_with_tours,
                "average_viral_score": 0
            }
        }

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_db()
    logger.info("ListingSpark AI Backend with 360° Tours Started! 🚀")
