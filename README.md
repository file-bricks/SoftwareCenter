# SoftwareCenter

Ein leichtgewichtiger, plattformuebergreifender Desktop-Organizer fuer Software-Verknuepfungen mit Tab-basierter Kategorisierung.

## Funktionen

- **Tab-Organisation** - Programme in benennbare, verschiebbare Tabs gruppieren
- **Drag & Drop** - Dateien per Drag & Drop hinzufuegen
- **Zwei Ansichtsmodi** - Kacheln (grosse Icons) und Liste
- **Automatische Speicherung** - Tabs, Inhalte und Fensterposition bleiben erhalten
- **Kontextmenue** - Rechtsklick zum Oeffnen oder Entfernen
- **Cross-Platform** - Windows, macOS und Linux
- **Native Icons** - Automatische Anzeige der System-Anwendungsicons

## Voraussetzungen

- Python 3.10+
- PySide6

## Installation

```bash
pip install -r requirements.txt
```

## Starten

```bash
python SoftwareCenter.py
```

Unter Windows auch per `START.bat` oder der vorkompilierten `SoftwareCenter.exe` aus den [Releases](https://github.com/lukisch/SoftwareCenter/releases).

## Verwendung

| Aktion | Anleitung |
|--------|-----------|
| Programme hinzufuegen | Dateien (EXE, Skripte etc.) ins Fenster ziehen |
| Tabs organisieren | Toolbar > "Neuer Tab", Doppelklick zum Umbenennen |
| Ansicht wechseln | Toolbar > Kacheln / Liste |
| Programme starten | Doppelklick oder Rechtsklick > Oeffnen/Starten |
| Eintraege entfernen | Rechtsklick > Loeschen (entfernt nur die Verknuepfung) |

## EXE erstellen

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name=SoftwareCenter SoftwareCenter.py
```

Die EXE liegt anschliessend in `dist/`.

## Technik

| Komponente | Technologie |
|------------|------------|
| Sprache | Python 3.10+ |
| GUI-Framework | PySide6 (Qt for Python) |
| Speicherung | QSettings (Windows Registry / INI) |
| Codeumfang | ~350 Zeilen |

---

## English

A lightweight, cross-platform desktop organizer for managing software shortcuts with tab-based categorization.

### Features

- **Tab Organization** - Group programs into renamable, movable tabs
- **Drag & Drop** - Add files via drag and drop
- **Two View Modes** - Tiles (large icons) and list
- **Auto Save** - Tabs, contents, and window position are persisted
- **Context Menu** - Right-click to open or remove
- **Cross-Platform** - Windows, macOS, and Linux
- **Native Icons** - Automatic display of system application icons

### Requirements

- Python 3.10+
- PySide6

### Installation

```bash
pip install -r requirements.txt
```

### Run

```bash
python SoftwareCenter.py
```

On Windows, you can also use `START.bat` or the prebuilt `SoftwareCenter.exe` from the [Releases](https://github.com/lukisch/SoftwareCenter/releases).

### Usage

| Action | Instructions |
|--------|-------------|
| Add programs | Drag files (EXE, scripts, etc.) into the window |
| Organize tabs | Toolbar > "New Tab", double-click to rename |
| Switch view | Toolbar > Tiles / List |
| Launch programs | Double-click or right-click > Open/Start |
| Remove entries | Right-click > Delete (removes shortcut only) |

### Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name=SoftwareCenter SoftwareCenter.py
```

The EXE will be in `dist/`.

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| GUI Framework | PySide6 (Qt for Python) |
| Storage | QSettings (Windows Registry / INI) |
| Code Size | ~350 lines |

## License

[MIT](LICENSE)

**Hinweis / Note:** Diese Anwendung verwendet / This application uses [PySide6](https://doc.qt.io/qtforpython-6/), lizenziert unter / licensed under LGPLv3. PySide6 wird dynamisch gelinkt / is dynamically linked.

---

## Haftung / Liability

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse aus GPL-3.0 / MIT / Apache-2.0 §§ 15–16 (je nach gewählter Lizenz).

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.

This project is an unpaid open-source donation. Liability is limited to intent and gross negligence (§ 521 German Civil Code). Use at your own risk. No warranty, no maintenance guarantee, no fitness-for-purpose assumed.

