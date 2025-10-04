#!/bin/bash

# =============================
# ListingSpark AI Full Startup
# =============================

# Absolute paths to MongoDB binaries
MONGOD_BIN="/usr/bin/mongod"
MONGOSH_BIN="/usr/bin/mongosh"

# Paths
DB_PATH=~/data/db
ADMIN_USER="admin"
ADMIN_PASS="SuperSecret123!"
DB_NAME="listingspark_ai"
BACKEND_DIR=~/listingspark-ai/backend

mkdir -p "$DB_PATH"

# --- Stop any running MongoDB ---
PIDS=$(pgrep mongod)
if [ ! -z "$PIDS" ]; then
    echo "Stopping existing MongoDB..."
    kill $PIDS
    sleep 2
fi

# --- Check if admin user exists ---
USER_EXISTS=$($MONGOSH_BIN --quiet --eval "db.getSiblingDB('admin').getUser('$ADMIN_USER')" | grep "$ADMIN_USER")

# --- Create admin if missing ---
if [ -z "$USER_EXISTS" ]; then
    echo "Starting MongoDB temporarily to create admin user..."
    $MONGOD_BIN --dbpath "$DB_PATH" --bind_ip 127.0.0.1 --fork --logpath "$DB_PATH/mongod.log"
    sleep 2

    echo "Creating admin user..."
    $MONGOSH_BIN <<EOF
use admin
db.createUser({
  user: "$ADMIN_USER",
  pwd: "$ADMIN_PASS",
  roles: [ { role: "root", db: "admin" } ]
})
EOF

    echo "Stopping temporary MongoDB..."
    pkill mongod
    sleep 2
fi

# --- Start MongoDB with authentication ---
echo "Starting MongoDB with authentication..."
$MONGOD_BIN --dbpath "$DB_PATH" --auth --bind_ip 127.0.0.1 --fork --logpath "$DB_PATH/mongod.log"
sleep 2

# --- Setup ListingSpark AI database and collections ---
echo "Setting up ListingSpark AI database..."
$MONGOSH_BIN -u "$ADMIN_USER" -p "$ADMIN_PASS" --authenticationDatabase admin <<EOF
use $DB_NAME

db.createCollection('users')
db.createCollection('properties')
db.createCollection('viral_content')
db.createCollection('virtual_tours')
db.createCollection('analytics')

// Create indexes for better performance
db.users.createIndex({ 'email': 1 }, { unique: true })
db.users.createIndex({ 'id': 1 }, { unique: true })
db.properties.createIndex({ 'user_id': 1 })
db.properties.createIndex({ 'id': 1 }, { unique: true })
db.viral_content.createIndex({ 'property_id': 1 })
db.analytics.createIndex({ 'property_id': 1 }, { unique: true })

print('✅ ListingSpark AI database setup complete!')
EOF

# --- Start backend ---
echo "🚀 Starting ListingSpark AI Backend..."
cd "$BACKEND_DIR"

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies (ignore missing ones for now)
pip install -r requirements.txt || echo "⚠️ Some packages failed to install (check emergentintegrations)"

# Start FastAPI backend
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
