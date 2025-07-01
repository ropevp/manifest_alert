@echo off
REM =============================================================================
REM Manifest Alert System - Auto Update Script
REM This script updates the local repository to the latest version from GitHub
REM =============================================================================

echo.
echo ========================================
echo  Manifest Alert System - Auto Update
echo ========================================
echo.

REM Change to the script's directory (where the batch file is located)
cd /d "%~dp0"

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

echo Step 1: Checking repository status...
git status --porcelain > temp_status.txt
set /p STATUS=<temp_status.txt
del temp_status.txt

if not "%STATUS%"=="" (
    echo.
    echo WARNING: You have local changes that will be preserved.
    echo Your changes will be temporarily saved during the update.
    echo.
    echo Saving local changes...
    git stash push -m "Auto-saved before update on %date% %time%"
    if errorlevel 1 (
        echo ERROR: Failed to save local changes.
        pause
        exit /b 1
    )
    set STASHED=1
) else (
    echo No local changes detected.
    set STASHED=0
)

echo.
echo Step 2: Fetching latest changes from GitHub...
git fetch origin
if errorlevel 1 (
    echo ERROR: Failed to fetch from GitHub. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo Step 3: Updating to latest version...
git pull origin main
if errorlevel 1 (
    echo ERROR: Failed to pull latest changes.
    if %STASHED%==1 (
        echo Restoring your local changes...
        git stash pop
    )
    pause
    exit /b 1
)

echo.
echo Step 4: Installing/updating Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo WARNING: Failed to install some dependencies.
    echo You may need to install them manually:
    echo   pip install -r requirements.txt
    echo.
)

REM Restore local changes if they were stashed
if %STASHED%==1 (
    echo.
    echo Step 5: Restoring your local changes...
    git stash pop
    if errorlevel 1 (
        echo WARNING: There may be conflicts with your local changes.
        echo Please review and resolve any conflicts manually.
        echo Your changes are still saved in git stash if needed.
    )
)

echo.
echo ========================================
echo  UPDATE COMPLETED SUCCESSFULLY!
echo ========================================
echo.
echo What's new in this version:
echo - Ultra-fast acknowledgment sync (0.5s during alerts)
echo - Enhanced user accountability with custom names
echo - Professional taskbar and system tray icons
echo - Window stability improvements
echo - Complete dependencies list
echo.
echo You can now run the application with: python main.py
echo.
echo Press any key to exit...
pause >nul
