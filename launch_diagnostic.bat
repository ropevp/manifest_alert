@echo off
REM Diagnostic Launcher for Manifest Alert System
REM This shows detailed information to help troubleshoot launch issues

echo ===================================================
echo Manifest Alert System - Diagnostic Launcher
echo ===================================================
echo.

echo Current Directory: %CD%
echo.

echo Checking for required files...
if exist "main.py" (
    echo ✅ main.py found
) else (
    echo ❌ main.py NOT found
    goto :error
)

if exist "requirements.txt" (
    echo ✅ requirements.txt found
) else (
    echo ❌ requirements.txt NOT found
)

if exist "resources\icon.ico" (
    echo ✅ icon.ico found
) else (
    echo ❌ icon.ico NOT found
)

if exist ".venv\Scripts\python.exe" (
    echo ✅ Virtual environment found
    set PYTHON_CMD=.venv\Scripts\python.exe
) else (
    echo ❌ Virtual environment NOT found - using system Python
    set PYTHON_CMD=python
)

echo.
echo Checking Python installation...
"%PYTHON_CMD%" --version
if %errorlevel% neq 0 (
    echo ❌ Python is not available
    goto :error
) else (
    echo ✅ Python is available
)

echo.
echo Checking Python modules...
"%PYTHON_CMD%" -c "import PyQt6; print('✅ PyQt6 available')" 2>nul || echo ❌ PyQt6 not available - run: %PYTHON_CMD% -m pip install -r requirements.txt

echo.
echo Attempting to launch application...
echo Press Ctrl+C to stop if it hangs
echo.

"%PYTHON_CMD%" main.py

echo.
echo Application exited with code: %errorlevel%
if %errorlevel% neq 0 (
    echo ❌ Application failed to start
    goto :error
) else (
    echo ✅ Application ran successfully
)

goto :end

:error
echo.
echo ===================================================
echo ❌ TROUBLESHOOTING HELP
echo ===================================================
echo.
echo Common solutions:
echo 1. Create virtual environment: python -m venv .venv
echo 2. Install dependencies: .venv\Scripts\pip install -r requirements.txt
echo 3. Check file locations - all files should be in same folder
echo 4. Run as Administrator if needed
echo.

:end
echo.
echo Press any key to exit...
pause >nul
