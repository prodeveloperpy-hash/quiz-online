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
    echo [SETUP] Creating Python virtual environment...
    where python >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Python is not installed. Install Python 3.11 or newer first.
        pause
        exit /b 1
    )
    python -m venv "backend\.venv"
    if errorlevel 1 goto DEPENDENCY_ERROR
    echo [SETUP] Installing backend requirements...
    "backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
    if errorlevel 1 goto DEPENDENCY_ERROR
)

if not exist "frontend\node_modules" (
    echo [SETUP] Installing frontend packages...
    where npm.cmd >nul 2>nul
    if errorlevel 1 (
        echo [ERROR] Node.js is not installed. Install Node.js 20 or newer first.
        pause
        exit /b 1
    )
    pushd "frontend"
    call npm.cmd install
    if errorlevel 1 (
        popd
        goto DEPENDENCY_ERROR
    )
    popd
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
set "MYSQL_SHELL=C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe"
set "NEW_DATABASE=0"

if not exist "%MYSQL_SERVER%" (
    echo [ERROR] Local MySQL Server 8.4 was not found.
    echo Install MySQL Server and run this launcher again.
    pause
    exit /b 1
)

if not exist "%~dp0mysql-data\mysql" (
    echo [SETUP] Initializing the local MySQL data directory...
    "%MYSQL_SERVER%" --defaults-file="%~dp0mysql-local.ini" --initialize-insecure --console
    if errorlevel 1 goto DATABASE_SETUP_ERROR
    set "NEW_DATABASE=1"
)

if "%NEW_DATABASE%"=="1" (
    echo [INFO] Starting local MySQL Server...
    start "Quiz Online - MySQL" /min "%MYSQL_SERVER%" --defaults-file="%~dp0mysql-local.ini" --console
) else (
    "%MYSQL_CLIENT%" --protocol=TCP -h 127.0.0.1 -u quiz_user --password=quiz_password ping --silent >nul 2>nul
    if errorlevel 1 (
        echo [INFO] Starting local MySQL Server...
        start "Quiz Online - MySQL" /min "%MYSQL_SERVER%" --defaults-file="%~dp0mysql-local.ini" --console
    )
)

echo [INFO] Waiting for local MySQL...
set /a DB_TRIES=0
:WAIT_FOR_DB_LOOP
if "%NEW_DATABASE%"=="1" (
    "%MYSQL_CLIENT%" --protocol=TCP -h 127.0.0.1 -u root ping --silent >nul 2>nul
) else (
"%MYSQL_CLIENT%" --protocol=TCP -h 127.0.0.1 -u quiz_user --password=quiz_password ping --silent >nul 2>nul
)
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

if "%NEW_DATABASE%"=="1" (
    echo [SETUP] Creating the online_quiz database and application user...
    "%MYSQL_SHELL%" --protocol=TCP -h 127.0.0.1 -u root -e "CREATE DATABASE IF NOT EXISTS online_quiz CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; CREATE USER IF NOT EXISTS 'quiz_user'@'localhost' IDENTIFIED BY 'quiz_password'; GRANT ALL PRIVILEGES ON online_quiz.* TO 'quiz_user'@'localhost'; ALTER USER 'root'@'localhost' IDENTIFIED BY 'RootQuiz2026'; FLUSH PRIVILEGES;"
    if errorlevel 1 goto DATABASE_SETUP_ERROR
)

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

echo [INFO] Closing any previous Quiz Online processes...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"127.0.0.1:8000 .*LISTENING"') do taskkill /PID %%P /T /F >nul 2>nul
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"127.0.0.1:5173 .*LISTENING"') do taskkill /PID %%P /T /F >nul 2>nul
timeout /t 2 /nobreak >nul

echo [INFO] Starting FastAPI backend in this session...
start "" /b cmd /c call "%~dp0run-backend.bat"

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
start "" /b cmd /c call "%~dp0run-frontend.bat"

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
echo Keep this window open while using Quiz Online.
echo Press any key to stop the backend and frontend safely.
pause >nul

echo.
echo [INFO] Stopping Quiz Online services...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"127.0.0.1:8000 .*LISTENING"') do taskkill /PID %%P /T /F >nul 2>nul
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"127.0.0.1:5173 .*LISTENING"') do taskkill /PID %%P /T /F >nul 2>nul
echo [OK] Backend and frontend stopped.
timeout /t 2 /nobreak >nul
endlocal
exit /b 0

:DEPENDENCY_ERROR
echo.
echo [ERROR] Automatic dependency installation failed.
echo Check your internet connection and try again.
pause
exit /b 1

:DATABASE_SETUP_ERROR
echo.
echo [ERROR] Automatic MySQL database setup failed.
echo Review the MySQL error shown above.
pause
exit /b 1
