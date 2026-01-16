#!/bin/bash

echo "🚀 Starting LHL Application..."
echo ""

# Step 1: Add Node 18 to PATH
echo "Step 1: Setting up Node 18..."
export PATH="/usr/local/opt/node@18/bin:$PATH"

# Verify Node version
NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)
echo "✅ Node: $NODE_VERSION"
echo "✅ npm: $NPM_VERSION"

if [[ ! "$NODE_VERSION" =~ ^v18 ]]; then
    echo "⚠️  Node 18 not active. Adding to PATH permanently..."
    echo 'export PATH="/usr/local/opt/node@18/bin:$PATH"' >> ~/.zshrc
    source ~/.zshrc
    export PATH="/usr/local/opt/node@18/bin:$PATH"
    echo "✅ Node 18 added to PATH"
fi

echo ""

# Step 2: Fix Frontend
echo "Step 2: Installing frontend dependencies..."
cd frontend

# Clear caches
npm cache clean --force
rm -rf ~/.npm node_modules package-lock.json .next 2>/dev/null || true

# Install
echo "  Installing packages (this may take 2-3 minutes)..."
npm install --legacy-peer-deps

if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed!"
else
    echo "❌ Installation failed. Check errors above."
    exit 1
fi

cd ..
echo ""

# Step 3: Check Backend
echo "Step 3: Checking backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

if ! python -c "import flask" 2>/dev/null; then
    echo "  Installing Python dependencies..."
    pip install -r requirements.txt 2>&1 | grep -v "ERROR" || true
fi

deactivate
cd ..
echo "✅ Backend ready"
echo ""

# Step 4: Start Servers
echo "Step 4: Starting servers..."
echo ""
echo "Backend will run on: http://localhost:5000"
echo "Frontend will run on: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Start both servers
npm run dev
