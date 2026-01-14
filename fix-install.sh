#!/bin/bash

echo "🔧 Fixing LHL Installation Issues..."
echo ""

# Fix 1: Clean npm cache (corrupted downloads)
echo "1. Cleaning npm cache..."
npm cache clean --force
echo "✓ Cache cleaned"
echo ""

# Fix 2: Install backend dependencies
echo "2. Installing backend dependencies..."
cd backend

# Check if venv exists, create if not
if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate
echo "   Installing Flask and dependencies from requirements.txt..."
pip install -r requirements.txt

deactivate
cd ..
echo "✓ Backend dependencies installed"
echo ""

# Fix 3: Install frontend dependencies
echo "3. Installing frontend dependencies..."
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
echo "✓ Frontend dependencies installed"
echo ""

echo "✅ Installation fixed!"
echo ""
echo "Now you can run: npm run dev"
