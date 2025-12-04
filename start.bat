@echo off
echo ========================================
echo AI Video Clipper - Quick Start
echo ========================================
echo.
echo Starting backend and frontend servers...
echo.

REM Start backend in new window
echo Starting backend server...
start "AI Video Clipper - Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

REM Wait a bit for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting frontend server...
start "AI Video Clipper - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Servers are starting...
echo ========================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to stop all servers...
pause >nul

REM Kill all related processes
taskkill /FI "WINDOWTITLE eq AI Video Clipper - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AI Video Clipper - Frontend*" /F >nul 2>&1

echo.
echo Servers stopped.
pause
