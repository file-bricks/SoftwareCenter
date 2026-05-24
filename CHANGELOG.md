# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-05-23

### Changed
- README, contributing guide, privacy policy, and release notes refreshed for the `file-bricks/SoftwareCenter` GitHub repository.
- Documented local smoke checks and clarified that build artifacts stay out of version control.
- Store listing metadata refreshed for current screenshots, capability metadata, and local QSettings wording.
- View toggles now stay in sync when switching tabs, and the last active tab is restored on startup.
- macOS `.app` bundles are now accepted as launch targets via drag and drop, matching the documented cross-platform scope.
- Linux `.desktop` launchers now show their declared app name and start via their `Exec` command instead of being treated like generic files.

### Added
- GitHub Actions smoke-test workflow for Python syntax and JSON metadata validation.
- Regression tests for tab/view state restoration and macOS `.app` bundle support.
- Regression tests for Linux `.desktop` launchers (display name and command execution).
- Portierungsplan für Desktop, Web/PWA und Mobil-Companion mit Austauschformat `softwarecenter-profile-v1.json`.

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
