# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-24

### Build / Release
- EXE neu gebaut 2026-06-01 (PyInstaller, `SoftwareCenter.spec`); 9/9 Tests grün, Smoke-Test bestanden. Vorherige EXE: 2026-05-01.

### Changed
- Der neue `web_companion/`-Reader stellt exportierte Profile jetzt als statische PWA für Android, iOS und Desktop dar, inklusive Offline-Wiederherstellung und Install-Hinweisen.
- README, contributing guide, privacy policy, and release notes refreshed for the `file-bricks/SoftwareCenter` GitHub repository.
- Documented local smoke checks and clarified that build artifacts stay out of version control.
- Store listing metadata refreshed for current screenshots, capability metadata, and local QSettings wording.
- View toggles now stay in sync when switching tabs, and the last active tab is restored on startup.
- macOS `.app` bundles are now accepted as launch targets via drag and drop, matching the documented cross-platform scope.
- Linux `.desktop` launchers now show their declared app name and start via their `Exec` command instead of being treated like generic files.
- `QSettings` persist tabs now store structured entry metadata as `entries_json`, while legacy `paths` imports remain readable.
- GitHub Actions now install the app dependencies and run the PySide6 regression tests on Python 3.10, 3.11, and 3.12.

### Added
- `web_companion/` mit lokaler Profilansicht, Demo-Profil, Manifest, Service Worker und Node-Smokes für `softwarecenter-profile-v1.json`.
- GitHub Actions smoke-test workflow for Python syntax and JSON metadata validation.
- Regression tests for tab/view state restoration and macOS `.app` bundle support.
- Regression tests for Linux `.desktop` launchers (display name and command execution).
- Public exchange-format documentation for `softwarecenter-profile-v1.json`; local planning notes stay outside the repository.
- Profile export/import via `Datei -> Profil exportieren/importieren` and matching toolbar actions.
- `EXPORTFORMAT.md` with the `softwarecenter-profile-v1.json` schema, `kind` values, and import behavior.
- Regression tests for portable profile export/import and metadata persistence.
- Community workflows updated to current `actions/stale` and `actions/first-interaction` majors.

## [1.0.0] - 2026-02-28

### Added
- Tab-basierte Organisation von Software-Verknüpfungen
- Drag & Drop zum Hinzufügen von Dateien
- Kachel- und Listenansicht
- Kontextmenü (Öffnen/Starten, Löschen)
- Persistente Speicherung von Tabs, Inhalten und Fensterposition
- Tab-Verwaltung (erstellen, umbenennen, schließen, verschieben)
- Cross-Platform-Unterstützung (Windows, macOS, Linux)
- Native System-Icons für Anwendungen
- Anwendungs-Icon
