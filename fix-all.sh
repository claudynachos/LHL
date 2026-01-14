#!/bin/bash

echo "🔧 Fixing All LHL Issues..."
echo ""

# Fix 1: Frontend dependencies
echo "1. Installing frontend dependencies..."
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
cd ..
echo "✓ Frontend dependencies installed"
echo ""

# Fix 2: Backend dependencies
echo "2. Installing backend dependencies..."
cd backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "   Installing Python packages..."
pip install -r requirements.txt
deactivate
cd ..
echo "✓ Backend dependencies installed"
echo ""

echo "✅ All fixes complete!"
echo ""
echo "Now run: npm run dev"
