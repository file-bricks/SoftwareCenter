# -*- coding: utf-8 -*-
"""Synchronize the portable launcher catalog into SoftwareCenter profiles.

The executable code lives in the Plan-D repository.  Synchronized catalog and
registry files remain data inputs and must be supplied explicitly on every
invocation.  The default mode is read-only; ``--apply`` is the only write gate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings


ORG = "LukasGeiger"
PROFILES = ("SoftwareCenter", "LaunchBoards")
VALID_STATES = {"PENDING", "ACTIVE", "SUPPRESSED"}
META_KEY = "launcher_catalog/managed_paths_json"
PROFILE_IMAGE_PATTERNS = tuple(
    re.compile(
        rf"^{re.escape(profile)}"
        r"(?:-[0-9][A-Za-z0-9._-]*-win64)?\.exe$",
        re.IGNORECASE,
    )
    for profile in PROFILES
)


@dataclass(frozen=True)
class RuntimeConfig:
    catalog: Path
    registry: Path
    software_root: Path
    local_dev_root: Path
    backup_dir: Path
    apply: bool
    restore_backup: Path | None = None


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.path.expandvars(str(path.expanduser()))))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synchronizes the portable launcher catalog (dry-run by default)."
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        required=True,
        help="Exact path to the software-launcher-catalog-v2 JSON file.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
        help="Exact path to DESKTOP-REGISTRY.txt.",
    )
    parser.add_argument(
        "--software-root",
        type=Path,
        required=True,
        help="Root used to resolve $SOFTWARE_ROOT launcher templates.",
    )
    parser.add_argument(
        "--local-dev-root",
        type=Path,
        required=True,
        help="Root used to resolve $LOCAL_DEV_ROOT launcher templates.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Local backup directory (default: <local-dev-root>/launcher_catalog_backups).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write both QSettings profiles and registry state after all gates pass.",
    )
    parser.add_argument(
        "--restore-backup",
        type=Path,
        help=(
            "Restore both profiles and the registry from a "
            "launcher-catalog-profile-backup-v2 file; requires --apply."
        ),
    )
    return parser


def parse_config(argv: Sequence[str] | None = None) -> RuntimeConfig:
    args = build_parser().parse_args(argv)
    local_dev_root = _absolute(args.local_dev_root)
    return RuntimeConfig(
        catalog=_absolute(args.catalog),
        registry=_absolute(args.registry),
        software_root=_absolute(args.software_root),
        local_dev_root=local_dev_root,
        backup_dir=_absolute(
            args.backup_dir
            if args.backup_dir is not None
            else local_dev_root / "launcher_catalog_backups"
        ),
        apply=bool(args.apply),
        restore_backup=(
            _absolute(args.restore_backup)
            if args.restore_backup is not None
            else None
        ),
    )


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def validate_config(config: RuntimeConfig) -> list[str]:
    errors: list[str] = []
    if not config.catalog.is_file():
        errors.append(f"Katalog fehlt: {config.catalog}")
    if not config.registry.is_file():
        errors.append(f"Registry fehlt: {config.registry}")
    if not config.software_root.is_dir():
        errors.append(f"Software-Root fehlt: {config.software_root}")
    if not config.local_dev_root.is_dir():
        errors.append(f"Local-Dev-Root fehlt: {config.local_dev_root}")
    if config.catalog == config.registry:
        errors.append("Katalog und Registry müssen verschiedene Dateien sein.")
    if config.restore_backup is not None:
        if not config.apply:
            errors.append("--restore-backup erfordert zusätzlich --apply.")
        if not config.restore_backup.is_file():
            errors.append(f"Restore-Backup fehlt: {config.restore_backup}")
    if config.apply:
        synchronized_root = config.software_root
        if config.software_root.parent.name.casefold() == ".topics":
            candidate = config.software_root.parent.parent
            if _is_within(config.registry, candidate):
                synchronized_root = candidate
        if _is_within(config.backup_dir, synchronized_root):
            errors.append(
                "Backup-Verzeichnis darf nicht innerhalb des synchronisierten "
                "Daten-Roots liegen."
            )
    return errors


def resolve_template(
    value: str, *, software_root: Path, local_dev_root: Path
) -> str:
    return (
        value.replace("$SOFTWARE_ROOT", str(software_root))
        .replace("$LOCAL_DEV_ROOT", str(local_dev_root))
    )


def norm(path: str) -> str:
    return (
        os.path.normcase(os.path.normpath(os.path.abspath(path))) if path else ""
    )


def detect_kind(path: str) -> str:
    lower = path.lower()
    if lower.endswith((".bat", ".cmd", ".ps1")):
        return "script"
    if lower.endswith(".lnk"):
        return "windows_shortcut"
    if os.path.isdir(path):
        return "directory"
    return "file"


def is_profile_running() -> bool | None:
    """Return profile state, or ``None`` when the native probe is unavailable."""
    try:
        completed = subprocess.run(
            ["tasklist", "/NH", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            shell=False,
        )
        if completed.returncode != 0:
            return None
        image_names = [
            row[0].strip()
            for row in csv.reader(completed.stdout.splitlines())
            if row and row[0].strip()
        ]
        return any(
            pattern.fullmatch(image_name)
            for image_name in image_names
            for pattern in PROFILE_IMAGE_PATTERNS
        )
    except Exception:
        return None


def load_profile(settings: QSettings) -> tuple[list[dict], int]:
    tabs: list[dict] = []
    size = settings.beginReadArray("tabs")
    for index in range(size):
        settings.setArrayIndex(index)
        name = str(settings.value("name", "Tab") or "Tab")
        view_mode = str(settings.value("view_mode", "tiles") or "tiles")
        entries_json = settings.value("entries_json", "")
        entries: list[dict] = []
        if isinstance(entries_json, str) and entries_json.strip():
            try:
                parsed = json.loads(entries_json)
                if isinstance(parsed, list):
                    entries = [
                        dict(entry) for entry in parsed if isinstance(entry, dict)
                    ]
            except json.JSONDecodeError:
                entries = []
        if not entries:
            paths = settings.value("paths", [])
            if isinstance(paths, str):
                paths = [paths]
            if isinstance(paths, Iterable):
                entries = [
                    {
                        "path": str(path),
                        "label": Path(str(path)).stem,
                        "kind": detect_kind(str(path)),
                        "notes": None,
                    }
                    for path in paths
                    if isinstance(path, str) and path.strip()
                ]
        tabs.append({"name": name, "view_mode": view_mode, "entries": entries})
    settings.endArray()
    current = settings.value("current_tab", 0)
    return tabs, current if isinstance(current, int) else 0


def save_profile(settings: QSettings, tabs: list[dict], current_tab: int) -> None:
    settings.setValue("current_tab", current_tab)
    settings.remove("tabs")
    settings.beginWriteArray("tabs")
    for index, tab in enumerate(tabs):
        settings.setArrayIndex(index)
        entries = tab["entries"]
        settings.setValue("name", tab["name"])
        settings.setValue("view_mode", tab.get("view_mode", "tiles"))
        settings.setValue("entries_json", json.dumps(entries, ensure_ascii=False))
        settings.setValue(
            "paths", [entry.get("path", "") for entry in entries]
        )
    settings.endArray()
    settings.sync()
    if settings.status() != QSettings.Status.NoError:
        raise OSError(
            "QSettings-Profil konnte nicht geschrieben werden: "
            f"{settings.fileName()}"
        )


def load_meta(settings: QSettings) -> dict[str, dict[str, str]]:
    raw = settings.value(META_KEY, "")
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(parsed, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in parsed.items()
        if isinstance(value, dict)
    }


def save_meta(settings: QSettings, meta: dict[str, dict[str, str]]) -> None:
    settings.setValue(
        META_KEY, json.dumps(meta, ensure_ascii=False, sort_keys=True)
    )
    settings.sync()
    if settings.status() != QSettings.Status.NoError:
        raise OSError(
            "QSettings-Metadaten konnten nicht geschrieben werden: "
            f"{settings.fileName()}"
        )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def backup_profiles(
    backup_dir: Path,
    staged: list[tuple[str, list[dict], int, dict[str, dict[str, str]]]],
    registry_path: Path,
    registry_bytes: bytes,
) -> Path:
    """Back up both profiles and the registry source before an apply run."""
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / (
        f"profiles_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
    )
    payload = {
        "format": "launcher-catalog-profile-backup-v2",
        "created_at": datetime.now().astimezone().isoformat(),
        "registry": {
            "source_path": str(registry_path),
            "sha256": _sha256(registry_bytes),
            "text": registry_bytes.decode("utf-8"),
        },
        "profiles": {
            profile: {
                "tabs": tabs,
                "current_tab": current_tab,
                "managed_paths": meta,
            }
            for profile, tabs, current_tab, meta in staged
        },
    }
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return target


def ensure_board(tabs: list[dict], board_name: str) -> int:
    for index, tab in enumerate(tabs):
        if tab["name"] == board_name:
            return index
    tabs.append({"name": board_name, "view_mode": "tiles", "entries": []})
    return len(tabs) - 1


def find_entry(
    tabs: list[dict], candidates: Iterable[str]
) -> tuple[int, int] | None:
    wanted = {norm(candidate) for candidate in candidates if candidate}
    for tab_index, tab in enumerate(tabs):
        for entry_index, entry in enumerate(tab["entries"]):
            if norm(str(entry.get("path", ""))) in wanted:
                return tab_index, entry_index
    return None


def read_catalog(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "software-launcher-catalog-v2":
        raise ValueError(f"Unerwartetes Katalogformat in {path}")
    apps = payload.get("apps")
    if not isinstance(apps, list):
        raise ValueError("Katalog enthält keine App-Liste")
    normalized: list[dict] = []
    for index, app in enumerate(apps):
        if not isinstance(app, dict):
            raise ValueError(f"Katalogeintrag {index} ist kein Objekt")
        app_id = app.get("id")
        if not isinstance(app_id, str) or not app_id.strip():
            raise ValueError(f"Katalogeintrag {index} besitzt keine gültige ID")
        launcher_template = app.get("launcher_template")
        if not isinstance(launcher_template, str):
            raise ValueError(
                f"Katalogeintrag {app_id} besitzt kein String-Pfadtemplate"
            )
        profiles = app.get("profiles", {})
        if not isinstance(profiles, dict):
            raise ValueError(
                f"Katalogeintrag {app_id} besitzt kein Profilobjekt"
            )
        normalized.append(dict(app))
    return normalized


def registry_states_for_spec(spec: str) -> dict[str, str]:
    result = {profile: "PENDING" for profile in PROFILES}
    for profile, value in re.findall(
        r"(?i)(SOFTWARECENTER|LAUNCHBOARDS)\s*=\s*([A-Z_]+)", spec
    ):
        profile_name = (
            "SoftwareCenter"
            if profile.casefold() == "softwarecenter"
            else "LaunchBoards"
        )
        result[profile_name] = value.upper()
    return result


def registry_states(path: Path) -> dict[str, dict[str, str]]:
    states: dict[str, dict[str, str]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*[A-Z_]+\s*\|\s*(.+?)\s*:\s*(.+?)\s*$", line)
        if not match:
            continue
        states[match.group(1).strip()] = registry_states_for_spec(
            match.group(2).strip()
        )
    return states


def write_registry_updates(
    path: Path, updates: dict[str, dict[str, str]]
) -> None:
    if not updates:
        return
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    changed = False
    remaining = set(updates)
    rewritten: list[str] = []
    for line in lines:
        match = re.match(
            r"^(\s*[A-Z_]+\s*\|\s*)(.+?)(\s*:\s*)(.*?)(\r?\n)?$", line
        )
        if not match or match.group(2).strip() not in updates:
            rewritten.append(line)
            continue
        app_id = match.group(2).strip()
        remaining.discard(app_id)
        spec = match.group(4).strip()
        desktop = re.search(
            r"(?i)(?:^|;)\s*DESKTOP\s*=\s*(ON|OFF)\s*(?:;|$)", spec
        )
        if desktop:
            desktop_state = desktop.group(1).upper()
        elif spec.upper() in {"ON", "OFF"}:
            desktop_state = spec.upper()
        else:
            desktop_state = "OFF"
        next_states = {**registry_states_for_spec(spec), **updates[app_id]}
        rendered = "; ".join(
            [f"DESKTOP={desktop_state}"]
            + [
                f"{profile.upper()}={next_states[profile]}"
                for profile in PROFILES
            ]
        )
        newline = match.group(5) or "\n"
        rewritten.append(
            f"{match.group(1)}{app_id}{match.group(3)}{rendered}{newline}"
        )
        changed = True
    if remaining:
        raise ValueError(
            "Registry enthält keine Zeile für: " + ", ".join(sorted(remaining))
        )
    if not changed:
        return
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False, dir=path.parent, newline=""
    ) as handle:
        handle.writelines(rewritten)
        temp_name = handle.name
    os.replace(temp_name, path)


def replace_file_bytes(path: Path, content: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        "wb", delete=False, dir=path.parent
    ) as handle:
        handle.write(content)
        temp_name = handle.name
    os.replace(temp_name, path)


@dataclass
class ProfileReport:
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    suppressed: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)


def reconcile_profile(
    profile: str,
    tabs: list[dict],
    meta: dict[str, dict[str, str]],
    apps: list[dict],
    *,
    software_root: Path,
    local_dev_root: Path,
) -> tuple[ProfileReport, dict[str, str]]:
    report = ProfileReport()
    registry_update: dict[str, str] = {}
    for app in apps:
        app_id = str(app["id"])
        desired = str(app.get("profiles", {}).get(profile, "PENDING")).upper()
        if desired not in VALID_STATES:
            report.blocked.append(
                f"{app_id} (ungültiger Registry-Zustand {desired})"
            )
            continue
        if desired == "SUPPRESSED":
            report.unchanged.append(f"{app_id} (unterdrückt)")
            continue
        target = resolve_template(
            str(app.get("launcher_template", "")),
            software_root=software_root,
            local_dev_root=local_dev_root,
        )
        if not target or not os.path.isfile(target):
            report.blocked.append(f"{app_id} (Startziel fehlt)")
            continue
        remembered = meta.get(app_id, {})
        hit = find_entry(tabs, [target, str(remembered.get("path", ""))])
        seen_before = bool(remembered.get("path"))
        if hit is None:
            if desired == "ACTIVE" and seen_before:
                registry_update[app_id] = "SUPPRESSED"
                report.suppressed.append(app_id)
                continue
            board = str(app.get("category", "Allgemein") or "Allgemein")
            tab_index = ensure_board(tabs, board)
            tabs[tab_index]["entries"].append(
                {
                    "path": target,
                    "label": app.get("name", app_id),
                    "kind": detect_kind(target),
                    "notes": None,
                }
            )
            meta[app_id] = {"path": target}
            registry_update[app_id] = "ACTIVE"
            report.added.append(f'{app_id} (Board "{board}")')
            continue
        tab_index, entry_index = hit
        entry = tabs[tab_index]["entries"][entry_index]
        if norm(str(entry.get("path", ""))) != norm(target):
            entry["path"] = target
            entry["kind"] = detect_kind(target)
            report.updated.append(
                f'{app_id} (Board "{tabs[tab_index]["name"]}")'
            )
        else:
            report.unchanged.append(
                f'{app_id} (Board "{tabs[tab_index]["name"]}")'
            )
        meta[app_id] = {"path": target}
        if desired == "PENDING":
            registry_update[app_id] = "ACTIVE"
    return report, registry_update


def print_report(profile: str, report: ProfileReport) -> None:
    print(f"\n{profile}")
    for title, entries, marker in (
        ("Neu", report.added, "+"),
        ("Pfade aktualisiert", report.updated, "~"),
        ("Vom Nutzer entfernt", report.suppressed, "-"),
        ("Blockiert", report.blocked, "!"),
    ):
        print(f"  {title}: {len(entries)}")
        for entry in entries:
            print(f"    {marker} {entry}")
    print(f"  Unverändert: {len(report.unchanged)}")


SettingsFactory = Callable[[str, str], QSettings]


def _restore_original_state(
    staged: list[
        tuple[QSettings, list[dict], int, dict[str, dict[str, str]]]
    ],
    backup_data: list[
        tuple[str, list[dict], int, dict[str, dict[str, str]]]
    ],
    registry_path: Path,
    registry_bytes: bytes,
) -> list[str]:
    errors: list[str] = []
    for (settings, _tabs, _current, _meta), (
        profile,
        original_tabs,
        original_current,
        original_meta,
    ) in zip(staged, backup_data, strict=True):
        try:
            save_profile(settings, original_tabs, original_current)
            save_meta(settings, original_meta)
        except (OSError, ValueError) as exc:
            errors.append(f"{profile}: {exc}")
    try:
        replace_file_bytes(registry_path, registry_bytes)
    except OSError as exc:
        errors.append(f"Registry: {exc}")
    return errors


def restore_backup_file(
    config: RuntimeConfig,
    *,
    settings_factory: SettingsFactory,
) -> int:
    assert config.restore_backup is not None
    try:
        payload = json.loads(
            config.restore_backup.read_text(encoding="utf-8")
        )
        if payload.get("format") != "launcher-catalog-profile-backup-v2":
            raise ValueError("unerwartetes Backupformat")
        registry = payload.get("registry")
        profiles = payload.get("profiles")
        if not isinstance(registry, dict) or not isinstance(profiles, dict):
            raise ValueError("Backup enthält keine Registry-/Profildaten")
        source_path = registry.get("source_path")
        registry_text = registry.get("text")
        registry_hash = registry.get("sha256")
        if not all(
            isinstance(value, str)
            for value in (source_path, registry_text, registry_hash)
        ):
            raise ValueError("Backup-Registrydaten sind unvollständig")
        if norm(source_path) != norm(str(config.registry)):
            raise ValueError(
                "Backup gehört zu einer anderen Registry-Datei: "
                f"{source_path}"
            )
        registry_bytes = registry_text.encode("utf-8")
        if _sha256(registry_bytes) != registry_hash:
            raise ValueError("Backup-Registryhash stimmt nicht")
        validated: list[
            tuple[QSettings, list[dict], int, dict[str, dict[str, str]]]
        ] = []
        for profile in PROFILES:
            profile_data = profiles.get(profile)
            if not isinstance(profile_data, dict):
                raise ValueError(f"Backup-Profil fehlt: {profile}")
            tabs = profile_data.get("tabs")
            current_tab = profile_data.get("current_tab")
            managed_paths = profile_data.get("managed_paths")
            if not isinstance(tabs, list) or not isinstance(current_tab, int):
                raise ValueError(f"Backup-Profil ungültig: {profile}")
            if not isinstance(managed_paths, dict):
                raise ValueError(f"Backup-Metadaten ungültig: {profile}")
            validated.append(
                (
                    settings_factory(ORG, profile),
                    tabs,
                    current_tab,
                    managed_paths,
                )
            )
        current_registry_bytes = config.registry.read_bytes()
        current_data: list[
            tuple[str, list[dict], int, dict[str, dict[str, str]]]
        ] = []
        for profile, (
            settings,
            _tabs,
            _current_tab,
            _managed_paths,
        ) in zip(PROFILES, validated, strict=True):
            current_tabs, current_tab = load_profile(settings)
            current_data.append(
                (profile, current_tabs, current_tab, load_meta(settings))
            )
    except (
        OSError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ABBRUCH: Restore-Validierung fehlgeschlagen: {exc}")
        print(f"Backup: {config.restore_backup}")
        return 3
    mutation_started = False
    try:
        for settings, tabs, current_tab, managed_paths in validated:
            mutation_started = True
            save_profile(settings, tabs, current_tab)
            save_meta(settings, managed_paths)
        replace_file_bytes(config.registry, registry_bytes)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ABBRUCH: Restore fehlgeschlagen: {exc}")
        print(f"Backup: {config.restore_backup}")
        if mutation_started:
            rollback_errors = _restore_original_state(
                validated,
                current_data,
                config.registry,
                current_registry_bytes,
            )
            if rollback_errors:
                print("RESTORE-ROLLBACK UNVOLLSTÄNDIG:")
                for error in rollback_errors:
                    print(f"  - {error}")
            else:
                print(
                    "RESTORE-ROLLBACK ERFOLGREICH: "
                    "vorheriger Zustand wiederhergestellt."
                )
        return 3
    print(f"Restore abgeschlossen: {config.restore_backup}")
    return 0


def execute(
    config: RuntimeConfig,
    *,
    settings_factory: SettingsFactory = QSettings,
    running_probe: Callable[[], bool | None] = is_profile_running,
) -> int:
    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ABBRUCH: {error}")
        return 2
    if config.apply:
        running_state = running_probe()
        if running_state is None:
            print(
                "ABBRUCH: Prozessstatus von SoftwareCenter und LaunchBoards "
                "konnte nicht verlässlich gelesen werden."
            )
            return 2
        if running_state:
            print(
                "ABBRUCH: SoftwareCenter oder LaunchBoards läuft. "
                "Bitte beide schließen und erneut ausführen."
            )
            return 2
    if config.restore_backup is not None:
        return restore_backup_file(
            config,
            settings_factory=settings_factory,
        )
    try:
        apps = read_catalog(config.catalog)
        state_overrides = registry_states(config.registry)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"ABBRUCH: Eingabedaten ungültig: {exc}")
        return 2
    for app in apps:
        app.setdefault("profiles", {}).update(
            state_overrides.get(str(app["id"]), {})
        )
    print(
        f"Launcher-Katalog: {len(apps)} Apps | "
        f"{'APPLY' if config.apply else 'DRY-RUN'}"
    )
    all_updates: dict[str, dict[str, str]] = {}
    staged: list[
        tuple[QSettings, list[dict], int, dict[str, dict[str, str]]]
    ] = []
    backup_data: list[
        tuple[str, list[dict], int, dict[str, dict[str, str]]]
    ] = []
    for profile in PROFILES:
        settings = settings_factory(ORG, profile)
        original_tabs, original_current_tab = load_profile(settings)
        original_meta = load_meta(settings)
        tabs = json.loads(json.dumps(original_tabs))
        meta = json.loads(json.dumps(original_meta))
        report, updates = reconcile_profile(
            profile,
            tabs,
            meta,
            apps,
            software_root=config.software_root,
            local_dev_root=config.local_dev_root,
        )
        print_report(profile, report)
        for app_id, state in updates.items():
            all_updates.setdefault(app_id, {})[profile] = state
        staged.append((settings, tabs, original_current_tab, meta))
        backup_data.append(
            (profile, original_tabs, original_current_tab, original_meta)
        )
    if not config.apply:
        print("\nDRY-RUN: keine Profile und keine Registry geschrieben.")
        return 0
    missing_registry_ids = sorted(set(all_updates) - set(state_overrides))
    if missing_registry_ids:
        print(
            "ABBRUCH: Registry enthält keine Zeile für: "
            + ", ".join(missing_registry_ids)
        )
        return 2
    backup: Path | None = None
    mutation_started = False
    try:
        original_registry_bytes = config.registry.read_bytes()
    except OSError as exc:
        print(
            "ABBRUCH: Registry ist unmittelbar vor dem Apply nicht mehr "
            f"stabil lesbar: {exc}"
        )
        return 2
    try:
        backup = backup_profiles(
            config.backup_dir,
            backup_data,
            config.registry,
            original_registry_bytes,
        )
        for settings, tabs, current_tab, meta in staged:
            mutation_started = True
            save_profile(settings, tabs, current_tab)
            save_meta(settings, meta)
        write_registry_updates(config.registry, all_updates)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ABBRUCH: Schreibvorgang fehlgeschlagen: {exc}")
        if backup is not None:
            print(f"Backup: {backup}")
        if backup is not None and mutation_started:
            rollback_errors = _restore_original_state(
                staged,
                backup_data,
                config.registry,
                original_registry_bytes,
            )
            if rollback_errors:
                print("ROLLBACK UNVOLLSTÄNDIG:")
                for error in rollback_errors:
                    print(f"  - {error}")
            else:
                print(
                    "ROLLBACK ERFOLGREICH: "
                    "Profile und Registry wiederhergestellt."
                )
        elif backup is None:
            print(
                "KEIN ROLLBACK-WRITE: Backup-Erstellung scheiterte "
                "vor Beginn der Mutation."
            )
        return 3
    print(f"\nBackup: {backup}")
    print(
        f"Geschrieben: {len(all_updates)} Registry-Einträge, "
        "beide lokale Profile aktualisiert."
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    return execute(parse_config(argv))


if __name__ == "__main__":
    raise SystemExit(main())
