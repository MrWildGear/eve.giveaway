@echo off
echo 🚀 EVE Giveaway Tool - Simple Build Script
echo ===========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

REM Check if PyInstaller is available
python -c "import PyInstaller" >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if %errorLevel% neq 0 (
        echo ❌ Failed to install PyInstaller!
        pause
        exit /b 1
    )
)

echo ✅ Python and PyInstaller ready
echo.

REM Clean previous builds
if exist "dist" (
    echo Cleaning previous build...
    rmdir /s /q dist
)
if exist "build" (
    echo Cleaning build cache...
    rmdir /s /q build
)
if exist "*.spec" (
    echo Cleaning spec files...
    del *.spec
)

echo.
echo 🔨 Building executable...
echo.

REM Build with PyInstaller
pyinstaller --onefile --windowed --name "EVE_Giveaway_Tool" --add-data "admins.txt;." --add-data "config.txt;." --exclude-module matplotlib --exclude-module numpy --exclude-module scipy --exclude-module PIL --exclude-module cv2 --exclude-module sklearn "src/main.py"

if %errorLevel% neq 0 (
    echo.
    echo ❌ Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ✅ Build completed successfully!
echo.

REM Copy config files to dist folder
if exist "dist\EVE_Giveaway_Tool.exe" (
    echo 📁 Copying configuration files...
    copy admins.txt dist\ >nul 2>&1
    copy config.txt dist\ >nul 2>&1
    
    echo.
    echo 📊 Build Summary:
    echo   • Executable: dist\EVE_Giveaway_Tool.exe
    echo   • Size: 
    for %%F in ("dist\EVE_Giveaway_Tool.exe") do echo     %%~zF bytes
    echo   • Created: 
    for %%F in ("dist\EVE_Giveaway_Tool.exe") do echo     %%~tF
    
    echo.
    echo 🎯 Ready to use! The executable is in the 'dist' folder.
    echo.
    echo 📋 Usage:
    echo   1. Copy the .exe file anywhere
    echo   2. Make sure admins.txt and config.txt are in the same folder
    echo   3. Edit config.txt to set your EVE logs path
    echo   4. Double-click to run
    echo   5. No Python installation needed!
    echo.
    echo 🔒 Security Note: If Windows Defender flags the file:
    echo   • This is normal for PyInstaller executables
    echo   • Add the folder to Windows Defender exclusions
    echo   • Or run the build as Administrator
    echo.
) else (
    echo ❌ Executable not found in dist folder!
)

echo.
pause
