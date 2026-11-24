# -*- coding: utf-8 -*-
"""Headless CLI and programmatic dual-use interface for SoftwareCenter & LaunchBoards.

Provides machine-readable (--json) and human-readable access to the exact same
QSettings storage, board lifecycle, entry normalization, search, profile export/import,
and target launch semantics as the PySide6 desktop GUI.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import QSettings

CLI_SUBCOMMANDS = frozenset({"boards", "entries", "search", "profile", "launch"})
CLI_TOP_FLAGS = frozenset({"-h", "--help", "-V", "--version", "--json", "--profile", "--settings-file"})


def should_dispatch_cli(args: Sequence[str]) -> bool:
    """Return True when argv tokens target the headless CLI instead of the GUI."""
    if not args:
        return False
    first = args[0]
    if first in CLI_SUBCOMMANDS or first in CLI_TOP_FLAGS:
        return True
    return any(first.startswith(prefix) for prefix in ("--profile=", "--settings-file="))


def _configure_stdio_utf8() -> None:
    """Ensure UTF-8 console output on Windows terminals without failing on mocked streams."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with contextlib.suppress(Exception):
                reconfigure(encoding="utf-8")


def _open_settings(profile_name: str, settings_file: str | None) -> tuple[object, QSettings]:
    import SoftwareCenter as sc

    profile = sc.PROFILE_LAUNCHBOARDS if profile_name == "launchboards" else sc.PROFILE_SOFTWARECENTER
    if settings_file:
        settings = QSettings(os.path.abspath(settings_file), QSettings.Format.IniFormat)
    else:
        settings = QSettings("LukasGeiger", profile.settings_app)
    return profile, settings


def _load_state(settings: QSettings) -> dict:
    """Read active tabs, closed boards, and favorites using SoftwareCenter's schema."""
    import SoftwareCenter as sc

    closed_boards: dict[str, dict] = {}
    favorites: set[str] = set()

    closed_size = settings.beginReadArray("closed_boards")
    for i in range(closed_size):
        settings.setArrayIndex(i)
        board_id = settings.value("board_id") or sc.new_board_id()
        name = str(settings.value("name", "Board") or "Board")
        view_mode = "list" if str(settings.value("view_mode", "tiles")).strip().lower() == "list" else "tiles"
        entries = sc._parse_entries_json(settings.value("entries_json", ""))
        favorite = sc._settings_bool(settings.value("favorite", False))
        closed_at = str(settings.value("closed_at", "") or sc.iso_now())
        closed_boards[board_id] = {
            "id": board_id,
            "name": name,
            "view_mode": view_mode,
            "entries": entries,
            "closed_at": closed_at,
        }
        if favorite:
            favorites.add(board_id)
    settings.endArray()

    active_tabs: list[dict] = []
    tab_size = settings.beginReadArray("tabs")
    for i in range(tab_size):
        settings.setArrayIndex(i)
        name = str(settings.value("name", "Tab") or "Tab")
        view_mode = "list" if str(settings.value("view_mode", "tiles")).strip().lower() == "list" else "tiles"
        entries = sc._parse_entries_json(settings.value("entries_json", ""))
        if not entries:
            raw_paths = settings.value("paths", [])
            if isinstance(raw_paths, str):
                raw_paths = [raw_paths]
            if isinstance(raw_paths, list):
                for p in raw_paths:
                    norm = sc.normalize_entry(p)
                    if norm:
                        entries.append(norm)
        board_id = settings.value("board_id") or sc.new_board_id()
        favorite = sc._settings_bool(settings.value("favorite", False))
        if favorite:
            favorites.add(board_id)
        active_tabs.append(
            {
                "id": board_id,
                "name": name,
                "view_mode": view_mode,
                "entries": entries,
            }
        )
    settings.endArray()

    if not active_tabs:
        active_tabs.append(
            {
                "id": sc.new_board_id(),
                "name": "Allgemein",
                "view_mode": "tiles",
                "entries": [],
            }
        )

    raw_current = settings.value("current_tab", 0)
    if isinstance(raw_current, bool):
        current_tab = 0
    else:
        try:
            current_tab = int(raw_current)
        except (TypeError, ValueError):
            current_tab = 0
    if not (0 <= current_tab < len(active_tabs)):
        current_tab = 0

    return {
        "current_tab": current_tab,
        "tabs": active_tabs,
        "closed_boards": closed_boards,
        "favorites": favorites,
    }


def _save_state(settings: QSettings, state: dict) -> None:
    """Persist state in the exact QSettings schema expected by MainWindow.load_settings."""
    tabs = state["tabs"]
    closed_boards = state["closed_boards"]
    favorites = state["favorites"]
    current_tab = state["current_tab"]
    if not (0 <= current_tab < len(tabs)):
        current_tab = 0

    settings.setValue("current_tab", current_tab)
    settings.remove("tabs")
    settings.beginWriteArray("tabs")
    for i, tab in enumerate(tabs):
        settings.setArrayIndex(i)
        settings.setValue("name", tab["name"])
        settings.setValue("view_mode", tab["view_mode"])
        settings.setValue("entries_json", json.dumps(tab["entries"], ensure_ascii=False))
        settings.setValue("paths", [e["path"] for e in tab["entries"]])
        settings.setValue("board_id", tab["id"])
        settings.setValue("favorite", tab["id"] in favorites)
    settings.endArray()

    settings.remove("closed_boards")
    settings.beginWriteArray("closed_boards")
    for i, board in enumerate(closed_boards.values()):
        settings.setArrayIndex(i)
        settings.setValue("board_id", board["id"])
        settings.setValue("name", board["name"])
        settings.setValue("view_mode", board["view_mode"])
        settings.setValue("entries_json", json.dumps(board["entries"], ensure_ascii=False))
        settings.setValue("favorite", board["id"] in favorites)
        settings.setValue("closed_at", board["closed_at"])
    settings.endArray()
    settings.sync()


def _find_board_ref(state: dict, identifier: str, include_closed: bool = True) -> tuple[str, int | str, dict] | None:
    """Locate a board by exact ID or case-insensitive exact name."""
    ident = identifier.strip()
    for idx, tab in enumerate(state["tabs"]):
        if tab["id"] == ident:
            return ("active", idx, tab)
    if include_closed and ident in state["closed_boards"]:
        return ("closed", ident, state["closed_boards"][ident])

    lowered = ident.casefold()
    matches: list[tuple[str, int | str, dict]] = []
    for idx, tab in enumerate(state["tabs"]):
        if tab["name"].casefold() == lowered:
            matches.append(("active", idx, tab))
    if include_closed:
        for bid, board in state["closed_boards"].items():
            if board["name"].casefold() == lowered:
                matches.append(("closed", bid, board))
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"Mehrdeutiger Board-Name '{identifier}'. Bitte eindeutige board_id angeben.")
    return None


def _atomic_write_json(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.tmp.", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def _target_exists(path_str: str) -> bool:
    import SoftwareCenter as sc

    if sc.is_web_url(path_str):
        return True
    return os.path.exists(path_str)


def _emit(payload: dict, text_lines: Sequence[str], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for line in text_lines:
            print(line)


def _emit_error(message: str, as_json: bool, code: int = 2) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": message, "exit_code": code}, ensure_ascii=False, indent=2))
    else:
        print(f"Fehler: {message}", file=sys.stderr)
    return code


def _build_parser(default_profile: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="SoftwareCenter",
        description="SoftwareCenter / LaunchBoards — Desktop-Organizer & Headless-CLI (P-022)",
    )
    parser.add_argument("-V", "--version", action="store_true", help="Version und Produktname ausgeben")
    parser.add_argument(
        "--profile",
        choices=("softwarecenter", "launchboards"),
        default=default_profile,
        help="Zielprofil auswählen (Standard gemäß Startpunkt)",
    )
    parser.add_argument(
        "--settings-file",
        help="Optionaler Pfad zu einer QSettings-INI-Datei (isoliert von System-QSettings)",
    )
    parser.add_argument("--json", action="store_true", help="Strukturierte JSON-Ausgabe")

    sub = parser.add_subparsers(dest="domain")

    # boards
    p_boards = sub.add_parser("boards", help="Boards auflisten, erstellen, umbenennen, schließen oder reaktivieren")
    sub_b = p_boards.add_subparsers(dest="action", required=True)
    p_bl = sub_b.add_parser("list", help="Boards auflisten")
    p_bl.add_argument("--include-closed", action="store_true", help="Auch geschlossene Boards anzeigen")
    p_bc = sub_b.add_parser("create", help="Neues Board erstellen")
    p_bc.add_argument("name", help="Board-Name")
    p_bc.add_argument("--view", choices=("tiles", "list"), default="tiles", help="Ansichtsmodus")
    p_br = sub_b.add_parser("rename", help="Board umbenennen")
    p_br.add_argument("board", help="Board-ID oder eindeutiger Board-Name")
    p_br.add_argument("new_name", help="Neuer Name")
    p_bcl = sub_b.add_parser("close", help="Aktives Board schließen (bleibt im Verlauf erhalten)")
    p_bcl.add_argument("board", help="Board-ID oder eindeutiger Board-Name")
    p_bre = sub_b.add_parser("reactivate", help="Geschlossenes Board wiederherstellen")
    p_bre.add_argument("board", help="Board-ID oder eindeutiger Board-Name")
    p_bf = sub_b.add_parser("favorite", help="Favoriten-Status eines Boards setzen")
    p_bf.add_argument("board", help="Board-ID oder eindeutiger Board-Name")
    p_bf.add_argument("--off", action="store_true", help="Favoriten-Markierung entfernen")

    # entries
    p_entries = sub.add_parser("entries", help="Einträge auf Boards auflisten, hinzufügen oder entfernen")
    sub_e = p_entries.add_subparsers(dest="action", required=True)
    p_el = sub_e.add_parser("list", help="Einträge auflisten")
    p_el.add_argument("--board", help="Optional auf ein Board (ID oder Name) filtern")
    p_ea = sub_e.add_parser("add", help="Eintrag zu einem aktiven Board hinzufügen")
    p_ea.add_argument("board", help="Board-ID oder eindeutiger Board-Name")
    p_ea.add_argument("target", help="Dateipfad, Ordner, Verknüpfung oder HTTP(S)-URL")
    p_ea.add_argument("--label", help="Optionale benutzerdefinierte Bezeichnung")
    p_ea.add_argument("--notes", help="Optionale Notiz")
    p_er = sub_e.add_parser("remove", help="Eintrag aus einem Board entfernen (löscht keine Zieldatei)")
    p_er.add_argument("board", help="Board-ID oder eindeutiger Board-Name")
    p_er.add_argument("target", help="Exakter Pfad oder exaktes Label des Eintrags")

    # search
    p_search = sub.add_parser("search", help="Boards und Einträge nach Suchbegriff filtern")
    p_search.add_argument("query", help="Suchbegriff (Groß-/Kleinschreibung ignoriert)")
    p_search.add_argument("--include-closed", action="store_true", help="Auch geschlossene Boards durchsuchen")

    # profile
    p_prof = sub.add_parser("profile", help="Profile exportieren, validieren oder importieren")
    sub_p = p_prof.add_subparsers(dest="action", required=True)
    p_pe = sub_p.add_parser("export", help="Aktives Profil als softwarecenter-profile-v1.json exportieren")
    p_pe.add_argument("output", help="Zielpfad für JSON-Datei")
    p_pv = sub_p.add_parser("validate", help="softwarecenter-profile-v1.json prüfen")
    p_pv.add_argument("input", help="Pfad zur JSON-Profildatei")
    p_pi = sub_p.add_parser("import", help="Aktive Boards durch JSON-Profil ersetzen (erfordert --yes)")
    p_pi.add_argument("input", help="Pfad zur JSON-Profildatei")
    p_pi.add_argument("--yes", action="store_true", help="Ersetzen des aktiven Profils ausdrücklich bestätigen")

    # launch
    p_launch = sub.add_parser("launch", help="Zielpfad oder HTTP(S)-URL über SoftwareCenter-Logik starten/prüfen")
    p_launch.add_argument("target", help="Dateipfad, Ordner, URL oder Eintragsbezeichnung")
    p_launch.add_argument("--board", help="Optional Eintragsname im angegebenen Board auflösen")
    p_launch.add_argument("--dry-run", action="store_true", help="Ziel nur prüfen, nicht ausführen")

    return parser


def _handle_boards(args, settings: QSettings, state: dict) -> tuple[int, dict, list[str]]:
    import SoftwareCenter as sc

    favorites = state["favorites"]
    if args.action == "list":
        rows = []
        for idx, tab in enumerate(state["tabs"]):
            rows.append(
                {
                    "id": tab["id"],
                    "name": tab["name"],
                    "status": "active",
                    "active_index": idx,
                    "view_mode": tab["view_mode"],
                    "entry_count": len(tab["entries"]),
                    "favorite": tab["id"] in favorites,
                    "closed_at": "",
                }
            )
        if args.include_closed:
            for board in sc.sort_boards_history(list(state["closed_boards"].values())):
                rows.append(
                    {
                        "id": board["id"],
                        "name": board["name"],
                        "status": "closed",
                        "active_index": None,
                        "view_mode": board["view_mode"],
                        "entry_count": len(board["entries"]),
                        "favorite": board["id"] in favorites,
                        "closed_at": board["closed_at"],
                    }
                )
        lines = [
            f"[{r['status']}] {r['name']} (id={r['id']}, entries={r['entry_count']}, view={r['view_mode']}, fav={r['favorite']})"
            for r in rows
        ]
        return 0, {"ok": True, "count": len(rows), "boards": rows}, lines

    if args.action == "create":
        name = args.name.strip()
        if not name:
            raise ValueError("Board-Name darf nicht leer sein.")
        new_tab = {
            "id": sc.new_board_id(),
            "name": name,
            "view_mode": args.view,
            "entries": [],
        }
        state["tabs"].append(new_tab)
        state["current_tab"] = len(state["tabs"]) - 1
        _save_state(settings, state)
        payload = {"ok": True, "board": {**new_tab, "entry_count": 0, "favorite": False}}
        return 0, payload, [f"Board erstellt: {name} (id={new_tab['id']})"]

    ref = _find_board_ref(state, args.board, include_closed=(args.action in ("rename", "favorite", "reactivate")))
    if ref is None:
        raise LookupError(f"Board nicht gefunden: {args.board}")
    kind, key, board = ref

    if args.action == "rename":
        new_name = args.new_name.strip()
        if not new_name:
            raise ValueError("Neuer Board-Name darf nicht leer sein.")
        board["name"] = new_name
        _save_state(settings, state)
        return 0, {"ok": True, "id": board["id"], "name": new_name}, [f"Board umbenannt: {new_name} (id={board['id']})"]

    if args.action == "close":
        if kind != "active":
            raise ValueError(f"Board ist bereits geschlossen: {board['name']}")
        if len(state["tabs"]) <= 1:
            raise ValueError("Der letzte aktive Tab kann nicht geschlossen werden.")
        closed = state["tabs"].pop(int(key))
        closed_rec = {
            "id": closed["id"],
            "name": closed["name"],
            "view_mode": closed["view_mode"],
            "entries": closed["entries"],
            "closed_at": sc.iso_now(),
        }
        state["closed_boards"][closed["id"]] = closed_rec
        _save_state(settings, state)
        return 0, {"ok": True, "board": closed_rec}, [f"Board geschlossen: {closed['name']} (id={closed['id']})"]

    if args.action == "reactivate":
        if kind != "closed":
            raise ValueError(f"Board ist bereits aktiv: {board['name']}")
        restored = state["closed_boards"].pop(str(key))
        tab = {
            "id": restored["id"],
            "name": restored["name"],
            "view_mode": restored["view_mode"],
            "entries": restored["entries"],
        }
        state["tabs"].append(tab)
        state["current_tab"] = len(state["tabs"]) - 1
        _save_state(settings, state)
        return 0, {"ok": True, "board": tab}, [f"Board reaktiviert: {tab['name']} (id={tab['id']})"]

    if args.action == "favorite":
        bid = board["id"]
        if args.off:
            favorites.discard(bid)
        else:
            favorites.add(bid)
        _save_state(settings, state)
        is_fav = bid in favorites
        return 0, {"ok": True, "id": bid, "favorite": is_fav}, [f"Favorit {'gesetzt' if is_fav else 'entfernt'}: {board['name']}"]

    raise ValueError(f"Unbekannte Board-Aktion: {args.action}")


def _handle_entries(args, settings: QSettings, state: dict) -> tuple[int, dict, list[str]]:
    import SoftwareCenter as sc

    if args.action == "list":
        selected_tabs = state["tabs"]
        if args.board:
            ref = _find_board_ref(state, args.board, include_closed=True)
            if ref is None:
                raise LookupError(f"Board nicht gefunden: {args.board}")
            selected_tabs = [ref[2]]
        items = []
        for tab in selected_tabs:
            for entry in tab["entries"]:
                items.append(
                    {
                        "board_id": tab["id"],
                        "board_name": tab["name"],
                        "label": entry["label"],
                        "path": entry["path"],
                        "kind": entry["kind"],
                        "notes": entry.get("notes"),
                        "exists": _target_exists(entry["path"]),
                    }
                )
        lines = [f"{e['board_name']}: {e['label']} -> {e['path']} [{e['kind']}]" for e in items]
        return 0, {"ok": True, "count": len(items), "entries": items}, lines

    ref = _find_board_ref(state, args.board, include_closed=False)
    if ref is None:
        raise LookupError(f"Aktives Board nicht gefunden: {args.board}")
    _, _, tab = ref

    if args.action == "add":
        raw_target = args.target.strip()
        if not sc.is_supported_launch_target(raw_target):
            raise ValueError(f"Nicht unterstütztes Startziel: {args.target}")
        resolved_path = sc.normalize_new_launch_path(raw_target)
        entry = sc.normalize_entry(
            {
                "path": resolved_path,
                "label": args.label if args.label else sc.default_entry_label(raw_target),
                "notes": args.notes,
            }
        )
        if entry is None:
            raise ValueError(f"Eintrag konnte nicht normalisiert werden: {args.target}")
        existing_paths = {e["path"] for e in tab["entries"]}
        if entry["path"] in existing_paths:
            return 0, {"ok": True, "added": False, "duplicate": True, "entry": entry}, [
                f"Bereits vorhanden in {tab['name']}: {entry['path']}"
            ]
        tab["entries"].append(entry)
        _save_state(settings, state)
        return 0, {"ok": True, "added": True, "board_id": tab["id"], "entry": entry}, [
            f"Hinzugefügt zu {tab['name']}: {entry['label']} ({entry['path']})"
        ]

    if args.action == "remove":
        needle = args.target.strip()
        remaining = []
        removed = []
        for entry in tab["entries"]:
            if entry["path"] == needle or entry["label"].casefold() == needle.casefold():
                removed.append(entry)
            else:
                remaining.append(entry)
        if not removed:
            raise LookupError(f"Eintrag nicht gefunden in {tab['name']}: {args.target}")
        tab["entries"] = remaining
        _save_state(settings, state)
        return 0, {"ok": True, "removed_count": len(removed), "removed": removed}, [
            f"{len(removed)} Eintrag/Einträge aus {tab['name']} entfernt."
        ]

    raise ValueError(f"Unbekannte Entry-Aktion: {args.action}")


def _handle_search(args, state: dict) -> tuple[int, dict, list[str]]:
    needle = args.query.strip().casefold()
    if not needle:
        raise ValueError("Suchbegriff darf nicht leer sein.")
    boards_to_scan = [(tab, "active") for tab in state["tabs"]]
    if args.include_closed:
        boards_to_scan.extend((board, "closed") for board in state["closed_boards"].values())

    hits = []
    for board, status in boards_to_scan:
        if needle in board["name"].casefold():
            hits.append(
                {
                    "kind": "board",
                    "status": status,
                    "board_id": board["id"],
                    "board_name": board["name"],
                }
            )
        for entry in board["entries"]:
            haystack = " ".join(
                part for part in (entry.get("label", ""), entry.get("path", ""), entry.get("notes") or "")
            ).casefold()
            if needle in haystack:
                hits.append(
                    {
                        "kind": "entry",
                        "status": status,
                        "board_id": board["id"],
                        "board_name": board["name"],
                        "label": entry["label"],
                        "path": entry["path"],
                        "entry_kind": entry["kind"],
                        "notes": entry.get("notes"),
                    }
                )
    lines = [
        (f"[board:{h['status']}] {h['board_name']}" if h["kind"] == "board" else f"[{h['board_name']}] {h['label']} -> {h['path']}")
        for h in hits
    ]
    return 0, {"ok": True, "query": args.query, "count": len(hits), "hits": hits}, lines


def _handle_profile(args, settings: QSettings, state: dict) -> tuple[int, dict, list[str]]:
    import SoftwareCenter as sc

    if args.action == "export":
        payload = {
            "format": sc.PROFILE_FORMAT,
            "format_version": sc.PROFILE_FORMAT_VERSION,
            "app_version": sc.__version__,
            "source_platform": sys.platform,
            "exported_at": sc.iso_now(),
            "current_tab": state["current_tab"],
            "tabs": [
                {
                    "name": tab["name"],
                    "view_mode": tab["view_mode"],
                    "entries": tab["entries"],
                }
                for tab in state["tabs"]
            ],
        }
        out_path = Path(args.output)
        _atomic_write_json(out_path, payload)
        return 0, {
            "ok": True,
            "output": str(out_path),
            "tabs": len(payload["tabs"]),
            "entries": sum(len(t["entries"]) for t in payload["tabs"]),
        }, [f"Profil exportiert: {out_path} ({len(payload['tabs'])} Tabs)"]

    in_path = Path(args.input)
    raw = json.loads(in_path.read_text(encoding="utf-8"))
    tabs = sc.validate_profile_payload(raw)
    missing_paths = [
        e["path"]
        for tab in tabs
        for e in tab["entries"]
        if not _target_exists(e["path"])
    ]

    if args.action == "validate":
        summary = {
            "ok": True,
            "valid": True,
            "input": str(in_path),
            "tabs": len(tabs),
            "entries": sum(len(t["entries"]) for t in tabs),
            "missing_targets": len(missing_paths),
        }
        return 0, summary, [
            f"Profil gültig: {in_path} ({summary['tabs']} Tabs, {summary['entries']} Einträge, {summary['missing_targets']} fehlende Pfade)"
        ]

    if args.action == "import":
        if not args.yes:
            raise ValueError("Profil-Import ersetzt die aktiven Boards. Bitte ausdrücklich mit --yes bestätigen.")
        raw_current = raw.get("current_tab", 0)
        if isinstance(raw_current, bool) or not isinstance(raw_current, int):
            current_tab = 0
            if not isinstance(raw_current, bool):
                try:
                    current_tab = int(raw_current)
                except (TypeError, ValueError):
                    current_tab = 0
        else:
            current_tab = raw_current
        state["tabs"] = [
            {
                "id": sc.new_board_id(),
                "name": t["name"],
                "view_mode": t["view_mode"],
                "entries": t["entries"],
            }
            for t in tabs
        ]
        state["current_tab"] = current_tab if 0 <= current_tab < len(state["tabs"]) else 0
        _save_state(settings, state)
        summary = {
            "ok": True,
            "imported": str(in_path),
            "tabs": len(state["tabs"]),
            "entries": sum(len(t["entries"]) for t in state["tabs"]),
        }
        return 0, summary, [f"Profil importiert: {in_path} ({summary['tabs']} Tabs, {summary['entries']} Einträge)"]

    raise ValueError(f"Unbekannte Profil-Aktion: {args.action}")


def _handle_launch(args, state: dict) -> tuple[int, dict, list[str]]:
    import SoftwareCenter as sc

    target_path = args.target
    if args.board:
        ref = _find_board_ref(state, args.board, include_closed=True)
        if ref is None:
            raise LookupError(f"Board nicht gefunden: {args.board}")
        needle = args.target.strip()
        match = next(
            (e for e in ref[2]["entries"] if e["path"] == needle or e["label"].casefold() == needle.casefold()),
            None,
        )
        if match is None:
            raise LookupError(f"Eintrag '{args.target}' in Board '{args.board}' nicht gefunden.")
        target_path = match["path"]

    exists = _target_exists(target_path)
    supported = sc.is_supported_launch_target(target_path)
    if args.dry_run:
        if not exists:
            raise LookupError(f"Ziel existiert nicht: {target_path}")
        payload = {"ok": True, "dry_run": True, "target": target_path, "exists": exists, "supported": supported}
        return 0, payload, [f"Dry-Run OK: {target_path} (supported={supported})"]

    if not exists:
        raise LookupError(f"Ziel existiert nicht: {target_path}")
    sc.open_file(target_path)
    return 0, {"ok": True, "launched": target_path}, [f"Gestartet: {target_path}"]


def cli_main(argv: Sequence[str] | None = None, default_profile=None) -> int:
    """Execute the headless SoftwareCenter/LaunchBoards CLI and return an exit code."""
    _configure_stdio_utf8()
    import SoftwareCenter as sc

    default_name = (
        "launchboards"
        if default_profile is not None and getattr(default_profile, "settings_app", "") == "LaunchBoards"
        else "softwarecenter"
    )
    parser = _build_parser(default_name)
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    as_json_hint = "--json" in raw_argv
    try:
        args = parser.parse_args(raw_argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else (0 if exc.code is None else 2)

    as_json = bool(args.json)
    profile, settings = _open_settings(args.profile, args.settings_file)

    if args.version:
        payload = {"ok": True, "product": profile.name, "version": sc.__version__, "settings_app": profile.settings_app}
        _emit(payload, [f"{profile.name} {sc.__version__}"], as_json)
        return 0

    if not args.domain:
        parser.print_help()
        return 0

    state = _load_state(settings)
    try:
        if args.domain == "boards":
            rc, payload, lines = _handle_boards(args, settings, state)
        elif args.domain == "entries":
            rc, payload, lines = _handle_entries(args, settings, state)
        elif args.domain == "search":
            rc, payload, lines = _handle_search(args, state)
        elif args.domain == "profile":
            rc, payload, lines = _handle_profile(args, settings, state)
        elif args.domain == "launch":
            rc, payload, lines = _handle_launch(args, state)
        else:
            return _emit_error(f"Unbekannter Befehl: {args.domain}", as_json_hint, code=2)
    except (ValueError, LookupError, json.JSONDecodeError) as exc:
        return _emit_error(str(exc), as_json, code=2)
    except OSError as exc:
        return _emit_error(str(exc), as_json, code=1)

    _emit(payload, lines, as_json)
    return rc
