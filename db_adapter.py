"""
Database Adapter for ListingSpark AI
Handles database initialization and access
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# Global database instances
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None


async def init_database():
    """Initialize MongoDB connection"""
    global _mongo_client, _mongo_db
    
    try:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        db_name = os.getenv("DB_NAME", "listingspark")
        
        _mongo_client = AsyncIOMotorClient(mongodb_url)
        _mongo_db = _mongo_client[db_name]
        
        # Test connection
        await _mongo_db.command('ping')
        logger.info(f"✅ Connected to MongoDB: {db_name}")
        
        # Create indexes
        await _mongo_db.users.create_index("email", unique=True)
        await _mongo_db.users.create_index("id", unique=True)
        await _mongo_db.listings.create_index("user_id")
        await _mongo_db.listings.create_index([("user_id", 1), ("status", 1)])
        await _mongo_db.mls_accounts.create_index("user_id")
        
        return _mongo_db
        
    except Exception as e:
        logger.warning(f"⚠️ MongoDB not available: {e}")
        logger.info("Running without MongoDB features")
        return None


async def get_database() -> Optional[AsyncIOMotorDatabase]:
    """Get the database instance"""
    return _mongo_db


async def close_database():
    """Close database connection"""
    global _mongo_client
    
    if _mongo_client:
        _mongo_client.close()
        logger.info("❌ Closed MongoDB connection")
