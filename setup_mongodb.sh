#!/bin/bash

echo "🗄️  Setting up MongoDB for ListingSpark AI..."

# Config
DB_PATH=~/data/db
ADMIN_USER="admin"
ADMIN_PASS="SuperSecret123!"
DB_NAME="listingspark_ai"

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

# Connect to MongoDB and create database + collections
echo "Setting up ListingSpark AI database..."
mongosh -u "$ADMIN_USER" -p "$ADMIN_PASS" --authenticationDatabase admin <<EOF
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

echo "✅ MongoDB setup complete!"
echo "Database: $DB_NAME"
echo "Connection: mongodb://$ADMIN_USER:$ADMIN_PASS@127.0.0.1:27017"
