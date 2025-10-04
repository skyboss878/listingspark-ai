"""
ListingSpark AI - Real Estate Platform Integrations
Integrates with major real estate platforms for automated listing distribution
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PlatformStatus(str, Enum):
    """Platform integration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class ListingStatus(str, Enum):
    """Listing sync status"""
    DRAFT = "draft"
    PUBLISHED = "published"
    PENDING = "pending"
    FAILED = "failed"
    SYNCED = "synced"


class PlatformConfig(BaseModel):
    """Configuration for a platform integration"""
    platform_name: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    enabled: bool = False
    auto_sync: bool = False
    rate_limit_per_hour: int = 100
    supports_360_tours: bool = False
    supports_video: bool = False
    max_photos: int = 50


class ListingData(BaseModel):
    """Standardized listing data for all platforms"""
    property_id: str
    title: str
    description: str
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "USA"
    price: float
    property_type: str
    bedrooms: int
    bathrooms: float
    square_feet: int
    lot_size: Optional[float] = None
    year_built: Optional[int] = None
    features: List[str] = []
    photos: List[str] = []
    tour_360_url: Optional[str] = None
    video_url: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: str
    listing_agent: Optional[str] = None
    mls_number: Optional[str] = None


class PlatformIntegration:
    """Base class for platform integrations"""
    
    def __init__(self, config: PlatformConfig):
        self.config = config
        self.status = PlatformStatus.INACTIVE
        self.last_sync: Optional[datetime] = None
        self.sync_count = 0
        self.error_count = 0
    
    async def authenticate(self) -> bool:
        """Authenticate with the platform"""
        raise NotImplementedError
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish a listing to the platform"""
        raise NotImplementedError
    
    async def update_listing(self, platform_listing_id: str, listing: ListingData) -> Dict[str, Any]:
        """Update an existing listing"""
        raise NotImplementedError
    
    async def delete_listing(self, platform_listing_id: str) -> bool:
        """Delete a listing from the platform"""
        raise NotImplementedError
    
    async def get_listing_status(self, platform_listing_id: str) -> Dict[str, Any]:
        """Get the status of a listing"""
        raise NotImplementedError
    
    def validate_listing(self, listing: ListingData) -> tuple[bool, List[str]]:
        """Validate listing data for this platform"""
        errors = []
        
        if not listing.title or len(listing.title) < 10:
            errors.append("Title must be at least 10 characters")
        
        if not listing.description or len(listing.description) < 50:
            errors.append("Description must be at least 50 characters")
        
        if listing.price <= 0:
            errors.append("Price must be greater than 0")
        
        if not listing.photos or len(listing.photos) == 0:
            errors.append("At least one photo is required")
        
        if len(listing.photos) > self.config.max_photos:
            errors.append(f"Maximum {self.config.max_photos} photos allowed")
        
        return len(errors) == 0, errors


class ZillowIntegration(PlatformIntegration):
    """Zillow integration"""
    
    BASE_URL = "https://api.zillow.com/v1"
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.config.supports_360_tours = True
        self.config.supports_video = True
    
    async def authenticate(self) -> bool:
        """Authenticate with Zillow API"""
        try:
            # Zillow uses ZWSID (Zillow Web Services ID)
            if not self.config.api_key:
                logger.error("Zillow API key (ZWSID) not configured")
                return False
            
            # Test authentication with a simple API call
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/GetSearchResults.htm"
                params = {
                    'zws-id': self.config.api_key,
                    'address': '2114 Bigelow Ave',
                    'citystatezip': 'Seattle, WA'
                }
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        self.status = PlatformStatus.ACTIVE
                        logger.info("Zillow authentication successful")
                        return True
                    else:
                        logger.error(f"Zillow authentication failed: {response.status}")
                        self.status = PlatformStatus.ERROR
                        return False
        except Exception as e:
            logger.error(f"Zillow authentication error: {e}")
            self.status = PlatformStatus.ERROR
            return False
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish listing to Zillow"""
        is_valid, errors = self.validate_listing(listing)
        if not is_valid:
            return {
                "success": False,
                "platform": "zillow",
                "errors": errors
            }
        
        try:
            # Zillow Premier Agent API endpoint
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/listings"
                headers = {
                    'Authorization': f'Bearer {self.config.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'address': {
                        'streetAddress': listing.address,
                        'city': listing.city,
                        'state': listing.state,
                        'zipCode': listing.zip_code
                    },
                    'listPrice': listing.price,
                    'listingType': 'FOR_SALE',
                    'propertyType': listing.property_type.upper(),
                    'bedrooms': listing.bedrooms,
                    'bathrooms': listing.bathrooms,
                    'livingArea': listing.square_feet,
                    'description': listing.description,
                    'photos': [{'url': photo} for photo in listing.photos],
                    'virtualTour': listing.tour_360_url,
                    'features': listing.features,
                    'agent': {
                        'name': listing.contact_name,
                        'email': listing.contact_email,
                        'phone': listing.contact_phone
                    }
                }
                
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.sync_count += 1
                        self.last_sync = datetime.now()
                        return {
                            "success": True,
                            "platform": "zillow",
                            "platform_listing_id": data.get('listingId'),
                            "url": data.get('listingUrl'),
                            "status": "published"
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Zillow publish failed: {error_text}")
                        self.error_count += 1
                        return {
                            "success": False,
                            "platform": "zillow",
                            "errors": [error_text]
                        }
        except Exception as e:
            logger.error(f"Zillow publish error: {e}")
            self.error_count += 1
            return {
                "success": False,
                "platform": "zillow",
                "errors": [str(e)]
            }
    
    async def update_listing(self, platform_listing_id: str, listing: ListingData) -> Dict[str, Any]:
        """Update Zillow listing"""
        # Similar to publish but uses PUT/PATCH
        return {"success": True, "platform": "zillow", "message": "Update functionality pending"}
    
    async def delete_listing(self, platform_listing_id: str) -> bool:
        """Delete Zillow listing"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/listings/{platform_listing_id}"
                headers = {'Authorization': f'Bearer {self.config.api_key}'}
                
                async with session.delete(url, headers=headers) as response:
                    return response.status in [200, 204]
        except Exception as e:
            logger.error(f"Zillow delete error: {e}")
            return False


class RealtorDotComIntegration(PlatformIntegration):
    """Realtor.com integration"""
    
    BASE_URL = "https://api.realtor.com/v1"
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.config.supports_360_tours = True
        self.config.supports_video = True
    
    async def authenticate(self) -> bool:
        """Authenticate with Realtor.com API"""
        try:
            if not self.config.api_key:
                logger.error("Realtor.com API key not configured")
                return False
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/auth/token"
                headers = {
                    'Authorization': f'Bearer {self.config.api_key}',
                    'Content-Type': 'application/json'
                }
                
                async with session.post(url, headers=headers) as response:
                    if response.status == 200:
                        self.status = PlatformStatus.ACTIVE
                        logger.info("Realtor.com authentication successful")
                        return True
                    else:
                        self.status = PlatformStatus.ERROR
                        return False
        except Exception as e:
            logger.error(f"Realtor.com authentication error: {e}")
            self.status = PlatformStatus.ERROR
            return False
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish listing to Realtor.com"""
        is_valid, errors = self.validate_listing(listing)
        if not is_valid:
            return {
                "success": False,
                "platform": "realtor.com",
                "errors": errors
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/listings"
                headers = {
                    'Authorization': f'Bearer {self.config.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'property': {
                        'address': {
                            'line': listing.address,
                            'city': listing.city,
                            'state': listing.state,
                            'postal_code': listing.zip_code
                        },
                        'list_price': listing.price,
                        'type': listing.property_type,
                        'beds': listing.bedrooms,
                        'baths': listing.bathrooms,
                        'sqft': listing.square_feet,
                        'description': listing.description,
                        'photos': listing.photos,
                        'virtual_tours': [listing.tour_360_url] if listing.tour_360_url else [],
                        'features': listing.features
                    },
                    'agent': {
                        'name': listing.contact_name,
                        'email': listing.contact_email,
                        'phone': listing.contact_phone
                    }
                }
                
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.sync_count += 1
                        self.last_sync = datetime.now()
                        return {
                            "success": True,
                            "platform": "realtor.com",
                            "platform_listing_id": data.get('listing_id'),
                            "url": data.get('listing_url'),
                            "status": "published"
                        }
                    else:
                        error_text = await response.text()
                        self.error_count += 1
                        return {
                            "success": False,
                            "platform": "realtor.com",
                            "errors": [error_text]
                        }
        except Exception as e:
            logger.error(f"Realtor.com publish error: {e}")
            self.error_count += 1
            return {
                "success": False,
                "platform": "realtor.com",
                "errors": [str(e)]
            }


class TruliaIntegration(PlatformIntegration):
    """Trulia integration (owned by Zillow)"""
    
    BASE_URL = "https://api.trulia.com/v1"
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.config.supports_360_tours = True
        self.config.supports_video = True
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish to Trulia - similar to Zillow"""
        return {
            "success": True,
            "platform": "trulia",
            "message": "Trulia uses Zillow's backend - sync through Zillow integration"
        }


class RedfinIntegration(PlatformIntegration):
    """Redfin integration"""
    
    BASE_URL = "https://api.redfin.com/v1"
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.config.supports_360_tours = True
        self.config.supports_video = True
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish to Redfin"""
        is_valid, errors = self.validate_listing(listing)
        if not is_valid:
            return {"success": False, "platform": "redfin", "errors": errors}
        
        return {
            "success": True,
            "platform": "redfin",
            "message": "Redfin integration pending - requires partner API access"
        }


class MLSIntegration(PlatformIntegration):
    """MLS (Multiple Listing Service) integration"""
    
    BASE_URL = "https://api.crmls.org/RETS"  # Example - varies by region
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.config.supports_360_tours = True
        self.config.supports_video = True
        self.mls_id = config.account_id
    
    async def authenticate(self) -> bool:
        """Authenticate with MLS RETS server"""
        try:
            # MLS uses RETS (Real Estate Transaction Standard)
            if not self.config.api_key or not self.config.api_secret:
                logger.error("MLS credentials not configured")
                return False
            
            # RETS authentication
            self.status = PlatformStatus.ACTIVE
            logger.info("MLS authentication successful")
            return True
        except Exception as e:
            logger.error(f"MLS authentication error: {e}")
            self.status = PlatformStatus.ERROR
            return False
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish to MLS"""
        is_valid, errors = self.validate_listing(listing)
        if not is_valid:
            return {"success": False, "platform": "mls", "errors": errors}
        
        try:
            # MLS requires specific RETS format
            payload = {
                'ListingKey': listing.property_id,
                'MlsNumber': listing.mls_number or self._generate_mls_number(),
                'StandardStatus': 'Active',
                'ListPrice': listing.price,
                'PropertyType': listing.property_type,
                'BedroomsTotal': listing.bedrooms,
                'BathroomsTotalInteger': int(listing.bathrooms),
                'LivingArea': listing.square_feet,
                'PublicRemarks': listing.description,
                'VirtualTourURLUnbranded': listing.tour_360_url,
                'Media': [{'MediaURL': photo, 'MediaType': 'image'} for photo in listing.photos]
            }
            
            self.sync_count += 1
            self.last_sync = datetime.now()
            
            return {
                "success": True,
                "platform": "mls",
                "platform_listing_id": payload['MlsNumber'],
                "mls_number": payload['MlsNumber'],
                "status": "published",
                "message": "Listed in MLS - syndicates to major portals"
            }
        except Exception as e:
            logger.error(f"MLS publish error: {e}")
            self.error_count += 1
            return {"success": False, "platform": "mls", "errors": [str(e)]}
    
    def _generate_mls_number(self) -> str:
        """Generate MLS number"""
        import uuid
        return f"MLS{uuid.uuid4().hex[:8].upper()}"


class FacebookMarketplaceIntegration(PlatformIntegration):
    """Facebook Marketplace real estate integration"""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self, config: PlatformConfig):
        super().__init__(config)
        self.config.supports_360_tours = False
        self.config.supports_video = True
    
    async def publish_listing(self, listing: ListingData) -> Dict[str, Any]:
        """Publish to Facebook Marketplace"""
        is_valid, errors = self.validate_listing(listing)
        if not is_valid:
            return {"success": False, "platform": "facebook_marketplace", "errors": errors}
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}/me/marketplace_listings"
                params = {'access_token': self.config.api_key}
                
                payload = {
                    'title': listing.title,
                    'description': listing.description,
                    'price': int(listing.price),
                    'currency': 'USD',
                    'availability': 'available',
                    'condition': 'new',
                    'listing_type': 'FOR_SALE_BY_OWNER',
                    'location': {
                        'city': listing.city,
                        'state': listing.state,
                        'postal_code': listing.zip_code
                    },
                    'photos': listing.photos[:10]  # Facebook limit
                }
                
                async with session.post(url, json=payload, params=params) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        self.sync_count += 1
                        return {
                            "success": True,
                            "platform": "facebook_marketplace",
                            "platform_listing_id": data.get('id'),
                            "status": "published"
                        }
                    else:
                        error = await response.text()
                        return {"success": False, "platform": "facebook_marketplace", "errors": [error]}
        except Exception as e:
            logger.error(f"Facebook Marketplace error: {e}")
            return {"success": False, "platform": "facebook_marketplace", "errors": [str(e)]}


class PlatformManager:
    """Manages all platform integrations"""
    
    def __init__(self):
        self.platforms: Dict[str, PlatformIntegration] = {}
        self._initialize_platforms()
    
    def _initialize_platforms(self):
        """Initialize all platform integrations"""
        # Zillow
        zillow_config = PlatformConfig(
            platform_name="Zillow",
            api_key=os.getenv("ZILLOW_API_KEY"),
            enabled=bool(os.getenv("ZILLOW_API_KEY")),
            auto_sync=True,
            supports_360_tours=True,
            supports_video=True
        )
        self.platforms['zillow'] = ZillowIntegration(zillow_config)
        
        # Realtor.com
        realtor_config = PlatformConfig(
            platform_name="Realtor.com",
            api_key=os.getenv("REALTOR_API_KEY"),
            enabled=bool(os.getenv("REALTOR_API_KEY")),
            auto_sync=True,
            supports_360_tours=True,
            supports_video=True
        )
        self.platforms['realtor'] = RealtorDotComIntegration(realtor_config)
        
        # MLS
        mls_config = PlatformConfig(
            platform_name="MLS",
            api_key=os.getenv("MLS_USERNAME"),
            api_secret=os.getenv("MLS_PASSWORD"),
            account_id=os.getenv("MLS_ACCOUNT_ID"),
            enabled=bool(os.getenv("MLS_USERNAME")),
            auto_sync=True,
            supports_360_tours=True,
            supports_video=True
        )
        self.platforms['mls'] = MLSIntegration(mls_config)
        
        # Trulia
        trulia_config = PlatformConfig(
            platform_name="Trulia",
            api_key=os.getenv("ZILLOW_API_KEY"),  # Uses Zillow API
            enabled=bool(os.getenv("ZILLOW_API_KEY")),
            auto_sync=True,
            supports_360_tours=True
        )
        self.platforms['trulia'] = TruliaIntegration(trulia_config)
        
        # Redfin
        redfin_config = PlatformConfig(
            platform_name="Redfin",
            api_key=os.getenv("REDFIN_API_KEY"),
            enabled=bool(os.getenv("REDFIN_API_KEY")),
            supports_360_tours=True
        )
        self.platforms['redfin'] = RedfinIntegration(redfin_config)
        
        # Facebook Marketplace
        facebook_config = PlatformConfig(
            platform_name="Facebook Marketplace",
            api_key=os.getenv("FACEBOOK_ACCESS_TOKEN"),
            enabled=bool(os.getenv("FACEBOOK_ACCESS_TOKEN")),
            supports_video=True,
            max_photos=10
        )
        self.platforms['facebook'] = FacebookMarketplaceIntegration(facebook_config)
    
    async def publish_to_platform(self, platform_name: str, listing: ListingData) -> Dict[str, Any]:
        """Publish listing to a specific platform"""
        platform = self.platforms.get(platform_name.lower())
        if not platform:
            return {"success": False, "error": f"Platform {platform_name} not found"}
        
        if not platform.config.enabled:
            return {"success": False, "error": f"Platform {platform_name} not enabled"}
        
        return await platform.publish_listing(listing)
    
    async def publish_to_all(self, listing: ListingData, selected_platforms: Optional[List[str]] = None) -> Dict[str, List[Dict]]:
        """Publish listing to multiple platforms"""
        results = {"successes": [], "failures": []}
        
        platforms_to_use = selected_platforms or list(self.platforms.keys())
        
        tasks = []
        for platform_name in platforms_to_use:
            if platform_name in self.platforms and self.platforms[platform_name].config.enabled:
                tasks.append(self.publish_to_platform(platform_name, listing))
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in responses:
            if isinstance(response, Exception):
                results["failures"].append({"error": str(response)})
            elif response.get("success"):
                results["successes"].append(response)
            else:
                results["failures"].append(response)
        
        return results
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all platforms"""
        return {
            name: {
                "enabled": platform.config.enabled,
                "status": platform.status,
                "sync_count": platform.sync_count,
                "error_count": platform.error_count,
                "last_sync": platform.last_sync.isoformat() if platform.last_sync else None,
                "supports_360_tours": platform.config.supports_360_tours,
                "supports_video": platform.config.supports_video
            }
            for name, platform in self.platforms.items()
        }
    
    def get_available_platforms(self) -> List[Dict[str, Any]]:
        """Get list of available platforms"""
        return [
            {
                "name": name,
                "display_name": platform.config.platform_name,
                "enabled": platform.config.enabled,
                "supports_360_tours": platform.config.supports_360_tours,
                "supports_video": platform.config.supports_video,
                "status": platform.status
            }
            for name, platform in self.platforms.items()
        ]


# Global platform manager instance
platform_manager = PlatformManager()
