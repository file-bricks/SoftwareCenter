# SoftwareCenter — Windows Store Build-Anleitung

Stand: 2026-11-08 (Tier-2 6-Sprachen Store-Readiness nach Policy P-006)

## Voraussetzungen

1. Python 3.10+ (Standard)
2. PyInstaller (`pip install pyinstaller`)
3. Windows SDK (für `makeappx.exe` und `signtool.exe`)
4. Code-Signing-Zertifikat (.pfx) für lokale MSIX-Signierung
5. Microsoft Store Entwicklerkonto (Partner Center, Store-ID `9NHZN7S3FD5F`)

## Schritt 1: EXE bauen

**WICHTIG:** IMMER über `build_exe.bat` bauen — nicht über einen freien `pyinstaller`-Aufruf ohne Flags.
Grund: `build_exe.bat` bündelt alle geforderten Assets, Locales und Bibliotheken.

```cmd
cd "C:\_Local_DEV\repos\SoftwareCenter"
build_exe.bat
```

Ergebnis: `SoftwareCenter.exe` bzw. `dist\SoftwareCenter\SoftwareCenter.exe`.

## Schritt 2: Preflight-Audit ausführen

Vor jeder MSIX-Paketierung und Einreichung muss der automatisierte Store-Readiness-Linter erfolgreich durchlaufen:

```cmd
python scripts\check_store_readiness.py
```

Erwartetes Ergebnis: `STORE READINESS CHECK PASSED (0 findings)`.

## Schritt 3: MSIX-Paket erstellen

Das MSIX-Paket wird über `makeappx.exe` anhand des Staging-Verzeichnisses `store_package/SoftwareCenter` gebaut:

```cmd
"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\makeappx.exe" pack /d "store_package\SoftwareCenter" /p "releases\windowsstore\SoftwareCenter.msix"
```

## Schritt 4: Signierung (für lokale Tests / Sideloading)

```cmd
"C:\Program Files (x86)\Windows Kits\10\App Certification Kit\signtool.exe" sign /fd SHA256 /a /f "<PFAD_ZUR_PFX>" /p "<PASSWORT>" /tr http://timestamp.digicert.com /td SHA256 "releases\windowsstore\SoftwareCenter.msix"
```

*Hinweis für Store-Einreichung:* Für den direkten Upload ins Microsoft Partner Center ist keine manuelle PFX-Signierung erforderlich; Microsoft signiert das hochgeladene Paket im Rahmen der Store-Zertifizierung automatisch.

## Schritt 5: WACK-Zertifizierungstest

Führe das Windows App Certification Kit aus:

```cmd
python scripts\run_windows_wack.py
```

oder direkt:

```cmd
appcert.exe test -appxpackagepath "releases\windowsstore\SoftwareCenter.msix" -reportoutputpath "releases\windowsstore\wack_report.xml"
```

## Schritt 6: Microsoft Partner Center Upload

1. Im Partner Center unter der reservierten App-Identität `Geiger.SoftwareCenter` (Store-ID `9NHZN7S3FD5F`) eine neue Übermittlung anlegen.
2. Das fertige Paket `SoftwareCenter.msix` hochladen.
3. Die 6-Sprachen Store-Listings aus `releases/windowsstore/store_listing_<lang>.md` in die jeweiligen Sprachfelder eintragen.
4. Screenshots und Kacheln hochladen.
5. Zur Zertifizierung einreichen.
