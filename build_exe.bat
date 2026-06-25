@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PROJECT_ROOT=%CD%"
set "BUILD_ROOT=C:\_Local_DEV\codex_build\softwarecenter"
set "SCANNER=%PROJECT_ROOT%\..\..\_tools\build_exclude_scanner.py"

python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)

echo Baue SoftwareCenter.exe...
if not exist "%BUILD_ROOT%" mkdir "%BUILD_ROOT%"

set "EXCLUDES="
if exist "%SCANNER%" (
    for /f "delims=" %%E in ('python "%SCANNER%" --project "%PROJECT_ROOT%" --emit pyinstaller') do set "EXCLUDES=%%E"
) else (
    echo [WARNUNG] Build-Exclude-Scanner nicht gefunden: "%SCANNER%"
)

python -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name SoftwareCenter ^
  --icon "%PROJECT_ROOT%\icon.ico" ^
  %EXCLUDES% ^
  --distpath "%BUILD_ROOT%\dist" ^
  --workpath "%BUILD_ROOT%\build" ^
  --specpath "%BUILD_ROOT%" ^
  "%PROJECT_ROOT%\SoftwareCenter.py"
if errorlevel 1 (
    pause
    exit /b 1
)
if not exist "dist" mkdir "dist"
if exist "%BUILD_ROOT%\dist\SoftwareCenter.exe" (
    copy /Y "%BUILD_ROOT%\dist\SoftwareCenter.exe" "dist\SoftwareCenter.exe" >nul
    copy /Y "%BUILD_ROOT%\dist\SoftwareCenter.exe" "SoftwareCenter.exe" >nul
    if exist "releases\v1.0.0" copy /Y "%BUILD_ROOT%\dist\SoftwareCenter.exe" "releases\v1.0.0\SoftwareCenter-1.0.0-win64.exe" >nul
)
echo Fertig: dist\SoftwareCenter.exe
