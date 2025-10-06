with open('server.py', 'r') as f:
    lines = f.readlines()

# Find line with "if row:" and fix the structure
for i in range(len(lines)):
    if i >= 488 and 'if row:' in lines[i] and lines[i].strip() == 'if row:':
        # This is line 489, fix the next few lines
        lines[i] = '            if row:\n'
        lines[i+1] = '                return {\n'
        lines[i+2] = '                    "id": row[0], "email": row[1], "name": row[2],\n'
        lines[i+3] = '                    "plan": row[4], "listings_created": row[5]\n'
        lines[i+4] = '                }\n'
        lines[i+5] = '            else:\n'
        lines[i+6] = '                raise HTTPException(401, "Invalid email or password")\n'
        # Remove the extra lines after
        del lines[i+7:i+13]
        break

with open('server.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed syntax error!")
