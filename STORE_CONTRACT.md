# SoftwareCenter Store-Vertrag

Stand: 2026-08-25

## Release- und Artefaktstatus

Es gibt am 2026-08-25 **keinen gültigen Store-Einreichkandidaten**. Die
Statusquellen werden deshalb ausdrücklich getrennt:

| Quelle | Readback | Bedeutung |
|---|---|---|
| `pyproject.toml` | `1.2.0` | aktuelle Source-/Build-Linie |
| `SoftwareCenter.py` | `__version__ = 1.2.0` | Runtime-/Exportstand der Quelle |
| `store_package.json` | `1.2.0.0` | kanonischer Store-Metadatenstand |
| `releases/v1.2.0/SoftwareCenter-1.2.0-win64.exe` | SHA-256 `1AD7F9FE5AA89A004402E4F6833A67FBF85810C20B8444B3C634474F0B59C6C7` | lokal, unsigniert, nicht WACK-geprüft |

Die Versionen sind einheitlich harmonisiert (`1.2.0` / `1.2.0.0`). Privacy-URL,
Support-URL, Publisher, Identity, `runFullTrust` und Kategorie sind in den
Metadaten konsistent. Vor einem Store-Release muss ein frisch signiertes MSIX mit
echtem WACK-Report erstellt werden; aktuell wird kein Signing oder Upload behauptet.

`store_package.json` ist die kanonische, versionierte Metadatenquelle. Die
lokale Packaging-Einstellung und das Staging-Manifest müssen sie abbilden, nicht
eigenständig abweichen.

| Feld | Kanonischer Wert |
|---|---|
| App / Identity | `SoftwareCenter` / `Geiger.SoftwareCenter` |
| Publisher | `CN=52596601-BAB4-4F3F-B182-E8F3F273B202` / `Geiger` |
| Version / EXE | `1.2.0.0` / `SoftwareCenter.exe` |
| Capability | `runFullTrust` |
| Ressourcen | `en-us`, `de-de` |
| Kategorie | `Utilities & Tools` |
| Privacy / Support | GitHub `PRIVACY_POLICY.md` / Issues |

`releases/windowsstore/store_settings.json` ist eine lokale Build-Einstellung
und verwendet für `capabilities` denselben Wert `runFullTrust`. Das
`AppxManifest.xml` führt ihn als `rescap:Capability`. Dieser Abgleich bedeutet
keine Signierung, keinen MSIX-Build und keine Store-Einreichung.

## Wiederholbarer Readback

```powershell
python -m json.tool store_package.json
[xml](Get-Content -Raw _WARTUNG/msix_staging/AppxManifest.xml)
```

`releases/windowsstore/store_settings.json` ist eine lokale, nicht versionierte
Build-Einstellung und liegt nicht in jedem Arbeitsverzeichnis vor; das
versionierte Staging-Manifest steht unter `_WARTUNG/msix_staging/`.

Danach Identity, Publisher, Version, `Application/@Executable`, die zwei
Ressourcen und `rescap:Capability/@Name` gegen die Tabelle vergleichen.
