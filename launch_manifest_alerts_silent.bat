@echo off
REM Silent Manifest Alert System Launcher
REM This launches the application using the virtual environment Python

REM Change to the script directory
cd /d "%~dp0"

REM Launch using the virtual environment Python with minimized window
start "" /min cmd /c ""%~dp0\.venv\Scripts\python.exe" main.py"
