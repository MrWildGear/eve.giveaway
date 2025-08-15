@echo off
echo ========================================
echo    EVE Giveaway Tool - Auto Installer
echo ========================================
echo.

echo Checking if Python is installed...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Installing Python 3.11...
    echo.
    echo Installing Python via winget...
    winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install Python via winget.
        echo Please install Python manually from: https://python.org
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Python installed successfully!
    echo Please restart this installer to continue.
    echo.
    pause
    exit /b 0
) else (
    echo Python is already installed!
    python --version
)

echo.
echo Checking if pip is available...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip not found. Please reinstall Python.
    pause
    exit /b 1
)

echo.
echo Installing required Python packages...
echo Installing watchdog and other dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install required packages.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo ========================================
echo           Setup Complete!
echo ========================================
echo.
echo Python and all dependencies installed successfully!
echo.
echo Next steps:
echo 1. Copy admins.template.txt to admins.txt
echo 2. Edit admins.txt with your admin usernames
echo 3. Run the tool with: python main.py
echo    or double-click run.bat
echo.
echo Enjoy your EVE Giveaway Tool! 🎮
echo.
pause
