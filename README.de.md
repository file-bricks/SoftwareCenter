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

## Installation

### Voraussetzungen

- Python 3.10+
- PySide6

```bash
pip install -r requirements.txt
```

### Starten

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
|------------|-------------|
| Sprache | Python 3.10+ |
| GUI-Framework | PySide6 (Qt for Python) |
| Speicherung | QSettings (Windows Registry / INI) |
| Codeumfang | ~350 Zeilen |

## Lizenz

Dieses Projekt steht unter der [MIT-Lizenz](LICENSE).

**Hinweis:** Diese Anwendung verwendet [PySide6](https://doc.qt.io/qtforpython-6/), lizenziert unter LGPLv3. PySide6 wird dynamisch gelinkt und ist nicht in diesem Repository enthalten.

---

English version: [README.md](README.md)
