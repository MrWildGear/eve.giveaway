@echo off
echo ========================================
echo    EVE Giveaway Tool - Complete Setup
echo ========================================
echo.

echo This script will:
echo 1. Install Python (if needed)
echo 2. Install required packages
echo 3. Set up admin configuration
echo 4. Create necessary files
echo.

set /p choice="Continue with setup? (Y/N): "
if /i "%choice%" neq "Y" (
    echo Setup cancelled.
    pause
    exit /b 0
)

echo.
echo ========================================
echo           Step 1: Python Check
echo ========================================

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
    echo Please restart this setup script to continue.
    echo.
    pause
    exit /b 0
) else (
    echo Python is already installed!
    python --version
)

echo.
echo ========================================
echo           Step 2: Dependencies
echo ========================================

echo Installing required Python packages...
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
echo           Step 3: Admin Setup
echo ========================================

if not exist "admins.txt" (
    echo Creating admin configuration file...
    copy "admins.template.txt" "admins.txt" >nul
    echo.
    echo IMPORTANT: Please edit admins.txt with your admin usernames!
    echo.
    echo Opening admins.txt for editing...
    notepad "admins.txt"
) else (
    echo Admin configuration file already exists.
)

echo.
echo ========================================
echo           Step 4: Verification
echo ========================================

echo Checking project files...
if exist "main.py" echo ✓ main.py found
if exist "requirements.txt" echo ✓ requirements.txt found
if exist "admins.txt" echo ✓ admins.txt found
if exist "run.bat" echo ✓ run.bat found

echo.
echo ========================================
echo           Setup Complete!
echo ========================================
echo.
echo Your EVE Giveaway Tool is ready to use!
echo.
echo Quick Start:
echo 1. Make sure EVE Online is running with chat logging enabled
echo 2. Double-click run.bat to start the tool
echo 3. Use !PIR 1-100 or !GTN 1-1000 in EVE chat to start games
echo.
echo For help, see README.md
echo.
echo Enjoy! 🎮
echo.
pause
