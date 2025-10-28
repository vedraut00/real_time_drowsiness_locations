@echo off
echo ========================================
echo   Hybrid Drowsiness Detection System
echo ========================================
echo.
echo Choose your detection mode:
echo 1. PC Mode - High performance with OpenCV window
echo 2. Web Mode - Browser-based detection
echo.
echo Starting hybrid system...
echo Access the dashboard at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
call venv_gpu\Scripts\activate.bat
python hybrid_detector.py

pause