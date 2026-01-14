#!/bin/bash

echo "Starting LHL servers..."
echo ""

# Check if frontend is installed
if [ ! -f "frontend/node_modules/.bin/next" ]; then
    echo "❌ Frontend not installed. Run: ./COMPLETE_FIX.sh first"
    exit 1
fi

# Start backend in background
echo "Starting backend on http://localhost:5000..."
cd backend
source venv/bin/activate
python app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:3000..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers starting!"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Logs:"
echo "  Backend:  tail -f backend.log"
echo "  Frontend: tail -f frontend.log"
echo ""
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Waiting for servers to start..."
sleep 5

# Check if servers are running
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo "✅ Backend is running on http://localhost:5000"
else
    echo "⚠️  Backend may not be running. Check backend.log"
fi

if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "⚠️  Frontend may not be running. Check frontend.log"
fi

echo ""
echo "Open http://localhost:3000 in your browser"
