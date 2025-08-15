@echo off
setlocal enabledelayedexpansion

echo ========================================
echo    Building Standalone Executable
echo ========================================
echo.

REM Check if running as administrator (recommended for better security)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as Administrator (recommended)
) else (
    echo ⚠️  Not running as Administrator - consider running as admin for better security
)
echo.

REM Check Windows Defender status
echo Checking Windows Defender status...
powershell -Command "Get-MpComputerStatus | Select-Object RealTimeProtectionEnabled, BehaviorMonitorEnabled, OnAccessProtectionEnabled | Format-Table" 2>nul
echo.

REM Install PyInstaller with specific version for stability
echo Installing PyInstaller...
pip install pyinstaller==5.13.2

echo.
echo Building executable with security optimizations...
echo.

REM Create a temporary spec file for better control
echo Creating optimized build configuration...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo block_cipher = None
echo a = Analysis(
echo     ['src\\main.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[('admins.txt', '.'), ('config.txt', '.')],
echo     hiddenimports=[],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=['matplotlib', 'numpy', 'scipy', 'PIL', 'cv2', 'sklearn'],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher^)
echo exe = EXE(
echo     pyz,
echo     a.scripts,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     [],
echo     name='EVE_Giveaway_Tool',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=False,
echo     upx_exclude=[],
echo     runtime_tmpdir=None,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon=None,
echo     version_file=None,
echo     uac_admin=False,
echo     uac_uiaccess=False,
echo     hookspath=[],
echo     runtime_hooks=[],
echo     exclude_binaries=False,
echo     name_suffix=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo ^)
) > build_config.spec

REM Build using the spec file
pyinstaller build_config.spec

REM Clean up temporary files
del build_config.spec

echo.
echo ========================================
echo           Build Complete!
echo ========================================
echo.

REM Verify the executable was created
if exist "dist\EVE_Giveaway_Tool.exe" (
    echo ✅ Executable created successfully
    echo.
    echo Copying configuration files to dist folder...
    copy admins.txt dist\ 2>nul
    copy config.txt dist\ 2>nul
    
    REM Get file size and creation info
    for %%F in ("dist\EVE_Giveaway_Tool.exe") do (
        echo 📁 File: %%~nxF
        echo 📏 Size: %%~zF bytes
        echo 🕒 Created: %%~tF
    )
    
    echo.
    echo 🔒 Security Recommendations:
    echo • Add the dist folder to Windows Defender exclusions if needed
    echo • Consider code signing the executable for production use
    echo • Test the executable in a sandbox environment first
    echo.
    echo 📋 Next Steps:
    echo 1. Copy the .exe file anywhere
    echo 2. Make sure admins.txt and config.txt are in the same folder as the .exe
    echo 3. Edit config.txt to customize EVE logs path and other settings
    echo 4. Double-click to run
    echo 5. No Python installation needed!
    echo.
    echo 💡 If Windows Defender flags the file:
    echo • Check the file in VirusTotal.com
    echo • Add the folder to Windows Defender exclusions
    echo • Consider running as Administrator during build
    echo.
) else (
    echo ❌ Build failed - executable not found
    echo Check the build output above for errors
)

echo.
pause
