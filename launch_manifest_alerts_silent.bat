@echo off
REM Silent Manifest Alert System Launcher
REM This launches the application using the virtual environment Python without persistent console

REM Change to the script directory
cd /d "%~dp0"

REM Launch using the virtual environment Python directly (no console window)
start "" "%~dp0\.venv\Scripts\pythonw.exe" main.py
