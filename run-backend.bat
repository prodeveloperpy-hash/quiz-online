@echo off
title Quiz Online - Backend
cd /d "%~dp0backend"
curl.exe --silent --fail --max-time 3 "http://127.0.0.1:8000/api/health" >nul 2>nul
if not errorlevel 1 (
    echo FastAPI backend is already running at http://127.0.0.1:8000
    echo No second server is required.
    exit /b 0
)

echo Starting FastAPI at http://127.0.0.1:8000
echo API documentation: http://127.0.0.1:8000/docs
echo.
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
if errorlevel 1 (
    echo.
    echo Backend stopped with an error. Keep this window open and review the message above.
    pause
)
