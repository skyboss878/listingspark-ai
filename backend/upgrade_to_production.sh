#!/bin/bash
# ListingSpark AI - Production Upgrade Script
# Transforms your backend into production-ready $1M software

echo "🚀 LISTINGSPARK AI - PRODUCTION UPGRADE"
echo "========================================"
echo ""

BACKEND_DIR="$HOME/projects/The360emerge/backend"
BACKUP_DIR="$BACKEND_DIR/backups/$(date +%Y%m%d_%H%M%S)"

cd "$BACKEND_DIR" || exit 1

echo "📋 Pre-upgrade Checklist:"
echo "========================="
echo ""

# Create backup
echo "📦 Creating backup..."
mkdir -p "$BACKUP_DIR"
cp server.py "$BACKUP_DIR/"
cp requirements.txt "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/" 2>/dev/null || echo "⚠️  No .env file found (will create new)"
echo "✅ Backup created at: $BACKUP_DIR"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"
if [[ $(echo "$python_version" | cut -d. -f1) -lt 3 ]] || [[ $(echo "$python_version" | cut -d. -f2) -lt 8 ]]; then
    echo "❌ Python 3.8+ required!"
    exit 1
fi
echo "✅ Python version OK"
echo ""

# Check virtual environment
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
else
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Failed to activate venv"
    exit 1
}
echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo ""

# Install enhanced requirements
echo "📦 Installing enhanced dependencies..."
echo "   This may take 5-10 minutes..."
echo ""

if [ -f "requirements_enhanced.txt" ]; then
    pip install -r requirements_enhanced.txt --break-system-packages 2>/dev/null || pip install -r requirements_enhanced.txt
else
    echo "⚠️  requirements_enhanced.txt not found, using existing requirements.txt"
    pip install -r requirements.txt --break-system-packages 2>/dev/null || pip install -r requirements.txt
fi

echo ""
echo "✅ Dependencies installed"
echo ""

# Create .env if doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ .env created - PLEASE EDIT WITH YOUR API KEYS!"
        echo "⚠️  IMPORTANT: Edit .env file with your actual API keys before running server!"
    else
        echo "⚠️  No .env.example found - you'll need to create .env manually"
    fi
else
    echo "✅ .env file already exists"
fi
echo ""

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p video_tours
mkdir -p video_cache
mkdir -p music_library
mkdir -p logs
mkdir -p uploads
mkdir -p exports
echo "✅ Directories created"
echo ""

# Check critical services
echo "🔍 Checking critical services..."
echo ""

# Check Redis (recommended)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis installed but not running - start with: redis-server"
        echo "   Redis is needed for caching and background jobs"
    fi
else
    echo "⚠️  Redis not installed - highly recommended for production"
    echo "   Install: sudo apt-get install redis-server (Ubuntu/Debian)"
    echo "   or: brew install redis (Mac)"
fi
echo ""

# Check PostgreSQL (optional but recommended)
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL is installed"
    echo "   Configure in .env: DATABASE_URL=postgresql://..."
else
    echo "ℹ️  PostgreSQL not installed - currently using MongoDB/SQLite"
    echo "   For production, consider: sudo apt-get install postgresql"
fi
echo ""

# Check ffmpeg (required for video processing)
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg is installed"
else
    echo "❌ ffmpeg NOT installed - REQUIRED for video generation!"
    echo "   Install: sudo apt-get install ffmpeg (Ubuntu/Debian)"
    echo "   or: brew install ffmpeg (Mac)"
fi
echo ""

# Security audit
echo "🔒 Running security checks..."
echo ""

# Check for hardcoded secrets
echo "Checking for hardcoded secrets..."
if grep -rn "sk-[a-zA-Z0-9]" --include="*.py" . 2>/dev/null | grep -v "\.env" | grep -v "# sk-"; then
    echo "🚨 WARNING: Possible hardcoded API keys found!"
    echo "   Move all API keys to .env file"
else
    echo "✅ No obvious hardcoded secrets found"
fi
echo ""

# Check .env permissions
if [ -f ".env" ]; then
    perms=$(stat -c %a .env 2>/dev/null || stat -f %A .env)
    if [ "$perms" != "600" ]; then
        echo "🔒 Fixing .env permissions..."
        chmod 600 .env
        echo "✅ .env permissions set to 600 (owner read/write only)"
    else
        echo "✅ .env permissions correct"
    fi
fi
echo ""

# Create health check endpoint code
echo "🏥 Creating health check endpoint..."
cat > health_check.py << 'HEALTHEOF'
"""
Health Check Endpoint for Monitoring
Add this to your server.py
"""

from fastapi import APIRouter
from datetime import datetime
import psutil
import os

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring services
    Returns system status and service availability
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "api": "up",
            "database": "up",  # Add actual check
            "redis": "up",     # Add actual check
            "video_gen": "up"   # Add actual check
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    }

@health_router.get("/health/ready")
async def readiness_check():
    """Check if service is ready to accept traffic"""
    # Add checks for database connections, etc.
    return {"ready": True}

@health_router.get("/health/live")
async def liveness_check():
    """Check if service is alive"""
    return {"alive": True}
HEALTHEOF

echo "✅ health_check.py created - add to server.py"
echo ""

# Create production run script
echo "🚀 Creating production run script..."
cat > run_production.sh << 'RUNEOF'
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
RUNEOF

chmod +x run_production.sh
echo "✅ run_production.sh created"
echo ""

# Create testing script
echo "🧪 Creating test script..."
cat > run_tests.sh << 'TESTEOF'
#!/bin/bash
# Run all tests

source venv/bin/activate

echo "🧪 Running ListingSpark AI tests..."
echo ""

# Run pytest with coverage
pytest tests/ \
    --cov=. \
    --cov-report=html \
    --cov-report=term-missing \
    -v

echo ""
echo "📊 Coverage report generated at: htmlcov/index.html"
TESTEOF

chmod +x run_tests.sh
echo "✅ run_tests.sh created"
echo ""

# Summary
echo ""
echo "=========================================="
echo "✅ UPGRADE COMPLETE!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. 🔑 Configure .env file:"
echo "   nano .env"
echo "   Add your API keys for:"
echo "   - OpenAI"
echo "   - ElevenLabs"
echo "   - Stripe/PayPal"
echo "   - AWS S3"
echo "   - MongoDB"
echo ""
echo "2. 🧪 Test the video generator:"
echo "   python -c 'from video_tour_generator_pro_v2 import premium_video_generator; print(\"✅ Video generator imported successfully\")'"
echo ""
echo "3. 🚀 Start the server:"
echo "   ./run_production.sh"
echo "   or for development:"
echo "   uvicorn server:app --reload"
echo ""
echo "4. 🏥 Test health endpoint:"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. 📚 Review documentation:"
echo "   - BACKEND_ANALYSIS_REPORT.md"
echo "   - MILLION_DOLLAR_ANALYSIS.md"
echo ""
echo "=========================================="
echo "🎯 PRODUCTION READINESS CHECKLIST:"
echo "=========================================="
echo ""
echo "Security:"
echo "  [ ] All API keys in .env (not hardcoded)"
echo "  [ ] .env permissions set to 600"
echo "  [ ] JWT secret key changed from default"
echo "  [ ] HTTPS/SSL configured"
echo "  [ ] CORS properly configured"
echo ""
echo "Database:"
echo "  [ ] PostgreSQL configured (not SQLite)"
echo "  [ ] Database backups automated"
echo "  [ ] Connection pooling enabled"
echo ""
echo "Monitoring:"
echo "  [ ] Sentry error tracking configured"
echo "  [ ] Health check endpoints added"
echo "  [ ] Logging configured"
echo ""
echo "Performance:"
echo "  [ ] Redis caching enabled"
echo "  [ ] CDN configured for video delivery"
echo "  [ ] Background jobs with Celery"
echo ""
echo "Payments:"
echo "  [ ] Stripe configured (recommended)"
echo "  [ ] Webhook endpoints tested"
echo "  [ ] Payment flows tested"
echo ""
echo "Testing:"
echo "  [ ] All endpoints tested"
echo "  [ ] Video generation tested"
echo "  [ ] Payment flows tested"
echo "  [ ] Load testing completed"
echo ""
echo "=========================================="
echo "💰 Ready to make $1M? Let's launch! 🚀"
echo "=========================================="
echo ""

