# Befunde — SoftwareCenter

**Erfasst am:** 2026-07-28  
**Rolle:** TICKET-MASTER / Plan-D-Handoff

## Entscheidung und Git-Provenienz

- Autorisierte Entscheidung `D-20260727-008`: lokalen Stand kontrolliert auf
  `origin/master` rebasen, Commit und Icons erhalten, anschließend erneut
  testen.
- Der ursprüngliche lokale Commit `4ccb965` wurde auf den Remote-Stand
  `83ab6b3` rebaset und als `8dfa64f` fortgeführt. `c89960c` dokumentierte den
  ersten Closeout.
- Die auf dem Remote bereits bewusst entfernte `web_companion`-Implementierung
  bleibt entfernt. Eine durch den Rebase übernommene, dadurch unzutreffende
  PWA-Zeile im Changelog wurde ebenfalls entfernt.
- Die im bisherigen OneDrive-Arbeitsstand enthaltenen
  `BUGSWEEP-41`-Pfadprüfungen wurden als eigener, testbarer Codebestand
  übernommen. Unabhängige Typografieänderungen sind keine Voraussetzung für
  diesen Fix.
- Die autorisierten Icon-Masterdateien wurden bitgenau erhalten:
  `SoftwareCenter.ico`
  (`4052B690501B8D0BCE19270A4DEDC7136B4995D84EA11BFF72D657B01565CDBC`)
  und `SoftwareCenter.png`
  (`BA3DF6B23BE8DF0706EE632CC9C5C282703E9468C3A644ABE1B886F7E0F02125`).

## Verifikation

- `python -m pytest -q`: **124 bestanden**
- Die portable Katalogroutine besitzt separat **12 bestandene Tests**,
  einschließlich read-only Daily Care, leerem/fehlerhaftem Scan,
  `SUPPRESSED`-Erhalt, Idempotenz, Prozess-Abbruch und
  Backup/Wiederherstellung beider Profile.
- Der reale Daily-Care-Lauf erkannte 59 Katalog-, Registry- und
  Kandidateneinträge. Drei fehlende Startziele und acht nur geplante
  Profiländerungen wurden gemeldet; es wurde keine Profil- oder
  Registry-Mutation vorgenommen.

## Tägliche Betriebsroutine

Der headless Job `softwarecenter.launchboards.daily-care` ist im
`ellmos-scheduler` für täglich 06:20 Uhr Europe/Berlin registriert und im
Automation Master als read-only, vergleichbare Automatisierung erfasst. Die
versteckte Windows-Aufgabe
`ellmos SoftwareCenter LaunchBoards Daily Care` führt täglich genau einen
Scheduler-Tick aus, holt verpasste Starts nach und vermeidet parallele
Instanzen. Ein kontrollierter Hintergrundstart endete mit Resultat `0`; der
Scheduler bestätigte dabei einen neuen `last_tick_at`. Damit ist die tägliche
Ausführung auf WORKSTATION-LG aktiviert, ohne sichtbares Fenster.
