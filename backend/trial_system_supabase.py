"""
Supabase-backed replacement for trial_system.py.
Same function names/signatures so server.py's imports don't need to change.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from supabase_adapter import _get_client


def init_trial_system(db_path: str = None):
    print("Trial system initialized (Supabase)")


def start_free_trial(user_id: str, db_path: str = None) -> Dict[str, Any]:
    client = _get_client()
    now = datetime.utcnow()
    trial_end = now + timedelta(days=3)
    client.table("users").update({
        "trial_started_at": now.isoformat(),
        "trial_ends_at": trial_end.isoformat(),
        "trial_status": "active"
    }).eq("id", user_id).execute()
    return {
        "trial_started_at": now.isoformat(),
        "trial_ends_at": trial_end.isoformat(),
        "trial_status": "active",
        "days_remaining": 3
    }


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def check_trial_status(user_id: str, db_path: str = None) -> Dict[str, Any]:
    client = _get_client()
    result = client.table("users").select(
        "trial_started_at, trial_ends_at, trial_status, subscription_status, subscription_id"
    ).eq("id", user_id).execute()

    if not result.data:
        return {"error": "User not found"}
    row = result.data[0]

    if row.get("subscription_status") == "active":
        return {"status": "subscribed", "subscription_status": "active", "trial_status": "subscribed"}

    if not row.get("trial_started_at"):
        return {
            "status": "no_trial", "trial_status": "not_started",
            "subscription_status": row.get("subscription_status") or "none"
        }

    now = datetime.utcnow()
    trial_end = _parse_ts(row["trial_ends_at"])

    if now > trial_end:
        client.table("users").update({"trial_status": "expired"}).eq("id", user_id).execute()
        return {
            "status": "expired", "trial_status": "expired",
            "trial_ended_at": trial_end.isoformat(),
            "needs_subscription": True,
            "subscription_status": row.get("subscription_status") or "none"
        }

    days_remaining = (trial_end - now).days
    hours_remaining = (trial_end - now).seconds // 3600
    return {
        "status": "active", "trial_status": "active",
        "trial_started_at": row["trial_started_at"], "trial_ends_at": row["trial_ends_at"],
        "days_remaining": days_remaining, "hours_remaining": hours_remaining,
        "needs_subscription": False,
        "subscription_status": row.get("subscription_status") or "none"
    }


def activate_subscription(user_id: str, subscription_id: str, db_path: str = None) -> Dict[str, Any]:
    client = _get_client()
    now = datetime.utcnow()
    client.table("users").update({
        "subscription_status": "active",
        "subscription_id": subscription_id,
        "subscription_started_at": now.isoformat(),
        "trial_status": "subscribed"
    }).eq("id", user_id).execute()
    return {
        "subscription_status": "active",
        "subscription_id": subscription_id,
        "subscription_started_at": now.isoformat()
    }


def cancel_subscription(user_id: str, db_path: str = None) -> bool:
    client = _get_client()
    client.table("users").update({"subscription_status": "cancelled"}).eq("id", user_id).execute()
    return True


def get_trial_info(user_id: str, db_path: str = None) -> Dict[str, Any]:
    status = check_trial_status(user_id, db_path)

    if status.get("status") == "active":
        return {
            "has_access": True, "trial_active": True,
            "days_remaining": status["days_remaining"], "hours_remaining": status["hours_remaining"],
            "trial_ends_at": status["trial_ends_at"],
            "message": f"Free trial: {status['days_remaining']} days remaining",
            "show_upgrade_prompt": status["days_remaining"] <= 1
        }
    elif status.get("status") == "expired":
        return {
            "has_access": False, "trial_active": False, "trial_expired": True,
            "needs_subscription": True,
            "message": "Your free trial has ended. Subscribe to continue using Real360 AI",
            "show_upgrade_prompt": True
        }
    elif status.get("status") == "subscribed":
        return {
            "has_access": True, "trial_active": False, "subscribed": True,
            "message": "Active subscription", "show_upgrade_prompt": False
        }
    else:
        return {
            "has_access": True, "trial_active": False, "trial_not_started": True,
            "message": "Welcome! Start your 3-day free trial", "show_upgrade_prompt": False
        }
