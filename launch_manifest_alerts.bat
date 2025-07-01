@echo off
REM Manifest Alert System Launcher
REM This batch file launches the application with proper error handling

echo Starting Manifest Alert System...

REM Change to the script directory
cd /d "%~dp0"

REM Check if virtual environment Python exists
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    echo Please run: python -m venv .venv
    echo Then run: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "main.py" (
    echo ERROR: main.py not found in current directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Launch the application using virtual environment Python
echo Launching Manifest Alert System...
".venv\Scripts\python.exe" main.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)
