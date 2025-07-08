@echo off
REM Silent Manifest Alert System Launcher
REM This launches the application using the virtual environment Python WITHOUT console window

REM Change to the script directory
cd /d "%~dp0"

REM Launch using pythonw.exe (windowless Python) to avoid console window entirely
start "" "%~dp0\.venv\Scripts\pythonw.exe" main.py
