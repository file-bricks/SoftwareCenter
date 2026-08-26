# SoftwareCenter / LaunchBoards product boundary

SoftwareCenter and LaunchBoards share the same Python implementation, but they
are separate desktop products. This contract prevents one product from taking
over the other's settings, single-instance endpoint, executable, Store
identity, or release artifact.

| Boundary | SoftwareCenter | LaunchBoards |
|---|---|---|
| Source entry point | `SoftwareCenter.py` | `launchboards.py` |
| Window/product name | `SoftwareCenter` | `LaunchBoards` |
| QSettings app namespace | `LukasGeiger/SoftwareCenter` | `LukasGeiger/LaunchBoards` |
| Single-instance prefix | `SoftwareCenter_singleton_` | `LaunchBoards_singleton_` |
| Runtime icon | `icon.ico` | `launchboards.ico` |
| Executable | `SoftwareCenter.exe` | `LaunchBoards.exe` |
| Store identity | `Geiger.SoftwareCenter` | `Geiger.LaunchBoards` |
| Store metadata | `store_package.json` | `store_package_launchboards.json` |
| Local release artifact | versioned SoftwareCenter path | `releases/v1.0.0/LaunchBoards-1.0.0-win64.exe` |

`STORE_CONTRACT.md`, `STORE_LISTING.md`, and `WINDOWS_STORE_PREP.md` remain the
canonical SoftwareCenter Store contract and contain no LaunchBoards identity or
artifact. LaunchBoards metadata is intentionally separate and does not alter
SoftwareCenter release hashes.

## Reproducible verification

Run the complete static and parallel-process boundary check:

```powershell
python scripts/verify_product_boundaries.py
```

The process smoke starts both source entry points concurrently with temporary
INI settings and task-specific `QLocalServer` names, then starts one duplicate
of each product. Both primary processes must remain alive while each duplicate
routes to only its matching primary and exits successfully. The verifier never
reads or overwrites the user's real QSettings namespaces.

For a local PyInstaller artifact, build outside the repository and attach its
size and SHA-256 to the same receipt:

```powershell
$PROJECT_ROOT = (Get-Location).Path
$BUILD_ROOT = Join-Path $env:TEMP "launchboards-build"
python -m PyInstaller --noconfirm --clean --windowed --onefile `
  --name LaunchBoards --icon "$PROJECT_ROOT\launchboards.ico" `
  --add-data "$PROJECT_ROOT\launchboards.ico;." `
  --add-data "$PROJECT_ROOT\icon.ico;." `
  --distpath "$BUILD_ROOT\dist" `
  --workpath "$BUILD_ROOT\build" `
  --specpath "$BUILD_ROOT" `
  "$PROJECT_ROOT\launchboards.py"
python scripts/verify_product_boundaries.py `
  --artifact "$BUILD_ROOT\dist\LaunchBoards.exe"
```

This is a local unsigned artifact and namespace verification. It is not a
claim of signing, WACK certification, Store publication, screenshot review,
keyboard acceptance, or screen-reader acceptance.

## Empirical local receipt — 2026-08-26

The documented command was executed on Windows 11 with Python 3.12.10 and
PyInstaller 6.21.0. The first dry run exposed and corrected the external
`--specpath`/relative-resource mismatch; the repeated build with absolute
project resource paths completed successfully outside the repository.

| Field | Readback |
|---|---|
| Artifact | external task-specific build root, `dist/LaunchBoards.exe` |
| Size | 47,405,951 bytes |
| SHA-256 | `d376e575cc49dbe780aa0c39eb327ac1c840e54254bb80e21afd341080bb7152` |
| Parallel source-process smoke | passed for SoftwareCenter and LaunchBoards |
| User settings | untouched; temporary INI backend used |
| Release state | unsigned local verification artifact, not published |
