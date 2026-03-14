# Store Listing -- SoftwareCenter

## Deutsch

### Kurzbeschreibung (max 100 Zeichen)
Desktop-Organizer: Programme in Tabs gruppieren, per Drag & Drop hinzufuegen, sofort starten.

### Beschreibung (max 10.000 Zeichen)
SoftwareCenter ist ein leichtgewichtiger Desktop-Organizer, der Ordnung in Ihre Software-Sammlung bringt. Statt sich durch verschachtelte Startmenue-Ordner oder ueberfuellte Desktops zu kaempfen, organisieren Sie Ihre Programme in uebersichtlichen Tabs -- genau so, wie es fuer Ihren Workflow passt.

**Kernfunktionen:**

- Tab-basierte Organisation: Erstellen Sie beliebig viele Tabs und benennen Sie diese nach Ihren Kategorien (z.B. "Entwicklung", "Grafik", "Office"). Tabs lassen sich per Drag & Drop umsortieren.

- Zwei Ansichtsmodi: Wechseln Sie zwischen einer Kachel-Ansicht mit grossen Icons fuer schnellen visuellen Zugriff und einer kompakten Listenansicht fuer grosse Sammlungen.

- Drag & Drop: Ziehen Sie EXE-Dateien, Skripte oder beliebige Programm-Verknuepfungen einfach ins Fenster -- fertig. Keine umstaendliche Konfiguration noetig.

- Native System-Icons: SoftwareCenter zeigt automatisch die Original-Icons Ihrer Anwendungen an, damit Sie Programme sofort wiedererkennen.

- Automatische Speicherung: Ihre gesamte Organisation -- Tabs, Inhalte, Fensterposition und Ansichtsmodus -- wird automatisch gespeichert und beim naechsten Start wiederhergestellt.

- Kontextmenue: Per Rechtsklick Programme starten oder Eintraege entfernen (nur die Verknuepfung wird entfernt, nie das Programm selbst).

**Fuer wen ist SoftwareCenter?**

- Power-User mit vielen installierten Programmen
- Entwickler, die zwischen verschiedenen Tools wechseln
- Jeden, der eine schnelle, aufgeraeumte Alternative zum Windows-Startmenue sucht

**Technische Details:**

- Minimaler Ressourcenverbrauch (~350 Zeilen Code)
- Keine Cloud-Anbindung, keine Telemetrie -- Ihre Daten bleiben lokal
- Einstellungen werden in der Windows Registry (QSettings) gespeichert

### Schluesselwoerter
App Launcher, Desktop Organizer, Software Verwaltung, Programmstarter, Tab Organizer, Schnellstart, Shortcut Manager, Drag and Drop, App Manager

### Kategorie
Productivity / Utilities

---

## English

### Short Description (max 100 chars)
Desktop organizer: group apps in tabs, add via drag & drop, launch instantly.

### Description (max 10,000 chars)
SoftwareCenter is a lightweight desktop organizer that brings order to your software collection. Instead of digging through nested start menu folders or cluttered desktops, organize your programs in clear, customizable tabs -- tailored to your workflow.

**Core Features:**

- Tab-based organization: Create as many tabs as you need and name them by category (e.g., "Development", "Graphics", "Office"). Tabs can be reordered via drag & drop.

- Two view modes: Switch between a tile view with large icons for quick visual access and a compact list view for large collections.

- Drag & Drop: Simply drag EXE files, scripts, or any program shortcuts into the window -- done. No complicated setup required.

- Native system icons: SoftwareCenter automatically displays the original icons of your applications so you can instantly recognize your programs.

- Auto save: Your entire organization -- tabs, contents, window position, and view mode -- is automatically saved and restored on next launch.

- Context menu: Right-click to launch programs or remove entries (only the shortcut is removed, never the program itself).

**Who is SoftwareCenter for?**

- Power users with many installed programs
- Developers switching between various tools
- Anyone looking for a fast, clean alternative to the Windows Start Menu

**Technical Details:**

- Minimal resource usage (~350 lines of code)
- No cloud connection, no telemetry -- your data stays local
- Settings stored in Windows Registry (QSettings)

### Keywords
App Launcher, Desktop Organizer, Software Manager, Program Starter, Tab Organizer, Quick Launch, Shortcut Manager, Drag and Drop, App Manager

### Category
Productivity / Utilities

---

## Store Submission Metadata

| Field | Value |
|---|---|
| Publisher CN | CN=52596601-BAB4-4F3F-B182-E8F3F273B202 |
| Publisher Display | Geiger |
| Identity Name | Geiger.SoftwareCenter |
| Version | 1.0.0.0 |
| Age Rating | 3+ |
| Price | Free |
| Privacy Policy URL | https://github.com/file-bricks/SoftwareCenter/blob/master/PRIVACY_POLICY.md |
| Support URL | https://github.com/file-bricks/SoftwareCenter/issues |
| Capabilities | (none) |

## Store Readiness Checklist

- [x] EXE built (dist/SoftwareCenter.exe, ~44 MB)
- [x] store_package.json -- publisher CN + URLs corrected
- [x] releases/windowsstore/store_settings.json -- publisher CN + URLs corrected
- [x] PRIVACY_POLICY.md created (EN + DE)
- [x] StoreAssets generated (store_package/SoftwareCenter/icons/)
- [x] store_assets/ -- legacy icons (Square44x44, Square150x150, Square310x310, Wide310x150)
- [x] LICENSE present
- [x] THIRD_PARTY_LICENSES.txt present
- [x] No hardcoded paths in source code
- [x] No debug print statements
- [x] PySide6 (LGPL) -- license compatible with Store distribution
- [ ] Screenshots -- FEHLEN (mindestens 1 Screenshot erforderlich fuer Store-Submission)
- [ ] MSIX package -- noch nicht erstellt (braucht Code-Signing-Zertifikat + makeappx)
- [ ] Code-Signing (.pfx) -- noch nicht konfiguriert in store_settings.json
