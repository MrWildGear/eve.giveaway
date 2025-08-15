@echo off
echo ========================================
echo    Creating Share Folder
echo ========================================
echo.

echo Creating "EVE Giveaway Tool" folder...
if exist "EVE Giveaway Tool" (
    echo Removing existing folder...
    rmdir /s /q "EVE Giveaway Tool"
)

mkdir "EVE Giveaway Tool"

echo.
echo Copying files from dist folder...
copy "dist\EVE_Giveaway_Tool.exe" "EVE Giveaway Tool\"
copy "dist\admins.txt" "EVE Giveaway Tool\"
copy "dist\admins.template.txt" "EVE Giveaway Tool\"

echo.
echo Copying additional documentation...
copy "README.md" "EVE Giveaway Tool\"
copy "LICENSE" "EVE Giveaway Tool\"

echo.
echo ========================================
echo           Share Folder Ready!
echo ========================================
echo.
echo Your share folder "EVE Giveaway Tool" contains:
echo.
echo 📁 EVE Giveaway Tool/
echo ├── EVE_Giveaway_Tool.exe    # Standalone app
echo ├── admins.txt                # Admin configuration
echo ├── admins.template.txt       # Setup template
echo ├── README.md                 # Documentation
echo └── LICENSE                   # License info
echo.
echo You can now:
echo 1. Zip the "EVE Giveaway Tool" folder
echo 2. Share it with other users
echo 3. They can extract and run immediately!
echo.
pause
