import re

with open('server.py', 'r') as f:
    content = f.read()

# Find the get_listings function and replace it
old_pattern = r'''@app\.get\("/api/listings", response_model=List\[Listing\]\)
async def get_listings\(
    current_user: User = Depends\(get_current_user\),
    db: AsyncIOMotorDatabase = Depends\(get_mongo_db\),
    status: Optional\[ListingStatus\] = None
\):
    query = \{"user_id": current_user\["id"\] if isinstance\(current_user, dict\) else current_user\.id\}
    if status:
        query\["status"\] = status

    listings = await db\.listings\.find\(query\)\.sort\("created_at", -1\)\.to_list\(100\)
    return \[Listing\(\*\*listing\) for listing in listings\]'''

new_function = '''@app.get("/api/listings", response_model=List[Listing])
async def get_listings(
    current_user: User = Depends(get_current_user),
    status: Optional[ListingStatus] = None
):
    """Get user listings from SQLite"""
    try:
        user_id = current_user["id"] if isinstance(current_user, dict) else current_user.id
        listings_data = sqlite_db.get_listings(user_id, status.value if status else None)
        return [Listing(**listing) for listing in listings_data]
    except Exception as e:
        logger.error(f"Error fetching listings: {e}")
        return []'''

content = re.sub(old_pattern, new_function, content, flags=re.MULTILINE | re.DOTALL)

with open('server.py', 'w') as f:
    f.write(content)

print("✅ Replaced get_listings function")
