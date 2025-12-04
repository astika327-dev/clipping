@echo off
echo ========================================
echo AI Video Clipper - Installation Script
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.10 or newer.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✓ Python found

REM Check Node.js
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js 18 or newer.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)
echo ✓ Node.js found

REM Check FFmpeg
echo [3/5] Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: FFmpeg not found!
    echo Please install FFmpeg from: https://ffmpeg.org/download.html
    echo Or the application may not work properly.
    echo.
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    echo ✓ FFmpeg found
)

REM Setup Backend
echo [4/5] Setting up backend...
cd backend

echo   - Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

echo   - Activating virtual environment...
call venv\Scripts\activate.bat

echo   - Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo ✓ Backend setup complete
cd ..

REM Setup Frontend
echo [5/5] Setting up frontend...
cd frontend

echo   - Installing Node dependencies...
npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)

echo ✓ Frontend setup complete
cd ..

echo.
echo ========================================
echo Installation Complete! 🎉
echo ========================================
echo.
echo To run the application:
echo.
echo 1. Open Terminal 1 (Backend):
echo    cd backend
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 2. Open Terminal 2 (Frontend):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Open browser: http://localhost:5173
echo.
echo For more info, read QUICKSTART.md
echo ========================================
pause
