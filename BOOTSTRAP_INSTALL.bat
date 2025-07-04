@echo off
echo.
echo ================================================
echo  Manifest Alert System V2 - Bootstrap Installer
echo ================================================
echo.
echo This will install Manifest Alert System to: C:\ManifestAlerts
echo.
pause

REM Create installation directory on C: drive
if not exist "C:\ManifestAlerts" (
    echo Creating installation directory...
    mkdir "C:\ManifestAlerts"
    if errorlevel 1 (
        echo ERROR: Cannot create C:\ManifestAlerts directory
        echo Please run as Administrator or check permissions
        pause
        exit /b 1
    )
) else (
    echo Installation directory already exists.
)

REM Navigate to installation directory
cd /d "C:\ManifestAlerts"

REM Download the main installer
echo.
echo Downloading installer from GitHub...
curl -o INSTALL.bat https://raw.githubusercontent.com/e10120323/manifest_alerts/main/INSTALL.bat
if errorlevel 1 (
    echo ERROR: Failed to download installer
    echo Please check your internet connection
    pause
    exit /b 1
)

REM Run the main installer
echo.
echo Running main installer...
echo.
INSTALL.bat

echo.
echo Bootstrap installation completed!
echo Installation location: C:\ManifestAlerts
echo.
pause
