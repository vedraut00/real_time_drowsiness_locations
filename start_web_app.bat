@echo off
echo ========================================
echo   Drowsiness Detection Web Interface
echo ========================================
echo.
echo Starting web server...
echo Access the dashboard at: http://localhost:5000
echo Admin panel at: http://localhost:5000/admin
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
call venv_gpu\Scripts\activate.bat
python web_app.py

pause