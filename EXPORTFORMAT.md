# Exportformat `softwarecenter-profile-v1.json`

Stand: 2026-08-25

## Zweck

Das Austauschformat `softwarecenter-profile-v1.json` beschreibt ein SoftwareCenter-Profil portabel für:

- Desktop-zu-Desktop-Übernahmen zwischen Windows, macOS und Linux
- Backups und manuelle Profilmigrationen ohne direkten Zugriff auf `QSettings`

Der Export kopiert keine lokalen Dateien und enthält keine Credentials.

## JSON-Schema

```json
{
  "format": "softwarecenter-profile-v1",
  "format_version": 1,
  "app_version": "1.0.0",
  "source_platform": "win32",
  "exported_at": "2026-05-24T08:00:00Z",
  "current_tab": 0,
  "tabs": [
    {
      "name": "Werkzeuge",
      "view_mode": "tiles",
      "entries": [
        {
          "label": "Editor",
          "path": "C:/Tools/Editor.exe",
          "kind": "file",
          "notes": null
        }
      ]
    }
  ]
}
```

## Feldregeln

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `format` | String | Ja | Fester Formatname `softwarecenter-profile-v1` |
| `format_version` | Integer | Ja | Aktuell `1` |
| `app_version` | String | Ja | SoftwareCenter-Version beim Export |
| `source_platform` | String | Ja | Ursprungsplattform wie `win32`, `darwin`, `linux` |
| `exported_at` | String | Ja | UTC-Zeitstempel im ISO-8601-Format |
| `current_tab` | Integer | Ja | Aktiver Tab beim Export |
| `tabs` | Liste | Ja | Profilinhalt |
| `tabs[].name` | String | Ja | Sichtbarer Tabname |
| `tabs[].view_mode` | String | Ja | `tiles` oder `list` |
| `tabs[].entries` | Liste | Ja | Launcher-Einträge des Tabs |
| `entries[].label` | String | Ja | Sichtbares Label im UI |
| `entries[].path` | String | Ja | Referenzierter lokaler Pfad |
| `entries[].kind` | String | Ja | Eintragstyp |
| `entries[].notes` | String oder `null` | Nein | Optionale Notiz für Migrationshinweise |

## `kind`-Werte

- `file`
- `windows_shortcut`
- `mac_app`
- `linux_desktop`
- `script`
- `url`
- `unknown`

## Importverhalten

- Der Import ersetzt das aktuell geladene Profil.
- Fehlende lokale Pfade bleiben als Referenz sichtbar und werden nicht stillschweigend verworfen.
- Beim Öffnen eines fehlenden Pfads zeigt SoftwareCenter weiter eine Warnung an.
- Alte `QSettings` ohne `entries_json` bleiben lesbar; dann werden nur die bisherigen Pfadlisten übernommen.

## UI-Zugriff

- `Datei -> Profil exportieren`
- `Datei -> Profil importieren`
- dieselben Aktionen zusätzlich in der Toolbar

## Verifizierter Desktop-Readback (2026-08-25)

`tests/fixtures/profile_export_redacted.json` ist ein redigiertes Beispiel mit
zwei Tabs, Umlauten, `kind`/`notes` und einem absichtlich nicht vorhandenen
Pfad. `tests/test_export_contract.py` erzeugt zusätzlich einen echten
Desktop-Export in einem temporären Verzeichnis, liest ihn mit `json.loads` und
`validate_profile_payload` zurück und importiert ihn erneut in SoftwareCenter.
Der Readback bestätigt, dass Pfade nur Referenzen bleiben, Notizen UTF-8-fest
bleiben und keine Credential-/Token-/Password-Felder exportiert werden.

Der frühere `web_companion/`-Reader wurde am 2026-07-23 entfernt. Die CI prüft
seine Abwesenheit als bewusste Grenze; eine spätere Wiederaufnahme muss zuerst
`package.json`, `npm test` und die drei Node-Syntaxchecks mitbringen.
