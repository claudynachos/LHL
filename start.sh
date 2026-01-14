#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Legend Hockey League - Starting Application${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
    echo -e "${GREEN}✓ Backend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Backend virtual environment found${NC}"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Frontend dependencies not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Frontend dependencies found${NC}"
fi

# Check if database is seeded
echo ""
echo -e "${YELLOW}Make sure PostgreSQL is running and database is seeded!${NC}"
echo -e "Run ${BLUE}python3 scripts/seed_database.py${NC} if you haven't already"
echo ""

# Start both servers
BACKEND_PORT=5000
if lsof -nP -iTCP:${BACKEND_PORT} -sTCP:LISTEN >/dev/null 2>&1; then
    echo -e "${YELLOW}Port ${BACKEND_PORT} is in use. Switching backend to 5001...${NC}"
    BACKEND_PORT=5001
fi

echo -e "${GREEN}Starting servers...${NC}"
echo -e "  Backend will run on: ${BLUE}http://localhost:${BACKEND_PORT}${NC}"
echo -e "  Frontend will run on: ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all servers${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start backend
cd backend
source venv/bin/activate
PORT=${BACKEND_PORT} python -m app &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend
cd frontend
NEXT_PUBLIC_API_URL="http://localhost:${BACKEND_PORT}" npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for both processes
wait
