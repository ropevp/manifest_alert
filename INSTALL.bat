@echo off
REM =================================================================
REM Manifest Alert System - ONE-CLICK INSTALLER & UPDATER
REM Use this file for both fresh installation and updates
REM Run this file in the folder where you want to install the application 
REM Running C:\INSTALL.bat C: will create the folder C:\manifest_alerts
REM =================================================================

echo.
echo ===============================================================
echo           MANIFEST ALERT SYSTEM - INSTALLER/UPDATER
echo ===============================================================
echo.

REM Check if this is an update (git folder exists) or fresh install
if exist ".git" (
    echo DETECTED: Existing installation - UPDATING...
    goto :update
) else (
    echo DETECTED: Fresh installation - INSTALLING...
    goto :install
)

:install
echo.
echo [1/4] Checking prerequisites...

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed
    echo Please install Git from: https://git-scm.com/download/win
    echo After installing Git, run this script again
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    echo Please install Python from: https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✅ Git and Python are available

echo.
echo [2/4] Downloading Manifest Alert System...
git clone https://github.com/ropevp/manifest_alert.git .
if %errorlevel% neq 0 (
    echo ERROR: Failed to download from GitHub
    echo Check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo [3/4] Setting up virtual environment and dependencies...
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [4/4] Creating desktop shortcut...
.venv\Scripts\python.exe install_shortcuts.py

echo.
echo ===============================================================
echo ✅ INSTALLATION COMPLETE!
echo ===============================================================
echo.
echo To launch Manifest Alert System:
echo   • Double-click desktop shortcut
echo   • Or press Windows key and type "Manifest Alert"
echo.
echo To update in the future: Run this same file again
echo.
goto :end

:update
echo.
echo [1/4] Backing up your settings...
if exist "data\config.json" (
    copy "data\config.json" "data\config.json.backup" >nul
    echo ✅ Settings backed up
) else (
    echo ℹ️  No existing settings found
)

echo.
echo [2/4] Downloading latest version...
git fetch origin
git reset --hard origin/3.00
if %errorlevel% neq 0 (
    echo ERROR: Failed to download updates
    echo Check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo [3/4] Updating dependencies...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\pip install -r requirements.txt
) else (
    echo Creating virtual environment...
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt
)

if exist "data\config.json.backup" (
    if not exist "data\config.json" (
        copy "data\config.json.backup" "data\config.json" >nul
        echo ✅ Settings restored
    )
)

echo.
echo [4/4] Updating desktop shortcuts...
.venv\Scripts\python.exe install_shortcuts.py

echo.
echo ===============================================================
echo ✅ UPDATE COMPLETE!
echo ===============================================================
echo.
echo Manifest Alert System has been updated to the latest version
echo Launch using your desktop shortcut or Start Menu
echo.

:end
echo Press any key to exit...
pause >nul
