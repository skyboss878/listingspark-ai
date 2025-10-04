#!/bin/bash

# ListingSpark AI - Automated Deployment Script
# This script sets up the professional real estate platform

set -e  # Exit on error

echo "======================================================================"
echo "  ListingSpark AI - Professional Real Estate Platform Deployment"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Working directory: $SCRIPT_DIR"
echo ""

# Step 1: Backup existing files
echo -e "${YELLOW}Step 1: Backing up existing files...${NC}"
if [ -f "server.py" ]; then
    BACKUP_FILE="server.py.backup_$(date +%Y%m%d_%H%M%S)"
    cp server.py "$BACKUP_FILE"
    echo -e "${GREEN}✓ Backed up server.py to $BACKUP_FILE${NC}"
fi

if [ -f "listingspark.db" ]; then
    BACKUP_DB="listingspark.db.backup_$(date +%Y%m%d_%H%M%S)"
    cp listingspark.db "$BACKUP_DB"
    echo -e "${GREEN}✓ Backed up database to $BACKUP_DB${NC}"
fi
echo ""

# Step 2: Check required files
echo -e "${YELLOW}Step 2: Checking required files...${NC}"
MISSING_FILES=0

if [ ! -f "platform_integrations.py" ]; then
    echo -e "${RED}✗ platform_integrations.py not found${NC}"
    echo "  Please save the platform_integrations artifact to this directory"
    MISSING_FILES=1
fi

if [ ! -f "server.py" ]; then
    echo -e "${RED}✗ server.py not found${NC}"
    echo "  Please save the updated server.py to this directory"
    MISSING_FILES=1
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo -e "${RED}Missing required files. Exiting.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All required files found${NC}"
echo ""

# Step 3: Install Python dependencies
echo -e "${YELLOW}Step 3: Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    echo "Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
fastapi>=0.104.1
uvicorn>=0.24.0
aiosqlite>=0.19.0
pydantic>=2.5.0
python-multipart>=0.0.6
openai>=1.3.0
Pillow>=10.0.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
EOF
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi
echo ""

# Step 4: Setup .env file
echo -e "${YELLOW}Step 4: Setting up environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo "Creating .env template..."
    cat > .env << 'EOF'
# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Zillow (Free tier available)
ZILLOW_API_KEY=
ZILLOW_ENABLED=false

# Realtor.com
REALTOR_API_KEY=
REALTOR_ENABLED=false

# MLS Access
MLS_USERNAME=
MLS_PASSWORD=
MLS_ACCOUNT_ID=
MLS_ENABLED=false

# Facebook Marketplace
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_ENABLED=false

# Redfin
REDFIN_API_KEY=
REDFIN_ENABLED=false

# Application Settings
HOST=0.0.0.0
PORT=8000
DATABASE_PATH=./listingspark.db
DOMAIN=http://localhost:8000
EOF
    echo -e "${GREEN}✓ Created .env template${NC}"
    echo -e "${YELLOW}  ⚠ Please edit .env and add your API keys${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi
echo ""

# Step 5: Initialize/Update Database
echo -e "${YELLOW}Step 5: Setting up database...${NC}"
sqlite3 listingspark.db << 'EOF'
-- Create platform_syncs table
CREATE TABLE IF NOT EXISTS platform_syncs (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    platform_name TEXT NOT NULL,
    platform_listing_id TEXT,
    platform_url TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties (id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_platform_syncs_property ON platform_syncs(property_id);
CREATE INDEX IF NOT EXISTS idx_platform_syncs_platform ON platform_syncs(platform_name);
CREATE INDEX IF NOT EXISTS idx_platform_syncs_status ON platform_syncs(status);

-- Create rooms table if not exists
CREATE TABLE IF NOT EXISTS rooms (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    space_name TEXT NOT NULL,
    space_type TEXT NOT NULL,
    space_category TEXT NOT NULL,
    description TEXT,
    square_feet INTEGER,
    image_360_url TEXT,
    thumbnail_url TEXT,
    processing_status TEXT DEFAULT 'pending',
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE
);

-- Create tours table if not exists
CREATE TABLE IF NOT EXISTS tours (
    id TEXT PRIMARY KEY,
    property_id TEXT NOT NULL,
    tour_name TEXT NOT NULL,
    tour_url TEXT,
    status TEXT DEFAULT 'draft',
    total_scenes INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (property_id) REFERENCES properties (id) ON DELETE CASCADE
);

-- Create custom_amenities table if not exists
CREATE TABLE IF NOT EXISTS custom_amenities (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    amenity_name TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT 'Custom',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_rooms_property ON rooms(property_id);
CREATE INDEX IF NOT EXISTS idx_tours_property ON tours(property_id);
CREATE INDEX IF NOT EXISTS idx_custom_amenities_user ON custom_amenities(user_id);
EOF

echo -e "${GREEN}✓ Database tables created/updated${NC}"
echo ""

# Step 6: Create necessary directories
echo -e "${YELLOW}Step 6: Creating directories...${NC}"
mkdir -p uploads
mkdir -p tours
mkdir -p logs
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Step 7: Verify setup
echo -e "${YELLOW}Step 7: Verifying setup...${NC}"
echo "Database tables:"
sqlite3 listingspark.db ".tables"
echo ""

echo "Directory structure:"
ls -la | grep -E "^d" | awk '{print "  " $9}'
echo ""

# Step 8: Test imports
echo -e "${YELLOW}Step 8: Testing Python imports...${NC}"
python3 << 'EOF'
try:
    import fastapi
    import aiosqlite
    import openai
    from PIL import Image
    import aiohttp
    print("✓ All Python modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    exit(1)

try:
    from platform_integrations import platform_manager
    print("✓ Platform integrations module loaded")
except Exception as e:
    print(f"✗ Platform integrations error: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Python environment verified${NC}"
else
    echo -e "${RED}✗ Python environment has issues${NC}"
    exit 1
fi
echo ""

# Step 9: Summary
echo "======================================================================"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo "======================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Start the server:"
echo "   python server.py"
echo ""
echo "3. Test the API:"
echo "   curl http://localhost:8000/health"
echo "   curl http://localhost:8000/platforms"
echo ""
echo "4. View API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "Quick commands:"
echo "  - View logs: tail -f logs/*.log"
echo "  - Check database: sqlite3 listingspark.db '.tables'"
echo "  - Test platforms: curl -X POST http://localhost:8000/platforms/zillow/test"
echo ""
echo "======================================================================"
echo ""

# Offer to start server
read -p "Would you like to start the server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting ListingSpark AI server..."
    echo ""
    python server.py
fi
