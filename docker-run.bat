@echo off
echo ========================================
echo  Drowsiness Detection - Docker Launcher
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Building Docker image...
docker-compose build

if %errorlevel% neq 0 (
    echo [ERROR] Failed to build Docker image!
    pause
    exit /b 1
)

echo.
echo [2/3] Starting container...
docker-compose up -d

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start container!
    pause
    exit /b 1
)

echo.
echo [3/3] Container started successfully!
echo.
echo ========================================
echo  Access the application at:
echo  http://localhost:5000
echo ========================================
echo.
echo Commands:
echo  - View logs:    docker-compose logs -f
echo  - Stop:         docker-compose down
echo  - Restart:      docker-compose restart
echo.

REM Wait a moment for the service to start
timeout /t 3 /nobreak >nul

REM Open browser
start http://localhost:5000

echo Opening browser...
echo.
pause
