# Releases

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
