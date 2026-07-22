# SoftwareCenter Store-Vertrag

Stand: 2026-07-22

`store_package.json` ist die kanonische, versionierte Metadatenquelle. Die
lokale Packaging-Einstellung und das Staging-Manifest müssen sie abbilden, nicht
eigenständig abweichen.

| Feld | Kanonischer Wert |
|---|---|
| App / Identity | `SoftwareCenter` / `Geiger.SoftwareCenter` |
| Publisher | `CN=52596601-BAB4-4F3F-B182-E8F3F273B202` / `Geiger` |
| Version / EXE | `1.0.0.0` / `SoftwareCenter.exe` |
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
python -m json.tool releases/windowsstore/store_settings.json
[xml](Get-Content -Raw releases/windowsstore/msix_staging/AppxManifest.xml)
```

Danach Identity, Publisher, Version, `Application/@Executable`, die zwei
Ressourcen und `rescap:Capability/@Name` gegen die Tabelle vergleichen.
