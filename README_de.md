<img src="assets/banner.png" width="100%" alt="SoftwareCenter Banner">

# SoftwareCenter

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Pytest 182 Passed](https://img.shields.io/badge/pytest-182%20passed-brightgreen.svg)](https://docs.pytest.org/)
[![Plattformen: Windows | macOS | Linux](https://img.shields.io/badge/Plattformen-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/file-bricks/SoftwareCenter)
[![Datenschutz: 100% Local-First](https://img.shields.io/badge/Datenschutz-100%25%20Local--First-brightgreen.svg)](SECURITY.md)
[![Sicherheit: 48h SLA](https://img.shields.io/badge/Sicherheit-48h%20SLA-blue.svg)](SECURITY.md)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](LICENSE)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython-6/)
[![Ecosystem: file-bricks](https://img.shields.io/badge/Ecosystem-file--bricks-blue.svg)](https://github.com/file-bricks)
[![Umbrella: open-bricks](https://img.shields.io/badge/Umbrella-open--bricks-purple.svg)](https://github.com/open-bricks)
[![LLM Indexing Ready](https://img.shields.io/badge/LLM-Ready-blueviolet.svg)](llms.txt)

[English](README.md) · [Deutsch](README_de.md)

Ein leichtgewichtiger, plattformübergreifender Desktop-Organizer für Software-Verknüpfungen mit Tab-basierter Kategorisierung.

> [!NOTE]
> **KI / LLM Integration & Maschinelles Register:** SoftwareCenter bietet maschinenlesbare Metadaten in [`llms.txt`](llms.txt) und unterstützt Profil-Migrationen über versioniertes JSON (`softwarecenter-profile-v1.json`).

![SoftwareCenter Hauptfenster](README/screenshots/main.png)

## Schnellnavigation

- [Einstieg](#einstieg)
- [Funktionen](#funktionen)
- [Systemarchitektur](#systemarchitektur)
- [Lebenszyklus-Ablaufdiagramm](#lebenszyklus-ablaufdiagramm)
- [Kernfähigkeiten & Sicherheitsinvarianten](#kernfähigkeiten--sicherheitsinvarianten)
- [Geschwister-Ökosystem & Schwesterprodukte](#geschwister-ökosystem--schwesterprodukte)
- [Auffindbarkeit](#auffindbarkeit)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Starten](#starten)
- [Verwendung](#verwendung)
- [EXE erstellen](#exe-erstellen)
- [Qualitätssicherung](#qualitätssicherung)
- [Headless-Katalogpflege](#headless-katalogpflege)
- [Austauschformat](#austauschformat)
- [Schwesterprodukt-Grenze](#schwesterprodukt-grenze)
- [Windows-Store-Artefakte](#windows-store-artefakte)
- [Technik](#technik)
- [Sicherheitsrichtlinie](#sicherheitsrichtlinie)
- [Lizenz](#lizenz)
- [Haftung](#haftung)

## Einstieg

| Eigenschaft | Details |
|---|---|
| **Tech Stack** | Python 3.10+ / PySide6 (Qt) / QSettings |
| **Lizenz** | MIT (PySide6 dynamisch gelinkt unter LGPLv3) |
| **Austauschformat** | `softwarecenter-profile-v1.json` (siehe [EXPORTFORMAT.md](EXPORTFORMAT.md)) |
| **Letzte Prüfung** | 2026-09-07 (lokal: 182 Tests, Plattform-Smokes, Compileall, JSON, Export-Fixture, Produktgrenz-Prozess-/Artefaktprüfung; WACK weiterhin nur Dry-Run) |

## Funktionen

- **Tab-Organisation** - Programme in benennbare, verschiebbare Tabs gruppieren
- **Drag & Drop** - Dateien per Drag & Drop hinzufügen
- **Zwei Ansichtsmodi** - Kacheln (große Icons) und Liste
- **Automatische Speicherung** - Tabs, Inhalte und Fensterposition bleiben erhalten
- **Kontextmenü** - Rechtsklick zum Öffnen oder Entfernen
- **Cross-Platform** - Windows, macOS und Linux
- **Native Icons** - Automatische Anzeige der System-Anwendungsicons
- **Windows-Verknüpfungen** - `.lnk`-Dateien mit `.exe`- oder Ordnerziel werden beim Hinzufügen als Originalziel gespeichert
- **macOS-App-Bundles** - `.app`-Programme lassen sich per Drag & Drop hinzufügen
- **Linux-Desktop-Starter** - `.desktop`-Launcher werden mit ihrem App-Namen angezeigt und korrekt gestartet
- **Profil-Export/Import** - Versioniertes Austauschformat `softwarecenter-profile-v1.json` für Migrationen und Backups
- **Mehrfachauswahl** - Mehrere Einträge können gemeinsam gelöscht werden
- **Offline-first** - keine Telemetrie, keine Accounts, keine Cloud-Anbindung

## Systemarchitektur

```mermaid
graph TD
    A["Benutzer / Drag & Drop Eingabe"] --> B["PySide6 Hauptfenster (SoftwareCenter.py)"]
    B --> C["Tab- & Board-Verwaltung"]
    B --> D["Kachel- & Listenansichten"]
    
    C --> E["Plattform-Auflösung"]
    E --> E1["Windows (.lnk / .exe / Ordner)"]
    E --> E2["macOS (.app Bundles)"]
    E --> E3["Linux (.desktop Launcher)"]
    
    C --> F["Status-Persistenz (QSettings / Registry)"]
    C --> G["JSON-Profil Import/Export (softwarecenter-profile-v1.json)"]
    
    B --> H["Windows Store & Build-Pipeline"]
    H --> H1["PyInstaller EXE Build"]
    H --> H2["WACK Dry-Run / MSIX-Paketierung"]
    H --> H3["Reproduzierbarer Store-Screenshot-Generator"]
```

## Lebenszyklus-Ablaufdiagramm

```mermaid
sequenceDiagram
    autonumber
    actor User as Desktop-Nutzer
    participant SC as SoftwareCenter UI (PySide6)
    participant Res as Plattform-Auflöser (.lnk / .app / .desktop)
    participant Tab as Tab- & Board-Manager
    participant Set as QSettings-Persistenz (Registry / INI)
    participant Exp as Profil-Exporter (softwarecenter-profile-v1.json)

    User->>SC: Datei / Verknüpfung per Drag & Drop ablegen
    SC->>Res: Pfad auflösen (z. B. .lnk -> reales EXE-/Ordner-Ziel)
    Res-->>SC: Valider Zielpfad & Systemicon ermittelt
    SC->>Tab: Duplikatprüfung & Element im Board registrieren
    Tab->>SC: Kachel- / Listenzeile rendern
    Tab->>Set: Tabs, Reihenfolge & Fenstergeometrie atomar speichern
    Set-->>SC: Zustand lokal persistent gesichert
    User->>SC: Doppelklick zum Start oder "Profil exportieren"
    alt Programm starten
        SC->>User: Zielanwendung mit normalen Nutzerrechten ausführen
    else Profil exportieren
        SC->>Exp: Boards, Tabs und Einträge serialisieren
        Exp-->>User: Bereinigte softwarecenter-profile-v1.json schreiben (Null Secrets)
    end
```

## Kernfähigkeiten & Sicherheitsinvarianten

| Invariante / Fähigkeit | Architektur-Garantie | Verifikations-Mechanismus |
|---|---|---|
| **100% Local-First & Zero Egress** | Agiert rein lokal auf dem Client; keinerlei Telemetrie, kein Cloud-Tracking, keine Remote-Netzwerkaufrufe | Quellcode-Audit, Offline-Laufzeitcheck, Testsuite |
| **Unprivilegierter Betrieb (Non-Elevation)** | Läuft strikt mit Standard-Benutzerrechten; verlangt niemals UAC-Administratorrechte | Prozess-Sicherheitsdeskriptor-Prüfung |
| **Nicht-destruktive Verknüpfungsverwaltung** | Das Entfernen eines Eintrags löscht lediglich die UI-Referenz; niemals die Zieldatei auf der Festplatte | UI-Entfernungs-Isolationstests |
| **Sichere Pfad- & Link-Auflösung** | Löst Windows `.lnk`, macOS `.app` und Linux `.desktop` Ziele auf, ohne Skripte oder Befehle auszuführen | Statische Pfadauflösungs-Vertragstests |
| **Atomare Status-Persistenz** | QSettings sichert Fenstergeometrie, Tab-Anordnung und aktive Ansichtsmodi sicher im Betriebssystem | Atomare Roundtrip-Persistenztests |
| **Portables & Bereinigtes Austauschformat** | Schema-validierter JSON-Export (`softwarecenter-profile-v1.json`) ohne Passwörter, Token oder Secrets | `tests/test_export_contract.py` Regressionstests |
| **Schwesterprodukt-Isolation** | Getrennte QSettings-Namespaces, Mutex-Endpunkte und Store-Identitäten zwischen SoftwareCenter und LaunchBoards | `scripts/verify_product_boundaries.py` |
| **Multi-OS CI-Matrix-Garantie** | Validiert für Python 3.10-3.12 auf Windows, macOS und Linux Runnern | GitHub Actions Workflows und Plattform-Smokes |

## Geschwister-Ökosystem & Schwesterprodukte

SoftwareCenter ist fest verankert in der Desktop-Suite von **file-bricks** und der Open-Source-Dachorganisation **open-bricks**:

| Projekt | Ökosystem | Hauptfokus | Integration & Synergie |
|---|---|---|---|
| [`ProFiler`](https://github.com/file-bricks/ProFiler) | `file-bricks` | Dokument- & Dateiinspektion | Ergänzungs-App für Dateianalyse und forensische Profilierung |
| [`ExplorerPro`](https://github.com/file-bricks/ExplorerPro) | `file-bricks` | Mehr-Tab-Dateimanager | Komplementäre Dual-Pane-Dateiverwaltung für Desktop-Verknüpfungen |
| [`CloudLockFixer`](https://github.com/file-bricks/CloudLockFixer) | `file-bricks` | Cloud-Lock Diagnose & Entsperrung | Entsperrt blockierte Sync-Dateien und verknüpfte OneDrive-Ordner |
| [`knowledgedigest`](https://github.com/file-bricks/knowledgedigest) | `file-bricks` | Markdown- & Wissensbibliothek | Lokaler Wissens-Organizer für rechercheintensive Workflows |
| [`FormularErstellen`](https://github.com/doc-bricks/FormularErstellen) | `doc-bricks` | Formular- & Vorlagenerstellung | Desktop-Generator direkt über SoftwareCenter-Kacheln startbar |
| [`USR_PDFunlock`](https://github.com/doc-bricks/USR_PDFunlock) | `doc-bricks` | PDF-Passwort- & Berechtigungshelfer | Nicht-destruktive lokale PDF-Entsperrung |
| [`safe-start-for-codex`](https://github.com/dev-bricks/safe-start-for-codex) | `dev-bricks` | Automations-Anlaufschranke | Schützt Entwickler-Workstations vor Überlastungsspitzen beim Boot |
| [`MethodenAnalyser`](https://github.com/dev-bricks/MethodenAnalyser) | `dev-bricks` | AST-Quellcode-Analyse | Statische Analyse für Python-Desktop-Programme und Module |
| [`connectors`](https://github.com/ellmos-ai/connectors) | `ellmos-ai` | Agenten-Kommunikationsbrücke | Abhängigkeitsfreie Messaging- und Transport-Adapter |
| [`open-bricks`](https://github.com/open-bricks) | `open-bricks` | Open-Source-Desktop-Dach | Standards, Governance und plattformübergreifendes Packaging |

## Auffindbarkeit

SoftwareCenter ist am besten als **lokaler PySide6-App-Launcher** oder **Desktop-Shortcut-Organizer** einzuordnen. Das Tool liegt zwischen Windows-Startmenü, Desktop-Verknüpfungsordnern und großen Software-Inventarsystemen: Es startet vorhandene Programme, gruppiert Verknüpfungen in Tabs und exportiert/importiert portable Profile.

Nützliche Suchphrasen:

- `SoftwareCenter PySide6 Desktop Organizer`
- `lokaler App Launcher Python PySide6`
- `Desktop Verknüpfungen in Tabs organisieren`
- `softwarecenter-profile-v1.json`
- `Offline Software Launcher ohne Cloud ohne Telemetrie`

Es ist nicht Microsoft Configuration Manager Software Center, kein App Store, kein Paketmanager und kein Remote-Deployment-Portal.

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

Unter Windows auch per `START.bat`. Für eine lokale EXE-Aktualisierung ist zusätzlich `build_exe.bat` vorhanden.

## Verwendung

| Aktion | Anleitung |
|--------|-----------|
| Programme hinzufügen | Dateien, Ordner, Verknüpfungen, unter macOS `.app`-Bundles oder unter Linux `.desktop`-Starter ins Fenster ziehen; Windows-`.lnk`-Dateien mit `.exe`- oder Ordnerziel werden auf das Originalziel aufgelöst |
| Tabs organisieren | Toolbar > "Neuer Tab", Doppelklick zum Umbenennen |
| Ansicht wechseln | Toolbar > Kacheln / Liste |
| Programme starten | Doppelklick oder Rechtsklick > Öffnen/Starten |
| Einträge entfernen | Rechtsklick > Löschen (entfernt nur die Verknüpfung) |
| Profil exportieren | `Datei > Profil exportieren` oder Toolbar-Aktion |
| Profil importieren | `Datei > Profil importieren` oder Toolbar-Aktion; ersetzt das aktuelle Profil |

## EXE erstellen

```bash
build_exe.bat

# oder direkt
python -m PyInstaller --noconfirm --clean SoftwareCenter.spec
```

Die EXE liegt anschließend in `dist/SoftwareCenter.exe` und wird durch `build_exe.bat` zusätzlich nach `SoftwareCenter.exe` im Projektwurzelverzeichnis kopiert.

## Qualitätssicherung

```bash
python -m compileall -q SoftwareCenter.py manage_translations.py translator.py
python -m json.tool locales/translations.json
python -m json.tool store_package.json
python -m pytest -q
python tests/macos_platform_smoke.py
python tests/linux_platform_smoke.py
python scripts/verify_product_boundaries.py
```

Der gehostete Workflow und seine ausdrückliche Grenze für den optionalen
Web-Companion sind in [CI_CONTRACT.md](CI_CONTRACT.md) dokumentiert.

Die GitHub Actions führen diese Smoke-Checks ebenfalls aus; der macOS-Job prüft `.app`-Import, `open`-Startpfad, QSettings und den Profil-Export headless auf `macos-latest`, der Linux-Job zusätzlich `.desktop`-Import, `Exec`-/`xdg-open`-Startpfade, QSettings und den Profil-Export auf `ubuntu-latest`. Build-Artefakte wie `SoftwareCenter.exe`, `build/`, `dist/`, `releases/` und lokale Aufgaben-/Testdateien bleiben per `.gitignore` außerhalb des Repos.

Für den Windows-Store-Pfad prüft `python scripts/run_windows_wack.py --dry-run` die lokalen MSIX/AppCert-Pfade und gibt den reproduzierbaren WACK-Befehl aus. Der eigentliche Zertifizierungslauf sollte aus einer erhöhten PowerShell gegen ein frisch signiertes MSIX vor der Einreichung ausgeführt werden.

## Headless-Katalogpflege

Die optionale Katalogroutine liegt als Plan-D-Runtime-Code unter
`scripts/softwarecenter_sync.py`. Synchronisierte Katalog- und Registry-Dateien
werden als explizite CLI-Eingaben übergeben; ohne `--apply` bleibt der Lauf
read-only. Der gepinnte Scheduler-Payload, Apply-Gates, native Readbacks und das
Rollback stehen in [RUNTIME_DAILY_CARE.md](RUNTIME_DAILY_CARE.md).

## Austauschformat

Profile lassen sich als `softwarecenter-profile-v1.json` exportieren und wieder importieren. Das Format enthält Tabs, Ansichtsmodus und Einträge mit `label`, `path`, `kind` und optionalen `notes`, aber keine kopierten Dateien und keine Credentials. Details stehen in [EXPORTFORMAT.md](EXPORTFORMAT.md).

## Schwesterprodukt-Grenze

LaunchBoards nutzt denselben Unterbau, besitzt aber einen eigenen
QSettings-Namespace, Single-Instance-Endpunkt, ein eigenes Icon, Executable,
eine eigene Store-Identität und einen getrennten Releasepfad. Die
reproduzierbaren statischen, isolierten Parallelprozess- und Artefaktprüfungen
sind in [PRODUCT_BOUNDARIES.md](PRODUCT_BOUNDARIES.md) dokumentiert.

## Windows-Store-Artefakte

Der Windows-Store-Track beinhaltet einen reproduzierbaren Screenshot-Generator für
die aktuelle Desktop-Benutzeroberfläche. `python generate_store_screenshots.py`
aktualisiert `README/screenshots/store/` mit vier bereinigten Store-Grafiken und `summary.json`.

## Technik

| Komponente | Technologie |
|------------|------------|
| Sprache | Python 3.10+ |
| GUI-Framework | PySide6 (Qt for Python) |
| Speicherung | QSettings (Windows Registry / INI) |
| Codeumfang | ~690 Zeilen |

## Sicherheitsrichtlinie

Sicherheit und Datenschutz stehen an erster Stelle. Siehe [SECURITY.md](SECURITY.md) für vollständige Richtlinien zur Meldung von Schwachstellen, unser 48-Stunden-SLA und die Kern-Invarianten.

## Lizenz

[MIT](LICENSE)

**Hinweis:** Diese Anwendung verwendet [PySide6](https://doc.qt.io/qtforpython-6/), lizenziert unter LGPLv3. PySide6 wird dynamisch gelinkt.

---

## Haftung

Dieses Projekt ist eine **unentgeltliche Open-Source-Schenkung** im Sinne der §§ 516 ff. BGB. Die Haftung des Urhebers ist gemäß **§ 521 BGB** auf **Vorsatz und grobe Fahrlässigkeit** beschränkt. Ergänzend gelten die Haftungsausschlüsse der MIT-Lizenz.

Nutzung auf eigenes Risiko. Keine Wartungszusage, keine Verfügbarkeitsgarantie, keine Gewähr für Fehlerfreiheit oder Eignung für einen bestimmten Zweck.
