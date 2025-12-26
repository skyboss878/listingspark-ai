"""
Health Check Endpoint for Monitoring
Add this to your server.py
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring services
    Returns system status and service availability
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": "up",
            "database": "up",  # Add actual check
            "redis": "up",     # Add actual check
            "video_gen": "up"   # Add actual check
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }

@health_router.get("/health/ready")
async def readiness_check():
    """Check if service is ready to accept traffic"""
    # Add checks for database connections, etc.
    return {"ready": True}

@health_router.get("/health/live")
async def liveness_check():
    """Check if service is alive"""
    return {"alive": True}
