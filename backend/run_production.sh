#!/bin/bash
# Production server startup script

source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Copy .env.example to .env and configure your API keys"
    exit 1
fi

# Start server with production settings
echo "🚀 Starting ListingSpark AI in production mode..."
echo ""

# Option 1: Development (with auto-reload)
# uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Option 2: Production (multi-worker)
uvicorn server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --access-log \
    --no-use-colors
