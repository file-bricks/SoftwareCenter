# Security Policy / Sicherheitsrichtlinie

[English](#english) | [Deutsch](#deutsch)

---

<a name="english"></a>
## English

### Supported Versions

We provide security updates and patches for the following versions of SoftwareCenter:

| Version | Supported | Status |
|---------|-----------|--------|
| `1.2.x` | :white_check_mark: | Active Security Support |
| `1.1.x` | :white_check_mark: | Maintenance / Critical Fixes Only |
| `< 1.1.0` | :x: | End of Life (Upgrade Recommended) |

### Reporting a Vulnerability

If you discover a potential security vulnerability in SoftwareCenter, please do NOT open a public issue. We follow coordinated vulnerability disclosure:

1. **GitHub Private Vulnerability Reporting (Preferred):**
   Navigate to **Security > Advisories > Report a vulnerability** in the GitHub repository to open a confidential report.
2. **Direct Contact:**
   Send an email to:
   - `security@open-bricks.org`
   - `support@lukasgeiger.com`
   - `lukas@open-bricks.org`

Include as much information as possible:
- Steps to reproduce the issue
- Proof of Concept (PoC) or sample data
- Potential impact and affected components
- SoftwareCenter version and operating system environment

### Response SLA

- **Initial Response & Confirmation:** Within **48 hours**.
- **Triage & Severity Assessment:** Within **5 business days**.
- **Remediation & Patch Release:** Coordinated patch published via GitHub release and private advisory disclosure.

### Core Security Invariants

SoftwareCenter is designed with a defense-in-depth, local-first architecture:

1. **100% Local-First & Zero Network Egress:**
   The application operates strictly locally on your machine. It makes zero telemetry calls, contains no trackers, and communicates with no external cloud servers.
2. **Unprivileged Non-Elevation Execution:**
   SoftwareCenter runs entirely within standard user space. It never requests or requires administrative (UAC) elevation.
3. **Non-Destructive Shortcut Operations:**
   Removing or re-ordering items inside the UI only alters shortcut metadata in local settings; it never deletes, moves, or alters target application files.
4. **Safe Shell & Path Resolution:**
   Resolution of `.lnk` shortcuts, macOS `.app` bundles, and Linux `.desktop` entries is strictly restricted to filesystem target paths without executing arbitrary script content.
5. **Privacy-Preserving Profile Exchange:**
   The `softwarecenter-profile-v1.json` exchange format contains only public path pointers and layout configurations. It never extracts or exports passwords, tokens, or environment credentials.

---

<a name="deutsch"></a>
## Deutsch

### Unterstützte Versionen

Sicherheitsupdates und Patches werden für folgende SoftwareCenter-Versionen bereitgestellt:

| Version | Unterstützt | Status |
|---------|-------------|--------|
| `1.2.x` | :white_check_mark: | Aktiver Sicherheits-Support |
| `1.1.x` | :white_check_mark: | Wartungsmodus / Nur kritische Fehler |
| `< 1.1.0` | :x: | End of Life (Upgrade empfohlen) |

### Melden einer Schwachstelle

Wenn Sie eine Sicherheitslücke in SoftwareCenter vermuten, eröffnen Sie bitte KEIN öffentliches Issue. Wir bitten um vertrauliche Koordinierung:

1. **GitHub Private Vulnerability Reporting (Bevorzugt):**
   Navigieren Sie im GitHub-Repository zu **Security > Advisories > Report a vulnerability** für einen vertraulichen Bericht.
2. **Direkter Kontakt:**
   Senden Sie eine E-Mail an:
   - `security@open-bricks.org`
   - `support@lukasgeiger.com`
   - `lukas@open-bricks.org`

Bitte fügen Sie Ihrem Bericht folgende Details bei:
- Schritte zur Reproduktion der Schwachstelle
- Proof-of-Concept (PoC) oder Beispieldaten
- Potenzielle Auswirkungen und betroffene Komponenten
- SoftwareCenter-Version und Betriebssystemumgebung

### Reaktionszeiten (SLA)

- **Erste Rückmeldung:** Innerhalb von **48 Stunden**.
- **Triage & Risikobewertung:** Innerhalb von **5 Werktagen**.
- **Bereitstellung eines Fixes:** Koordiniertes Release über GitHub-Advisory und neue Patch-Version.

### Sicherheits- und Datenschutz-Invarianten

1. **100% Local-First & Null Datenausleitung (Zero Egress):**
   SoftwareCenter agiert vollständig lokal auf Ihrem Desktop. Es werden keinerlei Telemetriedaten, Trackingsignale oder Cloud-Synchronisationen ausgeführt.
2. **Unprivilegierter Betrieb (Non-Elevation):**
   Die Anwendung läuft strikt mit Standard-Benutzerrechten und verlangt niemals UAC-Administratorrechte.
3. **Nicht-destruktive Desktop-Operationen:**
   Das Löschen eines Eintrags in der UI entfernt lediglich den Verweis im Profil, löscht jedoch niemals die referenzierte Originaldatei oder Anwendung auf der Festplatte.
4. **Sichere Verknüpfungsauflösung:**
   Die Auflösung von `.lnk`-Dateien, macOS `.app`-Bundles und Linux `.desktop`-Dateien liest ausschließlich Dateipfade aus und führt niemals ungesicherten Skriptcode aus.
5. **Datenschutzfreundliches Profilformat:**
   Das Profilformat `softwarecenter-profile-v1.json` exportiert ausschließlich Layout- und Pfadkonfigurationen. Passwörter, Sitzungstoken oder Zugangsdaten verbleiben unberührt.
