# SoftwareCenter — ROADMAP

> Strategische Ideen und geplante Erweiterungen. Status-Schnappschuss; abgeschlossene Punkte wandern ins CHANGELOG.

## Vision: Universeller Ordnungslayer außerhalb des Dateisystems

SoftwareCenter soll **nicht nur App-Verknüpfungen** aufnehmen, sondern **alles, was man ablegen will** — Verknüpfungen, Dokumente, Ordner, Dateien, URLs. Der Nutzer ordnet Dinge frei in Tabs/Boards, **unabhängig davon, wo sie physisch im Dateisystem liegen**. Damit wird SoftwareCenter zu einem zweiten Ordnungslayer **über** dem Dateisystem.

- **Bereits unterstützt (technisch):** Drag & Drop von Dateien, Ordnern, `.lnk`-Verknüpfungen, `.url`, Skripten und Dokumenten. Intern unterscheidet die Engine schon die Typen `file`, `directory`, `windows_shortcut`, `url`, `script`, `mac_app`, `linux_desktop` (siehe `detect_entry_kind` / `is_supported_launch_target`).
- **Auszubauen:**
  - Klar kommunizieren, dass **beliebige** Dateien/Ordner/Dokumente ablegbar sind (nicht nur EXEs) — UI-Hinweis, Doku, Store-Listing.
  - Komfort für Nicht-App-Einträge: Kontextmenü „Im Explorer anzeigen", optionale Vorschau/Notiz, Sortierung.
  - Robustes Verhalten bei fehlenden Zielen (Eintrag bleibt sichtbar, klare Warnung).

## Idee: Zwillings-Produkt „Project-Boards"

Eine **identische Variante** des SoftwareCenter unter eigenem Namen **„Project-Boards"** herausbringen — positioniert als **eigenständiges, zweites Ordnungslayer außerhalb des Dateisystems** (Projekt-/Themen-Boards statt App-Launcher).

- **Gleiche Code-Basis, andere Positionierung/Branding:** SoftwareCenter = Fokus App-Launcher; Project-Boards = allgemeines Projekt-/Ordnungs-Board (Verknüpfungen, Dokumente, Ordner, Notizen je Projekt/Thema in eigenen Boards/Tabs).
- **Umsetzung:**
  - Identische Engine; separater Name, Icon, Store-Listing.
  - **Eigener QSettings-Namespace** (z. B. `QSettings("LukasGeiger", "ProjectBoards")`), damit beide Programme **parallel** mit getrennten Profilen laufen.
  - Gemeinsamer Kern als Modul, dünne App-Wrapper je Produkt — vermeidet Code-Duplikation.
  - Profil-Austauschformat (`softwarecenter-profile-v1.json`) für beide nutzbar.

## Offene technische Nachsorge (aus Build-/Reparaturlauf 2026-06-27)

- `build_exe.bat` nutzt feste Spec-Excludes statt `build_exclude_scanner.py` (Abweichung von BUILD-VERFAHREN §3/§4) — bei Gelegenheit angleichen.
- onedir-Builds erzeugen große `_internal/`-Strukturen in OneDrive (Sync-Last) — für Releases onefile bevorzugen, wo sinnvoll.
