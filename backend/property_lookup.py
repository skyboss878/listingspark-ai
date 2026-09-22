"""
RentCast property data lookup - given an address, returns year built,
bedrooms, bathrooms, square footage, lot size, and property type to
auto-fill the listing creation form.
"""

import os
import httpx

RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")
RENTCAST_BASE_URL = "https://api.rentcast.io/v1"

# Maps RentCast's propertyType strings to our internal PropertyType enum values
PROPERTY_TYPE_MAP = {
    "Single Family": "single_family",
    "Condo": "condo",
    "Townhouse": "townhouse",
    "Manufactured": "single_family",
    "Multi-Family": "multi_family",
    "Apartment": "multi_family",
    "Land": "land",
}


async def lookup_property(address: str, city: str = None, state: str = None, zip_code: str = None) -> dict:
    """
    Looks up public record data for a property by address.
    Returns {"found": bool, "data": {...} | None, "error": str | None}.
    """
    if not RENTCAST_API_KEY:
        return {"found": False, "data": None, "error": "RENTCAST_API_KEY not configured"}

    full_address = address
    if city:
        full_address += f", {city}"
    if state:
        full_address += f", {state}"
    if zip_code:
        full_address += f" {zip_code}"

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{RENTCAST_BASE_URL}/properties",
                params={"address": full_address},
                headers={"X-Api-Key": RENTCAST_API_KEY},
            )

            if response.status_code == 404:
                return {"found": False, "data": None, "error": "No property record found for this address"}

            if response.status_code != 200:
                return {"found": False, "data": None, "error": f"RentCast returned {response.status_code}: {response.text[:200]}"}

            results = response.json()
            if not results or not isinstance(results, list) or len(results) == 0:
                return {"found": False, "data": None, "error": "No property record found for this address"}

            record = results[0]

            mapped_type = PROPERTY_TYPE_MAP.get(record.get("propertyType"), "single_family")
            features = record.get("features") or {}

            return {
                "found": True,
                "data": {
                    "property_type": mapped_type,
                    "bedrooms": record.get("bedrooms"),
                    "bathrooms": record.get("bathrooms"),
                    "square_feet": record.get("squareFootage"),
                    "lot_size": record.get("lotSize"),
                    "year_built": record.get("yearBuilt"),
                    "zoning": record.get("zoning"),
                    "features_detected": {
                        "pool": features.get("pool", False),
                        "garage": features.get("garage", False),
                        "garage_spaces": features.get("garageSpaces"),
                        "fireplace": features.get("fireplace", False),
                        "cooling_type": features.get("coolingType"),
                        "heating_type": features.get("heatingType"),
                        "room_count": features.get("roomCount"),
                    },
                },
                "error": None,
            }
    except Exception as e:
        return {"found": False, "data": None, "error": f"Lookup failed: {str(e)}"}
