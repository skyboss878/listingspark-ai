from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import aiosqlite
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
router = APIRouter()

DATABASE_PATH = Path(__file__).parent.parent / "listingspark.db"

class SubscriptionSave(BaseModel):
    subscription_id: str
    plan_type: str
    status: str = "active"

@router.post("/save")
async def save_subscription(subscription: SubscriptionSave, authorization: Optional[str] = Header(None)):
    """Save PayPal subscription details to user account"""
    try:
        # For now, we'll use email from the subscription or a basic auth
        # You can enhance this with proper JWT token parsing later
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Create subscription column if it doesn't exist
            try:
                await db.execute("""
                    ALTER TABLE users ADD COLUMN subscription_id TEXT
                """)
                await db.execute("""
                    ALTER TABLE users ADD COLUMN subscription_plan TEXT
                """)
                await db.execute("""
                    ALTER TABLE users ADD COLUMN subscription_status TEXT
                """)
                await db.commit()
            except:
                pass  # Column already exists
            
            # For demo, update the most recent user
            # In production, you'd parse the JWT token from authorization header
            await db.execute("""
                UPDATE users 
                SET subscription_id = ?,
                    subscription_plan = ?,
                    subscription_status = ?,
                    plan = ?
                WHERE id = (SELECT id FROM users ORDER BY created_at DESC LIMIT 1)
            """, (subscription.subscription_id, subscription.plan_type, subscription.status, subscription.plan_type))
            
            await db.commit()
        
        logger.info(f"Subscription saved: {subscription.subscription_id}")
        
        return {
            "success": True,
            "message": "Subscription activated successfully",
            "plan_type": subscription.plan_type
        }
        
    except Exception as e:
        logger.error(f"Error saving subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save subscription: {str(e)}")

@router.get("/status")
async def get_subscription_status(authorization: Optional[str] = Header(None)):
    """Get subscription status"""
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            async with db.execute("""
                SELECT subscription_id, subscription_plan, subscription_status 
                FROM users 
                ORDER BY created_at DESC LIMIT 1
            """) as cursor:
                row = await cursor.fetchone()
                
                if not row or not row[0]:
                    return {
                        "has_subscription": False,
                        "plan_type": None
                    }
                
                return {
                    "has_subscription": True,
                    "subscription_id": row[0],
                    "plan_type": row[1],
                    "status": row[2]
                }
        
    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")
