@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PROJECT_ROOT=%CD%"
set "BUILD_ROOT=C:\_Local_DEV\codex_build\launchboards"
set "SCANNER=%PROJECT_ROOT%\..\..\_tools\build_exclude_scanner.py"

echo Baue LaunchBoards.exe...
if not exist "%BUILD_ROOT%" mkdir "%BUILD_ROOT%"
set "EXCLUDES="
if exist "%SCANNER%" (
    for /f "delims=" %%E in ('python "%SCANNER%" --project "%PROJECT_ROOT%" --emit pyinstaller') do set "EXCLUDES=%%E"
)
python -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name LaunchBoards ^
  --icon "%PROJECT_ROOT%\launchboards.ico" ^
  --add-data "%PROJECT_ROOT%\launchboards.ico;." ^
  --add-data "%PROJECT_ROOT%\icon.ico;." ^
  %EXCLUDES% ^
  --distpath "%BUILD_ROOT%\dist" ^
  --workpath "%BUILD_ROOT%\build" ^
  --specpath "%BUILD_ROOT%" ^
  "%PROJECT_ROOT%\launchboards.py"
if errorlevel 1 ( exit /b 1 )
if not exist "dist" mkdir "dist"
copy /Y "%BUILD_ROOT%\dist\LaunchBoards.exe" "dist\LaunchBoards.exe" >nul
copy /Y "%BUILD_ROOT%\dist\LaunchBoards.exe" "LaunchBoards.exe" >nul
if exist "releases\v1.0.0" copy /Y "%BUILD_ROOT%\dist\LaunchBoards.exe" "releases\v1.0.0\LaunchBoards-1.0.0-win64.exe" >nul
echo Fertig: dist\LaunchBoards.exe
