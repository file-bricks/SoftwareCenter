# Store Listing -- SoftwareCenter

## Deutsch

### Kurzbeschreibung (max 100 Zeichen)
Desktop-Organizer: Programme in Tabs gruppieren, per Drag & Drop hinzufügen, sofort starten.

### Beschreibung (max 10.000 Zeichen)
SoftwareCenter ist ein leichtgewichtiger Desktop-Organizer, der Ordnung in Ihre Software-Sammlung bringt. Statt sich durch verschachtelte Startmenü-Ordner oder überfüllte Desktops zu kämpfen, organisieren Sie vorhandene Programme, Skripte und Verknüpfungen in übersichtlichen Tabs -- genau so, wie es für Ihren Workflow passt.

**Kernfunktionen:**

- Tab-basierte Organisation: Erstellen Sie beliebig viele Tabs und benennen Sie diese nach Ihren Kategorien (z.B. "Entwicklung", "Grafik", "Office"). Tabs lassen sich per Drag & Drop umsortieren.

- Zwei Ansichtsmodi: Wechseln Sie zwischen einer Kachel-Ansicht mit großen Icons für schnellen visuellen Zugriff und einer kompakten Listenansicht für große Sammlungen.

- Drag & Drop: Ziehen Sie EXE-Dateien, Skripte oder beliebige Programm-Verknüpfungen einfach ins Fenster -- fertig. Keine umständliche Konfiguration nötig.

- Native System-Icons: SoftwareCenter zeigt automatisch die Original-Icons Ihrer Anwendungen an, damit Sie Programme sofort wiedererkennen.

- Automatische Speicherung: Ihre gesamte Organisation -- Tabs, Inhalte, Fensterposition und Ansichtsmodus -- wird automatisch gespeichert und beim nächsten Start wiederhergestellt.

- Kontextmenü: Per Rechtsklick Programme starten oder Einträge entfernen (nur die Verknüpfung wird entfernt, nie das Programm selbst).

- Profil-Export/Import: Ihre Tab-Struktur kann als `softwarecenter-profile-v1.json` gesichert und später wieder importiert werden.

**Für wen ist SoftwareCenter?**

- Power-User mit vielen installierten Programmen
- Entwickler, die zwischen verschiedenen Tools wechseln
- Jeden, der eine schnelle, aufgeräumte Alternative zum Windows-Startmenü sucht

**Technische Details:**

- Minimaler Ressourcenverbrauch (~690 Zeilen Code)
- Keine Cloud-Anbindung, keine Telemetrie -- Ihre Daten bleiben lokal
- Einstellungen werden lokal per QSettings gespeichert

### Schlüsselwörter
App Launcher, Desktop Organizer, Software Verwaltung, Programmstarter, Tab Organizer, Schnellstart, Shortcut Manager, Drag and Drop, App Manager, Offline Launcher, PySide6

### Kategorie
Productivity / Utilities

---

## English

### Short Description (max 100 chars)
Desktop organizer: group apps in tabs, add via drag & drop, launch instantly.

### Description (max 10,000 chars)
SoftwareCenter is a lightweight desktop organizer that brings order to your software collection. Instead of digging through nested start menu folders or cluttered desktops, organize existing programs, scripts, and shortcuts in clear, customizable tabs -- tailored to your workflow.

**Core Features:**

- Tab-based organization: Create as many tabs as you need and name them by category (e.g., "Development", "Graphics", "Office"). Tabs can be reordered via drag & drop.

- Two view modes: Switch between a tile view with large icons for quick visual access and a compact list view for large collections.

- Drag & Drop: Simply drag EXE files, scripts, or any program shortcuts into the window -- done. No complicated setup required.

- Native system icons: SoftwareCenter automatically displays the original icons of your applications so you can instantly recognize your programs.

- Auto save: Your entire organization -- tabs, contents, window position, and view mode -- is automatically saved and restored on next launch.

- Context menu: Right-click to launch programs or remove entries (only the shortcut is removed, never the program itself).

- Profile export/import: Save your tab structure as `softwarecenter-profile-v1.json` and import it again later.

**Who is SoftwareCenter for?**

- Power users with many installed programs
- Developers switching between various tools
- Anyone looking for a fast, clean alternative to the Windows Start Menu

**Technical Details:**

- Minimal resource usage (~690 lines of code)
- No cloud connection, no telemetry -- your data stays local
- Settings are stored locally via QSettings

### Keywords
App Launcher, Desktop Organizer, Software Manager, Program Starter, Tab Organizer, Quick Launch, Shortcut Manager, Drag and Drop, App Manager, Offline Launcher, PySide6

### Category
Utilities & Tools

---

## Store Submission Metadata

| Field | Value |
|---|---|
| Publisher CN | CN=52596601-BAB4-4F3F-B182-E8F3F273B202 |
| Publisher Display | Geiger |
| Identity Name | Geiger.SoftwareCenter |
| Version | 1.2.0.0 |
| Age Rating | 3+ |
| Price | Free |
| Privacy Policy URL | https://github.com/file-bricks/SoftwareCenter/blob/master/PRIVACY_POLICY.md |
| Support URL | https://github.com/file-bricks/SoftwareCenter/issues |
| Capabilities | runFullTrust |

## Store Readiness Checklist

- [x] EXE built (dist/SoftwareCenter.exe, ~44 MB)
- [x] store_package.json -- publisher CN + URLs corrected
- [x] releases/windowsstore/store_settings.json -- publisher CN + URLs corrected (local build settings, not tracked)
- [x] PRIVACY_POLICY.md created (EN + DE)
- [x] StoreAssets generated (store_package/SoftwareCenter/icons/)
- [x] store_assets/ -- legacy icons (Square44x44, Square150x150, Square310x310, Wide310x150)
- [x] LICENSE present
- [x] THIRD_PARTY_LICENSES.txt present
- [x] No hardcoded paths in source code
- [x] No debug print statements
- [x] PySide6 (LGPL) -- license compatible with Store distribution
- [x] README-Screenshot vorhanden (`README/screenshots/main.png`)
- [x] Store-Screenshot-Set erzeugbar: `python generate_store_screenshots.py` schreibt `README/screenshots/store/main-window.png`, `tab-organization.png`, `tiles-view.png`, `list-view.png` und `summary.json`
- [x] MSIX package vorhanden (`releases/SoftwareCenter.msix`, Stand 2026-03-13)
- [ ] Code-Signing (.pfx) -- noch nicht konfiguriert in store_settings.json
- [x] WACK-Workflow und manuelles Store-Testprotokoll sind dokumentiert
- [ ] Vor der nächsten Einreichung: signiertes MSIX neu bauen, echten WACK-Lauf ausführen und Report ablegen

## WACK-Workflow

### Reproduzierbarer Dry-Run

```powershell
python scripts/run_windows_wack.py --dry-run
```

Der Dry-Run prüft:

- erwarteten MSIX-Pfad (`releases/SoftwareCenter.msix`)
- Report-Ziel (`releases/windowsstore/test_reports/`)
- gefundenes `appcert.exe`
- den exakten WACK-Befehl für den echten Lauf

### Echter WACK-Lauf

```powershell
python scripts/run_windows_wack.py
```

Hinweise:

- bevorzugt aus einer erhöhten PowerShell starten
- gegen ein frisches signiertes MSIX ausführen
- XML-, Log- und JSON-Zusammenfassung landen unter `releases/windowsstore/test_reports/`
- vorhandene XML-Reports lassen sich später mit `python scripts/run_windows_wack.py --parse-report <report.xml>` erneut in eine JSON-Zusammenfassung umwandeln

## Manuelles Store-Testprotokoll

Vor einer Einreichung auf einem sauberen Windows-System oder einer frischen VM prüfen:

1. MSIX installieren und Erststart ohne Warn- oder Absturzdialog durchführen.
2. Neue Tabs anlegen, umbenennen, schließen und nach Neustart korrekt wiederherstellen.
3. EXE, `.lnk` und Skript-Dateien per Drag & Drop hinzufügen und erfolgreich starten.
4. Kachel- und Listenansicht umschalten; Ansicht muss pro Tab konsistent bleiben.
5. Profil als `softwarecenter-profile-v1.json` exportieren, neues Profil importieren und Inhalt korrekt ersetzen.
6. Entfernte Einträge dürfen nur die Verknüpfung löschen, nie die Zieldatei.
7. App schließen und erneut öffnen; QSettings-Persistenz für Tabs, Einträge, Fensterzustand und aktive Ansicht prüfen.
8. Deinstallation durchführen; keine unerwarteten Restdateien außerhalb der normalen QSettings-/App-Pfade.
