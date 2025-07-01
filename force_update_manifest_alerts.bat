@echo off
REM =============================================================================
REM Manifest Alert System - Force Update Script (Clean Overwrite)
REM This script forces update to match GitHub exactly, discarding local changes
REM =============================================================================

echo.
echo =============================================
echo  Manifest Alert System - FORCE UPDATE
echo =============================================
echo.
echo WARNING: This will overwrite ALL local changes!
echo Your local modifications will be PERMANENTLY LOST!
echo.
echo Press Ctrl+C to cancel, or any other key to continue...
pause >nul

REM Change to the script's directory
cd /d "%~dp0"

echo.
echo Current directory: %CD%
echo.

REM Check if this is a git repository
if not exist ".git" (
    echo ERROR: This doesn't appear to be a git repository!
    echo Please place this batch file in the root of your manifest_alerts folder.
    echo.
    pause
    exit /b 1
)

echo Step 1: Fetching latest changes from GitHub...
git fetch origin
if errorlevel 1 (
    echo ERROR: Failed to fetch from GitHub. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo Step 2: Force updating to match GitHub exactly...
git reset --hard origin/main
if errorlevel 1 (
    echo ERROR: Failed to reset to latest version.
    pause
    exit /b 1
)

echo.
echo Step 3: Cleaning up any untracked files...
git clean -fd

echo.
echo Step 4: Installing/updating Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Failed to install some dependencies.
    echo You may need to install them manually:
    echo   pip install -r requirements.txt
    echo.
)

echo.
echo ========================================
echo  FORCE UPDATE COMPLETED!
echo ========================================
echo.
echo Your installation now exactly matches GitHub.
echo You can run the application with: python main.py
echo.
echo Press any key to exit...
pause >nul
