@echo off
echo 🤖 Setting up Telegram Bot for Drowsiness Detection...
echo.

REM Activate virtual environment
call venv_gpu\Scripts\activate.bat

REM Run setup
python setup_telegram.py

echo.
echo Setup complete! You can now run DrowsinessDetector_Universal.py
pause