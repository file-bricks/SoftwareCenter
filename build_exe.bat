@echo off
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)
echo Baue SoftwareCenter.exe...
powershell -NoProfile -Command "Get-ChildItem -LiteralPath 'build','dist' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force"
python -m PyInstaller --noconfirm SoftwareCenter.spec
if errorlevel 1 (
    pause
    exit /b 1
)
if exist "dist\SoftwareCenter.exe" copy /Y "dist\SoftwareCenter.exe" "SoftwareCenter.exe" >nul
echo Fertig: dist\SoftwareCenter.exe
