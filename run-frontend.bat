@echo off
title Quiz Online - Frontend
cd /d "%~dp0frontend"
echo Starting React at http://localhost:5173
echo.
npm.cmd run dev -- --host 127.0.0.1
if errorlevel 1 (
    echo.
    echo Frontend stopped with an error. Keep this window open and review the message above.
    pause
)
