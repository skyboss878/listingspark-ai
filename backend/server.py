import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
import aiosqlite
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Body, Form
from platform_integrations import platform_manager, ListingData, ListingStatus
from pydantic import BaseModel
from app.ai_content_engine import ViralContentEngine
import uuid
import json
from openai import AsyncOpenAI
from PIL import Image
from elevenlabs_voice import elevenlabs_engine
from ai_image_enhancer import ai_enhancer
from dotenv import load_dotenv
load_dotenv()
from video_tour_generator_pro import premium_video_generator, VideoConfig, BrandingConfig
from payment import router as payment_router
from routes import subscription
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
    password: str


class UserLogin(BaseModel):
    email: str
    password: str
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
# Health check routes
@app.get("/")
async def root():
    return {"status": "ok", "service": "ListingSpark AI", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0-professional"}

@app.get("/api/health")
async def api_health_check():
    return {"status": "healthy", "version": "2.0.0-professional"}

# Include payment router
app.include_router(payment_router, prefix="/api/payment", tags=["payment"])
api_router = app

app.include_router(subscription.router, prefix="/api/subscription", tags=["subscription"])
# Authentication routes
@app.post("/api/users")
async def create_user(user_data: UserCreate):
    """Create a new user"""
    user_id = str(uuid.uuid4())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO users (id, email, name, password, plan) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_data.email, user_data.name, user_data.password, "free")
            )
            await db.commit()
            return {
                "id": user_id,
                "email": user_data.email,
                "name": user_data.name,
                "plan": "free",
                "listings_created": 0
            }
        except aiosqlite.IntegrityError:
            raise HTTPException(400, "Email already exists")

@app.post("/api/login")
async def login(user_data: UserLogin):
    """Login or create user"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?", (user_data.email, user_data.password)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "name": row[2],
                    "plan": row[4], "listings_created": row[5]
                }
            else:
                raise HTTPException(401, "Invalid email or password")
async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
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

@api_router.get("/voice-options")
async def get_voice_options():
    """Get available voice options for narration"""
    return {
        "voices": elevenlabs_engine.voices,
        "enabled": elevenlabs_engine.enabled
    }

@api_router.post("/properties/{property_id}/generate-narrated-tour")
async def generate_narrated_tour(
    property_id: str,
    background_tasks: BackgroundTasks,
    voice_id: str = "professional_female",
    include_music: bool = True
):
    """Generate complete 360° tour with professional voice narration"""
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get property data
        async with db.execute(
            "SELECT * FROM properties WHERE id = ?", (property_id,)
        ) as cursor:
            prop_row = await cursor.fetchone()
            if not prop_row:
                raise HTTPException(404, "Property not found")
            
            property_data = {
                'id': prop_row[0],
                'user_id': prop_row[1],
                'title': prop_row[2],
                'description': prop_row[3],
                'address': prop_row[4],
                'price': prop_row[5],
                'property_type': prop_row[6],
                'bedrooms': prop_row[7],
                'bathrooms': prop_row[8],
                'square_feet': prop_row[9]
            }
        
        # Get rooms with 360 images
        async with db.execute(
            """SELECT * FROM rooms 
               WHERE property_id = ? AND processing_status = 'completed' 
               ORDER BY sort_order""",
            (property_id,)
        ) as cursor:
            room_rows = await cursor.fetchall()
            
            if not room_rows:
                raise HTTPException(400, "No completed rooms found for this property")
            
            rooms = [{
                'id': r[0],
                'property_id': r[1],
                'space_name': r[2],
                'space_type': r[3],
                'space_category': r[4],
                'description': r[5],
                'square_feet': r[6],
                'image_360_url': r[7],
                'sort_order': r[10]
            } for r in room_rows]
    
    # Start background processing
    background_tasks.add_task(
        process_narrated_tour_background,
        property_id,
        property_data,
        rooms,
        voice_id,
        include_music
    )
    
    return {
        "message": "Narrated tour generation started",
        "property_id": property_id,
        "voice": elevenlabs_engine.voices.get(voice_id, {}).get('name', 'Default'),
        "status": "processing"
    }

async def process_narrated_tour_background(
    property_id: str,
    property_data: dict,
    rooms: list,
    voice_id: str,
    include_music: bool
):
    """Background task to generate narrated tour"""
    try:
        tour_dir = TOURS_DIR / property_id
        tour_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate all narrations
        logger.info(f"Generating narrations for property {property_id}")
        narrations = await elevenlabs_engine.generate_tour_narration(
            property_data,
            rooms,
            voice_id=voice_id,
            output_dir=tour_dir / "audio"
        )
        
        if not narrations:
            logger.error("Failed to generate narrations")
            return
        
        # Create enhanced tour HTML with audio
        scenes = []
        for room in rooms:
            room_name = room['space_name']
            audio_file = narrations.get(room_name)
            
            scene = {
                'id': room['id'],
                'name': room_name,
                'category': room['space_category'],
                'imageUrl': room['image_360_url'],
                'pitch': 0,
                'yaw': 0,
                'fov': 100,
                'audioUrl': f"/tours/{property_id}/audio/{audio_file.name}" if audio_file else None
            }
            scenes.append(scene)
        
        # Generate enhanced HTML with audio player
        tour_html = generate_narrated_tour_html(
            property_id,
            property_data['title'],
            scenes,
            narrations.get('intro'),
            narrations.get('outro')
        )
        
        html_path = tour_dir / "tour_narrated.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(tour_html)
        
        tour_url = f"/tours/{property_id}/tour_narrated.html"
        
        # Update database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create narrated_tours table if not exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS narrated_tours (
                    id TEXT PRIMARY KEY,
                    property_id TEXT NOT NULL,
                    tour_url TEXT,
                    voice_id TEXT,
                    narration_files TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties (id)
                )
            """)
            
            tour_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO narrated_tours 
                (id, property_id, tour_url, voice_id, narration_files, status)
                VALUES (?, ?, ?, ?, ?, 'completed')
            """, (
                tour_id,
                property_id,
                tour_url,
                voice_id,
                json.dumps([str(p) for p in narrations.values()])
            ))
            
            await db.execute(
                "UPDATE properties SET has_tour = 1 WHERE id = ?",
                (property_id,)
            )
            
            await db.commit()
        
        logger.info(f"Narrated tour completed for property {property_id}")
        
    except Exception as e:
        logger.error(f"Error in narrated tour generation: {e}", exc_info=True)

def generate_narrated_tour_html(
    tour_id: str,
    property_title: str,
    scenes: list,
    intro_audio: Path = None,
    outro_audio: Path = None
) -> str:
    """Generate HTML for narrated 360° tour"""
    scenes_json = json.dumps(scenes)
    intro_url = f"/tours/{tour_id}/audio/{intro_audio.name}" if intro_audio else ""
    outro_url = f"/tours/{tour_id}/audio/{outro_audio.name}" if outro_audio else ""
    
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
            background: rgba(0,0,0,0.8); padding: 15px 25px; border-radius: 12px;
            backdrop-filter: blur(10px); display: flex; justify-content: space-between; align-items: center;
        }}
        
        .tour-title {{ color: white; font-size: 24px; font-weight: 600; }}
        .tour-subtitle {{ color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 4px; }}
        
        .audio-controls {{
            position: absolute; top: 100px; right: 20px; z-index: 1000;
            background: rgba(0,0,0,0.8); padding: 15px; border-radius: 12px;
            backdrop-filter: blur(10px);
        }}
        
        .audio-btn {{
            background: rgba(255,255,255,0.2); border: none; color: white;
            padding: 10px 15px; border-radius: 8px; cursor: pointer;
            font-size: 14px; margin: 5px 0; width: 100%;
            transition: all 0.3s;
        }}
        
        .audio-btn:hover {{ background: rgba(255,255,255,0.3); }}
        .audio-btn.playing {{ background: #3b82f6; }}
        
        .scene-nav {{
            position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); z-index: 1000;
            background: rgba(0,0,0,0.8); padding: 15px; border-radius: 12px;
            backdrop-filter: blur(10px); display: flex; gap: 10px; flex-wrap: wrap;
            max-width: 90vw; justify-content: center;
        }}
        
        .scene-btn {{
            background: rgba(255,255,255,0.1); color: white; border: 2px solid rgba(255,255,255,0.3);
            padding: 10px 20px; border-radius: 8px; cursor: pointer; transition: all 0.3s;
            font-size: 14px; font-weight: 500;
        }}
        
        .scene-btn:hover {{ background: rgba(255,255,255,0.2); }}
        .scene-btn.active {{ background: #3b82f6; border-color: #3b82f6; }}
        
        .narration-indicator {{
            position: absolute; bottom: 100px; left: 20px; z-index: 1000;
            background: rgba(59, 130, 246, 0.9); padding: 12px 20px; border-radius: 8px;
            color: white; font-size: 14px; display: none; align-items: center; gap: 10px;
        }}
        
        .narration-indicator.active {{ display: flex; }}
        
        .audio-wave {{
            width: 20px; height: 20px; border: 2px solid white;
            border-radius: 50%; border-top-color: transparent;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
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
    
    <div class="audio-controls">
        <button id="playIntro" class="audio-btn">🎙️ Play Intro</button>
        <button id="toggleNarration" class="audio-btn">🔊 Auto Narration: ON</button>
        <button id="playOutro" class="audio-btn">🎙️ Play Outro</button>
    </div>
    
    <div class="narration-indicator" id="narrationIndicator">
        <div class="audio-wave"></div>
        <span>Narration playing...</span>
    </div>
    
    <div id="panorama"></div>
    <div class="scene-nav" id="sceneNav"></div>
    
    <audio id="introAudio" src="{intro_url}"></audio>
    <audio id="outroAudio" src="{outro_url}"></audio>
    <audio id="sceneAudio"></audio>
    
    <script>
        const scenes = {scenes_json};
        let viewer;
        let currentSceneIndex = 0;
        let autoNarration = true;
        
        const introAudio = document.getElementById('introAudio');
        const outroAudio = document.getElementById('outroAudio');
        const sceneAudio = document.getElementById('sceneAudio');
        const narrationIndicator = document.getElementById('narrationIndicator');
        
        function initTour() {{
            if (scenes.length === 0) return;
            
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
                        pitch: 0,
                        yaw: 0,
                        hfov: 100,
                        autoRotate: -2
                    }};
                    return acc;
                }}, {{}})
            }});
            
            createSceneNavigation();
            updateCurrentRoom(0);
            
            // Play intro on load
            if (autoNarration && introAudio.src) {{
                setTimeout(() => introAudio.play(), 1000);
            }}
        }}
        
        function createSceneNavigation() {{
            const nav = document.getElementById('sceneNav');
            scenes.forEach((scene, index) => {{
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
            viewer.loadScene(scenes[index].id);
            updateCurrentRoom(index);
            
            document.querySelectorAll('.scene-btn').forEach((btn, i) => {{
                btn.classList.toggle('active', i === index);
            }});
            
            // Play room narration
            if (autoNarration && scenes[index].audioUrl) {{
                sceneAudio.src = scenes[index].audioUrl;
                sceneAudio.play();
            }}
        }}
        
        function updateCurrentRoom(index) {{
            document.getElementById('currentRoom').textContent = scenes[index].name;
        }}
        
        // Audio controls
        document.getElementById('playIntro').onclick = () => {{
            stopAllAudio();
            introAudio.play();
        }};
        
        document.getElementById('playOutro').onclick = () => {{
            stopAllAudio();
            outroAudio.play();
        }};
        
        document.getElementById('toggleNarration').onclick = function() {{
            autoNarration = !autoNarration;
            this.textContent = autoNarration ? '🔊 Auto Narration: ON' : '🔇 Auto Narration: OFF';
            this.classList.toggle('playing', autoNarration);
            if (!autoNarration) stopAllAudio();
        }};
        
        function stopAllAudio() {{
            introAudio.pause();
            outroAudio.pause();
            sceneAudio.pause();
        }}
        
        // Show/hide narration indicator
        [introAudio, outroAudio, sceneAudio].forEach(audio => {{
            audio.onplay = () => narrationIndicator.classList.add('active');
            audio.onpause = () => narrationIndicator.classList.remove('active');
            audio.onended = () => narrationIndicator.classList.remove('active');
        }});
        
        window.addEventListener('load', initTour);
    </script>
</body>
</html>"""

@api_router.get("/voice-quota")
async def check_voice_quota():
    """Check ElevenLabs API quota"""
    quota = await elevenlabs_engine.check_quota()
    return quota
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

api_router.post("/properties/{property_id}/upload-room-360")
async def upload_room_with_enhancement(
    property_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    room_name: str = Form(...),
    room_type: str = Form(...),
    enhance: bool = Form(True)
):
    """Upload 360° room image with AI enhancement"""
    
    # Create room entry
    room_id = str(uuid.uuid4())
    upload_path = UPLOADS_DIR / f"{room_id}_{file.filename}"
    
    # Save uploaded file
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # AI Enhancement if requested
    if enhance:
        try:
            enhanced_path = ai_enhancer.enhance_real_estate_photo(
                upload_path,
                output_path=upload_path.parent / f"{room_id}_enhanced.jpg",
                enhancement_level="standard"
            )
            upload_path = enhanced_path
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
    
    # Validate 360 image
    is_valid, message = Tour360Processor.validate_360_image(str(upload_path))
    if not is_valid:
        upload_path.unlink()
        raise HTTPException(400, message)
    
    # Process in background
    background_tasks.add_task(
        process_room_360_background,
        room_id,
        property_id,
        str(upload_path),
        room_name,
        room_type
    )
    
    return {
        "room_id": room_id,
        "message": "Processing enhanced 360° image",
        "status": "processing"
    }

@api_router.post("/properties/{property_id}/generate-complete-tour")
async def generate_complete_tour(
    property_id: str,
    background_tasks: BackgroundTasks,
    rooms: list = Body(...),
    voice_narration: bool = True,
    add_music: bool = True,
    property_type: str = "house"
):
    """Generate complete professional tour with narration and music"""
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get property data
        async with db.execute(
            "SELECT * FROM properties WHERE id = ?", (property_id,)
        ) as cursor:
            prop_row = await cursor.fetchone()
            if not prop_row:
                raise HTTPException(404, "Property not found")
            
            property_data = {
                'id': prop_row[0],
                'title': prop_row[2],
                'description': prop_row[3],
                'address': prop_row[4],
                'price': prop_row[5],
                'property_type': prop_row[6],
                'bedrooms': prop_row[7],
                'bathrooms': prop_row[8],
                'square_feet': prop_row[9]
            }
        
        # Get all room data from database
        room_ids = [r['imageId'] for r in rooms]
        room_data = []
        
        for room_id in room_ids:
            async with db.execute(
                "SELECT * FROM rooms WHERE id = ?", (room_id,)
            ) as cursor:
                room_row = await cursor.fetchone()
                if room_row:
                    room_data.append({
                        'id': room_row[0],
                        'space_name': room_row[2],
                        'space_type': room_row[3],
                        'space_category': room_row[4],
                        'description': room_row[5],
                        'image_360_url': room_row[7]
                    })
    
    # Start background processing
    background_tasks.add_task(
        process_complete_tour_background,
        property_id,
        property_data,
        room_data,
        voice_narration,
        add_music,
        property_type
    )
    
    return {
        "message": "Professional tour generation started",
        "property_id": property_id,
        "total_rooms": len(room_data),
        "estimated_time_minutes": len(room_data) * 2
    }

async def process_complete_tour_background(
    property_id: str,
    property_data: dict,
    rooms: list,
    voice_narration: bool,
    add_music: bool,
    property_type: str
):
    """Background task for complete tour generation"""
    try:
        tour_dir = TOURS_DIR / property_id
        tour_dir.mkdir(parents=True, exist_ok=True)
        
        narrations = {}
        
        # Generate voice narration if enabled
        if voice_narration and elevenlabs_engine.enabled:
            logger.info(f"Generating narrations for {len(rooms)} rooms")
            
            # Choose voice based on property type
            voice_map = {
                'luxury': 'luxury_male',
                'commercial': 'professional_male',
                'apartment': 'friendly_female',
                'house': 'professional_female'
            }
            voice_id = voice_map.get(property_type, 'professional_female')
            
            narrations = await elevenlabs_engine.generate_tour_narration(
                property_data,
                rooms,
                voice_id=voice_id,
                output_dir=tour_dir / "audio"
            )
        
        # Build scene list with narration
        scenes = []
        for i, room in enumerate(rooms):
            room_name = room['space_name']
            audio_file = narrations.get(room_name)
            
            scene = {
                'id': room['id'],
                'name': room_name,
                'category': room.get('space_category', ''),
                'imageUrl': room['image_360_url'],
                'pitch': 0,
                'yaw': 0,
                'fov': 100,
                'audioUrl': f"/tours/{property_id}/audio/{audio_file.name}" if audio_file else None,
                'order': i
            }
            scenes.append(scene)
        
        # Generate enhanced HTML tour
        tour_html = generate_professional_tour_html(
            property_id,
            property_data,
            scenes,
            narrations.get('intro'),
            narrations.get('outro'),
            add_music
        )
        
        html_path = tour_dir / "tour.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(tour_html)
        
        tour_url = f"/tours/{property_id}/tour.html"
        
        # Update database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            tour_id = str(uuid.uuid4())
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS complete_tours (
                    id TEXT PRIMARY KEY,
                    property_id TEXT NOT NULL,
                    tour_url TEXT,
                    voice_enabled BOOLEAN,
                    music_enabled BOOLEAN,
                    total_scenes INTEGER,
                    property_type TEXT,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties (id)
                )
            """)
            
            await db.execute("""
                INSERT INTO complete_tours 
                (id, property_id, tour_url, voice_enabled, music_enabled, 
                 total_scenes, property_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'completed')
            """, (
                tour_id,
                property_id,
                tour_url,
                voice_narration,
                add_music,
                len(scenes),
                property_type
            ))
            
            await db.execute(
                "UPDATE properties SET has_tour = 1 WHERE id = ?",
                (property_id,)
            )
            
            await db.commit()
        
        logger.info(f"Complete professional tour generated: {property_id}")
        
    except Exception as e:
        logger.error(f"Complete tour generation failed: {e}", exc_info=True)

def generate_professional_tour_html(
    property_id: str,
    property_data: dict,
    scenes: list,
    intro_audio: Path = None,
    outro_audio: Path = None,
    add_music: bool = False
) -> str:
    """Generate professional HTML tour with all features"""
    
    scenes_json = json.dumps(scenes)
    intro_url = f"/tours/{property_id}/audio/{intro_audio.name}" if intro_audio else ""
    outro_url = f"/tours/{property_id}/audio/{outro_audio.name}" if outro_audio else ""
    
    # Background music URLs (you'll need to host these)
    music_urls = {
        'luxury': '/static/music/luxury_ambient.mp3',
        'modern': '/static/music/modern_upbeat.mp3',
        'relaxed': '/static/music/relaxed_acoustic.mp3'
    }
    music_url = music_urls.get(property_data.get('property_type', ''), music_urls['modern'])
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{property_data['title']} - Professional Virtual Tour</title>
    <meta name="description" content="{property_data['description']}">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{property_data['title']}">
    <meta property="og:description" content="{property_data['description']}">
    
    <!-- Twitter -->
    <meta property="twitter:card" content="summary_large_image">
    <meta property="twitter:title" content="{property_data['title']}">
    
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css"/>
    <script src="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js"></script>
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica', sans-serif;
            overflow: hidden;
            background: #000;
        }}
        
        #panorama {{ width: 100vw; height: 100vh; }}
        
        /* Premium Header */
        .tour-header {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            z-index: 1000;
            background: linear-gradient(to bottom, rgba(0,0,0,0.9), transparent);
            padding: 25px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .property-info {{
            color: white;
        }}
        
        .property-title {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }}
        
        .property-details {{
            font-size: 16px;
            opacity: 0.9;
            display: flex;
            gap: 20px;
            align-items: center;
        }}
        
        .detail-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .property-price {{
            font-size: 24px;
            font-weight: 700;
            color: #4ade80;
            text-shadow: 0 2px 10px rgba(0,0,0,0.5);
        }}
        
        /* Audio Controls */
        .audio-controls {{
            position: absolute;
            top: 120px;
            right: 30px;
            z-index: 1000;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(10px);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        
        .audio-btn {{
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            padding: 12px 20px;
            border-radius: 10px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            margin: 6px 0;
            width: 100%;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .audio-btn:hover {{ background: rgba(255,255,255,0.2); }}
        .audio-btn.active {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        
        /* Navigation */
        .scene-nav {{
            position: absolute;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(10px);
            padding: 20px 25px;
            border-radius: 16px;
            display: flex;
            gap: 12px;
            max-width: 90vw;
            overflow-x: auto;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }}
        
        .scene-btn {{
            background: rgba(255,255,255,0.1);
            color: white;
            border: 2px solid rgba(255,255,255,0.2);
            padding: 12px 24px;
            border-radius: 12px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            white-space: nowrap;
            transition: all 0.3s;
        }}
        
        .scene-btn:hover {{ 
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }}
        
        .scene-btn.active {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-color: #667eea;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        }}
        
        /* Narration Indicator */
        .narration-indicator {{
            position: absolute;
            bottom: 120px;
            left: 30px;
            z-index: 1000;
            background: rgba(102, 126, 234, 0.95);
            padding: 15px 25px;
            border-radius: 12px;
            color: white;
            font-size: 14px;
            font-weight: 600;
            display: none;
            align-items: center;
            gap: 12px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
        }}
        
        .narration-indicator.active {{ display: flex; }}
        
        .audio-wave {{
            width: 24px;
            height: 24px;
            border: 3px solid white;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Loading Screen */
        .loading-screen {{
            position: fixed;
            inset: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            transition: opacity 0.5s;
        }}
        
        .loading-screen.hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        
        .loading-content {{
            text-align: center;
            color: white;
        }}
        
        .loading-spinner {{
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        
        /* Branding */
        .powered-by {{
            position: absolute;
            bottom: 30px;
            left: 30px;
            z-index: 1000;
            background: rgba(0,0,0,0.7);
            padding: 10px 20px;
            border-radius: 8px;
            color: white;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .powered-by a {{
            color: #667eea;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <!-- Loading Screen -->
    <div class="loading-screen" id="loadingScreen">
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <h2 style="font-size: 24px; margin-bottom: 10px;">Loading Professional Tour...</h2>
            <p style="opacity: 0.9;">Preparing your immersive experience</p>
        </div>
    </div>

    <!-- Tour Header -->
    <div class="tour-header">
        <div class="property-info">
            <div class="property-title">{property_data['title']}</div>
            <div class="property-details">
                <span class="detail-item">📍 {property_data['address']}</span>
                <span class="detail-item">🛏️ {property_data.get('bedrooms', '')} bed</span>
                <span class="detail-item">🚿 {property_data.get('bathrooms', '')} bath</span>
                <span class="detail-item">📐 {property_data.get('square_feet', '')} ft²</span>
            </div>
        </div>
        <div class="property-price">{property_data['price']}</div>
    </div>
    
    <!-- Audio Controls -->
    <div class="audio-controls">
        <button id="playIntro" class="audio-btn">🎙️ Play Intro</button>
        <button id="toggleNarration" class="audio-btn active">🔊 Narration: ON</button>
        <button id="toggleMusic" class="audio-btn {"active" if add_music else ""}">🎵 Music: {"ON" if add_music else "OFF"}</button>
        <button id="playOutro" class="audio-btn">🎙️ Play Outro</button>
    </div>
    
    <!-- Narration Indicator -->
    <div class="narration-indicator" id="narrationIndicator">
        <div class="audio-wave"></div>
        <span>Playing narration...</span>
    </div>
    
    <!-- Panorama Viewer -->
    <div id="panorama"></div>
    
    <!-- Scene Navigation -->
    <div class="scene-nav" id="sceneNav"></div>
    
    <!-- Branding -->
    <div class="powered-by">
        Powered by <a href="https://listingspark.ai" target="_blank">ListingSpark AI</a>
    </div>
    
    <!-- Audio Elements -->
    <audio id="introAudio" src="{intro_url}" preload="auto"></audio>
    <audio id="outroAudio" src="{outro_url}" preload="auto"></audio>
    <audio id="sceneAudio" preload="auto"></audio>
    <audio id="backgroundMusic" src="{music_url if add_music else ''}" loop preload="auto" volume="0.3"></audio>
    
    <script>
        const scenes = {scenes_json};
        let viewer;
        let currentSceneIndex = 0;
        let autoNarration = true;
        let musicEnabled = {"true" if add_music else "false"};
        
        const introAudio = document.getElementById('introAudio');
        const outroAudio = document.getElementById('outroAudio');
        const sceneAudio = document.getElementById('sceneAudio');
        const backgroundMusic = document.getElementById('backgroundMusic');
        const narrationIndicator = document.getElementById('narrationIndicator');
        const loadingScreen = document.getElementById('loadingScreen');
        
        function initTour() {{
            if (scenes.length === 0) {{
                alert('No scenes available for this tour');
                return;
            }}
            
            // Initialize Pannellum viewer
            viewer = pannellum.viewer('panorama', {{
                default: {{
                    firstScene: scenes[0].id,
                    sceneFadeDuration: 1500,
                    autoLoad: true
                }},
                scenes: scenes.reduce((acc, scene) => {{
                    acc[scene.id] = {{
                        type: "equirectangular",
                        panorama: scene.imageUrl,
                        pitch: 0,
                        yaw: 0,
                        hfov: 100,
                        autoRotate: -2,
                        autoRotateInactivityDelay: 3000
                    }};
                    return acc;
                }}, {{}})
            }});
            
            viewer.on('load', () => {{
                setTimeout(() => {{
                    loadingScreen.classList.add('hidden');
                }}, 1000);
            }});
            
            createSceneNavigation();
            updateCurrentRoom(0);
            
            // Auto-play intro
            if (autoNarration && introAudio.src) {{
                setTimeout(() => introAudio.play(), 2000);
            }}
            
            // Start background music
            if (musicEnabled && backgroundMusic.src) {{
                backgroundMusic.play().catch(e => console.log('Music autoplay blocked'));
            }}
        }}
        
        function createSceneNavigation() {{
            const nav = document.getElementById('sceneNav');
            scenes.forEach((scene, index) => {{
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
            viewer.loadScene(scenes[index].id);
            updateCurrentRoom(index);
            
            document.querySelectorAll('.scene-btn').forEach((btn, i) => {{
                btn.classList.toggle('active', i === index);
            }});
            
            // Play room narration
            if (autoNarration && scenes[index].audioUrl) {{
                sceneAudio.src = scenes[index].audioUrl;
                sceneAudio.play();
            }}
        }}
        
        function updateCurrentRoom(index) {{
            // Update any UI showing current room
        }}
        
        // Audio controls
        document.getElementById('playIntro').onclick = () => {{
            stopSceneAudio();
            introAudio.play();
        }};
        
        document.getElementById('playOutro').onclick = () => {{
            stopSceneAudio();
            outroAudio.play();
        }};
        
        document.getElementById('toggleNarration').onclick = function() {{
            autoNarration = !autoNarration;
            this.innerHTML = autoNarration ? '🔊 Narration: ON' : '🔇 Narration: OFF';
            this.classList.toggle('active', autoNarration);
            if (!autoNarration) stopSceneAudio();
        }};
        
        document.getElementById('toggleMusic').onclick = function() {{
            musicEnabled = !musicEnabled;
            this.innerHTML = musicEnabled ? '🎵 Music: ON' : '🎵 Music: OFF';
            this.classList.toggle('active', musicEnabled);
            
            if (musicEnabled) {{
                backgroundMusic.play();
            }} else {{
                backgroundMusic.pause();
            }}
        }};
        
        function stopSceneAudio() {{
            introAudio.pause();
            outroAudio.pause();
            sceneAudio.pause();
        }}
        
        // Show/hide narration indicator
        [introAudio, outroAudio, sceneAudio].forEach(audio => {{
            audio.onplay = () => narrationIndicator.classList.add('active');
            audio.onpause = () => narrationIndicator.classList.remove('active');
            audio.onended = () => narrationIndicator.classList.remove('active');
        }});
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') {{
                switchScene(Math.max(0, currentSceneIndex - 1));
            }} else if (e.key === 'ArrowRight') {{
                switchScene(Math.min(scenes.length - 1, currentSceneIndex + 1));
            }}
        }});
        
        window.addEventListener('load', initTour);
    </script>
</body>
</html>"""

# Add tour analytics endpoint
@api_router.get("/properties/{property_id}/tour-analytics")
async def get_tour_analytics(property_id: str):
    """Get analytics for property tour"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("""
            SELECT COUNT(*) as views, 
                   AVG(CAST(strftime('%s', 'now') - strftime('%s', created_at) AS REAL)) as avg_duration
            FROM tour_views 
            WHERE property_id = ?
        """, (property_id,)) as cursor:
            row = await cursor.fetchone()
            return {
                "total_views": row[0] if row else 0,
                "avg_duration_seconds": row[1] if row else 0
            }

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
