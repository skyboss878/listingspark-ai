"""
Free Trial Management System
Handles 3-day free trials and subscription prompts
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum


class TrialStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SUBSCRIBED = "subscribed"


def init_trial_system(db_path: str = "listingspark.db"):
    """Initialize trial tracking table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add trial columns to users table if they don't exist
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'trial_started_at' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN trial_started_at TEXT")
    if 'trial_ends_at' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN trial_ends_at TEXT")
    if 'trial_status' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN trial_status TEXT DEFAULT 'active'")
    if 'subscription_status' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'none'")
    if 'subscription_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_id TEXT")
    if 'subscription_started_at' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_started_at TEXT")
    
    conn.commit()
    conn.close()
    print("✅ Trial system initialized")


def start_free_trial(user_id: str, db_path: str = "listingspark.db") -> Dict[str, Any]:
    """Start a 3-day free trial for a user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.utcnow()
    trial_end = now + timedelta(days=3)
    
    cursor.execute("""
        UPDATE users
        SET trial_started_at = ?,
            trial_ends_at = ?,
            trial_status = 'active'
        WHERE id = ?
    """, (now.isoformat(), trial_end.isoformat(), user_id))
    
    conn.commit()
    conn.close()
    
    return {
        "trial_started_at": now.isoformat(),
        "trial_ends_at": trial_end.isoformat(),
        "trial_status": "active",
        "days_remaining": 3
    }


def check_trial_status(user_id: str, db_path: str = "listingspark.db") -> Dict[str, Any]:
    """Check if user's trial is still valid"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT trial_started_at, trial_ends_at, trial_status, 
               subscription_status, subscription_id
        FROM users
        WHERE id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": "User not found"}
    
    # If already subscribed, no trial check needed
    if row['subscription_status'] == 'active':
        return {
            "status": "subscribed",
            "subscription_status": "active",
            "trial_status": "subscribed"
        }
    
    # If no trial started yet, return that
    if not row['trial_started_at']:
        return {
            "status": "no_trial",
            "trial_status": "not_started",
            "subscription_status": row['subscription_status'] or "none"
        }
    
    # Check if trial has expired
    now = datetime.utcnow()
    trial_end = datetime.fromisoformat(row['trial_ends_at'])
    
    if now > trial_end:
        # Trial expired - update status
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET trial_status = 'expired'
            WHERE id = ?
        """, (user_id,))
        conn.commit()
        conn.close()
        
        return {
            "status": "expired",
            "trial_status": "expired",
            "trial_ended_at": trial_end.isoformat(),
            "needs_subscription": True,
            "subscription_status": row['subscription_status'] or "none"
        }
    
    # Trial is still active
    days_remaining = (trial_end - now).days
    hours_remaining = (trial_end - now).seconds // 3600
    
    return {
        "status": "active",
        "trial_status": "active",
        "trial_started_at": row['trial_started_at'],
        "trial_ends_at": row['trial_ends_at'],
        "days_remaining": days_remaining,
        "hours_remaining": hours_remaining,
        "needs_subscription": False,
        "subscription_status": row['subscription_status'] or "none"
    }


def activate_subscription(
    user_id: str,
    subscription_id: str,
    db_path: str = "listingspark.db"
) -> Dict[str, Any]:
    """Activate paid subscription for user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.utcnow()
    
    cursor.execute("""
        UPDATE users
        SET subscription_status = 'active',
            subscription_id = ?,
            subscription_started_at = ?,
            trial_status = 'subscribed'
        WHERE id = ?
    """, (subscription_id, now.isoformat(), user_id))
    
    conn.commit()
    conn.close()
    
    return {
        "subscription_status": "active",
        "subscription_id": subscription_id,
        "subscription_started_at": now.isoformat()
    }


def cancel_subscription(user_id: str, db_path: str = "listingspark.db") -> bool:
    """Cancel user subscription"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE users
        SET subscription_status = 'cancelled'
        WHERE id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()
    
    return True


def get_trial_info(user_id: str, db_path: str = "listingspark.db") -> Dict[str, Any]:
    """Get detailed trial information for dashboard"""
    status = check_trial_status(user_id, db_path)
    
    if status.get("status") == "active":
        return {
            "has_access": True,
            "trial_active": True,
            "days_remaining": status["days_remaining"],
            "hours_remaining": status["hours_remaining"],
            "trial_ends_at": status["trial_ends_at"],
            "message": f"Free trial: {status['days_remaining']} days remaining",
            "show_upgrade_prompt": status["days_remaining"] <= 1
        }
    elif status.get("status") == "expired":
        return {
            "has_access": False,
            "trial_active": False,
            "trial_expired": True,
            "needs_subscription": True,
            "message": "Your free trial has ended. Subscribe to continue using Real360 AI",
            "show_upgrade_prompt": True
        }
    elif status.get("status") == "subscribed":
        return {
            "has_access": True,
            "trial_active": False,
            "subscribed": True,
            "message": "Active subscription",
            "show_upgrade_prompt": False
        }
    else:
        return {
            "has_access": True,
            "trial_active": False,
            "trial_not_started": True,
            "message": "Welcome! Start your 3-day free trial",
            "show_upgrade_prompt": False
        }
