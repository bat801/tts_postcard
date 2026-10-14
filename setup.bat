@echo off
setlocal

REM ============================================================
REM  Voice Postcard - Automated Setup (Silero TTS)
REM  Run from project folder: D:\_OpenCodeProjects\tts_postcard
REM ============================================================

echo.
echo ============================================================
echo  VOICE POSTCARD - SETUP
echo ============================================================
echo.

REM --- Check we are in project folder ---
if not exist "main.py" (
    echo [ERROR] main.py not found.
    echo Run setup.bat from project folder: D:\_OpenCodeProjects\tts_postcard
    echo.
    pause
    exit /b 1
)

REM --- Check Python ---
echo [1/7] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PY_VER=%%i
echo     Found: %PY_VER%

REM --- Create venv ---
echo.
echo [2/7] Creating virtual environment (venv)...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo     venv created.
) else (
    echo     venv already exists, skipping.
)

REM --- Activate venv ---
echo.
echo [3/7] Activating venv...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

REM --- Verify python points to venv ---
echo.
echo [4/7] Verifying venv activation...
where python | findstr /i "venv" >nul
if errorlevel 1 (
    echo [ERROR] Python does NOT point to venv!
    echo Output of where python:
    where python
    echo.
    echo Run manually: venv\Scripts\activate.bat
    pause
    exit /b 1
)
echo     OK: Python inside venv.

REM --- Upgrade pip ---
echo.
echo [5/7] Upgrading pip...
python -m pip install --upgrade pip >nul
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing...
) else (
    echo     pip upgraded.
)

REM --- Install torch + torchaudio (CPU) ---
echo.
echo [6/7] Installing PyTorch and Torchaudio (CPU)...
echo     This may take 1-3 minutes...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo [ERROR] Failed to install torch/torchaudio.
    echo Check internet connection.
    pause
    exit /b 1
)
echo     torch + torchaudio installed.

REM --- Install other dependencies ---
echo.
echo [7/7] Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo     Dependencies installed.

echo.
echo ============================================================
echo  SETUP COMPLETE!
echo ============================================================
echo.
echo To run the application:
echo   1. Double-click run.bat
echo   OR in terminal:
echo      venv\Scripts\activate.bat
echo      python main.py
echo.
echo Model cache folder: .cache\torch\
echo Output WAV folder: output\
echo.
pause
endlocal