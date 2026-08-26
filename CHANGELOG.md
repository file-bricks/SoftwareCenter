# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-08-25

- Added a reproducible SoftwareCenter/LaunchBoards product-boundary verifier:
  separate QSettings and single-instance namespaces, native parallel-process
  routing, icons, executables, Store identities, and release paths are checked
  without touching real user settings or mixing SoftwareCenter release hashes.
- Locked the optional web-companion CI boundary into regression tests and
  strengthened the desktop export fixture with aggregate secret-key and
  no-local-file-copy checks.
- Added an explicit Node 20.x CI boundary for the removed `web_companion/`;
  reintroductions must provide `npm test` and the three Node syntax checks.
- Added a redacted, UTF-8 profile export fixture and a real desktop
  export/import roundtrip covering multiple tabs, `kind`/`notes`, umlauts and
  an intentionally missing path. No credentials, tokens or passwords are
  exported; the PWA path remains intentionally absent.
- Reconciled Store documentation with the actual local artifacts: the v1.2.0
  EXE hash is recorded as unsigned and non-WACK.
- Tab-Leiste (R4): Verwaiste Schließen-Knöpfe (`QAbstractButton`-Kinder der `QTabBar`) werden in `_update_tab_closable_state()` beim Umschalten zwischen Einzel- und Mehr-Board-Ansichten explizit ausgeblendet, wodurch überlagernde Doppel-X-Artefakte über Tab-Beschriftungen verhindert werden.
- Regressionstests: Testabdeckung für TabBar-Close-Button-Lebenszyklus (`tests/test_tabbar_orphan_close_button.py`) und Unit-Regressionstest (`TestBugR4_TabBarOrphanCloseButtons` in `tests/test_bug_regressions.py`) verifiziert.

## [Unreleased] - 2026-08-13

### Store-Resubmit nach Ablehnung 10.1.1.3

- Store-Screenshots kommen nicht mehr aus dem Qt-Offscreen-Plugin. Dieses rendert
  auf Windows keine Glyphen; die eingereichten PNGs zeigten Kästchen statt Text
  und wurden am 2026-08-11 nach Policy 10.1.1.3 („Inaccurate Representation")
  abgelehnt. `generate_store_screenshots.py` nutzt jetzt das im Haus bereits
  bewährte Rezept aus ProfiPrompt (`a656d01`) und CleanMarkdown (`bf5f226`):
  native Qt-Plattform, Fenster über `Qt.WA_DontShowOnScreen` trotzdem unsichtbar,
  isoliertes Temp-APPDATA und ein Font-Rendering-Selbsttest vor dem Capture.
- `_assert_font_rendering()` prüft zweistufig: Plattform-Plugin und eine echte
  Glyphen-Probe (A/B/g/8/M einzeln rendern — bei Tofu sind alle Renderings
  identisch, weil jede Glyphe dasselbe .notdef-Kästchen ist). Der Lauf bricht mit
  klarem Fehler ab, statt lautlos unlesbare Bilder zu schreiben. Empirisch
  belegt: unter `offscreen` liefert die Probe `False`, auf `windows` `True`.
- Die vier Store-PNGs werden aus einem gespeicherten und neu geladenen Profil
  aufgenommen — so, wie ein wiederkehrender Nutzer die App sieht — und zeigen
  jetzt vier verschiedene Ansichten statt zweimal dasselbe Board.
- Jeder Screenshot wird beim Erzeugen gegen die Store-Mindestgröße 1366x768
  geprüft.
- Bildkomposition nachgebessert: Die vorherigen 1600x960-Aufnahmen zeigten sechs
  bzw. vierzehn Kacheln in einem sonst leeren Fenster — rund 80 % weiße Fläche.
  Ein so leeres Fenster zeigt das Produkt nicht so, wie es benutzt wird, und lädt
  dieselbe Bewertung nach 10.1.1.3 erneut ein. Jetzt: kompakteres Fenster
  1440x900 und eine tabellengesteuerte Demo-Sammlung mit 80 (Arbeitsplatz),
  78 (Office), 24 (Review) und 10 (Setup) frei erfundenen, neutralen Einträgen.
  Die Kachelansichten füllen damit sieben Reihen, die Listenansichten laufen über
  die volle Fensterhöhe.
- Versions-Mismatch aufgelöst: Runtime, `pyproject.toml`, `store_package.json`,
  Staging-Manifest, `STORE_CONTRACT.md` und `STORE_LISTING.md` führen einheitlich
  1.2.0 bzw. 1.2.0.0. Ein neuer Test in `tests/test_store_contract.py` hält die
  Quellen zusammen.

## [Unreleased] - 2026-08-04

### Maintenance & Discoverability
- Added `file-bricks` ecosystem and `open-bricks` umbrella badges to `README.md` and `README_de.md`.
- Enhanced GFM callout note for `llms.txt` and machine-readable index discovery.
- Refreshed verification timestamps to 2026-08-04 across documentation and `llms.txt`.
- Revalidated Pytest test suite (161/161 passed 100% green).

## [Unreleased] - 2026-08-02

### Maintenance

- Revalidated the local source with 161 passing Pytest tests, Linux and macOS
  platform smokes, compileall, JSON validation, and the Windows WACK dry-run.
- Refreshed the README and `llms.txt` verification dates to 2026-08-02.
- Recorded 11 existing Ruff style/import findings for a future focused cleanup;
  no code or release artifact was changed in this maintenance pass.

## [Unreleased] - 2026-07-28

- Ported the launcher-catalog reconciliation routine into the Plan-D repository
  as `scripts/softwarecenter_sync.py`. Catalog, registry, software root, and
  local development root are now explicit CLI inputs instead of being derived
  from the script location.
- The catalog runtime remains dry-run by default, retains both QSettings
  profiles and `SUPPRESSED` semantics, starts no shell, and gates `--apply`
  behind process readback plus a local profile/registry backup.
- Added regression coverage and a pinned-runtime scheduler migration/rollback
  contract in `RUNTIME_DAILY_CARE.md`. No live scheduler or Windows Task is
  changed by this source update.
- The Windows build entrypoint now derives the release artifact directory and
  filename from `project.version` in `pyproject.toml`. Current builds therefore
  land under `releases/v1.2.0/SoftwareCenter-1.2.0-win64.exe` instead of
  overwriting the historical v1.0.0 artifact with newer code.
- Added a stdlib-only version reader and regression coverage for the versioned
  build contract.
- The build-exclude scanner is now resolved from `SOFTWARE_ROOT` or the
  standard `OneDrive/.TOPICS/.SOFTWARE` root instead of the nonexistent
  `C:\_Local_DEV\_tools` fallback.
- Updated the README test badges after the expanded suite passed 126/126.

### Added

- Preserved the authorized desktop icon master files and dormant packaging
  source variants recovered from the controlled OneDrive handoff.

### Fixed

- Path helpers now reject missing and non-string launch targets safely
  (`BUGSWEEP-41`), including list entries without a stored `UserRole` path.
- Revalidated the headless suite after the controlled remote rebase:
  124 tests pass.

## [Unreleased] - 2026-07-27

### Discoverability & README Design
- Added Mermaid System Architecture Diagrams to `README.md` and `README_de.md` illustrating PySide6 UI, platform resolvers, QSettings persistence, JSON profile exchange, and Windows Store packaging pipeline.
- Synchronized Pytest status badge (`118 passed`).
- Updated `llms.txt`, `README.md`, and `README_de.md` timestamps (`Last-checked: 2026-07-27`).
- Verified 118/118 Pytest test suite pass.

## [Unreleased] - 2026-07-26

### Added
- Windows Store Release Readiness (TW-SC-02): Created `WINDOWS_STORE_PREP.md`, `SUPPORT.md`, and automated test suite `tests/test_store_materials.py` (118/118 tests passed) validating canonical store metadata, package identity (`Geiger.SoftwareCenter`), capabilities (`runFullTrust`), category, executable reference, and privacy/support documentation.

## [Unreleased] - 2026-07-25

### Maintenance & Technical Hygiene
- Standardized PEP 621 `pyproject.toml` with `[tool.pytest.ini_options]` (`pythonpath = "."`), enabling direct invocation of `pytest`.
- Updated `llms.txt`, `README.md`, and `README_de.md` timestamps (`Last-checked: 2026-07-25`).
- Added Shields.io badges and GFM LLM Integration Note (`> [!NOTE]`) to `README.md` and `README_de.md`.

### Removed
- Web/PWA-Companion entfernt — Usecase-Prüfung 2026-07-23 (LG): reine Leseansicht ohne Startfunktion, kein Nutzer-Usecase; Profil-Export bleibt erhalten.

### Changed

- Store metadata now has one documented source of truth: `store_package.json`.
  The local packaging settings and staging manifest must mirror its identity,
  executable, `runFullTrust` capability, resources, URLs and category.

### Fixed

- v1.0.0 release documentation no longer implies a verified Windows EXE: the
  retained EXE hash differs from the expected manifest hash and is unsigned, so
  the release stays blocked pending a reproducible authorized rebuild.

### Build / Release
- Icon/EXE/START-Health-Check 2026-06-19: vorhandenes `icon.ico` weiterverwendet, `START.bat` auf EXE-first umgestellt, `build_exe.bat` auf lokalen Buildpfad `C:\_Local_DEV\codex_build\softwarecenter` mit Build-Exclude-Scanner aktualisiert und `SoftwareCenter.exe` neu gebaut.
- EXE neu gebaut 2026-06-01 (PyInstaller, `SoftwareCenter.spec`); 9/9 Tests grün, Smoke-Test bestanden. Vorherige EXE: 2026-05-01.

### Added
- Tray-Zuverlässigkeit (Ticket T-20260721-02): Icons werden jetzt über eine zentrale `resource_path()`-Auflösung geladen (mit `sys._MEIPASS`-Fallback für den PyInstaller-Onefile-Build) und fallen bei fehlender ICO-Datei auf das Fenster-Icon, zuletzt auf ein Qt-Standardicon zurück — nie mehr ein stillschweigendes Null-Icon. `build_exe.bat` und `SoftwareCenter.spec` bündeln `icon.ico` jetzt zusätzlich als Laufzeit-Ressource (`--add-data`/`datas`), nicht mehr nur als EXE-Metadaten-Icon. Der Vertrag „Schalter an/aus" ist jetzt exakt: aus = kein Tray-Icon (Schließen beendet die App), an = Icon sofort erzeugen, Ausschalten entfernt es sofort. Ist der Systemtray beim Start nicht verfügbar, versucht die App bis zu 5× im Abstand von 1,5s erneut und zeigt danach einen sichtbaren Hinweis; die App läuft niemals unsichtbar ohne Tray weiter. Beide Produktprofile (SoftwareCenter, LaunchBoards) nutzen weiterhin eigene Namen, Icons und QSettings-Namespaces.
- Tray-Navigation (Ticket T-20260721-03): Das Tray-Menü listet jetzt alle aktiven Boards (Stufe 1, Auswahl öffnet das Hauptfenster direkt auf dem Board) und bietet pro Board ein Untermenü mit den hinterlegten Einträgen (Stufe 2, Start über denselben sicheren `open_file`-Pfad wie im Hauptfenster); nicht-favorisierte Boards zeigen höchstens 10 Einträge plus „… N weitere"-Hinweis, Favoriten-Boards vollständig. Bei mehr als 20 aktiven Boards schaltet das Menü automatisch auf reine Stufe 1 zurück. Ein Suchfeld oben im Menü filtert live über Board-Namen und Eintrags-Labels (Praefix-/Substring-Ranking); Enter aktiviert den besten Treffer. Das Menü baut sich bei jedem Öffnen aus dem Live-Zustand neu auf, sodass Umbenennen, Schließen, Reaktivieren und endgültiges Löschen nie verwaiste Einträge hinterlassen. Geschlossene Boards erscheinen nicht im Tray. Tests in `tests/test_tray_navigation.py`.
- Board-Lebenszyklus (Ticket T-20260721-01): Jedes Board (Tab) besitzt jetzt eine feste, dauerhafte Identität. „Board schließen" entfernt es nur aus der Tab-Leiste (`closed_at` wird gesetzt); Name, Einträge, Reihenfolge, Ansicht und Favorit-Status bleiben vollständig erhalten und überleben einen Neustart. Neues Seitenfenster (Hamburger-Button „☰" rechts oben in der Toolbar) listet ALLE Boards mit zwei Reitern „Verlauf" (zuletzt geschlossenes Board zuerst) und „Alphabetisch"; die zuletzt gewählte Ansicht wird gemerkt. Rechtsklick im Panel bietet „Favorit" (gelber Stern) und „Löschen" (Mülleimer-Icon) — endgültiges Löschen fragt nur bei Favoriten nach, Nicht-Favoriten werden sofort entfernt. Neue Einstellung „Einfacher Modus" (Datei-Menü, kein Default) zeigt nur den Verlauf ohne Favoriten und ergänzt einen „Verlauf leeren"-Button, der geschlossene Nicht-Favoriten endgültig löscht und Favoriten verschont. Bestehende gespeicherte Boards werden beim ersten Start verlustfrei als aktive Boards migriert. Gilt gemeinsam für SoftwareCenter und LaunchBoards (geteilter Kern, getrennte QSettings-Profile). Tests in `tests/test_board_lifecycle.py`.
- Neues App-Icon im Superman-Wappen-Stil: rotes Schild mit fettem, leicht schrägem weißem „SC" und weißem Rand. Reproduzierbar über `generate_icon.py`; ersetzt `icon.ico`, `DesktopIcon.ico`, die Windows-Store-Logos (`store_assets/*.png`) sowie die PWA-Icons und das `icon.svg` des Web-Companions (maskable-/apple-touch-Varianten mit rotem Vollhintergrund).
- Kontextmenü „Senden an" (verschieben) und „Duplizieren auf" (kopieren): Einträge lassen sich per Rechtsklick auf ein anderes Board (Tab) verschieben oder zusätzlich dort anzeigen. Submenüs listen alle Boards außer dem aktuellen und erscheinen nur bei vorhandener Auswahl und mindestens einem weiteren Board. Label, Typ und Notizen bleiben erhalten, bereits vorhandene Pfade werden im Ziel-Board nicht dupliziert. Tests in `tests/test_features_board_transfer.py`.

### Changed
- UX-/Accessibility-Review: Die kompakte `x`-Schaltfläche zum Schließen von Boards bleibt visuell unverändert, exponiert im Tab-Bar-Kontext jetzt aber sprechende Tooltips sowie tabbezogene Accessible Names und Descriptions statt praktisch nur eines Symbols.
- Windows-`.lnk`-Dateien, die auf eine `.exe` oder einen Ordner zeigen, werden beim Hinzufügen jetzt als Originalziel gespeichert und angezeigt; direkte Ordner-Drops werden ebenfalls unterstützt, nicht auflösbare Links bleiben kompatibel als `.lnk`-Eintrag erhalten.
- Web Companion: Service-Worker-Cache auf v3 angehoben und Offline-Fetch-Fehler liefern jetzt einen HTTP-503-Fallback statt unkontrolliert zu scheitern.
- Die Windows-Store-Vorbereitung enthält jetzt ein reproduzierbares Screenshot-Set aus der echten Desktop-Oberfläche statt nur eines offenen TODO-Markers.
- README.md, README_de.md, `llms.txt`, and store listing copy now include sharper discovery positioning for SoftwareCenter as a local-first PySide6 app launcher and desktop shortcut organizer, with explicit disambiguation from Microsoft/SCCM Software Center, app stores, package managers, and remote deployment portals.
- UX-/Accessibility-Review: Der einzige verbleibende Tab zeigt kein irreführendes Schließen-Symbol mehr; die Schaltfläche erscheint erst wieder, wenn wirklich mehr als ein Tab vorhanden ist.
- The Windows Store path now has a reproducible local WACK runner plus a documented manual test protocol instead of an undocumented final certification step.
- macOS source smoke is now documented and wired into CI for `.app` import, `open` launching, settings persistence, and profile export verification.
- Linux-`.desktop`-Launcher verwerfen jetzt auch eingebettete Feldcode-Argumente wie `--open=%f` oder `--profile=%u`, statt sie als wörtliche Platzhalter an Prozesse weiterzureichen.
- Der neue `web_companion/`-Reader stellt exportierte Profile jetzt als statische PWA für Android, iOS und Desktop dar, inklusive Offline-Wiederherstellung und Install-Hinweisen.
- README, contributing guide, privacy policy, and release notes refreshed for the `file-bricks/SoftwareCenter` GitHub repository.
- Documented local smoke checks and clarified that build artifacts stay out of version control.
- Linux source smoke documented and wired into CI for `.desktop` import, launch fallback, settings persistence, and export verification.
- Store listing metadata refreshed for current screenshots, capability metadata, and local QSettings wording.
- View toggles now stay in sync when switching tabs, and the last active tab is restored on startup.
- macOS `.app` bundles are now accepted as launch targets via drag and drop, matching the documented cross-platform scope.
- Linux `.desktop` launchers now show their declared app name and start via their `Exec` command instead of being treated like generic files.
- `QSettings` persist tabs now store structured entry metadata as `entries_json`, while legacy `paths` imports remain readable.
- GitHub Actions now install the app dependencies and run the PySide6 regression tests on Python 3.10, 3.11, and 3.12.

### Added
- Regressionstests für Windows-Shortcut-Auflösung, Ordner-Drops und den Fallback auf unveränderte `.lnk`-Einträge.
- `generate_store_screenshots.py` für reproduzierbare Windows-Store-Screenshots und `README/screenshots/store/README.md` als Generator-Doku.
- Regressionstest `tests/test_store_screenshots.py` für PNG-Header, Mindestauflösung und `summary.json`.
- `llms.txt` in the repository root for LLM documentation visibility.
- Regressionstest dafür, dass die Tab-Schließen-Schaltfläche beim letzten verbleibenden Tab ausgeblendet bleibt und nach dem Hinzufügen weiterer Tabs wieder erscheint.
- `scripts/run_windows_wack.py` for local Windows App Certification Kit dry-runs, real runs, and XML-to-JSON report summaries.
- Regression tests for the WACK helper, covering MSIX/report path resolution and report parsing.
- `tests/macos_platform_smoke.py` as a reproducible headless macOS source smoke for `.app` bundles and profile persistence.
- Regressionstest für Linux-`.desktop`-Launcher mit eingebetteten Feldcodes, damit nur echte statische Argumente übrig bleiben und Escapes wie `%%f` korrekt erhalten werden.
- `web_companion/` mit lokaler Profilansicht, Demo-Profil, Manifest, Service Worker und Node-Smokes für `softwarecenter-profile-v1.json`.
- GitHub Actions smoke-test workflow for Python syntax and JSON metadata validation.
- `tests/linux_platform_smoke.py` as a reproducible headless Linux source smoke for `.desktop` launchers and profile persistence.
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
