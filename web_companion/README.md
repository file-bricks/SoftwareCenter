# SoftwareCenter Companion

Der Ordner `web_companion/` enthält eine statische Web/PWA-Ansicht für
`softwarecenter-profile-v1.json`.

## Zweck

- Profilübersicht für Android, iPhone, iPad und Desktop
- Offline-Lesen des zuletzt geladenen Exportstands
- Filter nach Tab, Typ und Suchbegriff
- Keine Launcher-Funktion, keine Pfad-Ausführung, keine Cloud

## Start

```bash
cd web_companion
python -m http.server 4177
```

Danach im Browser öffnen:

- `http://127.0.0.1:4177/`
- `http://127.0.0.1:4177/?demo=1` für das eingebaute Demo-Profil

## Import

1. In der Desktop-App ein Profil als `softwarecenter-profile-v1.json` exportieren.
2. Im Companion `Profil importieren` wählen.
3. Der letzte geladene Stand bleibt lokal im Browser-Speicher für Offline-Starts erhalten.

## Qualität

```bash
node --test tests/library.test.mjs
node --check app.js
node --check library.js
```
