@echo off
echo.
echo ================================================
echo  Manifest Alert System V2 - Bootstrap Installer
echo ================================================
echo.
echo This will install Manifest Alert System to: C:\ManifestAlerts
echo.
pause

REM Download the main installer to current directory
echo.
echo Downloading installer from GitHub...
curl -o INSTALL.bat https://raw.githubusercontent.com/ropevp/manifest_alert/main/INSTALL.bat
if errorlevel 1 (
    echo ERROR: Failed to download installer
    echo Please check your internet connection
    pause
    exit /b 1
)

REM Run the main installer (it will handle creating C:\ManifestAlerts)
echo.
echo Running main installer...
echo.
INSTALL.bat

echo.
echo Bootstrap installation completed!
echo Installation location: C:\ManifestAlerts
echo.
pause
