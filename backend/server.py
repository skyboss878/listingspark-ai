import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
# Import Platform Module
import aiosqlite
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from platform_integrations import platform_manager, ListingData, ListingStatus
from pydantic import BaseModel
from app.ai_content_engine import ViralContentEngine
from openai import AsyncOpenAI
from PIL import Image
from dotenv import load_dotenv
load_dotenv()
from video_tour_generator_pro import premium_video_generator, VideoConfig, BrandingConfig
from payment import router as payment_router
# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent
DATABASE_PATH = ROOT_DIR / "listingspark.db"
UPLOADS_DIR = ROOT_DIR / "uploads"
TOURS_DIR = ROOT_DIR / "tours"

UPLOADS_DIR.mkdir(exist_ok=True)
TOURS_DIR.mkdir(exist_ok=True)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Initialize AI Content Engine
viral_content_engine = ViralContentEngine()

app.include_router(payment_router, prefix="/api/payment", tags=["payment"])

# Professional Space Types for Real Estate
SPACE_TYPES = {
    "Living Spaces": [
        "Living Room", "Family Room", "Great Room", "Den", "Library",
        "Formal Dining Room", "Breakfast Nook", "Sunroom", "Florida Room"
    ],
    "Kitchen & Utility": [
        "Kitchen", "Pantry", "Butler's Pantry", "Laundry Room", "Mudroom"
    ],
    "Bedrooms": [
        "Master Bedroom", "Master Suite", "Bedroom 2", "Bedroom 3", 
        "Bedroom 4", "Bedroom 5", "Guest Room", "Nursery"
    ],
    "Bathrooms": [
        "Master Bathroom", "Full Bathroom", "Half Bathroom", "Jack and Jill Bathroom",
        "Powder Room", "Pool Bathroom"
    ],
    "Work & Recreation": [
        "Home Office", "Study", "Game Room", "Home Theater", "Media Room",
        "Gym", "Exercise Room", "Craft Room", "Workshop", "Wine Cellar",
        "Bar", "Playroom"
    ],
    "Storage & Entry": [
        "Foyer", "Entry Hall", "Hallway", "Staircase", "Walk-in Closet",
        "Closet", "Storage Room", "Utility Closet"
    ],
    "Basement & Attic": [
        "Basement", "Finished Basement", "Basement Bedroom", 
        "Attic", "Finished Attic", "Bonus Room"
    ],
    "Garage & Parking": [
        "Garage (1-Car)", "Garage (2-Car)", "Garage (3-Car)", 
        "Carport", "Driveway", "Parking Pad"
    ],
    "Outdoor Living": [
        "Front Porch", "Back Porch", "Covered Patio", "Open Patio",
        "Deck", "Balcony", "Screened Porch", "Pergola", "Gazebo"
    ],
    "Yard & Garden": [
        "Front Yard", "Backyard", "Side Yard", "Garden", "Vegetable Garden",
        "Landscaping", "Lawn", "Courtyard"
    ],
    "Special Features": [
        "Swimming Pool", "Pool Area", "Hot Tub", "Spa", "Sauna",
        "Tennis Court", "Basketball Court", "Outdoor Kitchen",
        "Fire Pit", "Pond", "Fountain"
    ],
    "Outbuildings": [
        "Shed", "Storage Shed", "Pool House", "Guest House",
        "Detached Garage", "Barn", "Studio", "Workshop"
    ]
}

# Standard Amenities
STANDARD_AMENITIES = {
    "Interior Features": [
        "Hardwood Floors", "Tile Floors", "Carpet", "Granite Countertops",
        "Marble Countertops", "Stainless Steel Appliances", "Updated Appliances",
        "Fireplace", "Gas Fireplace", "Wood Burning Fireplace", "Cathedral Ceilings",
        "Crown Molding", "Recessed Lighting", "Ceiling Fans", "Walk-in Closets",
        "Built-in Shelving", "Skylight", "Bay Window", "French Doors"
    ],
    "Systems & Technology": [
        "Central Air", "Central Heat", "Dual HVAC", "Smart Thermostat",
        "Smart Home System", "Security System", "Video Doorbell", 
        "Surround Sound", "Built-in Speakers", "Ethernet Wiring"
    ],
    "Kitchen Features": [
        "Island", "Breakfast Bar", "Double Oven", "Gas Range",
        "Induction Cooktop", "Wine Cooler", "Ice Maker", "Pot Filler",
        "Custom Cabinets", "Soft-Close Drawers", "Pantry"
    ],
    "Bathroom Features": [
        "Double Vanity", "Soaking Tub", "Separate Shower", "Walk-in Shower",
        "Rainfall Showerhead", "Heated Floors", "Bidet", "Linen Closet"
    ],
    "Outdoor Features": [
        "Fenced Yard", "Privacy Fence", "Sprinkler System", "Outdoor Lighting",
        "Mature Trees", "Fruit Trees", "Professional Landscaping", "Irrigation System"
    ],
    "Garage & Storage": [
        "Attached Garage", "Detached Garage", "Garage Door Opener",
        "Workshop in Garage", "Extra Storage", "Attic Storage"
    ],
    "Energy Efficiency": [
        "Solar Panels", "Energy Star Appliances", "Tankless Water Heater",
        "Double Pane Windows", "LED Lighting", "Insulated Garage Door"
    ],
    "Community & Location": [
        "HOA", "Gated Community", "Pool Access", "Clubhouse Access",
        "Playground", "Walking Trails", "Near Shopping", "Near Schools"
    ]
}

# Models
class UserCreate(BaseModel):
    email: str
    name: str

class User(BaseModel):
    id: str
    email: str
    name: str
    plan: str = "free"
    listings_created: int = 0

class PropertyCreate(BaseModel):
    user_id: str
    title: str
    description: str
    address: str
    price: str
    property_type: str
    bedrooms: int
    bathrooms: float
    square_feet: int
    features: List[str] = []

class Property(BaseModel):
    id: str
    user_id: str
    title: str
    description: str
    address: str
    price: str
    property_type: str
    bedrooms: int
    bathrooms: float
    square_feet: int
    features: List[str]
    has_tour: bool = False
    created_at: str

class RoomCreate(BaseModel):
    property_id: str
    space_name: str
    space_type: str
    space_category: str
    description: Optional[str] = None
    square_feet: Optional[int] = None

class Room(BaseModel):
    id: str
    property_id: str
    space_name: str
    space_type: str
    space_category: str
    description: Optional[str]
    square_feet: Optional[int]
    image_360_url: Optional[str]
    thumbnail_url: Optional[str]
    processing_status: str
    sort_order: int
    created_at: str

class CustomAmenityCreate(BaseModel):
    user_id: str
    amenity_name: str
    category: str = "Custom"
class PublishRequest(BaseModel):
    """Request to publish listing to platforms"""
    property_id: str
    platforms: List[str]  # List of platform names to publish to
    contact_name: str
    contact_email: str
    contact_phone: str
    listing_agent: Optional[str] = None


class PlatformSyncRecord(BaseModel):
    """Record of a platform sync"""
    id: str
    property_id: str
    platform_name: str
    platform_listing_id: Optional[str]
    platform_url: Optional[str]
    status: str
    error_message: Optional[str]
    synced_at: str
class Tour360Processor:
    """Process 360-degree equirectangular images"""
    MIN_WIDTH = 2048
    WEB_WIDTH = 4096
    THUMBNAIL_SIZE = (400, 200)

    @staticmethod
    def validate_360_image(image_path: str) -> tuple[bool, str]:
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                if width < Tour360Processor.MIN_WIDTH:
                    return False, f"Image too small. Minimum width: {Tour360Processor.MIN_WIDTH}px"
                aspect_ratio = width / height
                if not (1.8 <= aspect_ratio <= 2.2):
                    return False, f"Not a 360° equirectangular image. Expected 2:1 ratio, got {aspect_ratio:.2f}:1"
                return True, "Valid 360° image"
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    @staticmethod
    async def process_360_image(image_path: str, tour_dir: Path, scene_name: str) -> dict:
        try:
            processed_path = tour_dir / f"{scene_name}_360.jpg"
            thumbnail_path = tour_dir / f"{scene_name}_thumb.jpg"
            
            with Image.open(image_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                if img.width > Tour360Processor.WEB_WIDTH:
                    new_height = int(img.height * Tour360Processor.WEB_WIDTH / img.width)
                    img = img.resize((Tour360Processor.WEB_WIDTH, new_height), Image.Resampling.LANCZOS)
                
                img.save(processed_path, 'JPEG', quality=85, optimize=True)
                
                thumb = img.copy()
                thumb.thumbnail(Tour360Processor.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                thumb.save(thumbnail_path, 'JPEG', quality=75)
            
            return {
                'processed_path': processed_path.name,
                'thumbnail_path': thumbnail_path.name,
                'status': 'success'
            }
        except Exception as e:
            raise Exception(f"Image processing failed: {str(e)}")

    @staticmethod
    def generate_tour_html(tour_id: str, property_title: str, scenes: List[dict]) -> str:
        """Generate professional 360° tour viewer"""
        scenes_json = json.dumps(scenes)
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{property_title} - Virtual Tour</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css"/>
    <script src="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; overflow: hidden; }}
        #panorama {{ width: 100vw; height: 100vh; }}
        .tour-header {{
            position: absolute; top: 20px; left: 20px; right: 20px; z-index: 1000;
            background: rgba(0,0,0,0.7); padding: 15px 25px; border-radius: 12px;
            backdrop-filter: blur(10px); display: flex; justify-content: space-between; align-items: center;
        }}
        .tour-title {{ color: white; font-size: 24px; font-weight: 600; }}
        .tour-subtitle {{ color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 4px; }}
        .scene-nav {{
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 1000;
            background: rgba(0,0,0,0.7); padding: 15px; border-radius: 12px;
            backdrop-filter: blur(10px); display: flex; gap: 10px; flex-wrap: wrap;
            max-width: 90vw; justify-content: center;
        }}
        .scene-btn {{
            background: rgba(255,255,255,0.1); color: white; border: 2px solid rgba(255,255,255,0.3);
            padding: 10px 20px; border-radius: 8px; cursor: pointer; transition: all 0.3s;
            font-size: 14px; font-weight: 500;
        }}
        .scene-btn:hover {{ background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.5); }}
        .scene-btn.active {{ background: #3b82f6; border-color: #3b82f6; }}
        .scene-category {{
            width: 100%; text-align: center; color: rgba(255,255,255,0.6);
            font-size: 12px; text-transform: uppercase; letter-spacing: 1px;
            margin-top: 10px;
        }}
        .branding {{
            position: absolute; top: 20px; right: 20px; z-index: 1000;
            background: rgba(0,0,0,0.7); padding: 10px 20px; border-radius: 8px;
            color: white; font-size: 12px; backdrop-filter: blur(10px);
        }}
    </style>
</head>
<body>
    <div class="tour-header">
        <div>
            <div class="tour-title">{property_title}</div>
            <div class="tour-subtitle" id="currentRoom">Loading...</div>
        </div>
    </div>
    <div class="branding">Powered by ListingSpark AI</div>
    <div id="panorama"></div>
    <div class="scene-nav" id="sceneNav"></div>
    
    <script>
        const scenes = {scenes_json};
        let viewer;
        let currentSceneIndex = 0;

        function initTour() {{
            if (scenes.length === 0) {{
                document.getElementById('panorama').innerHTML = 
                    '<div style="display: flex; align-items: center; justify-content: center; height: 100vh; color: white; font-size: 24px;">No scenes available</div>';
                return;
            }}

            viewer = pannellum.viewer('panorama', {{
                default: {{
                    firstScene: scenes[0].id,
                    sceneFadeDuration: 1000,
                    autoLoad: true
                }},
                scenes: scenes.reduce((acc, scene) => {{
                    acc[scene.id] = {{
                        type: "equirectangular",
                        panorama: scene.imageUrl,
                        pitch: scene.pitch || 0,
                        yaw: scene.yaw || 0,
                        hfov: scene.fov || 100,
                        autoRotate: -2
                    }};
                    return acc;
                }}, {{}})
            }});

            createSceneNavigation();
            updateCurrentRoom(0);
            
            fetch('/api/tours/{tour_id}/view', {{ method: 'POST' }}).catch(e => console.log(e));
        }}

        function createSceneNavigation() {{
            const nav = document.getElementById('sceneNav');
            let lastCategory = '';
            
            scenes.forEach((scene, index) => {{
                if (scene.category && scene.category !== lastCategory) {{
                    const categoryDiv = document.createElement('div');
                    categoryDiv.className = 'scene-category';
                    categoryDiv.textContent = scene.category;
                    nav.appendChild(categoryDiv);
                    lastCategory = scene.category;
                }}
                
                const btn = document.createElement('button');
                btn.className = 'scene-btn' + (index === 0 ? ' active' : '');
                btn.textContent = scene.name;
                btn.onclick = () => switchScene(index);
                nav.appendChild(btn);
            }});
        }}

        function switchScene(index) {{
            if (index < 0 || index >= scenes.length) return;
            
            currentSceneIndex = index;
            viewer.loadScene(scenes[index].id, scenes[index].pitch || 0, scenes[index].yaw || 0, scenes[index].fov || 100);
            updateCurrentRoom(index);
            
            document.querySelectorAll('.scene-btn').forEach((btn, i) => {{
                btn.classList.toggle('active', i === index);
            }});
        }}

        function updateCurrentRoom(index) {{
            const room = scenes[index];
            document.getElementById('currentRoom').textContent = 
                room.category ? `${{room.category}} - ${{room.name}}` : room.name;
        }}

        window.addEventListener('load', initTour);
    </script>
</body>
</html>"""

# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("=" * 60)
    logger.info("ListingSpark AI Professional Backend Started!")
    logger.info(f"Database: {DATABASE_PATH}")
    logger.info(f"Tours Directory: {TOURS_DIR}")
    logger.info("=" * 60)
    yield
    logger.info("Shutting down ListingSpark AI Backend")

# Initialize FastAPI
app = FastAPI(
    title="ListingSpark AI Professional",
    description="Professional real estate virtual tour platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/tours", StaticFiles(directory=str(TOURS_DIR)), name="tours")

api_router = app

# Database initialization
async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                plan TEXT DEFAULT 'free',
                listings_created INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                space_name TEXT NOT NULL,
                space_type TEXT NOT NULL,
                space_category TEXT NOT NULL,
                description TEXT,
                square_feet INTEGER,
                image_360_url TEXT,
                thumbnail_url TEXT,
                processing_status TEXT DEFAULT 'pending',
                sort_order INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE
            )
        """)
        
        await db.commit()
        logger.info("Database initialized successfully")

    

@api_router.get("/properties/{property_id}/rooms")
async def get_property_rooms(property_id: str):
    """Get all rooms for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM rooms WHERE property_id = ? ORDER BY sort_order",
            (property_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                'id': row[0], 'property_id': row[1], 'space_name': row[2],
                'space_type': row[3], 'space_category': row[4],
                'description': row[5], 'square_feet': row[6],
                'image_360_url': row[7], 'thumbnail_url': row[8],
                'processing_status': row[9], 'sort_order': row[10],
                'created_at': row[11]
            } for row in rows]

@api_router.post("/rooms/{room_id}/upload-360")
async def upload_room_360(room_id: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload 360° image for a room"""
    upload_path = UPLOADS_DIR / f"{room_id}_{file.filename}"
    
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    is_valid, message = Tour360Processor.validate_360_image(str(upload_path))
    if not is_valid:
        upload_path.unlink()
        raise HTTPException(400, message)
    
    background_tasks.add_task(process_room_360_background, room_id, str(upload_path))
    
    return {"room_id": room_id, "status": "processing", "message": "Processing 360° image..."}

async def process_room_360_background(room_id: str, image_path: str):
    """Background processing for room 360 image"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("SELECT property_id, space_name FROM rooms WHERE id = ?", (room_id,)) as cursor:
                room = await cursor.fetchone()
                if not room:
                    return
                
                property_id, space_name = room
            
            room_dir = TOURS_DIR / property_id / room_id
            room_dir.mkdir(parents=True, exist_ok=True)
            
            result = await Tour360Processor.process_360_image(image_path, room_dir, space_name.replace(" ", "_"))
            
            image_url = f"/tours/{property_id}/{room_id}/{result['processed_path']}"
            thumbnail_url = f"/tours/{property_id}/{room_id}/{result['thumbnail_path']}"
            
            async with aiosqlite.connect(DATABASE_PATH) as db:
                await db.execute("""
                    UPDATE rooms 
                    SET image_360_url = ?, thumbnail_url = ?, processing_status = 'completed'
                    WHERE id = ?
                """, (image_url, thumbnail_url, room_id))
                await db.commit()
            
            logger.info(f"Room {room_id} 360 image processed successfully")
    
    except Exception as e:
        logger.error(f"Room 360 processing error: {e}")
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE rooms SET processing_status = 'failed' WHERE id = ?",
                (room_id,)
            )
            await db.commit()

@api_router.delete("/rooms/{room_id}")
async def delete_room(room_id: str):
    """Delete a room"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        await db.commit()
    return {"message": "Room deleted successfully"}

@api_router.put("/rooms/{room_id}/reorder")
async def reorder_room(room_id: str, new_order: int):
    """Update room sort order"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute(
            "UPDATE rooms SET sort_order = ? WHERE id = ?",
            (new_order, room_id)
        )
        await db.commit()
    return {"message": "Room order updated"}

# Tour Generation
@api_router.post("/properties/{property_id}/generate-tour")
async def generate_property_tour(property_id: str, background_tasks: BackgroundTasks):
    """Generate complete virtual tour from all rooms"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Check property exists
        async with db.execute("SELECT title FROM properties WHERE id = ?", (property_id,)) as cursor:
            property_row = await cursor.fetchone()
            if not property_row:
                raise HTTPException(404, "Property not found")
            property_title = property_row[0]
        
        # Get all completed rooms
        async with db.execute(
            """SELECT id, space_name, space_category, image_360_url, sort_order 
               FROM rooms 
               WHERE property_id = ? AND processing_status = 'completed' AND image_360_url IS NOT NULL
               ORDER BY sort_order""",
            (property_id,)
        ) as cursor:
            rooms = await cursor.fetchall()
            
            if not rooms:
                raise HTTPException(400, "No completed rooms with 360° images found")
        
        tour_id = str(uuid.uuid4())
        
        # Create tour record
        await db.execute("""
            INSERT INTO tours (id, property_id, tour_name, status, total_scenes)
            VALUES (?, ?, ?, 'generating', ?)
        """, (tour_id, property_id, f"{property_title} - Virtual Tour", len(rooms)))
        await db.commit()
    
    background_tasks.add_task(generate_tour_background, tour_id, property_id, property_title, rooms)
    
    return {"tour_id": tour_id, "status": "generating", "message": "Generating virtual tour..."}

async def generate_tour_background(tour_id: str, property_id: str, property_title: str, rooms: list):
    """Background task to generate complete tour"""
    try:
        scenes = []
        for idx, room in enumerate(rooms):
            room_id, space_name, space_category, image_url, sort_order = room
            scenes.append({
                'id': room_id,
                'name': space_name,
                'category': space_category,
                'imageUrl': image_url,
                'pitch': 0,
                'yaw': 0,
                'fov': 100
            })
        
        # Generate HTML tour
        tour_html = Tour360Processor.generate_tour_html(tour_id, property_title, scenes)
        tour_dir = TOURS_DIR / property_id
        tour_dir.mkdir(parents=True, exist_ok=True)
        
        html_path = tour_dir / "tour.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(tour_html)
        
        tour_url = f"/tours/{property_id}/tour.html"
        
        # Update database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                UPDATE tours 
                SET tour_url = ?, status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (tour_url, tour_id))
            
            await db.execute(
                "UPDATE properties SET has_tour = 1 WHERE id = ?",
                (property_id,)
            )
            await db.commit()
        
        logger.info(f"Tour {tour_id} generated successfully with {len(scenes)} scenes")
    
    except Exception as e:
        logger.error(f"Tour generation error: {e}")
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                "UPDATE tours SET status = 'failed' WHERE id = ?",
                (tour_id,)
            )
            await db.commit()

@api_router.get("/properties/{property_id}/tour")
async def get_property_tour(property_id: str):
    """Get the tour for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM tours WHERE property_id = ? ORDER BY created_at DESC LIMIT 1",
            (property_id,)
        ) as cursor:
            tour = await cursor.fetchone()
            if not tour:
                raise HTTPException(404, "No tour found for this property")
            
            return {
                'id': tour[0],
                'property_id': tour[1],
                'tour_name': tour[2],
                'tour_url': tour[3],
                'status': tour[4],
                'total_scenes': tour[5],
                'created_at': tour[6],
                'completed_at': tour[7]
            }

@api_router.post("/tours/{tour_id}/view")
async def track_tour_view(tour_id: str):
    """Track tour view for analytics"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT property_id FROM tours WHERE id = ?", (tour_id,)) as cursor:
            result = await cursor.fetchone()
            if not result:
                raise HTTPException(404, "Tour not found")
            property_id = result[0]
        
        await db.execute("""
            INSERT INTO analytics (property_id, tour_views, views)
            VALUES (?, 1, 1)
            ON CONFLICT(property_id) DO UPDATE SET
               tour_views = tour_views + 1,
               views = views + 1
        """, (property_id,))
        await db.commit()
    
    return {"message": "View tracked"}

# Analytics
@api_router.get("/properties/{property_id}/analytics")
async def get_property_analytics(property_id: str):
    """Get analytics for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM analytics WHERE property_id = ?",
            (property_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return {
                    "property_id": property_id, "views": 0, "shares": 0,
                    "engagement_rate": 0.0, "viral_score": 0, "tour_views": 0
                }
            
            return {
                "property_id": row[1], "views": row[2], "shares": row[3],
                "engagement_rate": row[4], "viral_score": row[5],
                "tour_views": row[6], "trending_status": row[7]
            }

@api_router.get("/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    """Get user dashboard statistics"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, has_tour FROM properties WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            properties = await cursor.fetchall()
        
        total_properties = len(properties)
        total_views = 0
        total_shares = 0
        total_tour_views = 0
        properties_with_tours = sum(1 for p in properties if p[1])
        
        for prop in properties:
            async with db.execute(
                "SELECT views, shares, tour_views FROM analytics WHERE property_id = ?",
                (prop[0],)
            ) as cursor:
                analytics = await cursor.fetchone()
                if analytics:
                    total_views += analytics[0]
                    total_shares += analytics[1]
                    total_tour_views += analytics[2]
        
        avg_engagement = (total_shares / total_views * 100) if total_views > 0 else 0
        
        return {
            "user_id": user_id,
            "statistics": {
                "total_properties": total_properties,
                "properties_with_tours": properties_with_tours,
                "total_views": total_views,
                "total_shares": total_shares,
                "total_tour_views": total_tour_views,
                "avg_engagement_rate": round(avg_engagement, 2)
            }
        }


@api_router.get("/platforms")
async def get_available_platforms():
    """Get all available platform integrations"""
    return {
        "platforms": platform_manager.get_available_platforms(),
        "status": platform_manager.get_platform_status()
    }

@api_router.get("/platforms/status")
async def get_platforms_status():
    """Get detailed status of all platform integrations"""
    return platform_manager.get_platform_status()

@api_router.get("/space-types")
async def get_space_types():
    """Get all available space types organized by category"""
    return SPACE_TYPES

@api_router.get("/standard-amenities")
async def get_standard_amenities():
    """Get all standard amenities organized by category"""
    return STANDARD_AMENITIES


# ============================================================================
# PLATFORM INTEGRATION ENDPOINTS
# ============================================================================

async def get_standard_amenities():
    """Get all standard amenities organized by category"""
    return STANDARD_AMENITIES

@api_router.get("/health")

@api_router.post("/properties/{property_id}/generate-video-tour")
async def generate_video_tour(
    property_id: str,
    background_tasks: BackgroundTasks,
    voice_provider: str = "edge-tts",  # or elevenlabs
    voice_id: str = "professional_female",
    music_genre: str = "upbeat",
    export_social: bool = True,
    agent_name: Optional[str] = None,
    agent_phone: Optional[str] = None,
    agent_email: Optional[str] = None,
    logo_path: Optional[str] = None
):
    """Generate professional narrated video tour with music"""
    
    # Get property and rooms
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM properties WHERE id = ?", (property_id,)
        ) as cursor:
            prop_row = await cursor.fetchone()
            if not prop_row:
                raise HTTPException(404, "Property not found")
            
            property_data = {
                'id': prop_row[0], 'title': prop_row[2],
                'description': prop_row[3], 'address': prop_row[4],
                'price': prop_row[5], 'property_type': prop_row[6],
                'bedrooms': prop_row[7], 'bathrooms': prop_row[8],
                'square_feet': prop_row[9],
                'features': json.loads(prop_row[10] or '[]')
            }
        
        async with db.execute(
            """SELECT * FROM rooms 
               WHERE property_id = ? AND processing_status = 'completed' 
               ORDER BY sort_order""",
            (property_id,)
        ) as cursor:
            room_rows = await cursor.fetchall()
            if not room_rows:
                raise HTTPException(400, "No completed rooms with images found")
            
            rooms = [{
                'id': r[0], 'space_name': r[2], 'space_type': r[3],
                'space_category': r[4], 'description': r[5],
                'image_360_url': r[7]
            } for r in room_rows]
    
    # Configure video generation
    video_config = VideoConfig(
        voice_provider=voice_provider,
        voice_id=voice_id,
        music_genre=music_genre
    )
    
    branding_config = BrandingConfig(
        agent_name=agent_name or "",
        phone=agent_phone or "",
        email=agent_email or "",
        logo_path=logo_path
    )
    
    # Start generation in background
    background_tasks.add_task(
        generate_video_background,
        property_id,
        property_data,
        rooms,
        video_config,
        branding_config,
        export_social
    )
    
    return {
        "message": "Video tour generation started",
        "property_id": property_id,
        "estimated_time_minutes": len(rooms) * 0.5,  # Rough estimate
        "status": "processing"
    }

async def generate_video_background(
    property_id: str,
    property_data: dict,
    rooms: List[dict],
    config: VideoConfig,
    branding: BrandingConfig,
    export_social: bool
):
    """Background task for video generation"""
    try:
        result = await premium_video_generator.generate_tour_video(
            property_id, property_data, rooms, config, branding, export_social
        )
        
        # Update database with video info
        async with aiosqlite.connect(DATABASE_PATH) as db:
            if result['success']:
                await db.execute("""
                    UPDATE properties 
                    SET has_tour = 1 
                    WHERE id = ?
                """, (property_id,))
                
                # Store video metadata
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS video_tours (
                        id TEXT PRIMARY KEY,
                        property_id TEXT NOT NULL,
                        video_url TEXT,
                        duration_seconds INTEGER,
                        script TEXT,
                        social_exports TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (property_id) REFERENCES properties (id)
                    )
                """)
                
                await db.execute("""
                    INSERT INTO video_tours 
                    (id, property_id, video_url, duration_seconds, script, social_exports)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    property_id,
                    result['video_url'],
                    result.get('duration_seconds', 0),
                    json.dumps(result.get('script', {})),
                    json.dumps(result.get('social_exports', {}))
                ))
                
                await db.commit()
                logger.info(f"Video tour completed for {property_id}")
            else:
                logger.error(f"Video generation failed: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"Video background task failed: {e}", exc_info=True)

@api_router.get("/properties/{property_id}/video-tour")
async def get_video_tour(property_id: str):
    """Get video tour info for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM video_tours WHERE property_id = ? ORDER BY created_at DESC LIMIT 1",
            (property_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, "No video tour found")
            
            return {
                'id': row[0],
                'property_id': row[1],
                'video_url': row[2],
                'duration_seconds': row[3],
                'script': json.loads(row[4]),
                'social_exports': json.loads(row[5]),
                'created_at': row[6]
            }

@api_router.post("/api/properties/{property_id}/generate-viral-content")
async def generate_viral_content(property_id: str, platforms: Optional[List[str]] = None):
    """Generate AI-powered viral social media content"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, "Property not found")
            property_data = {
                'id': row[0], 'title': row[2], 'description': row[3], 'address': row[4],
                'price': row[5], 'property_type': row[6], 'bedrooms': row[7],
                'bathrooms': row[8], 'square_feet': row[9],
                'features': json.loads(row[10] or '[]'), 'has_tour': bool(row[11])
            }
    
    if not platforms:
        platforms = ["instagram", "tiktok", "facebook", "twitter"]
    
    try:
        content_results = await viral_content_engine.generate_batch_content(property_data, platforms)
        viral_contents = []
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""CREATE TABLE IF NOT EXISTS viral_content (
                id TEXT PRIMARY KEY, property_id TEXT NOT NULL, platform TEXT NOT NULL,
                content_type TEXT NOT NULL, content TEXT NOT NULL, viral_score INTEGER NOT NULL,
                hashtags TEXT, ai_generated BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id))""")
            
            for platform, content_data in content_results.items():
                viral_content_id = str(uuid.uuid4())
                await db.execute(
                    """INSERT INTO viral_content (id, property_id, platform, content_type, content, 
                       viral_score, hashtags, ai_generated) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (viral_content_id, property_id, platform, content_data.get('content_type', 'caption'),
                     content_data['content'], content_data['viral_score'], 
                     json.dumps(content_data['hashtags']), content_data.get('ai_generated', True)))
                
                viral_contents.append({
                    'id': viral_content_id, 'property_id': property_id, 'platform': platform,
                    'content': content_data['content'], 'viral_score': content_data['viral_score'],
                    'hashtags': content_data['hashtags'], 'ai_generated': content_data.get('ai_generated', True)
                })
            await db.commit()
        
        return {"message": "Viral content generated", "content": viral_contents, "ai_enabled": viral_content_engine.enabled}
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")

@api_router.get("/api/properties/{property_id}/viral-content")
async def get_viral_content(property_id: str):
    """Get all viral content"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM viral_content WHERE property_id = ? ORDER BY created_at DESC", (property_id,)) as cursor:
            rows = await cursor.fetchall()
            return [{'id': r[0], 'property_id': r[1], 'platform': r[2], 'content_type': r[3],
                    'content': r[4], 'viral_score': r[5], 'hashtags': json.loads(r[6] or '[]'),
                    'ai_generated': bool(r[7]), 'created_at': r[8]} for r in rows]

@api_router.get("/voice-options")
async def get_voice_options():
    """Get available voice options for video tours"""
    return premium_video_generator.voice_engine.voices

async def health_check():
    return {"status": "healthy", "version": "2.0.0-professional"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
