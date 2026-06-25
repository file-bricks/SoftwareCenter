@echo off
cd /d "%~dp0"
if exist "dist\SoftwareCenter.exe" (
    start "" "dist\SoftwareCenter.exe"
    exit /b 0
)
if exist "SoftwareCenter.exe" (
    start "" "SoftwareCenter.exe"
    exit /b 0
)
if exist "releases\v1.0.0\SoftwareCenter-1.0.0-win64.exe" (
    start "" "releases\v1.0.0\SoftwareCenter-1.0.0-win64.exe"
    exit /b 0
)
python "SoftwareCenter.py"
pause
