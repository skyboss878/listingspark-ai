# 🏠✨ ListingSpark AI - Viral Real Estate Platform

Transform boring property listings into viral social media content that sells houses faster!

## Features

- 🤖 AI-powered content generation for Instagram, TikTok, and Facebook  
- 📈 Viral score prediction and analytics
- 🎯 Platform-optimized content creation
- 📊 Performance tracking and engagement metrics
- 💼 Multi-property management dashboard
- 🚀 Real-time content generation

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB 4.4+

### Installation

1. **Clone and setup:**
```bash
git clone <your-repo>
cd listingspark-ai
chmod +x setup.sh
./setup.shStart the application:Terminal 1 (Backend):./start_backend.shTerminal 2 (Frontend):./start_frontend.shAccess the app:Frontend: http://localhost:3000Backend API: http://localhost:8000ConfigurationBackend Environment (.env)MONGO_URL="mongodb://localhost:27017"
DB_NAME="listingspark_ai"
EMERGENT_LLM_KEY=your_ai_key_here
STRIPE_SECRET_KEY=your_stripe_key_hereFrontend Environment (.env)REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_APP_NAME=ListingSpark AIAPI EndpointsPropertiesPOST /api/properties - Create propertyGET /api/properties/{user_id} - Get user propertiesPOST /api/properties/{id}/viral-content - Generate contentGET /api/properties/{id}/analytics - Get analyticsUsersPOST /api/users - Create userGET /api/users/{id} - Get userGET /api/dashboard/{user_id} - Dashboard dataProject Structurelistingspark-ai/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main server
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment config
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── App.js        # Main app
│   │   └── App.css       # Styles
│   └── package.json      # Node dependencies
├── setup.sh               # Main setup script
├── start_backend.sh       # Backend starter
└── start_frontend.sh      # Frontend starterTechnology StackBackend:FastAPI (Python web framework)MongoDB (Database)EmergentAI (LLM integration)Stripe (Payments)Frontend:React 18Tailwind CSSFramer MotionReact RouterSupport📧 Email: info@launchlocal.com
📞 Phone: 661-932-0000LicenseProprietary - All rights reserved EOF**20. Make scripts executable:**

```bash
chmod +x setup.sh
chmod +x start_backend.sh
chmod +x start_frontend.sh
chmod +x setup_mongodb.sh21. Final .gitignore:cat > .gitignore << 'EOF'
# Dependencies
node_modules/
backend/.venv/
backend/__pycache__/

# Environment files
.env
.env.local
.env.production

# Build files
frontend/build/
frontend/dist/

# Database
*.db
*.sqlite

# Logs
*.log
backend/logs/

# Uploads
backend/uploads/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Temporary files
*.tmp
*.temp
