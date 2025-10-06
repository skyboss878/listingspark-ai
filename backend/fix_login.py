with open('server.py', 'r') as f:
    content = f.read()

# Find and replace the broken login function
broken_section = '''        async with db.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?", (user_data.email, user_data.password)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
            else:
                raise HTTPException(401, "Invalid email or password")
                return {
                    "id": row[0], "email": row[1], "name": row[2],
                    "plan": row[4], "listings_created": row[5]
                }

            return {
                "id": user_id, "email": user_data.email,
                "name": user_data.name, "plan": "free", "listings_created": 0
            }'''

fixed_section = '''        async with db.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (user_data.email, user_data.password)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "id": row[0], "email": row[1], "name": row[2],
                    "plan": row[4], "listings_created": row[5]
                }
            else:
                raise HTTPException(401, "Invalid email or password")'''

content = content.replace(broken_section, fixed_section)

with open('server.py', 'w') as f:
    f.write(content)

print("✅ Fixed!")
