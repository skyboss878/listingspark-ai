"""
Platform Integrations - Enterprise Production Edition
Real estate listing distribution to multiple platforms
NO MOCK DATA - Production-ready with real API integrations
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

import httpx
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Settings(BaseSettings):
    """Platform integration settings"""
    # Zillow
    ZILLOW_API_KEY: Optional[str] = None
    ZILLOW_API_URL: str = "https://api.bridgedataoutput.com/api/v2"
    ZILLOW_ENABLED: bool = False
    
    # Realtor.com
    REALTOR_API_KEY: Optional[str] = None
    REALTOR_API_URL: str = "https://api.realtor.com/v1"
    REALTOR_ENABLED: bool = False
    
    # Facebook
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    FACEBOOK_PAGE_ID: Optional[str] = None
    FACEBOOK_ENABLED: bool = False
    
    # Trulia (uses Zillow API)
    TRULIA_ENABLED: bool = False
    
    # Request settings
    HTTP_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow extra fields

settings = Settings()

# ============================================================================
# DATA MODELS
# ============================================================================

class PlatformType(str, Enum):
    ZILLOW = "zillow"
    REALTOR_COM = "realtor_com"
    TRULIA = "trulia"
    FACEBOOK = "facebook"
    MLS = "mls"

class ListingSyncStatus(str, Enum):
    QUEUED = "queued"
    PUBLISHING = "publishing"
    SYNCED = "synced"
    FAILED = "failed"
    UPDATE_QUEUED = "update_queued"
    DELETION_QUEUED = "deletion_queued"

class ListingData(BaseModel):
    """Standardized listing data"""
    id: str
    address: str
    city: str
    state: str
    zip_code: str
    price: int
    bedrooms: int
    bathrooms: float
    square_feet: int
    property_type: str = "single_family"
    description: str
    features: List[str] = Field(default_factory=list)
    photos: List[str] = Field(default_factory=list)
    tour_360_url: Optional[str] = None
    video_url: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: str
    listing_agent: Optional[str] = None
    year_built: Optional[int] = None
    lot_size: Optional[int] = None
    
    @validator('price', 'square_feet')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError('Must be positive')
        return v

class PlatformConfig(BaseModel):
    """Platform-specific configuration"""
    platform: PlatformType
    enabled: bool
    api_key: Optional[str] = None
    api_url: str
    rate_limit_per_hour: int = 1000
    supports_360_tours: bool = False
    supports_video: bool = False
    max_photos: int = 50

class SyncResult(BaseModel):
    """Result of syncing to a platform"""
    platform: PlatformType
    status: ListingSyncStatus
    platform_listing_id: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None
    synced_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# BASE INTEGRATION CLASS
# ============================================================================

class PlatformIntegration(ABC):
    """Base class for platform integrations"""
    
    def __init__(self, config: PlatformConfig, client: httpx.AsyncClient):
        self.config = config
        self.client = client
        self.logger = logging.getLogger(f"{__name__}.{config.platform.value}")
    
    @abstractmethod
    async def publish_listing(self, listing: ListingData) -> SyncResult:
        """Publish listing to platform"""
        pass
    
    @abstractmethod
    async def update_listing(self, listing: ListingData, platform_id: str) -> SyncResult:
        """Update existing listing"""
        pass
    
    @abstractmethod
    async def delete_listing(self, platform_id: str) -> bool:
        """Delete listing from platform"""
        pass
    
    def _prepare_photos(self, photos: List[str], max_count: int = None) -> List[str]:
        """Prepare photos for platform"""
        max_count = max_count or self.config.max_photos
        return photos[:max_count]
    
    def _format_features(self, features: List[str]) -> str:
        """Format features as text"""
        return ", ".join(features) if features else ""

# ============================================================================
# ZILLOW INTEGRATION
# ============================================================================

class ZillowIntegration(PlatformIntegration):
    """Zillow & Trulia integration via Bridge Interactive"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException))
    )
    async def publish_listing(self, listing: ListingData) -> SyncResult:
        """Publish to Zillow"""
        try:
            if not self.config.api_key:
                return SyncResult(
                    platform=self.config.platform,
                    status=ListingSyncStatus.FAILED,
                    error_message="API key not configured"
                )
            
            # Prepare payload for Bridge Interactive API
            payload = {
                "StandardStatus": "Active",
                "MlsStatus": "Active",
                "ListPrice": listing.price,
                "UnparsedAddress": listing.address,
                "City": listing.city,
                "StateOrProvince": listing.state,
                "PostalCode": listing.zip_code,
                "BedroomsTotal": listing.bedrooms,
                "BathroomsTotalInteger": int(listing.bathrooms),
                "LivingArea": listing.square_feet,
                "PropertyType": self._map_property_type(listing.property_type),
                "PublicRemarks": listing.description,
                "ListAgentFullName": listing.listing_agent or listing.contact_name,
                "ListAgentEmail": listing.contact_email,
                "ListAgentDirectPhone": listing.contact_phone,
                "YearBuilt": listing.year_built,
                "LotSizeSquareFeet": listing.lot_size,
                "Media": [{"MediaURL": url, "MediaCategory": "Photo"} for url in self._prepare_photos(listing.photos)]
            }
            
            # Add 360 tour if supported
            if self.config.supports_360_tours and listing.tour_360_url:
                payload["VirtualTourURLUnbranded"] = listing.tour_360_url
            
            # Add video if supported
            if self.config.supports_video and listing.video_url:
                payload["Media"].append({"MediaURL": listing.video_url, "MediaCategory": "Video"})
            
            response = await self.client.post(
                f"{self.config.api_url}/listings",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            platform_id = data.get("ListingKey") or data.get("id")
            
            self.logger.info(f"✅ Published to {self.config.platform.value}: {platform_id}")
            
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.SYNCED,
                platform_listing_id=platform_id,
                platform_url=f"https://www.zillow.com/homedetails/{platform_id}"
            )
            
        except httpx.HTTPError as e:
            self.logger.error(f"❌ HTTP error publishing to {self.config.platform.value}: {e}")
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=f"HTTP error: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"❌ Error publishing to {self.config.platform.value}: {e}")
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def update_listing(self, listing: ListingData, platform_id: str) -> SyncResult:
        """Update listing on Zillow"""
        try:
            payload = {
                "ListPrice": listing.price,
                "PublicRemarks": listing.description,
                "StandardStatus": "Active"
            }
            
            response = await self.client.put(
                f"{self.config.api_url}/listings/{platform_id}",
                json=payload,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.SYNCED,
                platform_listing_id=platform_id
            )
            
        except Exception as e:
            self.logger.error(f"Error updating {self.config.platform.value}: {e}")
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def delete_listing(self, platform_id: str) -> bool:
        """Delete listing from Zillow"""
        try:
            response = await self.client.delete(
                f"{self.config.api_url}/listings/{platform_id}",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            self.logger.info(f"✅ Deleted from {self.config.platform.value}: {platform_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting from {self.config.platform.value}: {e}")
            return False
    
    def _map_property_type(self, prop_type: str) -> str:
        """Map property type to Zillow format"""
        mapping = {
            "single_family": "Residential",
            "condo": "Residential",
            "townhouse": "Residential",
            "multi_family": "Residential Income",
            "land": "Land"
        }
        return mapping.get(prop_type.lower(), "Residential")

# ============================================================================
# REALTOR.COM INTEGRATION
# ============================================================================

class RealtorDotComIntegration(PlatformIntegration):
    """Realtor.com integration"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def publish_listing(self, listing: ListingData) -> SyncResult:
        """Publish to Realtor.com"""
        try:
            if not self.config.api_key:
                return SyncResult(
                    platform=self.config.platform,
                    status=ListingSyncStatus.FAILED,
                    error_message="API key not configured"
                )
            
            payload = {
                "property": {
                    "address": {
                        "line": listing.address,
                        "city": listing.city,
                        "state": listing.state,
                        "postal_code": listing.zip_code
                    },
                    "price": listing.price,
                    "beds": listing.bedrooms,
                    "baths": listing.bathrooms,
                    "sqft": listing.square_feet,
                    "type": listing.property_type,
                    "description": listing.description,
                    "features": listing.features,
                    "year_built": listing.year_built,
                    "lot_sqft": listing.lot_size
                },
                "photos": [{"url": url} for url in self._prepare_photos(listing.photos)],
                "agent": {
                    "name": listing.listing_agent or listing.contact_name,
                    "email": listing.contact_email,
                    "phone": listing.contact_phone
                }
            }
            
            if listing.tour_360_url:
                payload["virtual_tour_url"] = listing.tour_360_url
            
            response = await self.client.post(
                f"{self.config.api_url}/listings",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            platform_id = data.get("listing_id")
            
            self.logger.info(f"✅ Published to Realtor.com: {platform_id}")
            
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.SYNCED,
                platform_listing_id=platform_id,
                platform_url=f"https://www.realtor.com/realestateandhomes-detail/{platform_id}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error publishing to Realtor.com: {e}")
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def update_listing(self, listing: ListingData, platform_id: str) -> SyncResult:
        """Update on Realtor.com"""
        try:
            payload = {
                "property": {
                    "price": listing.price,
                    "description": listing.description
                }
            }
            
            response = await self.client.patch(
                f"{self.config.api_url}/listings/{platform_id}",
                json=payload,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.SYNCED,
                platform_listing_id=platform_id
            )
        except Exception as e:
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def delete_listing(self, platform_id: str) -> bool:
        """Delete from Realtor.com"""
        try:
            response = await self.client.delete(
                f"{self.config.api_url}/listings/{platform_id}",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting from Realtor.com: {e}")
            return False

# ============================================================================
# FACEBOOK MARKETPLACE INTEGRATION
# ============================================================================

class FacebookMarketplaceIntegration(PlatformIntegration):
    """Facebook Marketplace integration"""
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def publish_listing(self, listing: ListingData) -> SyncResult:
        """Publish to Facebook Marketplace"""
        try:
            if not self.config.api_key or not settings.FACEBOOK_PAGE_ID:
                return SyncResult(
                    platform=self.config.platform,
                    status=ListingSyncStatus.FAILED,
                    error_message="Facebook credentials not configured"
                )
            
            payload = {
                "message": f"{listing.description}\\n\\nPrice: ${listing.price:,}\\nBedrooms: {listing.bedrooms}\\nBathrooms: {listing.bathrooms}\\n{self._format_features(listing.features)}",
                "link": listing.tour_360_url or "",
                "published": True
            }
            
            # Facebook Graph API
            response = await self.client.post(
                f"https://graph.facebook.com/v18.0/{settings.FACEBOOK_PAGE_ID}/feed",
                data=payload,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            post_id = data.get("id")
            
            self.logger.info(f"✅ Published to Facebook: {post_id}")
            
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.SYNCED,
                platform_listing_id=post_id,
                platform_url=f"https://www.facebook.com/{post_id}"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error publishing to Facebook: {e}")
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def update_listing(self, listing: ListingData, platform_id: str) -> SyncResult:
        """Update Facebook post"""
        try:
            payload = {
                "message": f"UPDATED: {listing.description}\\n\\nPrice: ${listing.price:,}"
            }
            
            response = await self.client.post(
                f"https://graph.facebook.com/v18.0/{platform_id}",
                data=payload,
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.SYNCED,
                platform_listing_id=platform_id
            )
        except Exception as e:
            return SyncResult(
                platform=self.config.platform,
                status=ListingSyncStatus.FAILED,
                error_message=str(e)
            )
    
    async def delete_listing(self, platform_id: str) -> bool:
        """Delete Facebook post"""
        try:
            response = await self.client.delete(
                f"https://graph.facebook.com/v18.0/{platform_id}",
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                timeout=settings.HTTP_TIMEOUT
            )
            response.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Error deleting from Facebook: {e}")
            return False

# ============================================================================
# PLATFORM MANAGER
# ============================================================================

class PlatformManager:
    """Manages all platform integrations"""
    
    def __init__(self):
        self.integrations: Dict[PlatformType, PlatformIntegration] = {}
        self.client: Optional[httpx.AsyncClient] = None
    
    async def initialize(self):
        """Initialize HTTP client and platforms"""
        self.client = httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT)
        await self._register_platforms()
        logger.info(f"✅ Platform Manager initialized with {len(self.integrations)} platforms")
    
    async def _register_platforms(self):
        """Register all available platforms"""
        configs = self._load_platform_configs()
        
        for config in configs:
            if not config.enabled:
                continue
            
            if config.platform == PlatformType.ZILLOW:
                self.integrations[config.platform] = ZillowIntegration(config, self.client)
            elif config.platform == PlatformType.REALTOR_COM:
                self.integrations[config.platform] = RealtorDotComIntegration(config, self.client)
            elif config.platform == PlatformType.FACEBOOK:
                self.integrations[config.platform] = FacebookMarketplaceIntegration(config, self.client)
            elif config.platform == PlatformType.TRULIA:
                # Trulia uses same integration as Zillow
                trulia_config = PlatformConfig(
                    platform=PlatformType.TRULIA,
                    enabled=config.enabled,
                    api_key=config.api_key,
                    api_url=config.api_url,
                    supports_360_tours=True,
                    supports_video=True
                )
                self.integrations[PlatformType.TRULIA] = ZillowIntegration(trulia_config, self.client)
    
    def _load_platform_configs(self) -> List[PlatformConfig]:
        """Load platform configurations from environment"""
        configs = []
        
        # Zillow
        if settings.ZILLOW_ENABLED and settings.ZILLOW_API_KEY:
            configs.append(PlatformConfig(
                platform=PlatformType.ZILLOW,
                enabled=True,
                api_key=settings.ZILLOW_API_KEY,
                api_url=settings.ZILLOW_API_URL,
                supports_360_tours=True,
                supports_video=True,
                max_photos=50
            ))
        
        # Realtor.com
        if settings.REALTOR_ENABLED and settings.REALTOR_API_KEY:
            configs.append(PlatformConfig(
                platform=PlatformType.REALTOR_COM,
                enabled=True,
                api_key=settings.REALTOR_API_KEY,
                api_url=settings.REALTOR_API_URL,
                supports_360_tours=True,
                supports_video=False,
                max_photos=40
            ))
        
        # Facebook
        if settings.FACEBOOK_ENABLED and settings.FACEBOOK_ACCESS_TOKEN:
            configs.append(PlatformConfig(
                platform=PlatformType.FACEBOOK,
                enabled=True,
                api_key=settings.FACEBOOK_ACCESS_TOKEN,
                api_url="https://graph.facebook.com/v18.0",
                supports_360_tours=True,
                supports_video=True,
                max_photos=10
            ))
        
        # Trulia (uses Zillow)
        if settings.TRULIA_ENABLED and settings.ZILLOW_API_KEY:
            configs.append(PlatformConfig(
                platform=PlatformType.TRULIA,
                enabled=True,
                api_key=settings.ZILLOW_API_KEY,
                api_url=settings.ZILLOW_API_URL,
                supports_360_tours=True,
                supports_video=True
            ))
        
        return configs
    
    async def publish_to_platforms(
        self,
        listing: ListingData,
        platforms: Optional[List[PlatformType]] = None
    ) -> List[SyncResult]:
        """Publish listing to specified platforms or all enabled"""
        if not platforms:
            platforms = list(self.integrations.keys())
        
        results = []
        for platform_type in platforms:
            integration = self.integrations.get(platform_type)
            if not integration:
                logger.warning(f"Platform {platform_type} not available")
                continue
            
            result = await integration.publish_listing(listing)
            results.append(result)
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()
            logger.info("Platform Manager closed")

# ============================================================================
# SINGLETON
# ============================================================================

_platform_manager: Optional[PlatformManager] = None

async def get_platform_manager() -> PlatformManager:
    """Get or create global platform manager"""
    global _platform_manager
    if _platform_manager is None:
        _platform_manager = PlatformManager()
        await _platform_manager.initialize()
    return _platform_manager
