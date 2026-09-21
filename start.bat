@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Quiz Online Launcher
color 0B

cd /d "%~dp0"

echo.
echo ========================================================
echo              QUIZ ONLINE - LOCAL LAUNCHER
echo ========================================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend virtual environment was not found.
    echo Run the installation steps in SETUP.md first.
    echo.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [ERROR] Frontend packages were not found.
    echo Open a terminal in the frontend folder and run: npm.cmd install
    echo.
    pause
    exit /b 1
)

if not exist "backend\.env" (
    copy /Y "backend\.env.example" "backend\.env" >nul
    echo [OK] Created backend\.env
)

if not exist "frontend\.env" (
    copy /Y "frontend\.env.example" "frontend\.env" >nul
    echo [OK] Created frontend\.env
)

set "MYSQL_SERVER=C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe"
set "MYSQL_CLIENT=C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqladmin.exe"

if not exist "%MYSQL_SERVER%" (
    echo [ERROR] Local MySQL Server 8.4 was not found.
    echo Install MySQL Server and run this launcher again.
    pause
    exit /b 1
)

"%MYSQL_CLIENT%" --protocol=TCP -h 127.0.0.1 -u quiz_user --password=quiz_password ping --silent >nul 2>nul
if errorlevel 1 (
    echo [INFO] Starting local MySQL Server...
    start "Quiz Online - MySQL" /min "%MYSQL_SERVER%" --defaults-file="%~dp0mysql-local.ini" --console
)

echo [INFO] Waiting for local MySQL...
set /a DB_TRIES=0
:WAIT_FOR_DB_LOOP
"%MYSQL_CLIENT%" --protocol=TCP -h 127.0.0.1 -u quiz_user --password=quiz_password ping --silent >nul 2>nul
if not errorlevel 1 goto DB_READY
set /a DB_TRIES+=1
if !DB_TRIES! GEQ 30 goto DB_TIMEOUT
timeout /t 2 /nobreak >nul
goto WAIT_FOR_DB_LOOP

:DB_TIMEOUT
echo [ERROR] Local MySQL did not become ready within 60 seconds.
echo Review mysql-data\MURSHAD.err for details.
pause
exit /b 1

:DB_READY
echo [OK] Local MySQL is ready.

echo [INFO] Creating/updating demo accounts...
pushd "backend"
".venv\Scripts\python.exe" seed.py
if errorlevel 1 (
    popd
    echo.
    echo [ERROR] Could not connect to MySQL.
    echo Start Docker Desktop or your local MySQL service, then run start.bat again.
    echo See SETUP.md for database configuration.
    pause
    exit /b 1
)
popd

echo [INFO] Checking FastAPI backend...
curl.exe --silent --fail --max-time 3 "http://127.0.0.1:8000/api/health" >nul 2>nul
if errorlevel 1 (
    echo [INFO] Starting FastAPI backend...
    start "Quiz Online - Backend" cmd /k call "%~dp0run-backend.bat"
) else (
    echo [OK] FastAPI backend is already running.
)

echo [INFO] Waiting for FastAPI backend...
set /a API_TRIES=0
:WAIT_FOR_API_LOOP
curl.exe --silent --fail --max-time 3 "http://127.0.0.1:8000/api/health" >nul 2>nul
if not errorlevel 1 goto API_READY
set /a API_TRIES+=1
if !API_TRIES! GEQ 20 goto API_TIMEOUT
timeout /t 1 /nobreak >nul
goto WAIT_FOR_API_LOOP

:API_TIMEOUT
echo [ERROR] Backend did not respond at http://127.0.0.1:8000/api/health
echo Review the "Quiz Online - Backend" window for the exact error.
pause
exit /b 1

:API_READY
echo [OK] FastAPI backend is responding.

echo [INFO] Starting React frontend...
start "Quiz Online - Frontend" cmd /k call "%~dp0run-frontend.bat"

echo [INFO] Waiting for the application...
timeout /t 5 /nobreak >nul
start "" "http://localhost:5173"

echo.
echo ========================================================
echo  Application started successfully.
echo  Frontend:  http://localhost:5173
echo  API Docs:  http://localhost:8000/docs
echo ========================================================
echo.
echo You may close this launcher window.
timeout /t 8 /nobreak >nul
endlocal
