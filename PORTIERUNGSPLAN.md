# Portierungsplan - SoftwareCenter

Stand: 2026-05-24

## Kurzentscheidung

SoftwareCenter bleibt zuerst eine plattformübergreifende Desktop-App auf Basis von Python und PySide6. Das ist für den Zweck des Projekts der richtige Schwerpunkt, weil der Kernnutzen im Starten lokaler Programme, Skripte, `.app`-Bundles und `.desktop`-Starter liegt. Dieser Nutzen ist auf Windows, macOS und Linux direkt vorhanden, auf Android/iOS aber nur eingeschränkt, weil mobile Betriebssysteme keinen freien Zugriff auf beliebige lokale Desktop-Programme erlauben.

Die bevorzugte Erweiterung ist deshalb:

1. Windows Store als erster Distributionskanal für die Desktop-App.
2. macOS- und Linux-Builds als P2/P3-Desktop-Ziele aus derselben Codebasis.
3. Web/PWA nur als Companion für App-Kataloge, Startlisten, Dokumentation und Export/Import.
4. Android/iOS über diese PWA statt als nativer Clone.
5. Austauschformat `softwarecenter-profile-v1.json`, damit Desktop-Profile später in Web/Mobil-Companion oder andere Desktop-Installationen übernommen werden können.

## Warum plattformübergreifend sinnvoll ist

- Nachfrage: Der Nutzen ist für Power-User, Entwickler und Personen mit vielen Werkzeugen nicht Windows-spezifisch.
- Mobilität: Auf mobilen Geräten ist kein vollwertiger lokaler App-Launcher realistisch, aber eine synchronisierte Übersicht der eigenen Tool-Sammlung kann nützlich sein.
- Usecases: Desktop bleibt Arbeitsstation und Launcher; Web/Mobil dient als Inventar, Notizzettel, Setup-Checkliste und portable Referenz.
- Wartung: PySide6 und QSettings unterstützen bereits Windows, macOS und Linux; getrennte native Mobile-Apps hätten deutlich mehr Aufwand bei geringerem Kernnutzen.

## Optionenbewertung

| Option | Bewertung | Entscheidung |
|---|---|---|
| Windows Store Release | Sehr sinnvoll. Passt zur Store-Pipeline, Zielgruppe und vorhandenen MSIX-Vorarbeit. | P0/P1 umsetzen. |
| Android Version oder Clone | Als nativer Clone nicht sinnvoll, weil mobile Sandboxes keine Desktop-Programme starten. | Nur PWA-Companion als P2. |
| Webapp | Sinnvoll als Profil-Viewer, Katalog, Exportprüfung und Setup-Checkliste. | P2 nach Exportformat. |
| iOS Version | Native App derzeit nicht sinnvoll aus denselben Sandbox-Gründen wie Android. | Über PWA mit iOS-Testmatrix abdecken. |
| Mac App | Sinnvoll, weil `.app`-Bundles bereits unterstützt werden. | P2 Build-/Smoke-Ziel. |
| Linux Version | Sinnvoll, weil `.desktop`-Starter bereits unterstützt werden. | P2 Build-/Smoke-Ziel. |

## Zielarchitektur

### Desktop-Linie

- Codebasis bleibt `SoftwareCenter.py` mit PySide6.
- Windows bleibt Referenzplattform und Store-Ziel.
- macOS und Linux werden als Source-/Build-Ziele mit Smoke-Tests geführt.
- Plattformlogik bleibt klein und explizit: Windows `os.startfile`, macOS `open`, Linux `.desktop`/`xdg-open`.

### Web/Mobil-Companion

- Keine direkte Launcher-Funktion.
- Fokus auf Profilansicht, Kategorien, App-Liste, Notizen, Setup-Status und Exportvalidierung.
- PWA genügt für Android/iOS/Web, solange keine echte mobile Systemintegration benötigt wird.

### Austauschformat

Geplantes Format: `softwarecenter-profile-v1.json`

Mindestfelder:

- `format_version`
- `exported_at`
- `source_platform`
- `app_version`
- `tabs[]`
- `tabs[].name`
- `tabs[].view_mode`
- `tabs[].entries[]`
- `entries[].label`
- `entries[].path`
- `entries[].kind` (`file`, `windows_shortcut`, `mac_app`, `linux_desktop`, `script`, `url`, `unknown`)
- `entries[].notes`

Der Export darf keine lokalen Dateien kopieren und keine Credentials enthalten. Er beschreibt nur die Launcher-Struktur.

## Umsetzungspfad

| Priorität | Aufgabe | Ergebnis |
|---|---|---|
| P0 | `softwarecenter-profile-v1.json` spezifizieren und Export/Import als CLI oder Menüaktion planen. | Desktop-Profile werden übertragbar. |
| P1 | Windows-Store-Submission abschließen: Store-Screenshots, Signierung, WACK-Protokoll, Store-Testprotokoll. | Einreichfähiges Windows-Paket. |
| P2 | macOS- und Linux-Smoke-Tests dokumentieren und in CI/Release-Checkliste aufnehmen. | Cross-Platform-Versprechen ist überprüfbar. |
| P2 | Web/PWA-Companion als statische Profilansicht aus dem Exportformat konzipieren. | Android/iOS/Web werden ohne nativen Clone abgedeckt. |
| P3 | Native Android-/iOS-App erst neu bewerten, falls konkrete Nachfrage nach mobiler Inventarverwaltung entsteht. | Kein unnötiger Mobile-Fork. |

## Status

- Windows: funktionsfähig, Store-Pipeline vorhanden, Store-Einreichung noch nicht vollständig abgeschlossen.
- macOS: `.app`-Bundles werden akzeptiert; Build- und Smoke-Dokumentation fehlt.
- Linux: `.desktop`-Starter werden gelesen und gestartet; Build- und Smoke-Dokumentation fehlt.
- Web/Mobil: noch nicht begonnen; sinnvoller Startpunkt ist das Exportformat.
