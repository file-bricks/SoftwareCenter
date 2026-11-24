---
name: softwarecenter
version: "1.2.0"
description: Cross-platform local-first PySide6 desktop organizer and headless CLI for managing boards, shortcuts, files, folders, HTTP(S) URLs, and portable softwarecenter-profile-v1.json profiles (SoftwareCenter & LaunchBoards).
---

# SoftwareCenter — Product & Agent Skill (`v1.2.0`)

## Purpose & Scope

SoftwareCenter (and its sister product profile **LaunchBoards**) is a local-first desktop organizer built with Python 3.10+ and PySide6. It groups references to local programs, documents, folders, scripts, Windows `.lnk` shortcuts, macOS `.app` bundles, Linux `.desktop` entries, and HTTP(S) URLs into persistent tab-based boards.

- **Version:** `1.2.0`
- **Repository:** `https://github.com/file-bricks/SoftwareCenter`
- **License:** MIT (`LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md`)
- **Quick machine index:** [`llms.txt`](llms.txt) (compatibility pointer: [`llm.txt`](llm.txt))

### When to use this skill

- Inspect, create, rename, close, reactivate, or favorite organizer boards headlessly.
- List, search, add, or remove launcher entries without opening a GUI window.
- Export, validate, or import portable `softwarecenter-profile-v1.json` profiles (`EXPORTFORMAT.md`).
- Validate or launch a registered target path/URL via the same resolution rules as the desktop UI.

### Non-goals & Boundaries

- **Not a package manager or app store:** SoftwareCenter does not download, install, or auto-update software.
- **No cloud sync or accounts:** All settings stay locally in `QSettings` (`LukasGeiger/SoftwareCenter` or `LukasGeiger/LaunchBoards`) or an explicit `--settings-file` INI file.
- **Non-destructive entry removal:** Removing an entry or closing a board never deletes files on disk.
- **Launch context:** Launching a target delegates to OS APIs (`os.startfile`/ShellExecute on Windows, `open` on macOS, `xdg-open` or `.desktop` `Exec` on Linux) and is not sandboxed.
- **Windows Store packaging vs. source:** Store/WACK certification is separate (`WINDOWS_STORE_PREP.md`); this skill documents verified source & CLI behavior.

---

## Installation & Prerequisites

```bash
pip install -r requirements.txt
# Optional editable install for `softwarecenter` / `launchboards` console scripts:
pip install -e .
```

- **Requirements:** Python `>=3.10`, `PySide6>=6.5.0`.
- **Headless environments (Linux CI/SSH):** Set `QT_QPA_PLATFORM=offscreen` only if GUI widgets are instantiated; `softwarecenter_cli.py` uses `QSettings` without opening any GUI window.

---

## Human vs. Agent Usage (Dual Use)

| Task | Human (Desktop GUI) | Agent / Script (Headless CLI) |
|---|---|---|
| Start GUI | `python SoftwareCenter.py` (or `python launchboards.py`) | Do **not** invoke without CLI args in headless runs |
| Check version | `Hilfe -> Über SoftwareCenter` | `python SoftwareCenter.py --version --json` |
| List boards | Hamburger panel (`Ctrl+B`) | `python SoftwareCenter.py --json boards list --include-closed` |
| Create / manage boards | Toolbar (`Ctrl+T`), tab context menu | `boards create`, `boards rename`, `boards close`, `boards reactivate`, `boards favorite` |
| Add / remove entries | Drag & drop, right-click `Remove` | `entries add <board> <target>`, `entries remove <board> <target>` |
| Search | Quick filter (`Ctrl+F`) or tray search | `python SoftwareCenter.py --json search "<query>"` |
| Export / import profile | `Datei -> Profil exportieren/importieren` | `profile export <out.json>`, `profile validate <in.json>`, `profile import <in.json> --yes` |
| Launch target | Double-click or `Enter` | `python SoftwareCenter.py --json launch "<target>" --dry-run` (or without `--dry-run`) |

---

## CLI Reference & Safe Workflows

### Global Options

- `--profile {softwarecenter,launchboards}`: Select product profile (`softwarecenter` default for `SoftwareCenter.py`; `launchboards` default for `launchboards.py`).
- `--settings-file <path.ini>`: Read/write an isolated INI file (`QSettings.Format.IniFormat`) instead of the user's live system `QSettings`. **Prefer `--settings-file` for dry-runs, migrations, and automated tests.**
- `--json`: Emit structured JSON on stdout (`{"ok": true, ...}` on success, `{"ok": false, "error": ..., "exit_code": ...}` on error).
- `-V, --version`: Print product name and version (`1.2.0`).

### Common Commands

```bash
# 1. Inspect boards & entries safely in JSON
python SoftwareCenter.py --json --settings-file ./profile.ini boards list --include-closed
python SoftwareCenter.py --json --settings-file ./profile.ini entries list --board "Allgemein"

# 2. Create a board and register a file/URL with notes
python SoftwareCenter.py --json --settings-file ./profile.ini boards create "Tools" --view list
python SoftwareCenter.py --json --settings-file ./profile.ini entries add "Tools" "https://example.org" --label "Docs" --notes "Reference"

# 3. Search across active and closed boards
python SoftwareCenter.py --json --settings-file ./profile.ini search "Docs" --include-closed

# 4. Validate and export/import portable profiles (softwarecenter-profile-v1)
python SoftwareCenter.py --json --settings-file ./profile.ini profile export ./backup.json
python SoftwareCenter.py --json profile validate ./backup.json
python SoftwareCenter.py --json --settings-file ./target.ini profile import ./backup.json --yes

# 5. Pre-check or launch a target
python SoftwareCenter.py --json --settings-file ./profile.ini launch "Docs" --board "Tools" --dry-run
```

### Guardrails, Side Effects & Exit Codes

- **Destructive replacement guard:** `profile import <file>` replaces all active tabs in the target profile and **refuses with exit code `2`** unless `--yes` is passed explicitly. Always run `profile validate` and `profile export` before importing into a live profile.
- **Last-tab protection:** `boards close` refuses with exit code `2` when only one active board remains (matching GUI behavior).
- **Ambiguous board names:** If multiple boards share the same name, pass the exact `board_id` returned by `boards list --json`.
- **Exit codes:**
  - `0` — Success (`"ok": true`)
  - `1` — OS / file I/O / launch error
  - `2` — Validation error, missing `--yes` confirmation, unknown board/entry, or invalid arguments

### Result Verification (Readback)

After any write command (`boards create`, `entries add`, `profile import`), verify persisted state with:

```bash
python SoftwareCenter.py --json --settings-file ./profile.ini boards list --include-closed
python SoftwareCenter.py --json --settings-file ./profile.ini entries list
```

---

## Related Documentation

- [`llms.txt`](llms.txt) — Canonical short machine index
- [`EXPORTFORMAT.md`](EXPORTFORMAT.md) — `softwarecenter-profile-v1.json` schema
- [`PRODUCT_BOUNDARIES.md`](PRODUCT_BOUNDARIES.md) — SoftwareCenter vs. LaunchBoards isolation contract
- [`SECURITY.md`](SECURITY.md) — Security policy, supported versions, reporting channels
