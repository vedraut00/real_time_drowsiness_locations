@echo off
echo ========================================
echo Complete CUDA Setup for RTX 3070 Ti
echo ========================================

echo.
echo Detected GPU: RTX 3070 Ti
echo CUDA Version: 12.8
echo Driver Version: 571.96

echo.
echo Step 1: Installing cuDNN from your download...
set "CUDNN_PATH=C:\Users\gorakh\Downloads\cudnn-windows-x86_64-8.9.6.50_cuda11-archive"

if exist "%CUDNN_PATH%" (
    echo Found cuDNN archive at: %CUDNN_PATH%
    
    echo Extracting cuDNN to CUDA directory...
    set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
    
    if exist "%CUDA_PATH%" (
        echo Copying cuDNN files to CUDA installation...
        xcopy "%CUDNN_PATH%\bin\*" "%CUDA_PATH%\bin\" /Y /I
        xcopy "%CUDNN_PATH%\include\*" "%CUDA_PATH%\include\" /Y /I
        xcopy "%CUDNN_PATH%\lib\*" "%CUDA_PATH%\lib\" /Y /I /S
        echo cuDNN installed successfully!
    ) else (
        echo ERROR: CUDA installation not found at %CUDA_PATH%
        echo Please install CUDA Toolkit 12.8 first
        pause
        exit /b 1
    )
) else (
    echo ERROR: cuDNN archive not found at %CUDNN_PATH%
    echo Please download cuDNN and place it there, or update the path
    pause
    exit /b 1
)

echo.
echo Step 2: Setting up Python environment...
if exist venv_gpu (
    echo Removing old virtual environment...
    rmdir /s /q venv_gpu
)

echo Creating fresh virtual environment...
python -m venv venv_gpu
call venv_gpu\Scripts\activate.bat

echo.
echo Step 3: Installing CUDA-compatible PyTorch...
python -m pip install --upgrade pip

echo Installing PyTorch with CUDA 12.1 (compatible with CUDA 12.8)...
pip install torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121 --extra-index-url https://download.pytorch.org/whl/cu121

echo.
echo Step 4: Installing other dependencies...
pip install "numpy>=1.21.0,<2.0.0"
pip install ultralytics>=8.0.196
pip install opencv-contrib-python>=4.8.0
pip install mediapipe>=0.10.13
pip install PyQt5>=5.15.10
pip install pillow>=10.0.0 matplotlib>=3.7.0 pandas>=2.0.0 scipy>=1.11.0
pip install pyyaml>=6.0.0 requests>=2.31.0 tqdm>=4.66.0
pip install sounddevice>=0.4.6 psutil>=5.9.0

echo.
echo Step 5: Testing CUDA installation...
python -c "import torch; print(f'PyTorch Version: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}'); print(f'GPU Name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}'); print(f'GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB' if torch.cuda.is_available() else 'N/A')"

echo.
echo Step 6: Testing all imports...
python -c "import cv2, mediapipe, ultralytics, PyQt5; print('✅ All imports successful!')"

echo.
echo Step 7: Running GPU performance test...
python quick_cuda_test.py

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Your RTX 3070 Ti is now ready for GPU-accelerated drowsiness detection!
echo.
echo To run the detector:
echo 1. venv_gpu\Scripts\activate.bat
echo 2. python DrowsinessDetector_Universal.py
echo.
pause