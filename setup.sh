#!/bin/bash

echo "🏠✨ Setting up ListingSpark AI - Viral Real Estate Platform"
echo "=================================================="

# Make scripts executable
chmod +x start_backend.sh
chmod +x start_frontend.sh 
chmod +x setup_mongodb.sh

# Check requirements
echo "Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
else
    echo "✅ Python 3 found"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
else
    echo "✅ Node.js found"
fi

# Setup MongoDB
echo "Setting up MongoDB..."
./setup_mongodb.sh

# Setup backend
echo "Setting up backend..."
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# Setup frontend  
echo "Setting up frontend..."
cd frontend
npm install
cd ..

echo ""
echo "🎉 Setup complete! ListingSpark AI is ready to launch!"
echo ""
echo "To start the application:"
echo "1. Terminal 1: ./start_backend.sh   (Backend API)"
echo "2. Terminal 2: ./start_frontend.sh  (Frontend App)" 
echo ""
echo "Then visit: http://localhost:3000"
echo ""
echo "📧 Support: info@launchlocal.com"
echo "📞 Phone: 661-932-0000"
