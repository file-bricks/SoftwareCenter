# Releases

## v1.2.0 — lokaler Build, keine Freigabe (Readback 2026-08-25)

`releases/v1.2.0/SoftwareCenter-1.2.0-win64.exe` ist lokal vorhanden und
hashgleich zur gespeicherten `SHA256SUMS.txt`:

- SHA-256: `1AD7F9FE5AA89A004402E4F6833A67FBF85810C20B8444B3C634474F0B59C6C7`
- Status: **UNSIGNIERT · NICHT WACK-ZERTIFIZIERT · KEIN STORE-RELEASE**
- Builddatum: 2026-07-29; Provenienz: `1e9e7dc626f5a4ff09fdce37bdbe0cb3975650b9`

Die Versionen in Runtime, pyproject.toml und store_package.json sind
einheitlich auf 1.2.0 / 1.2.0.0 harmonisiert. Bis ein frisches signiertes MSIX
mit echtem WACK-Readback erzeugt ist, bleibt der lokale Build ein Prüfartefakt.

## v1.0.0 — release block

Die lokale v1.0.0-EXE ist **nicht freigegeben**: Ihre beobachtete SHA-256
stimmt nicht mit der erhaltenen erwarteten Manifestzeile überein und die Datei
ist nicht signiert. Sie bleibt unverändert erhalten; kein Hash-Rewrite, Ersatz,
Upload oder Release folgt aus dieser Dokumentation. Der Source-ZIP-Hash ist
separat verifiziert. Der vollständige lokale Befund steht in
`releases/v1.0.0/PROVENANCE.md`.

Enthaltene Artefakte:

- `SoftwareCenter-1.0.0-win64.exe`
- `SoftwareCenter-1.0.0-source.zip`
- `CHANGELOG.txt`
- `SHA256SUMS.txt` (EXE-Zeile gesperrt, siehe Provenienz)

Build-Hinweise:

- Build-Entrypoint: `build_exe.bat`
- PyInstaller-Spec: `SoftwareCenter.spec`
- Store-Paket bleibt ein lokales Build-Artefakt und wird nicht im Git-Repository getrackt.
