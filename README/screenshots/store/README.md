# Store-Screenshots

Stand: 2026-06-17

## Reproduzierbare Erzeugung

```powershell
python generate_store_screenshots.py
```

Der Generator rendert die echte PySide6-Oberfläche in einem temporären
Arbeitsbereich mit redigierten Demo-Dateien. Private Pfade, echte Programme und
lokale Nutzerinhalte landen dadurch nicht im finalen Store-Set.

## Enthaltenes Screenshot-Set

1. `main-window.png` - Hauptfenster mit lokaler Launcher-Sammlung
2. `tab-organization.png` - mehrere Workflow-Tabs im selben Profil
3. `tiles-view.png` - Kachelansicht für schnellen Zugriff
4. `list-view.png` - Listenansicht für größere Sammlungen
5. `summary.json` - kompakte Inventarliste der erzeugten Artefakte

## Qualitätsregeln

- Keine privaten Dateinamen, realen Installationspfade oder Nutzerinhalte im Store-Set
- Einheitliche Fenstergröße und klare, helle Lesbarkeit
- Keine Build-Artefakte oder temporären Testordner sichtbar
