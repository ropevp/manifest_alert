@echo off
setlocal enabledelayedexpansion

echo.
echo ================================================
echo  Manifest Alert System V2 - One-Click Installer
echo ================================================
echo.

REM Get current directory
set "CURRENT_DIR=%cd%"

REM Check if we're in a git repository
if exist ".git" (
    echo Existing installation detected - updating...
    echo.
    
    echo Fetching latest changes from GitHub...
    git fetch origin main
    if errorlevel 1 (
        echo ERROR: Failed to fetch from repository
        pause
        exit /b 1
    )
    
    echo Resetting to latest version...
    git reset --hard origin/main
    if errorlevel 1 (
        echo ERROR: Failed to reset to latest version
        pause
        exit /b 1
    )
    
    echo.
    echo Update completed successfully!
    echo.
) else (
    echo Fresh installation - cloning repository...
    echo.
    
    REM Check if we have any files (except this installer)
    set "FILE_COUNT=0"
    for %%f in (*) do (
        if not "%%f"=="INSTALL.bat" (
            set /a FILE_COUNT+=1
        )
    )
    
    if !FILE_COUNT! gtr 0 (
        echo ERROR: This directory is not empty. Please run INSTALL.bat in an empty directory.
        echo Current directory: %CURRENT_DIR%
        pause
        exit /b 1
    )
    
    echo Cloning from GitHub...
    git clone https://github.com/e10120323/manifest_alerts.git .
    if errorlevel 1 (
        echo ERROR: Failed to clone repository
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    
    echo.
    echo Repository cloned successfully!
    echo.
)

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

echo Setting up virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo Installing/updating dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip
    pause
    exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Installing shortcuts...
.venv\Scripts\python.exe install_shortcuts.py --silent
if errorlevel 1 (
    echo WARNING: Shortcut installation failed (continuing...)
) else (
    echo Desktop and Start Menu shortcuts created.
)

echo.
echo ================================================
echo Installation completed successfully!
echo ================================================
echo.
echo Next steps:
echo 1. Double-click the 'Manifest Alert System' desktop shortcut
echo 2. Or run: launch_manifest_alerts.bat
echo 3. Or launch silently: launch_manifest_alerts_silent.bat
echo.
echo For configuration, see: USER_INSTRUCTIONS.md
echo.
pause
