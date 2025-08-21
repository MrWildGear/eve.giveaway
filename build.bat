@echo off
echo 🚀 EVE Giveaway Tool - Build Script Launcher
echo =============================================
echo.

REM Check if we're in the right directory
if not exist "src\main.py" (
    echo ❌ Error: src\main.py not found!
    echo Please run this script from the project root directory.
    echo.
    pause
    exit /b 1
)

echo ✅ Project structure verified
echo.

REM Check if simple build script exists
if not exist "build_simple.bat" (
    echo ❌ Error: build_simple.bat not found!
    echo Please ensure the build script exists.
    echo.
    pause
    exit /b 1
)

echo 🔨 Launching simple build script...
echo.

REM Run the simple build script
call build_simple.bat

echo.
echo 🎯 Build process completed!
echo Check the output above for any errors or success messages.
echo.
pause
