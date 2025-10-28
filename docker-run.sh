#!/bin/bash

echo "========================================"
echo " Drowsiness Detection - Docker Launcher"
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running!"
    echo "Please start Docker and try again."
    exit 1
fi

echo "[1/3] Building Docker image..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to build Docker image!"
    exit 1
fi

echo ""
echo "[2/3] Starting container..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to start container!"
    exit 1
fi

echo ""
echo "[3/3] Container started successfully!"
echo ""
echo "========================================"
echo " Access the application at:"
echo " http://localhost:5000"
echo "========================================"
echo ""
echo "Commands:"
echo " - View logs:    docker-compose logs -f"
echo " - Stop:         docker-compose down"
echo " - Restart:      docker-compose restart"
echo ""

# Wait for service to start
sleep 3

# Try to open browser (works on most Linux systems)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5000
elif command -v open > /dev/null; then
    open http://localhost:5000
fi

echo "Opening browser..."
