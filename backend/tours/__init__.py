"""
360° Virtual Tour Processing Module
Handles equirectangular image processing, tour generation, and hotspot management
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Hotspot:
    """Represents a clickable hotspot in a 360 scene"""
    id: str
    position: Dict[str, float]  # {x, y, z} or {pitch, yaw}
    target_scene: Optional[str] = None
    label: str = ""
    description: str = ""
    icon: str = "info"

@dataclass
class Scene:
    """Represents a single 360° scene"""
    id: str
    name: str
    image_path: str
    image_url: str
    thumbnail_url: str
    hotspots: List[Hotspot]
    initial_view: Dict[str, float]  # {pitch, yaw, fov}
    order: int = 0

class Tour360Processor:
    """Process and manage 360° virtual tours"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp'}
    
    # Minimum dimensions for 360 images (equirectangular 2:1)
    MIN_WIDTH = 2048
    MIN_HEIGHT = 1024
    
    # Optimal dimensions for web
    WEB_WIDTH = 4096
    WEB_HEIGHT = 2048
    THUMBNAIL_SIZE = (400, 200)
    
    @staticmethod
    def validate_360_image(image_path: str) -> Tuple[bool, str]:
        """
        Validate if an image is suitable for 360° viewing
        Returns: (is_valid, error_message)
        """
        try:
            if not os.path.exists(image_path):
                return False, "File does not exist"
            
            # Check file extension
            ext = Path(image_path).suffix.lower()
            if ext not in Tour360Processor.SUPPORTED_FORMATS:
                return False, f"Unsupported format. Use: {', '.join(Tour360Processor.SUPPORTED_FORMATS)}"
            
            # Open and analyze image
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum dimensions
                if width < Tour360Processor.MIN_WIDTH or height < Tour360Processor.MIN_HEIGHT:
                    return False, f"Image too small. Minimum: {Tour360Processor.MIN_WIDTH}x{Tour360Processor.MIN_HEIGHT}"
                
                # Check aspect ratio (equirectangular should be 2:1)
                aspect_ratio = width / height
                if not (1.8 <= aspect_ratio <= 2.2):
                    return False, f"Invalid aspect ratio {aspect_ratio:.2f}. Expected 2:1 for equirectangular images"
                
                # Check if image is RGB
                if img.mode not in ('RGB', 'RGBA'):
                    return False, f"Invalid color mode: {img.mode}. Expected RGB or RGBA"
                
                return True, "Valid 360° image"
                
        except Exception as e:
            logger.error(f"Error validating image: {e}")
            return False, f"Error reading image: {str(e)}"
    
    @staticmethod
    async def process_360_image(
        image_path: str,
        tour_dir: Path,
        scene_name: str = "scene"
    ) -> Dict[str, any]:
        """
        Process a 360° image for web viewing
        Returns: Dict with processed image paths and metadata
        """
        try:
            # Validate image
            is_valid, message = Tour360Processor.validate_360_image(image_path)
            if not is_valid:
                raise ValueError(message)
            
            # Create output paths
            processed_path = tour_dir / f"{scene_name}_processed.jpg"
            thumbnail_path = tour_dir / f"{scene_name}_thumb.jpg"
            
            # Process main image
            with Image.open(image_path) as img:
                original_size = img.size
                
                # Convert to RGB if needed
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                
                # Resize if too large
                if img.width > Tour360Processor.WEB_WIDTH:
                    new_height = int(img.height * Tour360Processor.WEB_WIDTH / img.width)
                    img = img.resize((Tour360Processor.WEB_WIDTH, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized image from {original_size} to {img.size}")
                
                # Optimize and save
                img.save(processed_path, "JPEG", quality=85, optimize=True, progressive=True)
                
                # Create thumbnail
                thumb = img.copy()
                thumb.thumbnail(Tour360Processor.THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                thumb.save(thumbnail_path, "JPEG", quality=80, optimize=True)
            
            # Get file sizes
            processed_size = os.path.getsize(processed_path)
            thumb_size = os.path.getsize(thumbnail_path)
            
            return {
                "success": True,
                "processed_path": str(processed_path),
                "thumbnail_path": str(thumbnail_path),
                "processed_size": processed_size,
                "thumbnail_size": thumb_size,
                "dimensions": {
                    "width": Tour360Processor.WEB_WIDTH,
                    "height": Tour360Processor.WEB_HEIGHT
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing 360 image: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def create_tour_viewer_html(
        scenes: List[Scene],
        tour_name: str = "Virtual Tour",
        initial_scene: int = 0
    ) -> str:
        """
        Generate standalone HTML viewer for 360° tour with navigation
        Uses Pannellum library (lightweight, no dependencies)
        """
        
        # Convert scenes to JSON
        scenes_data = []
        for scene in scenes:
            scene_dict = {
                "id": scene.id,
                "name": scene.name,
                "panorama": scene.image_url,
                "pitch": scene.initial_view.get("pitch", 0),
                "yaw": scene.initial_view.get("yaw", 0),
                "hfov": scene.initial_view.get("fov", 100),
                "hotSpots": []
            }
            
            # Add hotspots
            for hotspot in scene.hotspots:
                hotspot_dict = {
                    "id": hotspot.id,
                    "pitch": hotspot.position.get("pitch", 0),
                    "yaw": hotspot.position.get("yaw", 0),
                    "type": "scene" if hotspot.target_scene else "info",
                    "text": hotspot.label,
                    "sceneId": hotspot.target_scene
                }
                if hotspot.description:
                    hotspot_dict["description"] = hotspot.description
                scene_dict["hotSpots"].append(hotspot_dict)
            
            scenes_data.append(scene_dict)
        
        scenes_json = json.dumps(scenes_data, indent=2)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{tour_name}</title>
    
    <!-- Pannellum CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css"/>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
            background: #000;
        }}
        
        #panorama {{
            width: 100vw;
            height: 100vh;
        }}
        
        .tour-header {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(180deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%);
            padding: 20px;
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .tour-title {{
            color: white;
            font-size: 24px;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }}
        
        .fullscreen-btn {{
            background: rgba(255,255,255,0.2);
            border: 2px solid rgba(255,255,255,0.5);
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
            backdrop-filter: blur(10px);
        }}
        
        .fullscreen-btn:hover {{
            background: rgba(255,255,255,0.3);
            border-color: rgba(255,255,255,0.8);
        }}
        
        .scene-navigation {{
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(10px);
            padding: 15px 25px;
            border-radius: 50px;
            display: flex;
            gap: 10px;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        
        .scene-btn {{
            background: rgba(255,255,255,0.1);
            border: 2px solid rgba(255,255,255,0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s;
            white-space: nowrap;
        }}
        
        .scene-btn:hover {{
            background: rgba(255,255,255,0.2);
            border-color: rgba(255,255,255,0.5);
            transform: translateY(-2px);
        }}
        
        .scene-btn.active {{
            background: rgba(255,255,255,0.9);
            color: #000;
            border-color: white;
        }}
        
        .controls-hint {{
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            z-index: 1000;
            animation: fadeOut 5s forwards;
        }}
        
        @keyframes fadeOut {{
            0%, 70% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}
        
        .loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 18px;
            z-index: 2000;
        }}
        
        .hotspot-tooltip {{
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 13px;
            max-width: 200px;
        }}
    </style>
</head>
<body>
    <div class="tour-header">
        <div class="tour-title">{tour_name}</div>
        <button class="fullscreen-btn" onclick="toggleFullscreen()">⛶ Fullscreen</button>
    </div>
    
    <div class="controls-hint">
        🖱️ Click and drag to look around • Scroll to zoom
    </div>
    
    <div id="panorama"></div>
    
    <div class="scene-navigation" id="sceneNav">
        <!-- Scene buttons will be generated here -->
    </div>
    
    <!-- Pannellum JS -->
    <script src="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js"></script>
    
    <script>
        const scenes = {scenes_json};
        let viewer = null;
        let currentSceneIndex = {initial_scene};
        
        // Initialize the tour
        function initTour() {{
            const firstScene = scenes[currentSceneIndex];
            
            viewer = pannellum.viewer('panorama', {{
                "default": {{
                    "firstScene": firstScene.id,
                    "sceneFadeDuration": 1000,
                    "autoLoad": true
                }},
                "scenes": {{}}
            }});
            
            // Add all scenes
            scenes.forEach(scene => {{
                viewer.addScene(scene.id, {{
                    "type": "equirectangular",
                    "panorama": scene.panorama,
                    "pitch": scene.pitch,
                    "yaw": scene.yaw,
                    "hfov": scene.hfov,
                    "hotSpots": scene.hotSpots.map(hs => ({{
                        ...hs,
                        "clickHandlerFunc": hs.type === "scene" ? 
                            () => loadScene(scenes.findIndex(s => s.id === hs.sceneId)) :
                            undefined,
                        "createTooltipFunc": (hotSpotDiv, args) => {{
                            const tooltip = document.createElement('div');
                            tooltip.className = 'hotspot-tooltip';
                            tooltip.textContent = args.text;
                            if (args.description) {{
                                tooltip.innerHTML += '<br><small>' + args.description + '</small>';
                            }}
                            hotSpotDiv.appendChild(tooltip);
                        }}
                    })))
                }});
            }});
            
            // Generate scene navigation buttons
            generateSceneButtons();
        }}
        
        function generateSceneButtons() {{
            const nav = document.getElementById('sceneNav');
            nav.innerHTML = '';
            
            scenes.forEach((scene, index) => {{
                const btn = document.createElement('button');
                btn.className = 'scene-btn' + (index === currentSceneIndex ? ' active' : '');
                btn.textContent = scene.name;
                btn.onclick = () => loadScene(index);
                nav.appendChild(btn);
            }});
        }}
        
        function loadScene(index) {{
            if (index < 0 || index >= scenes.length) return;
            
            currentSceneIndex = index;
            const scene = scenes[index];
            viewer.loadScene(scene.id);
            
            // Update button states
            document.querySelectorAll('.scene-btn').forEach((btn, i) => {{
                btn.classList.toggle('active', i === index);
            }});
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowLeft') {{
                loadScene(currentSceneIndex - 1);
            }} else if (e.key === 'ArrowRight') {{
                loadScene(currentSceneIndex + 1);
            }} else if (e.key === 'f' || e.key === 'F') {{
                toggleFullscreen();
            }}
        }});
        
        // Initialize on load
        window.addEventListener('load', initTour);
    </script>
</body>
</html>"""
        
        return html
    
    @staticmethod
    def add_navigation_hotspots(scenes: List[Scene]) -> List[Scene]:
        """
        Automatically add navigation hotspots between consecutive scenes
        """
        for i, scene in enumerate(scenes):
            # Add "Next" hotspot if not last scene
            if i < len(scenes) - 1:
                next_scene = scenes[i + 1]
                hotspot = Hotspot(
                    id=f"nav_next_{i}",
                    position={"pitch": -10, "yaw": 90},
                    target_scene=next_scene.id,
                    label=f"→ {next_scene.name}",
                    description="Go to next room",
                    icon="arrow"
                )
                scene.hotspots.append(hotspot)
            
            # Add "Previous" hotspot if not first scene
            if i > 0:
                prev_scene = scenes[i - 1]
                hotspot = Hotspot(
                    id=f"nav_prev_{i}",
                    position={"pitch": -10, "yaw": -90},
                    target_scene=prev_scene.id,
                    label=f"← {prev_scene.name}",
                    description="Go to previous room",
                    icon="arrow"
                )
                scene.hotspots.append(hotspot)
        
        return scenes
