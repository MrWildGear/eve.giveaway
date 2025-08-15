@echo off
echo ========================================
echo    EVE Giveaway Tool - Diagnostics
echo ========================================
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)

echo.
echo Checking Python packages...
pip list | findstr watchdog
if %errorlevel% neq 0 (
    echo WARNING: watchdog package not found!
    echo Run: pip install -r requirements.txt
)

echo.
echo Checking tkinter availability...
python -c "import tkinter; print('✓ tkinter available')"
if %errorlevel% neq 0 (
    echo ERROR: tkinter not available!
    echo This usually means Python was installed without tkinter.
    echo Try reinstalling Python with 'Add to PATH' and 'tcl/tk and IDLE' options.
)

echo.
echo Checking system display...
echo Display settings:
wmic path Win32_VideoController get Name,VideoModeDescription /format:list | findstr "="

echo.
echo Checking Windows theme...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" /v AppsUseLightTheme 2>nul
if %errorlevel% neq 0 (
    echo Could not determine Windows theme setting
)

echo.
echo ========================================
echo           Test GUI Launch
echo ========================================
echo.
echo Attempting to launch a simple test window...
echo If you see a window, the issue is with the main application.
echo If you don't see a window, there's a system-level GUI issue.
echo.

python -c "import tkinter as tk; root = tk.Tk(); root.title('Test Window'); root.geometry('300x200'); root.configure(bg='red'); tk.Label(root, text='Test Window - Click to close', bg='red', fg='white').pack(expand=True); root.bind('<Button-1>', lambda e: root.destroy()); root.mainloop()"

echo.
echo Test completed. Check if you saw a red test window.
echo.
pause
