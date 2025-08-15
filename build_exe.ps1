# EVE Giveaway Tool Build Script (PowerShell)
# Enhanced security and Windows Defender compatibility

param(
    [switch]$SkipChecks,
    [switch]$Verbose
)

# Set execution policy for this session only
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Building Standalone Executable" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($isAdmin) {
    Write-Host "✅ Running as Administrator (recommended)" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Not running as Administrator - consider running as admin for better security" -ForegroundColor Yellow
}
Write-Host ""

# Check Windows Defender status
if (-not $SkipChecks) {
    Write-Host "Checking Windows Defender status..." -ForegroundColor Blue
    try {
        $defenderStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
        if ($defenderStatus) {
            $statusTable = @{
                "Real-Time Protection" = if ($defenderStatus.RealTimeProtectionEnabled) { "✅ Enabled" } else { "❌ Disabled" }
                "Behavior Monitor"     = if ($defenderStatus.BehaviorMonitorEnabled) { "✅ Enabled" } else { "❌ Disabled" }
                "On-Access Protection" = if ($defenderStatus.OnAccessProtectionEnabled) { "✅ Enabled" } else { "❌ Disabled" }
            }
            
            foreach ($key in $statusTable.Keys) {
                $color = if ($statusTable[$key] -like "*✅*") { "Green" } else { "Red" }
                Write-Host "  $key`: $($statusTable[$key])" -ForegroundColor $color
            }
        }
    }
    catch {
        Write-Host "  ⚠️  Could not check Windows Defender status" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Check Python and pip availability
Write-Host "Checking Python environment..." -ForegroundColor Blue
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ $pythonVersion" -ForegroundColor Green
    
    $pipVersion = pip --version 2>&1
    Write-Host "  ✅ $pipVersion" -ForegroundColor Green
}
catch {
    Write-Host "  ❌ Python or pip not found in PATH" -ForegroundColor Red
    Write-Host "  Please ensure Python is installed and added to PATH" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Install PyInstaller with specific version for stability
Write-Host "Installing PyInstaller..." -ForegroundColor Blue
try {
    pip install pyinstaller==5.13.2
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ PyInstaller installed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Failed to install PyInstaller" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Error installing PyInstaller: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Create optimized build configuration
Write-Host "Creating optimized build configuration..." -ForegroundColor Blue
$specContent = @"
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('admins.txt', '.'), ('config.txt', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'PIL', 'cv2', 'sklearn', 'tkinter.test', 'test', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EVE_Giveaway_Tool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    version_file=None,
    uac_admin=False,
    uac_uiaccess=False,
    hookspath=[],
    runtime_hooks=[],
    exclude_binaries=False,
    name_suffix=None,
)
"@

$specContent | Out-File -FilePath "build_config.spec" -Encoding UTF8
Write-Host "  ✅ Build configuration created" -ForegroundColor Green
Write-Host ""

# Build the executable
Write-Host "Building executable with security optimizations..." -ForegroundColor Blue
try {
    pyinstaller build_config.spec
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Build completed successfully" -ForegroundColor Green
    }
    else {
        Write-Host "  ❌ Build failed" -ForegroundColor Red
        exit 1
    }
}
catch {
    Write-Host "  ❌ Error during build: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Clean up temporary files
Remove-Item "build_config.spec" -ErrorAction SilentlyContinue
Remove-Item "build" -Recurse -ErrorAction SilentlyContinue

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "           Build Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verify the executable was created
$exePath = "dist\EVE_Giveaway_Tool.exe"
if (Test-Path $exePath) {
    Write-Host "✅ Executable created successfully" -ForegroundColor Green
    Write-Host ""
    
    # Copy configuration files
    Write-Host "Copying configuration files to dist folder..." -ForegroundColor Blue
    try {
        Copy-Item "admins.txt" "dist\" -ErrorAction SilentlyContinue
        Copy-Item "config.txt" "dist\" -ErrorAction SilentlyContinue
        Write-Host "  ✅ Configuration files copied" -ForegroundColor Green
    }
    catch {
        Write-Host "  ⚠️  Some configuration files could not be copied" -ForegroundColor Yellow
    }
    
    # Get file information
    $fileInfo = Get-Item $exePath
    Write-Host ""
    Write-Host "📁 File: $($fileInfo.Name)" -ForegroundColor White
    Write-Host "📏 Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB ($($fileInfo.Length) bytes)" -ForegroundColor White
    Write-Host "🕒 Created: $($fileInfo.CreationTime)" -ForegroundColor White
    Write-Host "🔒 SHA256: $((Get-FileHash $exePath -Algorithm SHA256).Hash)" -ForegroundColor White
    
    Write-Host ""
    Write-Host "🔒 Security Recommendations:" -ForegroundColor Yellow
    Write-Host "  • Add the dist folder to Windows Defender exclusions if needed" -ForegroundColor White
    Write-Host "  • Consider code signing the executable for production use" -ForegroundColor White
    Write-Host "  • Test the executable in a sandbox environment first" -ForegroundColor White
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Copy the .exe file anywhere" -ForegroundColor White
    Write-Host "  2. Make sure admins.txt and config.txt are in the same folder as the .exe" -ForegroundColor White
    Write-Host "  3. Edit config.txt to customize EVE logs path and other settings" -ForegroundColor White
    Write-Host "  4. Double-click to run" -ForegroundColor White
    Write-Host "  5. No Python installation needed!" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 If Windows Defender flags the file:" -ForegroundColor Yellow
    Write-Host "  • Check the file in VirusTotal.com" -ForegroundColor White
    Write-Host "  • Add the folder to Windows Defender exclusions" -ForegroundColor White
    Write-Host "  • Consider running as Administrator during build" -ForegroundColor White
    Write-Host "  • Use the generated SHA256 hash to verify file integrity" -ForegroundColor White
    
}
else {
    Write-Host "❌ Build failed - executable not found" -ForegroundColor Red
    Write-Host "Check the build output above for errors" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
