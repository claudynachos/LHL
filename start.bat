@echo off
REM Windows startup script for LHL

echo ================================================
echo   Legend Hockey League - Starting Application
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo Virtual environment not found. Creating...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
    echo Backend dependencies installed
) else (
    echo Backend virtual environment found
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo Frontend dependencies not found. Installing...
    cd frontend
    call npm install
    cd ..
    echo Frontend dependencies installed
) else (
    echo Frontend dependencies found
)

echo.
echo Make sure PostgreSQL is running and database is seeded!
echo Run: python scripts\seed_database.py if you haven't already
echo.

echo Starting servers...
echo   Backend will run on: http://localhost:5000
echo   Frontend will run on: http://localhost:3000
echo.
echo Press Ctrl+C to stop all servers
echo.

REM Start backend in new window
start "LHL Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start frontend in new window
start "LHL Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are starting in separate windows
echo Close the windows or press Ctrl+C in each to stop
echo.
pause
