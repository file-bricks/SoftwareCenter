# -*- coding: utf-8 -*-
"""Regression coverage for the Plan-D launcher-catalog runtime."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from scripts import softwarecenter_sync as sync


def app(app_id: str, target: str, state: str = "PENDING") -> dict:
    return {
        "id": app_id,
        "name": app_id,
        "category": "DATA",
        "launcher_template": target,
        "profiles": {
            "SoftwareCenter": state,
            "LaunchBoards": state,
        },
    }


def write_inputs(
    tmp_path: Path, *, state: str = "PENDING", target: Path | None = None
) -> tuple[Path, Path, Path, Path]:
    software_root = tmp_path / "software"
    local_dev_root = tmp_path / "local-dev"
    tools = software_root / "_tools"
    tools.mkdir(parents=True)
    local_dev_root.mkdir()
    if target is None:
        target = software_root / "DATA" / "Werkzeug.exe"
        target.parent.mkdir()
        target.write_bytes(b"exe")
    catalog = tools / "software_apps.json"
    catalog.write_text(
        json.dumps(
            {
                "format": "software-launcher-catalog-v2",
                "apps": [app("Werkzeug", str(target), state)],
            }
        ),
        encoding="utf-8",
    )
    registry = tmp_path / "DESKTOP-REGISTRY.txt"
    registry.write_text(
        f"DATA | Werkzeug : DESKTOP=OFF; "
        f"SOFTWARECENTER={state}; LAUNCHBOARDS={state}\n",
        encoding="utf-8",
    )
    return catalog, registry, software_root, local_dev_root


def config_for(
    tmp_path: Path, *, apply: bool = False, state: str = "PENDING"
) -> sync.RuntimeConfig:
    catalog, registry, software_root, local_dev_root = write_inputs(
        tmp_path, state=state
    )
    return sync.RuntimeConfig(
        catalog=catalog,
        registry=registry,
        software_root=software_root,
        local_dev_root=local_dev_root,
        backup_dir=local_dev_root / "backups",
        apply=apply,
    )


def settings_factory(tmp_path: Path):
    settings_root = tmp_path / "settings"

    def factory(_organization: str, profile: str) -> QSettings:
        settings_root.mkdir(exist_ok=True)
        return QSettings(str(settings_root / f"{profile}.ini"), QSettings.IniFormat)

    return factory


def test_cli_requires_exact_catalog_registry_and_roots():
    parser = sync.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
    with pytest.raises(SystemExit):
        parser.parse_args(
            [
                "--catalog",
                "catalog.json",
                "--registry",
                "registry.txt",
            ]
        )


def test_parse_config_preserves_explicit_inputs_as_absolute_paths(tmp_path):
    values = [
        "--catalog",
        str(tmp_path / "catalog.json"),
        "--registry",
        str(tmp_path / "registry.txt"),
        "--software-root",
        str(tmp_path / "software"),
        "--local-dev-root",
        str(tmp_path / "dev"),
    ]
    result = sync.parse_config(values)
    assert result.catalog == tmp_path / "catalog.json"
    assert result.registry == tmp_path / "registry.txt"
    assert result.software_root == tmp_path / "software"
    assert result.local_dev_root == tmp_path / "dev"
    assert result.backup_dir == tmp_path / "dev" / "launcher_catalog_backups"
    assert result.apply is False


def test_missing_inputs_fail_closed_without_settings_access(tmp_path, capsys):
    touched = False

    def factory(_organization: str, _profile: str) -> QSettings:
        nonlocal touched
        touched = True
        raise AssertionError("settings must not be opened")

    config = sync.RuntimeConfig(
        catalog=tmp_path / "missing.json",
        registry=tmp_path / "missing.txt",
        software_root=tmp_path / "missing-software",
        local_dev_root=tmp_path / "missing-dev",
        backup_dir=tmp_path / "backups",
        apply=False,
    )
    assert sync.execute(config, settings_factory=factory) == 2
    assert touched is False
    assert "ABBRUCH" in capsys.readouterr().out


def test_apply_rejects_backup_inside_synchronized_software_root(tmp_path):
    config = config_for(tmp_path, apply=True)
    unsafe = sync.RuntimeConfig(
        **{
            **config.__dict__,
            "backup_dir": config.software_root / "backups",
        }
    )
    errors = sync.validate_config(unsafe)
    assert any("Backup-Verzeichnis" in error for error in errors)


def test_apply_rejects_backup_anywhere_inside_detected_onedrive_root(tmp_path):
    one_drive = tmp_path / "OneDrive"
    software_root = one_drive / ".TOPICS" / ".SOFTWARE"
    tools = software_root / "_tools"
    desktop = one_drive / "Desktop"
    local_dev = tmp_path / "local-dev"
    tools.mkdir(parents=True)
    desktop.mkdir()
    local_dev.mkdir()
    catalog = tools / "software_apps.json"
    catalog.write_text(
        '{"format":"software-launcher-catalog-v2","apps":[]}',
        encoding="utf-8",
    )
    registry = desktop / "DESKTOP-REGISTRY.txt"
    registry.write_text("", encoding="utf-8")
    config = sync.RuntimeConfig(
        catalog=catalog,
        registry=registry,
        software_root=software_root,
        local_dev_root=local_dev,
        backup_dir=one_drive / ".backups",
        apply=True,
    )
    assert any(
        "synchronisierten Daten-Roots" in error
        for error in sync.validate_config(config)
    )


def test_dry_run_writes_neither_registry_profiles_nor_backup(tmp_path):
    config = config_for(tmp_path)
    original_registry = config.registry.read_bytes()
    factory = settings_factory(tmp_path)

    assert sync.execute(config, settings_factory=factory) == 0

    assert config.registry.read_bytes() == original_registry
    assert not config.backup_dir.exists()
    assert not list((tmp_path / "settings").glob("*.ini"))


def test_apply_is_blocked_while_a_profile_is_running(tmp_path, capsys):
    config = config_for(tmp_path, apply=True)
    original_registry = config.registry.read_bytes()

    assert (
        sync.execute(
            config,
            settings_factory=settings_factory(tmp_path),
            running_probe=lambda: True,
        )
        == 2
    )

    assert config.registry.read_bytes() == original_registry
    assert not config.backup_dir.exists()
    assert "läuft" in capsys.readouterr().out


def test_apply_fails_closed_when_process_probe_is_unavailable(tmp_path, capsys):
    config = config_for(tmp_path, apply=True)

    assert (
        sync.execute(
            config,
            settings_factory=settings_factory(tmp_path),
            running_probe=lambda: None,
        )
        == 2
    )

    assert not config.backup_dir.exists()
    assert "nicht verlässlich" in capsys.readouterr().out


def test_apply_backs_up_then_writes_both_profiles_and_registry(tmp_path):
    config = config_for(tmp_path, apply=True)
    factory = settings_factory(tmp_path)

    assert (
        sync.execute(
            config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 0
    )

    registry = config.registry.read_text(encoding="utf-8")
    assert "SOFTWARECENTER=ACTIVE" in registry
    assert "LAUNCHBOARDS=ACTIVE" in registry
    backups = list(config.backup_dir.glob("profiles_*.json"))
    assert len(backups) == 1
    backup = json.loads(backups[0].read_text(encoding="utf-8"))
    assert backup["format"] == "launcher-catalog-profile-backup-v2"
    assert backup["registry"]["text"].splitlines()[-1].endswith(
        "LAUNCHBOARDS=PENDING"
    )
    for profile in sync.PROFILES:
        settings = factory(sync.ORG, profile)
        tabs, _current = sync.load_profile(settings)
        assert tabs[0]["entries"][0]["label"] == "Werkzeug"
        assert sync.load_meta(settings)["Werkzeug"]["path"].endswith(
            "Werkzeug.exe"
        )


def test_mid_apply_failure_reports_backup_and_rolls_back_all_state(
    tmp_path, monkeypatch, capsys
):
    config = config_for(tmp_path, apply=True)
    factory = settings_factory(tmp_path)
    original_registry = config.registry.read_bytes()
    real_save_profile = sync.save_profile
    calls = 0

    def fail_second_profile(settings, tabs, current_tab):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic second-profile failure")
        real_save_profile(settings, tabs, current_tab)

    monkeypatch.setattr(sync, "save_profile", fail_second_profile)

    assert (
        sync.execute(
            config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 3
    )

    output = capsys.readouterr().out
    backups = list(config.backup_dir.glob("profiles_*.json"))
    assert len(backups) == 1
    assert f"Backup: {backups[0]}" in output
    assert "ROLLBACK ERFOLGREICH" in output
    assert config.registry.read_bytes() == original_registry
    for profile in sync.PROFILES:
        settings = factory(sync.ORG, profile)
        assert sync.load_profile(settings)[0] == []
        assert sync.load_meta(settings) == {}


def test_backup_creation_failure_performs_no_restore_or_other_write(
    tmp_path, monkeypatch, capsys
):
    config = config_for(tmp_path, apply=True)
    writes: list[str] = []

    def fail_backup(*_args, **_kwargs):
        raise OSError("synthetic backup failure")

    monkeypatch.setattr(sync, "backup_profiles", fail_backup)
    monkeypatch.setattr(
        sync,
        "save_profile",
        lambda *_args, **_kwargs: writes.append("profile"),
    )
    monkeypatch.setattr(
        sync,
        "save_meta",
        lambda *_args, **_kwargs: writes.append("meta"),
    )
    monkeypatch.setattr(
        sync,
        "replace_file_bytes",
        lambda *_args, **_kwargs: writes.append("registry"),
    )

    assert (
        sync.execute(
            config,
            settings_factory=settings_factory(tmp_path),
            running_probe=lambda: False,
        )
        == 3
    )

    assert writes == []
    assert "KEIN ROLLBACK-WRITE" in capsys.readouterr().out


def test_registry_disappearing_before_apply_fails_cleanly_without_writes(
    tmp_path, monkeypatch, capsys
):
    config = config_for(tmp_path, apply=True)
    writes: list[str] = []
    base_factory = settings_factory(tmp_path)
    removed = False

    def deleting_factory(organization: str, profile: str) -> QSettings:
        nonlocal removed
        if not removed:
            config.registry.unlink()
            removed = True
        return base_factory(organization, profile)

    monkeypatch.setattr(
        sync,
        "save_profile",
        lambda *_args, **_kwargs: writes.append("profile"),
    )
    monkeypatch.setattr(
        sync,
        "save_meta",
        lambda *_args, **_kwargs: writes.append("meta"),
    )
    monkeypatch.setattr(
        sync,
        "replace_file_bytes",
        lambda *_args, **_kwargs: writes.append("registry"),
    )

    assert (
        sync.execute(
            config,
            settings_factory=deleting_factory,
            running_probe=lambda: False,
        )
        == 2
    )

    assert writes == []
    assert not config.backup_dir.exists()
    assert "unmittelbar vor dem Apply" in capsys.readouterr().out


def test_restore_backup_cli_restores_profiles_and_registry(tmp_path):
    config = config_for(tmp_path, apply=True)
    factory = settings_factory(tmp_path)
    assert (
        sync.execute(
            config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 0
    )
    backup = next(config.backup_dir.glob("profiles_*.json"))
    config.registry.write_text("DATA | Werkzeug : BROKEN\n", encoding="utf-8")
    for profile in sync.PROFILES:
        settings = factory(sync.ORG, profile)
        sync.save_profile(
            settings,
            [
                {
                    "name": "Changed",
                    "view_mode": "tiles",
                    "entries": [],
                }
            ],
            0,
        )
    restore_config = sync.RuntimeConfig(
        **{
            **config.__dict__,
            "restore_backup": backup,
        }
    )

    assert (
        sync.execute(
            restore_config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 0
    )

    assert "SOFTWARECENTER=PENDING" in config.registry.read_text(
        encoding="utf-8"
    )
    for profile in sync.PROFILES:
        settings = factory(sync.ORG, profile)
        assert sync.load_profile(settings)[0] == []
        assert sync.load_meta(settings) == {}


def test_failed_restore_compensates_to_the_pre_restore_state(
    tmp_path, monkeypatch, capsys
):
    config = config_for(tmp_path, apply=True)
    factory = settings_factory(tmp_path)
    assert (
        sync.execute(
            config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 0
    )
    backup = next(config.backup_dir.glob("profiles_*.json"))
    changed_registry = b"DATA | Werkzeug : BROKEN\r\n"
    config.registry.write_bytes(changed_registry)
    for profile in sync.PROFILES:
        settings = factory(sync.ORG, profile)
        sync.save_profile(
            settings,
            [
                {
                    "name": "Changed",
                    "view_mode": "tiles",
                    "entries": [],
                }
            ],
            0,
        )
    restore_config = sync.RuntimeConfig(
        **{
            **config.__dict__,
            "restore_backup": backup,
        }
    )
    real_save_profile = sync.save_profile
    calls = 0

    def fail_second_restore_profile(settings, tabs, current_tab):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("synthetic restore failure")
        real_save_profile(settings, tabs, current_tab)

    monkeypatch.setattr(
        sync, "save_profile", fail_second_restore_profile
    )

    assert (
        sync.execute(
            restore_config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 3
    )

    assert config.registry.read_bytes() == changed_registry
    for profile in sync.PROFILES:
        settings = factory(sync.ORG, profile)
        assert sync.load_profile(settings)[0][0]["name"] == "Changed"
    assert "RESTORE-ROLLBACK ERFOLGREICH" in capsys.readouterr().out


def test_restore_backup_requires_apply(tmp_path):
    config = config_for(tmp_path)
    backup = tmp_path / "backup.json"
    backup.write_text("{}", encoding="utf-8")
    restore_config = sync.RuntimeConfig(
        **{
            **config.__dict__,
            "restore_backup": backup,
        }
    )
    assert "--restore-backup erfordert" in "\n".join(
        sync.validate_config(restore_config)
    )


def test_pending_app_is_added_once_and_activated(tmp_path):
    target = tmp_path / "Werkzeug.exe"
    target.write_bytes(b"exe")
    tabs: list[dict] = []
    meta: dict[str, dict[str, str]] = {}

    report, updates = sync.reconcile_profile(
        "SoftwareCenter",
        tabs,
        meta,
        [app("Werkzeug", str(target))],
        software_root=tmp_path,
        local_dev_root=tmp_path,
    )

    assert report.added == ['Werkzeug (Board "DATA")']
    assert updates == {"Werkzeug": "ACTIVE"}
    assert tabs[0]["entries"][0]["path"] == str(target)
    assert meta["Werkzeug"]["path"] == str(target)


def test_deleted_active_entry_is_suppressed_not_readded(tmp_path):
    target = tmp_path / "Werkzeug.exe"
    target.write_bytes(b"exe")

    report, updates = sync.reconcile_profile(
        "SoftwareCenter",
        [],
        {"Werkzeug": {"path": str(target)}},
        [app("Werkzeug", str(target), "ACTIVE")],
        software_root=tmp_path,
        local_dev_root=tmp_path,
    )

    assert report.suppressed == ["Werkzeug"]
    assert updates == {"Werkzeug": "SUPPRESSED"}


def test_explicit_suppressed_state_never_readds_entry(tmp_path):
    target = tmp_path / "Werkzeug.exe"
    target.write_bytes(b"exe")

    report, updates = sync.reconcile_profile(
        "SoftwareCenter",
        [],
        {},
        [app("Werkzeug", str(target), "SUPPRESSED")],
        software_root=tmp_path,
        local_dev_root=tmp_path,
    )

    assert report.added == []
    assert report.unchanged == ["Werkzeug (unterdrückt)"]
    assert updates == {}


def test_active_entry_moved_by_user_is_not_moved_back(tmp_path):
    target = tmp_path / "Werkzeug.exe"
    target.write_bytes(b"exe")
    tabs = [
        {
            "name": "Eigene Auswahl",
            "view_mode": "tiles",
            "entries": [
                {
                    "path": str(target),
                    "label": "Werkzeug",
                    "kind": "file",
                    "notes": "persönlich",
                }
            ],
        }
    ]
    meta = {"Werkzeug": {"path": str(target)}}

    report, updates = sync.reconcile_profile(
        "SoftwareCenter",
        tabs,
        meta,
        [app("Werkzeug", str(target), "ACTIVE")],
        software_root=tmp_path,
        local_dev_root=tmp_path,
    )

    assert not report.added and not report.updated and not report.suppressed
    assert updates == {}
    assert tabs[0]["name"] == "Eigene Auswahl"
    assert tabs[0]["entries"][0]["notes"] == "persönlich"


def test_missing_target_stays_pending_for_a_later_build(tmp_path):
    target = tmp_path / "does-not-exist.exe"

    report, updates = sync.reconcile_profile(
        "SoftwareCenter",
        [],
        {},
        [app("Werkzeug", str(target))],
        software_root=tmp_path,
        local_dev_root=tmp_path,
    )

    assert report.blocked == ["Werkzeug (Startziel fehlt)"]
    assert updates == {}


def test_registry_update_keeps_desktop_state_and_writes_profile_fields(tmp_path):
    registry = tmp_path / "DESKTOP-REGISTRY.txt"
    registry.write_text("DATA | Werkzeug : OFF\n", encoding="utf-8")

    sync.write_registry_updates(
        registry,
        {
            "Werkzeug": {
                "SoftwareCenter": "ACTIVE",
                "LaunchBoards": "SUPPRESSED",
            }
        },
    )

    text = registry.read_text(encoding="utf-8")
    assert "DESKTOP=OFF" in text
    assert "SOFTWARECENTER=ACTIVE" in text
    assert "LAUNCHBOARDS=SUPPRESSED" in text


def test_registry_update_fails_closed_for_unknown_app_id(tmp_path):
    registry = tmp_path / "DESKTOP-REGISTRY.txt"
    registry.write_text("DATA | Bekannt : OFF\n", encoding="utf-8")
    original = registry.read_bytes()

    with pytest.raises(ValueError, match="Unbekannt"):
        sync.write_registry_updates(
            registry,
            {"Unbekannt": {"SoftwareCenter": "ACTIVE"}},
        )

    assert registry.read_bytes() == original


def test_apply_detects_unknown_registry_id_before_any_profile_write(tmp_path):
    config = config_for(tmp_path, apply=True)
    config.registry.write_text("DATA | AndereApp : OFF\n", encoding="utf-8")
    factory = settings_factory(tmp_path)

    assert (
        sync.execute(
            config,
            settings_factory=factory,
            running_probe=lambda: False,
        )
        == 2
    )

    assert not config.backup_dir.exists()
    assert not list((tmp_path / "settings").glob("*.ini"))


def test_portable_templates_use_only_explicit_roots(tmp_path):
    software_root = tmp_path / "software"
    local_dev_root = tmp_path / "local-dev"
    value = (
        r"$SOFTWARE_ROOT\DATA\App\App.exe;"
        r"$LOCAL_DEV_ROOT\repos\App\App.exe"
    )

    resolved = sync.resolve_template(
        value,
        software_root=software_root,
        local_dev_root=local_dev_root,
    )

    assert str(software_root) in resolved
    assert str(local_dev_root) in resolved
    assert "$SOFTWARE_ROOT" not in resolved
    assert "$LOCAL_DEV_ROOT" not in resolved
    assert str(Path(sync.__file__).parent) not in resolved


def test_process_probe_uses_argv_without_shell(monkeypatch):
    captured: dict = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(sync.subprocess, "run", fake_run)

    assert sync.is_profile_running() is False
    assert captured["argv"] == ["tasklist", "/NH", "/FO", "CSV"]
    assert captured["shell"] is False


@pytest.mark.parametrize(
    "image_name",
    [
        "SoftwareCenter.exe",
        "SoftwareCenter-1.2.0-win64.exe",
        "LaunchBoards.exe",
        "LaunchBoards-1.0.0-win64.exe",
    ],
)
def test_process_probe_blocks_all_supported_profile_image_names(
    monkeypatch, image_name
):
    output = f'"{image_name}","1234","Console","1","10,000 K"\n'

    def fake_run(argv, **_kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=output, stderr="")

    monkeypatch.setattr(sync.subprocess, "run", fake_run)
    assert sync.is_profile_running() is True


@pytest.mark.parametrize(
    "image_name",
    [
        "SoftwareCenterHelper.exe",
        "SoftwareCenter-copy.exe",
        "MyLaunchBoards.exe",
        "LaunchBoards-evil-win64.exe",
    ],
)
def test_process_probe_does_not_block_similarly_named_foreign_processes(
    monkeypatch, image_name
):
    output = f'"{image_name}","1234","Console","1","10,000 K"\n'

    def fake_run(argv, **_kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout=output, stderr="")

    monkeypatch.setattr(sync.subprocess, "run", fake_run)
    assert sync.is_profile_running() is False


def test_invalid_catalog_fails_closed_before_profile_writes(tmp_path):
    config = config_for(tmp_path)
    config.catalog.write_text('{"format":"wrong","apps":[]}', encoding="utf-8")

    assert (
        sync.execute(
            config,
            settings_factory=settings_factory(tmp_path),
        )
        == 2
    )

    assert not config.backup_dir.exists()
    assert not list((tmp_path / "settings").glob("*.ini"))


def test_runtime_migration_doc_uses_host_variables_not_a_personal_home_path():
    document = (
        Path(__file__).resolve().parents[1] / "RUNTIME_DAILY_CARE.md"
    ).read_text(encoding="utf-8")
    assert r"C:\Users\lukas" not in document
    assert "$env:USERPROFILE" in document
    assert "$env:LOCALAPPDATA" in document
