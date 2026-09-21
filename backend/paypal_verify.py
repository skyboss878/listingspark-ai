"""
Server-side PayPal subscription verification.
Confirms a subscription_id is genuinely ACTIVE with PayPal before granting
access - never trusts a subscription_id supplied by the client alone.
"""

import os
import httpx

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")

PAYPAL_BASE_URL = "https://api-m.paypal.com" if PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"


async def get_paypal_access_token() -> str:
    if not PAYPAL_CLIENT_ID or not PAYPAL_CLIENT_SECRET:
        raise RuntimeError("PayPal credentials not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            timeout=15.0
        )
        response.raise_for_status()
        return response.json()["access_token"]


async def verify_paypal_subscription(subscription_id: str) -> dict:
    """
    Calls PayPal's API directly to confirm a subscription is real and ACTIVE.
    Returns {"valid": bool, "status": str, ...} - source of truth is PayPal,
    never the client-supplied subscription_id alone.
    """
    try:
        token = await get_paypal_access_token()
    except Exception as e:
        return {"valid": False, "status": "error", "error": f"Could not authenticate with PayPal: {str(e)}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{PAYPAL_BASE_URL}/v1/billing/subscriptions/{subscription_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=15.0
            )
        except Exception as e:
            return {"valid": False, "status": "error", "error": f"PayPal request failed: {str(e)}"}

        if response.status_code == 404:
            return {"valid": False, "status": "not_found", "error": "Subscription not found on PayPal"}

        if response.status_code != 200:
            return {"valid": False, "status": "error", "error": f"PayPal returned {response.status_code}: {response.text[:200]}"}

        data = response.json()
        status = data.get("status")
        is_active = status == "ACTIVE"

        return {
            "valid": is_active,
            "status": status,
            "plan_id": data.get("plan_id"),
            "subscriber_email": data.get("subscriber", {}).get("email_address"),
            "detail": data
        }
