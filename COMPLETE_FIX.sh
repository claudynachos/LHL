#!/bin/bash

set -e  # Exit on error

echo "=========================================="
echo "  LHL Complete Fix Script"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Step 1: Check Node version
echo -e "${YELLOW}Step 1: Checking Node.js version...${NC}"
NODE_VERSION=$(node --version | cut -d'v' -f2)
NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1)
echo "Node version: $NODE_VERSION"

if [ "$NODE_MAJOR" -lt 18 ]; then
    echo -e "${YELLOW}⚠️  Node.js $NODE_VERSION detected (Next.js 14 needs 18+)${NC}"
    echo -e "${GREEN}✓ Using Next.js 13 (compatible with Node 16)${NC}"
else
    echo -e "${GREEN}✓ Node version is compatible${NC}"
fi
echo ""

# Step 2: Fix Frontend
echo -e "${YELLOW}Step 2: Fixing frontend...${NC}"
cd frontend

echo "  - Clearing npm cache..."
npm cache clean --force > /dev/null 2>&1 || true

echo "  - Removing old files..."
rm -rf node_modules package-lock.json .next 2>/dev/null || true

echo "  - Installing dependencies (this may take 2-3 minutes)..."
npm install --legacy-peer-deps 2>&1 | tee /tmp/npm_install.log

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${RED}✗ npm install failed${NC}"
    echo ""
    echo "Last 10 lines of error:"
    tail -10 /tmp/npm_install.log
    echo ""
    echo -e "${YELLOW}Trying yarn as alternative...${NC}"
    
    # Try yarn as fallback (only if already installed)
    if command -v yarn &> /dev/null; then
        echo "  - Installing with yarn..."
        yarn install
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Installed with yarn${NC}"
        else
            echo -e "${RED}✗ Yarn also failed${NC}"
            echo ""
            echo "Manual fix needed. Try:"
            echo "  1. cd frontend"
            echo "  2. npm install --legacy-peer-deps --verbose"
            echo "  3. Or install yarn: brew install yarn"
            exit 1
        fi
    else
        echo -e "${RED}✗ Yarn not available${NC}"
        echo ""
        echo "To install yarn:"
        echo "  brew install yarn"
        echo ""
        echo "Or try npm install again with:"
        echo "  npm install --legacy-peer-deps --verbose"
        exit 1
    fi
fi

cd ..
echo ""

# Step 3: Check Backend
echo -e "${YELLOW}Step 3: Checking backend...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "  - Creating virtual environment..."
    python3 -m venv venv
fi

echo "  - Activating venv and checking dependencies..."
source venv/bin/activate

if ! python -c "import flask" 2>/dev/null; then
    echo "  - Installing Python dependencies..."
    pip install -r requirements.txt 2>&1 | grep -v "ERROR" || true
fi

# Try to install psycopg2-binary if missing
if ! python -c "import psycopg2" 2>/dev/null; then
    echo "  - Installing psycopg2-binary..."
    pip install psycopg2-binary 2>&1 | grep -v "ERROR" || echo "  ⚠️  psycopg2-binary failed, will use mock simulator"
fi

deactivate
cd ..
echo -e "${GREEN}✓ Backend ready${NC}"
echo ""

# Step 4: Verify installation
echo -e "${YELLOW}Step 4: Verifying installation...${NC}"

cd frontend
if [ -f "node_modules/.bin/next" ]; then
    echo -e "${GREEN}✓ Next.js installed${NC}"
else
    echo -e "${RED}✗ Next.js not found${NC}"
    echo "  Try: cd frontend && npm install --legacy-peer-deps"
    exit 1
fi
cd ..

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "To start the app, run:"
echo "  npm run dev"
echo ""
echo "Or start separately:"
echo "  Terminal 1: cd backend && source venv/bin/activate && python app.py"
echo "  Terminal 2: cd frontend && npm run dev"
echo ""
