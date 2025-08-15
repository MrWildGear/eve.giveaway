@echo off
echo ========================================
echo    Building Standalone Executable
echo ========================================
echo.

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed --name "EVE_Giveaway_Tool" --icon=NONE --add-data "admins.txt;." src\main.py

echo.
echo ========================================
echo           Build Complete!
echo ========================================
echo.
echo Copying admins.txt to dist folder...
copy admins.txt dist\
echo.
echo Your executable is in the 'dist' folder:
echo dist\EVE_Giveaway_Tool.exe
echo.
echo You can now:
echo 1. Copy the .exe file anywhere
echo 2. Make sure admins.txt is in the same folder as the .exe
echo 3. Double-click to run
echo 4. No Python installation needed!
echo.
pause
