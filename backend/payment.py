from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import paypalrestsdk
import os
from typing import Optional, List

router = APIRouter()

# Configure PayPal
paypalrestsdk.configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

# Your exact pricing tiers
PRICING_TIERS = {
    "starter": {
        "name": "Starter",
        "price": "29.00",
        "currency": "USD",
        "interval": "month",
        "features": [
            "5 Property Listings",
            "Basic Viral Content Generation",
            "Instagram & Facebook Content",
            "Email Support",
            "Basic Analytics"
        ]
    },
    "professional": {
        "name": "Professional",
        "price": "79.00",
        "currency": "USD",
        "interval": "month",
        "features": [
            "Unlimited Property Listings",
            "Advanced AI Content Generation",
            "All Social Media Platforms",
            "Virtual Tour Creation",
            "Advanced Analytics",
            "Priority Support",
            "Custom Branding"
        ]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": "149.00",
        "currency": "USD",
        "interval": "month",
        "features": [
            "Everything in Professional",
            "Multi-Agent Team Access",
            "White-label Solution",
            "API Access",
            "Custom Integrations",
            "Dedicated Account Manager",
            "24/7 Phone Support"
        ]
    }
}

class PaymentCreate(BaseModel):
    tier: str
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None

@router.get("/pricing-tiers")
async def get_pricing_tiers():
    """Get all available pricing tiers"""
    return {"tiers": PRICING_TIERS}

@router.post("/create-payment")
async def create_payment(payment_data: PaymentCreate):
    """Create a PayPal payment"""
    
    if payment_data.tier not in PRICING_TIERS:
        raise HTTPException(status_code=400, detail="Invalid pricing tier")
    
    tier = PRICING_TIERS[payment_data.tier]
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    return_url = payment_data.return_url or f"{frontend_url}/payment/success"
    cancel_url = payment_data.cancel_url or f"{frontend_url}/payment/cancel"
    
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": return_url,
            "cancel_url": cancel_url
        },
        "transactions": [{
            "amount": {
                "total": tier["price"],
                "currency": tier["currency"]
            },
            "description": f"{tier['name']} Plan - Monthly Subscription",
            "custom": payment_data.tier
        }]
    })
    
    if payment.create():
        for link in payment.links:
            if link.rel == "approval_url":
                return {
                    "status": "created",
                    "payment_id": payment.id,
                    "approval_url": link.href,
                    "tier": payment_data.tier
                }
        raise HTTPException(status_code=500, detail="No approval URL found")
    else:
        raise HTTPException(status_code=500, detail=str(payment.error))

@router.get("/execute-payment")
async def execute_payment(paymentId: str, PayerID: str):
    """Execute payment after approval"""
    
    try:
        payment = paypalrestsdk.Payment.find(paymentId)
        
        if payment.execute({"payer_id": PayerID}):
            tier = payment.transactions[0].custom
            
            return {
                "status": "success",
                "payment_id": payment.id,
                "tier": tier,
                "payer_email": payment.payer.payer_info.email,
                "amount": payment.transactions[0].amount.total
            }
        else:
            raise HTTPException(status_code=400, detail=str(payment.error))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
