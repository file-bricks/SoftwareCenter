@echo off
setlocal
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PROJECT_ROOT=%CD%"
set "BUILD_ROOT=C:\_Local_DEV\codex_build\softwarecenter"
set "SCANNER="
if defined SOFTWARE_ROOT set "SCANNER=%SOFTWARE_ROOT%\_tools\build_exclude_scanner.py"
if not defined SCANNER if defined OneDrive set "SCANNER=%OneDrive%\.TOPICS\.SOFTWARE\_tools\build_exclude_scanner.py"
set "APP_VERSION="

for /f "usebackq delims=" %%V in (`python "%PROJECT_ROOT%\scripts\project_version.py" "%PROJECT_ROOT%\pyproject.toml"`) do set "APP_VERSION=%%V"
if not defined APP_VERSION (
    echo [FEHLER] project.version konnte nicht aus pyproject.toml gelesen werden.
    exit /b 1
)
set "RELEASE_DIR=%PROJECT_ROOT%\releases\v%APP_VERSION%"

python --version >nul 2>&1
if errorlevel 1 (
    echo [FEHLER] Python nicht gefunden!
    pause
    exit /b 1
)

echo Baue SoftwareCenter.exe...
if not exist "%BUILD_ROOT%" mkdir "%BUILD_ROOT%"

set "EXCLUDES="
if not defined SCANNER (
    echo [WARNUNG] Build-Exclude-Scanner nicht gefunden. SOFTWARE_ROOT oder OneDrive pruefen.
) else if exist "%SCANNER%" (
    for /f "delims=" %%E in ('python "%SCANNER%" --project "%PROJECT_ROOT%" --emit pyinstaller') do set "EXCLUDES=%%E"
) else (
    echo [WARNUNG] Build-Exclude-Scanner nicht gefunden. SOFTWARE_ROOT oder OneDrive pruefen.
)

python -m PyInstaller --noconfirm --clean --windowed --onefile ^
  --name SoftwareCenter ^
  --icon "%PROJECT_ROOT%\icon.ico" ^
  --add-data "%PROJECT_ROOT%\icon.ico;." ^
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
    if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"
    copy /Y "%BUILD_ROOT%\dist\SoftwareCenter.exe" "%RELEASE_DIR%\SoftwareCenter-%APP_VERSION%-win64.exe" >nul
)
echo Fertig: dist\SoftwareCenter.exe
