@echo off
title Drowsiness Detection System - RTX 3070 Ti Ready
color 0A

echo.
echo  ██████╗ ██████╗  ██████╗ ██╗    ██╗███████╗██╗███╗   ██╗███████╗███████╗███████╗
echo  ██╔══██╗██╔══██╗██╔═══██╗██║    ██║██╔════╝██║████╗  ██║██╔════╝██╔════╝██╔════╝
echo  ██║  ██║██████╔╝██║   ██║██║ █╗ ██║███████╗██║██╔██╗ ██║█████╗  ███████╗███████╗
echo  ██║  ██║██╔══██╗██║   ██║██║███╗██║╚════██║██║██║╚██╗██║██╔══╝  ╚════██║╚════██║
echo  ██████╔╝██║  ██║╚██████╔╝╚███╔███╔╝███████║██║██║ ╚████║███████╗███████║███████║
echo  ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ╚══╝╚══╝ ╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝╚══════╝
echo.
echo                    DETECTION SYSTEM - RTX 3070 Ti Optimized
echo.
echo ================================================================================

echo.
echo 🚀 System Status Check...

if exist venv_gpu (
    call venv_gpu\Scripts\activate.bat
    
    echo ✅ GPU Environment: Ready
    
    python -c "import torch; print('✅ CUDA Available:', torch.cuda.is_available()); print('🎮 GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')" 2>nul
    
    if errorlevel 1 (
        echo ❌ PyTorch/CUDA not properly configured
        echo.
        echo Choose an option:
        echo 1. Run CPU mode (works immediately)
        echo 2. Fix GPU setup
        echo 3. Exit
        echo.
        set /p choice="Enter choice (1-3): "
        
        if "!choice!"=="1" goto :cpu_mode
        if "!choice!"=="2" goto :fix_gpu
        if "!choice!"=="3" exit /b 0
        goto :cpu_mode
    )
    
    echo ✅ All systems ready!
    echo.
    echo Choose detection mode:
    echo.
    echo 🚀 1. GPU Mode (RTX 3070 Ti - Fastest)
    echo 💻 2. CPU Mode (Compatible)
    echo 🧪 3. Run Tests
    echo 🔧 4. System Info
    echo ❌ 5. Exit
    echo.
    set /p mode="Enter choice (1-5): "
    
    if "%mode%"=="1" goto :gpu_mode
    if "%mode%"=="2" goto :cpu_mode
    if "%mode%"=="3" goto :run_tests
    if "%mode%"=="4" goto :system_info
    if "%mode%"=="5" exit /b 0
    
    echo Invalid choice, starting GPU mode...
    goto :gpu_mode
    
) else (
    echo ⚠️  No GPU environment found
    echo.
    echo Choose setup option:
    echo 1. Quick CPU setup (immediate)
    echo 2. Full GPU setup (requires time)
    echo 3. Exit
    echo.
    set /p setup="Enter choice (1-3): "
    
    if "%setup%"=="1" goto :setup_cpu
    if "%setup%"=="2" goto :setup_gpu
    if "%setup%"=="3" exit /b 0
    goto :setup_cpu
)

:gpu_mode
echo.
echo 🚀 Starting GPU-Accelerated Drowsiness Detection...
echo 🎮 Using: RTX 3070 Ti
echo.
python DrowsinessDetector_Universal.py
goto :end

:cpu_mode
echo.
echo 💻 Starting CPU Drowsiness Detection...
echo.
python DrowsinessDetector_Universal.py
goto :end

:run_tests
echo.
echo 🧪 Running System Tests...
echo.
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
pause
goto :end

:system_info
echo.
echo 🔍 System Information:
echo.
python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
pause
goto :end

:setup_cpu
echo.
echo 💻 Setting up CPU environment...
python -m venv venv
call venv\Scripts\activate.bat
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics opencv-contrib-python mediapipe PyQt5 numpy pillow matplotlib pandas scipy pyyaml requests tqdm sounddevice psutil
echo ✅ CPU setup complete!
pause
goto :cpu_mode

:setup_gpu
echo.
echo 🚀 Starting full GPU setup...
echo This will install CUDA-enabled PyTorch and configure your RTX 3070 Ti
pause
call install_cuda_complete.bat
goto :end

:fix_gpu
echo.
echo 🔧 Fixing GPU configuration...
pip install torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121 --force-reinstall
pip install "numpy>=1.21.0,<2.0.0" --force-reinstall
echo ✅ GPU fix complete!
pause
goto :gpu_mode

:end
echo.
echo 👋 Thanks for using Drowsiness Detection System!
pause