@echo off
title Cineverse Launcher
echo ========================================================
echo               STARTING CINEVERSE WEB APP                
echo ========================================================
echo.

cd /d "%~dp0"

echo [1/3] Checking backend and frontend servers...
start /b cmd /c ".\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"
start /b cmd /c "cd frontend && npm run dev -- --port 3001 --host 0.0.0.0"

echo [2/3] Waiting for servers to get ready...
timeout /t 3 /nobreak >nul

echo [3/3] Opening Cineverse in your default browser...
start http://localhost:3001/

echo.
echo ========================================================
echo   Cineverse is running at: http://localhost:3001/
echo   (Keep this window open or minimize it while streaming)
echo ========================================================
echo.
pause
