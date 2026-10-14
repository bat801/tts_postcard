@echo off
setlocal
cd /d "%~dp0"

REM ============================================================
REM  Voice Postcard - Run Application (Silero TTS)
REM  ASCII-only, no BOM, no chcp
REM ============================================================

echo.
echo ============================================================
echo  VOICE POSTCARD - RUN
echo ============================================================
echo.

REM --- Check project files ---
if not exist "main.py" (
    echo [ERROR] main.py not found in %CD%
    echo Run setup.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] venv not found. Run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM --- Activate venv ---
echo [1/2] Activating venv...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate venv.
    pause
    exit /b 1
)

REM --- Verify python in venv ---
where python | findstr /i "venv" >nul
if errorlevel 1 (
    echo [ERROR] Python not in venv after activation.
    pause
    exit /b 1
)
echo     OK.

REM --- Run application with logging ---
echo.
echo [2/2] Starting main.py...
echo [INFO] Output logged to run.log
echo ------------------------------------------------------------
echo.

python main.py

echo.
echo ------------------------------------------------------------
echo Application finished.
pause
endlocal