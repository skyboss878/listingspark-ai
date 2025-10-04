#!/bin/bash

# =============================
# ListingSpark AI Startup Script
# =============================

# --- MongoDB Setup ---
DB_PATH=~/data/db
ADMIN_USER="admin"
ADMIN_PASS="SuperSecret123!"

mkdir -p "$DB_PATH"

# Kill any existing mongod processes
PIDS=$(pgrep mongod)
if [ ! -z "$PIDS" ]; then
    echo "Stopping existing MongoDB..."
    kill $PIDS
    sleep 2
fi

# Check if admin user exists
USER_EXISTS=$(mongosh --quiet --eval "db.getSiblingDB('admin').getUser('$ADMIN_USER')" | grep "$ADMIN_USER")

# If admin user missing, start mongod temporarily to create user
if [ -z "$USER_EXISTS" ]; then
    echo "Starting MongoDB temporarily to create admin user..."
    mongod --dbpath "$DB_PATH" --bind_ip 127.0.0.1 --fork --logpath "$DB_PATH/mongod.log"
    sleep 2
    echo "Creating admin user..."
    mongosh <<EOF
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

# Start MongoDB with authentication
echo "Starting MongoDB with authentication..."
mongod --dbpath "$DB_PATH" --auth --bind_ip 127.0.0.1 --fork --logpath "$DB_PATH/mongod.log"
sleep 2

# --- Backend Setup ---
echo "🚀 Starting ListingSpark AI Backend..."

cd ~/listingspark-ai/backend

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start FastAPI server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
