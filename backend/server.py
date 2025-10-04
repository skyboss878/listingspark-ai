import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import asynccontextmanager
Import Platform Module
import aiosqlite
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from platform_integrations import platform_manager, ListingData, ListingStatus
from pydantic import BaseModel
from openai import AsyncOpenAI
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

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
            INSERT INTO rooms (id, property_id, space_name, space_type, space_category, 
                             description, square_feet, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            room_id, room_data.property_id, room_data.space_name,
            room_data.space_type, room_data.space_category,
            room_data.description, room_data.square_feet, next_order
        ))
        await db.commit()
    
    return {"id": room_id, "message": "Room created successfully", "sort_order": next_order}

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

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0-professional"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000).execute("""
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
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tours (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                tour_name TEXT NOT NULL,
                tour_url TEXT,
                status TEXT DEFAULT 'draft',
                total_scenes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS custom_amenities (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                amenity_name TEXT NOT NULL UNIQUE,
                category TEXT DEFAULT 'Custom',
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS virtual_tours (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                tour_name TEXT NOT NULL,
                tour_url TEXT NOT NULL,
                thumbnail_url TEXT,
                processing_status TEXT DEFAULT 'processing',
                tour_type TEXT DEFAULT '360_image',
                scene_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tour_scenes (
                id TEXT PRIMARY KEY,
                tour_id TEXT NOT NULL,
                scene_name TEXT NOT NULL,
                image_url TEXT NOT NULL,
                thumbnail_url TEXT,
                pitch REAL DEFAULT 0,
                yaw REAL DEFAULT 0,
                fov REAL DEFAULT 100,
                scene_order INTEGER DEFAULT 0,
                FOREIGN KEY (tour_id) REFERENCES virtual_tours (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                property_id TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                engagement_rate REAL DEFAULT 0.0,
                viral_score INTEGER DEFAULT 0,
                tour_views INTEGER DEFAULT 0,
                trending_status TEXT DEFAULT 'normal',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS viral_content (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                content_type TEXT NOT NULL,
                content TEXT NOT NULL,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        
        await db.commit()
        logger.info("Database initialized successfully")

# ============================================================================
# API ENDPOINTS
# ============================================================================

# Users
@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate):
    user_id = str(uuid.uuid4())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM users WHERE email = ?", (user_data.email,)) as cursor:
            existing = await cursor.fetchone()
            if existing:
                return User(id=existing[0], email=existing[1], name=existing[2], 
                          plan=existing[3], listings_created=existing[4])
        
        await db.execute(
            "INSERT INTO users (id, email, name) VALUES (?, ?, ?)",
            (user_id, user_data.email, user_data.name)
        )
        await db.commit()
    
    return User(id=user_id, email=user_data.email, name=user_data.name, 
                plan="free", listings_created=0)

# Properties
@api_router.post("/properties")
async def create_property(property_data: PropertyCreate):
    property_id = str(uuid.uuid4())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            INSERT INTO properties (id, user_id, title, description, address, price,
                                  property_type, bedrooms, bathrooms, square_feet, features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            property_id, property_data.user_id, property_data.title,
            property_data.description, property_data.address, property_data.price,
            property_data.property_type, property_data.bedrooms, property_data.bathrooms,
            property_data.square_feet, json.dumps(property_data.features)
        ))
        await db.commit()
    
    return {"id": property_id, "message": "Property created successfully"}

@api_router.get("/properties/{user_id}")
async def get_user_properties(user_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM properties WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                'id': row[0], 'user_id': row[1], 'title': row[2],
                'description': row[3], 'address': row[4], 'price': row[5],
                'property_type': row[6], 'bedrooms': row[7], 'bathrooms': row[8],
                'square_feet': row[9], 'features': json.loads(row[10] or '[]'),
                'has_tour': bool(row[11]), 'created_at': row[12]
            } for row in rows]

@api_router.get("/properties/detail/{property_id}")
async def get_property_detail(property_id: str):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM properties WHERE id = ?", (property_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, "Property not found")
            
            return {
                'id': row[0], 'user_id': row[1], 'title': row[2],
                'description': row[3], 'address': row[4], 'price': row[5],
                'property_type': row[6], 'bedrooms': row[7], 'bathrooms': row[8],
                'square_feet': row[9], 'features': json.loads(row[10] or '[]'),
                'has_tour': bool(row[11]), 'created_at': row[12]
            }

# Space Types & Amenities
@api_router.get("/space-types")
async def get_space_types():
    """Get all available space types organized by category"""
    return SPACE_TYPES

@api_router.get("/standard-amenities")
async def get_standard_amenities():
    """Get all standard amenities organized by category"""
    return STANDARD_AMENITIES

@api_router.get("/custom-amenities/{user_id}")
async def get_custom_amenities(user_id: str):
    """Get user's custom amenities"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT id, amenity_name, category, usage_count FROM custom_amenities WHERE user_id = ? ORDER BY usage_count DESC",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                'id': row[0],
                'amenity_name': row[1],
                'category': row[2],
                'usage_count': row[3]
            } for row in rows]

@api_router.post("/custom-amenities")
async def create_custom_amenity(amenity_data: CustomAmenityCreate):
    """Create a new custom amenity"""
    amenity_id = str(uuid.uuid4())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            await db.execute("""
                INSERT INTO custom_amenities (id, user_id, amenity_name, category)
                VALUES (?, ?, ?, ?)
            """, (amenity_id, amenity_data.user_id, amenity_data.amenity_name, amenity_data.category))
            await db.commit()
            return {"id": amenity_id, "message": "Custom amenity created successfully"}
        except aiosqlite.IntegrityError:
            raise HTTPException(400, "This amenity already exists")

# Rooms/Spaces
@api_router.post("/rooms")
async def create_room(room_data: RoomCreate):
    """Create a new room/space for a property"""
    room_id = str(uuid.uuid4())
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get current max sort_order
        async with db.execute(
            "SELECT MAX(sort_order) FROM rooms WHERE property_id = ?",
            (room_data.property_id,)
        ) as cursor:
            max_order = await cursor.fetchone()
            next_order = (max_order[0] or 0) + 1
        
        await db.execute("""
            INSERT INTO rooms (id, property_id, space_name, space_type, space_category, 
                             description, square_feet, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            room_id, room_data.property_id, room_data.space_name,
            room_data.space_type, room_data.space_category,
            room_data.description, room_data.square_feet, next_order
        ))
        await db.commit()
    
    return {"id": room_id, "message": "Room created successfully", "sort_order": next_order}

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

# AI Content Generation
class AIContentEngine:
    """Generate viral marketing content using OpenAI"""
    
    @staticmethod
    async def generate_listing_description(property_data: dict) -> str:
        """Generate compelling property description"""
        try:
            has_tour = property_data.get('has_tour', False)
            tour_emphasis = "\n\nIMPORTANT: This property has a 360° VIRTUAL TOUR! Emphasize this heavily." if has_tour else ""
            
            prompt = f"""Write a compelling real estate listing description for:

Property Type: {property_data.get('property_type', 'home')}
Bedrooms: {property_data.get('bedrooms', 'N/A')}
Bathrooms: {property_data.get('bathrooms', 'N/A')}
Square Feet: {property_data.get('square_feet', 'N/A')}
Address: {property_data.get('address', 'Beautiful location')}
Price: ${property_data.get('price', 'Contact for pricing')}
Features: {', '.join(property_data.get('features', []))}{tour_emphasis}

Write an engaging, professional description that highlights the best features. Keep it under 200 words."""

            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"AI description generation failed: {e}")
            return property_data.get('description', 'Beautiful property available.')
    
    @staticmethod
    async def generate_social_post(property_data: dict, platform: str) -> dict:
        """Generate platform-specific social media content"""
        has_tour = property_data.get('has_tour', False)
        tour_text = "\n\n🎯 VIRTUAL 360° TOUR AVAILABLE! Explore every room interactively!" if has_tour else ""
        
        prompts = {
            "instagram": f"""Create an Instagram caption for this property:
{property_data.get('description', 'Beautiful property')}{tour_text}

Include emojis, hashtags, and make it engaging. Max 2200 characters.""",
            
            "facebook": f"""Create a Facebook post for this property listing:
{property_data.get('description', 'Beautiful property')}{tour_text}

Make it conversational and include a call-to-action.""",
            
            "twitter": f"""Create a Twitter/X post (280 chars max) for this property:
{property_data.get('description', 'Beautiful property')}{tour_text}"""
        }
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompts.get(platform, prompts["instagram"])}],
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                "platform": platform,
                "content": content,
                "viral_score": 85 if has_tour else 70,
                "optimal_time": "6:00 PM - 9:00 PM"
            }
        except Exception as e:
            logger.error(f"AI social post generation failed: {e}")
            return {
                "platform": platform,
                "content": f"Beautiful property available! {tour_text}",
                "viral_score": 50,
                "optimal_time": "6:00 PM - 9:00 PM"
            }

@api_router.post("/properties/{property_id}/viral-content")
async def generate_viral_content(property_id: str):
    """Generate viral marketing content for all platforms"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                raise HTTPException(404, "Property not found")
            
            property_data = {
                'id': row[0], 'title': row[2], 'description': row[3],
                'address': row[4], 'price': row[5], 'property_type': row[6],
                'bedrooms': row[7], 'bathrooms': row[8], 'square_feet': row[9],
                'features': json.loads(row[10] or '[]'), 'has_tour': bool(row[11])
            }
    
    platforms = ["instagram", "facebook", "twitter"]
    results = []
    
    for platform in platforms:
        content = await AIContentEngine.generate_social_post(property_data, platform)
        content_id = str(uuid.uuid4())
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute("""
                INSERT INTO viral_content (id, property_id, platform, content_type, content)
                VALUES (?, ?, ?, 'post', ?)
            """, (content_id, property_id, platform, content['content']))
            await db.commit()
        
        results.append(content)
    
    return {"property_id": property_id, "content": results}

@api_router.get("/properties/{property_id}/viral-content")
async def get_viral_content(property_id: str):
    """Get generated viral content for property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute(
            "SELECT * FROM viral_content WHERE property_id = ? ORDER BY generated_at DESC",
            (property_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                'id': row[0], 'property_id': row[1], 'platform': row[2],
                'content_type': row[3], 'content': row[4], 'generated_at': row[5]
            } for row in rows]

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

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0-professional"}

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


@api_router.post("/properties/{property_id}/publish")
async def publish_to_platforms(property_id: str, publish_request: PublishRequest, background_tasks: BackgroundTasks):
    """
    Publish property listing to selected platforms
    
    This is the MAIN endpoint realtors will use to distribute their listings
    """
    # Get property details from database
    async with aiosqlite.connect(DATABASE_PATH) as db:
        async with db.execute("SELECT * FROM properties WHERE id = ?", (property_id,)) as cursor:
            property_row = await cursor.fetchone()
            if not property_row:
                raise HTTPException(404, "Property not found")
            
            # Parse property data
            property_data = {
                'id': property_row[0],
                'user_id': property_row[1],
                'title': property_row[2],
                'description': property_row[3],
                'address': property_row[4],
                'price': property_row[5],
                'property_type': property_row[6],
                'bedrooms': property_row[7],
                'bathrooms': property_row[8],
                'square_feet': property_row[9],
                'features': json.loads(property_row[10] or '[]'),
                'has_tour': bool(property_row[11])
            }
        
        # Get property photos
        async with db.execute(
            "SELECT image_360_url FROM rooms WHERE property_id = ? AND image_360_url IS NOT NULL",
            (property_id,)
        ) as cursor:
            photos = [row[0] for row in await cursor.fetchall()]
        
        # Get tour URL if available
        tour_url = None
        if property_data['has_tour']:
            async with db.execute(
                "SELECT tour_url FROM tours WHERE property_id = ? AND status = 'completed' ORDER BY created_at DESC LIMIT 1",
                (property_id,)
            ) as cursor:
                tour = await cursor.fetchone()
                if tour:
                    tour_url = f"https://yourdomain.com{tour[0]}"  # Full URL needed for platforms
        
        # Parse address for platform requirements
        address_parts = property_data['address'].split(',')
        city = address_parts[1].strip() if len(address_parts) > 1 else "Unknown"
        state = address_parts[2].strip().split()[0] if len(address_parts) > 2 else "CA"
        zip_code = address_parts[2].strip().split()[1] if len(address_parts) > 2 else "00000"
        
        # Create standardized listing data
        listing = ListingData(
            property_id=property_id,
            title=property_data['title'],
            description=property_data['description'],
            address=address_parts[0].strip() if address_parts else property_data['address'],
            city=city,
            state=state,
            zip_code=zip_code,
            price=float(property_data['price'].replace('$', '').replace(',', '')),
            property_type=property_data['property_type'],
            bedrooms=property_data['bedrooms'],
            bathrooms=property_data['bathrooms'],
            square_feet=property_data['square_feet'],
            features=property_data['features'],
            photos=photos if photos else ['/default-property-image.jpg'],
            tour_360_url=tour_url,
            contact_name=publish_request.contact_name,
            contact_email=publish_request.contact_email,
            contact_phone=publish_request.contact_phone,
            listing_agent=publish_request.listing_agent
        )
    
    # Publish to selected platforms in background
    background_tasks.add_task(
        publish_listing_background,
        property_id,
        listing,
        publish_request.platforms
    )
    
    return {
        "message": "Publishing to platforms started",
        "property_id": property_id,
        "platforms": publish_request.platforms,
        "status": "processing"
    }


async def publish_listing_background(property_id: str, listing: ListingData, platforms: List[str]):
    """Background task to publish listing to platforms"""
    try:
        # Publish to all selected platforms
        results = await platform_manager.publish_to_all(listing, platforms)
        
        # Store sync records in database
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create platform_syncs table if not exists
            await db.execute("""
                CREATE TABLE IF NOT EXISTS platform_syncs (
                    id TEXT PRIMARY KEY,
                    property_id TEXT NOT NULL,
                    platform_name TEXT NOT NULL,
                    platform_listing_id TEXT,
                    platform_url TEXT,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties (id)
                )
            """)
            
            # Record successful syncs
            for success in results['successes']:
                sync_id = str(uuid.uuid4())
                await db.execute("""
                    INSERT INTO platform_syncs 
                    (id, property_id, platform_name, platform_listing_id, platform_url, status)
                    VALUES (?, ?, ?, ?, ?, 'published')
                """, (
                    sync_id,
                    property_id,
                    success.get('platform'),
                    success.get('platform_listing_id'),
                    success.get('url'),
                ))
            
            # Record failures
            for failure in results['failures']:
                sync_id = str(uuid.uuid4())
                error_msg = ', '.join(failure.get('errors', ['Unknown error']))
                await db.execute("""
                    INSERT INTO platform_syncs 
                    (id, property_id, platform_name, status, error_message)
                    VALUES (?, ?, ?, 'failed', ?)
                """, (
                    sync_id,
                    property_id,
                    failure.get('platform', 'unknown'),
                    error_msg
                ))
            
            await db.commit()
        
        logger.info(f"Published property {property_id} to {len(results['successes'])} platforms")
        
    except Exception as e:
        logger.error(f"Background publishing error: {e}")


@api_router.get("/properties/{property_id}/platform-syncs")
async def get_property_platform_syncs(property_id: str):
    """Get all platform sync records for a property"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Create table if not exists
        await db.execute("""
            CREATE TABLE IF NOT EXISTS platform_syncs (
                id TEXT PRIMARY KEY,
                property_id TEXT NOT NULL,
                platform_name TEXT NOT NULL,
                platform_listing_id TEXT,
                platform_url TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (property_id) REFERENCES properties (id)
            )
        """)
        await db.commit()
        
        async with db.execute(
            "SELECT * FROM platform_syncs WHERE property_id = ? ORDER BY synced_at DESC",
            (property_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [{
                'id': row[0],
                'property_id': row[1],
                'platform_name': row[2],
                'platform_listing_id': row[3],
                'platform_url': row[4],
                'status': row[5],
                'error_message': row[6],
                'synced_at': row[7]
            } for row in rows]


@api_router.post("/properties/{property_id}/sync-to/{platform_name}")
async def sync_to_single_platform(property_id: str, platform_name: str, contact_info: PublishRequest):
    """Sync a single property to one specific platform"""
    # Reuse the publish_to_platforms logic but for single platform
    contact_info.property_id = property_id
    contact_info.platforms = [platform_name]
    
    return await publish_to_platforms(property_id, contact_info, BackgroundTasks())


@api_router.delete("/platform-syncs/{sync_id}")
async def remove_from_platform(sync_id: str):
    """Remove listing from a platform and delete sync record"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get sync record
        async with db.execute(
            "SELECT platform_name, platform_listing_id FROM platform_syncs WHERE id = ?",
            (sync_id,)
        ) as cursor:
            sync = await cursor.fetchone()
            if not sync:
                raise HTTPException(404, "Sync record not found")
            
            platform_name, platform_listing_id = sync
        
        # Try to delete from platform
        if platform_listing_id:
            platform = platform_manager.platforms.get(platform_name)
            if platform:
                try:
                    await platform.delete_listing(platform_listing_id)
                except Exception as e:
                    logger.error(f"Error deleting from {platform_name}: {e}")
        
        # Delete sync record
        await db.execute("DELETE FROM platform_syncs WHERE id = ?", (sync_id,))
        await db.commit()
    
    return {"message": "Listing removed from platform", "sync_id": sync_id}


@api_router.post("/platforms/{platform_name}/test")
async def test_platform_connection(platform_name: str):
    """Test connection to a specific platform"""
    platform = platform_manager.platforms.get(platform_name)
    if not platform:
        raise HTTPException(404, f"Platform {platform_name} not found")
    
    try:
        authenticated = await platform.authenticate()
        return {
            "platform": platform_name,
            "connected": authenticated,
            "status": platform.status,
            "message": "Authentication successful" if authenticated else "Authentication failed"
        }
    except Exception as e:
        return {
            "platform": platform_name,
            "connected": False,
            "error": str(e)
        }


@api_router.get("/platforms/sync-summary/{user_id}")
async def get_user_sync_summary(user_id: str):
    """Get summary of all platform syncs for a user"""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Get all properties for user
        async with db.execute(
            "SELECT id FROM properties WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            property_ids = [row[0] for row in await cursor.fetchall()]
        
        if not property_ids:
            return {
                "user_id": user_id,
                "total_properties": 0,
                "total_syncs": 0,
                "syncs_by_platform": {},
                "syncs_by_status": {}
            }
        
        # Get all syncs for these properties
        placeholders = ','.join('?' * len(property_ids))
        async with db.execute(
            f"SELECT platform_name, status FROM platform_syncs WHERE property_id IN ({placeholders})",
            property_ids
        ) as cursor:
            syncs = await cursor.fetchall()
        
        # Aggregate data
        syncs_by_platform = {}
        syncs_by_status = {"published": 0, "failed": 0, "pending": 0}
        
        for platform_name, status in syncs:
            syncs_by_platform[platform_name] = syncs_by_platform.get(platform_name, 0) + 1
            syncs_by_status[status] = syncs_by_status.get(status, 0) + 1
        
        return {
            "user_id": user_id,
            "total_properties": len(property_ids),
            "total_syncs": len(syncs),
            "syncs_by_platform": syncs_by_platform,
            "syncs_by_status": syncs_by_status,
            "success_rate": round((syncs_by_status['published'] / len(syncs) * 100) if syncs else 0, 2)
        }


@api_router.post("/properties/{property_id}/republish")
async def republish_listing(property_id: str, platforms: Optional[List[str]] = None, background_tasks: BackgroundTasks = None):
    """Republish listing to platforms (update existing listings)"""
    # Get existing sync records
    async with aiosqlite.connect(DATABASE_PATH) as db:
        if platforms:
            placeholders = ','.join('?' * len(platforms))
            query = f"SELECT * FROM platform_syncs WHERE property_id = ? AND platform_name IN ({placeholders}) AND status = 'published'"
            params = [property_id] + platforms
        else:
            query = "SELECT * FROM platform_syncs WHERE property_id = ? AND status = 'published'"
            params = [property_id]
        
        async with db.execute(query, params) as cursor:
            existing_syncs = await cursor.fetchall()
        
        if not existing_syncs:
            raise HTTPException(404, "No published listings found to update")
        
        # Mark as pending update
        for sync in existing_syncs:
            await db.execute(
                "UPDATE platform_syncs SET status = 'updating' WHERE id = ?",
                (sync[0],)
            )
        await db.commit()
    
    return {
        "message": "Republishing started",
        "property_id": property_id,
        "platforms_updating": len(existing_syncs)
    }


# ============================================================================
# WEBHOOK ENDPOINTS - For platforms that support webhooks
# ============================================================================

@api_router.post("/webhooks/zillow")
async def zillow_webhook(data: dict):
    """Handle Zillow webhook notifications"""
    logger.info(f"Zillow webhook received: {data}")
    
    # Process webhook data
    # Update sync status, track views, etc.
    
    return {"status": "received"}


@api_router.post("/webhooks/realtor")
async def realtor_webhook(data: dict):
    """Handle Realtor.com webhook notifications"""
    logger.info(f"Realtor.com webhook received: {data}")
    return {"status": "received"}


@api_router.post("/webhooks/mls")
async def mls_webhook(data: dict):
    """Handle MLS webhook notifications"""
    logger.info(f"MLS webhook received: {data}")
    return {"status": "received"}


# ============================================================================
# BULK OPERATIONS
# ============================================================================

@api_router.post("/bulk/publish")
async def bulk_publish_properties(
    property_ids: List[str],
    platforms: List[str],
    contact_info: dict,
    background_tasks: BackgroundTasks
):
    """Publish multiple properties to multiple platforms at once"""
    results = {
        "total_properties": len(property_ids),
        "total_platforms": len(platforms),
        "started": []
    }
    
    for property_id in property_ids:
        try:
            publish_request = PublishRequest(
                property_id=property_id,
                platforms=platforms,
                contact_name=contact_info.get('contact_name', ''),
                contact_email=contact_info.get('contact_email', ''),
                contact_phone=contact_info.get('contact_phone', '')
            )
            
            await publish_to_platforms(property_id, publish_request, background_tasks)
            results['started'].append(property_id)
        except Exception as e:
            logger.error(f"Error bulk publishing {property_id}: {e}")
    
    return results


@api_router.get("/bulk/sync-status")
async def get_bulk_sync_status(property_ids: List[str]):
    """Get sync status for multiple properties"""
    results = []
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        for property_id in property_ids:
            async with db.execute(
                "SELECT platform_name, status FROM platform_syncs WHERE property_id = ?",
                (property_id,)
            ) as cursor:
                syncs = await cursor.fetchall()
                results.append({
                    "property_id": property_id,
                    "syncs": [{"platform": s[0], "status": s[1]} for s in syncs]
                })
    
    return results
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
