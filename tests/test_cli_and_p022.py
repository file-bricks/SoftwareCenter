# -*- coding: utf-8 -*-
"""Tests for the P-022 headless dual-use CLI, product skill, and profile/settings hardening."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import SoftwareCenter as sc
import softwarecenter_cli as cli

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)

ROOT = Path(__file__).resolve().parents[1]


def _run_cli(args: list[str], script: str = "SoftwareCenter.py") -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "QT_QPA_PLATFORM": "offscreen"}
    return subprocess.run(
        [sys.executable, str(ROOT / script), *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )


def test_cli_version_and_help_for_both_products():
    res_sc = _run_cli(["--version", "--json"])
    assert res_sc.returncode == 0
    data_sc = json.loads(res_sc.stdout)
    assert data_sc["ok"] is True
    assert data_sc["product"] == "SoftwareCenter"
    assert data_sc["version"] == sc.__version__

    res_lb = _run_cli(["--version", "--json"], script="launchboards.py")
    assert res_lb.returncode == 0
    data_lb = json.loads(res_lb.stdout)
    assert data_lb["product"] == "LaunchBoards"
    assert data_lb["version"] == sc.__version__

    res_help = _run_cli(["--help"])
    assert res_help.returncode == 0
    assert "boards" in res_help.stdout
    assert "entries" in res_help.stdout
    assert "profile" in res_help.stdout


def test_should_dispatch_cli_does_not_intercept_product_boundary_child_flags():
    assert cli.should_dispatch_cli([]) is False
    assert cli.should_dispatch_cli(["--child", "--product", "SoftwareCenter"]) is False
    assert cli.should_dispatch_cli(["-platform", "offscreen"]) is False
    assert cli.should_dispatch_cli(["--json", "boards", "list"]) is True
    assert cli.should_dispatch_cli(["boards", "list"]) is True


def test_cli_boards_entries_search_and_gui_qsettings_parity(tmp_path: Path):
    ini_path = tmp_path / "cli_parity.ini"
    target_file = tmp_path / "demo_tool.bat"
    target_file.write_text("@echo off\n", encoding="utf-8")

    # 1. Create board via CLI
    rc = cli.cli_main(["--json", "--settings-file", str(ini_path), "boards", "create", "Werkzeuge", "--view", "list"])
    assert rc == 0

    # 2. List boards and get IDs
    res_list = _run_cli(["--json", "--settings-file", str(ini_path), "boards", "list"])
    assert res_list.returncode == 0
    boards_payload = json.loads(res_list.stdout)
    names = [b["name"] for b in boards_payload["boards"]]
    assert names == ["Allgemein", "Werkzeuge"]
    tools_id = boards_payload["boards"][1]["id"]

    # 3. Add entries (local file + URL) and verify deduplication
    res_add = _run_cli(
        [
            "--json",
            "--settings-file",
            str(ini_path),
            "entries",
            "add",
            "Werkzeuge",
            str(target_file),
            "--label",
            "Demo Tool",
            "--notes",
            "Für Tests",
        ]
    )
    assert res_add.returncode == 0
    assert json.loads(res_add.stdout)["added"] is True

    res_dup = _run_cli(
        ["--json", "--settings-file", str(ini_path), "entries", "add", tools_id, str(target_file)]
    )
    assert res_dup.returncode == 0
    assert json.loads(res_dup.stdout)["duplicate"] is True

    res_url = _run_cli(
        ["--json", "--settings-file", str(ini_path), "entries", "add", "Werkzeuge", "https://example.org"]
    )
    assert res_url.returncode == 0

    # 4. Favorite + close + search --include-closed + reactivate
    assert cli.cli_main(["--json", "--settings-file", str(ini_path), "boards", "favorite", tools_id]) == 0
    assert cli.cli_main(["--json", "--settings-file", str(ini_path), "boards", "close", tools_id]) == 0

    # Refusing to close the last remaining active board
    res_last = _run_cli(["--json", "--settings-file", str(ini_path), "boards", "close", "Allgemein"])
    assert res_last.returncode == 2

    res_search = _run_cli(
        ["--json", "--settings-file", str(ini_path), "search", "Für Tests", "--include-closed"]
    )
    assert res_search.returncode == 0
    search_data = json.loads(res_search.stdout)
    assert search_data["count"] == 1
    assert search_data["hits"][0]["status"] == "closed"
    assert search_data["hits"][0]["label"] == "Demo Tool"

    assert cli.cli_main(["--json", "--settings-file", str(ini_path), "boards", "reactivate", tools_id]) == 0

    # 5. Open the exact same INI file in PySide6 MainWindow and verify full parity
    win = sc.MainWindow(settings=QSettings(str(ini_path), QSettings.Format.IniFormat))
    try:
        assert win.tabs.count() == 2
        assert win.tabs.tabText(1) == "Werkzeuge"
        page = win.tabs.widget(1)
        assert page.board_id == tools_id
        assert page.view_mode == "list"
        assert tools_id in win.favorites
        entries = page.list.get_all_entries()
        assert len(entries) == 2
        assert entries[0]["label"] == "Demo Tool"
        assert entries[0]["notes"] == "Für Tests"
    finally:
        win.close()

    # 6. Remove entry via CLI without deleting target file on disk
    res_rm = _run_cli(["--json", "--settings-file", str(ini_path), "entries", "remove", "Werkzeuge", "Demo Tool"])
    assert res_rm.returncode == 0
    assert json.loads(res_rm.stdout)["removed_count"] == 1
    assert target_file.exists()


def test_cli_profile_export_validate_import_and_launch_dry_run(tmp_path: Path):
    src_ini = tmp_path / "src.ini"
    dst_ini = tmp_path / "dst.ini"
    export_json = tmp_path / "exported.json"
    app_file = tmp_path / "runner.bat"
    app_file.write_text("@echo off\n", encoding="utf-8")

    assert cli.cli_main(["--settings-file", str(src_ini), "boards", "create", "DevTools"]) == 0
    assert (
        cli.cli_main(
            [
                "--settings-file",
                str(src_ini),
                "entries",
                "add",
                "DevTools",
                str(app_file),
                "--label",
                "Runner",
            ]
        )
        == 0
    )

    res_exp = _run_cli(["--json", "--settings-file", str(src_ini), "profile", "export", str(export_json)])
    assert res_exp.returncode == 0
    assert export_json.exists()

    res_val = _run_cli(["--json", "profile", "validate", str(export_json)])
    assert res_val.returncode == 0
    assert json.loads(res_val.stdout)["valid"] is True

    # Import must refuse without --yes
    res_imp_no = _run_cli(["--json", "--settings-file", str(dst_ini), "profile", "import", str(export_json)])
    assert res_imp_no.returncode == 2

    res_imp_yes = _run_cli(
        ["--json", "--settings-file", str(dst_ini), "profile", "import", str(export_json), "--yes"]
    )
    assert res_imp_yes.returncode == 0
    assert json.loads(res_imp_yes.stdout)["tabs"] == 2

    res_launch_dry = _run_cli(
        ["--json", "--settings-file", str(dst_ini), "launch", "Runner", "--board", "DevTools", "--dry-run"]
    )
    assert res_launch_dry.returncode == 0
    assert json.loads(res_launch_dry.stdout)["exists"] is True

    res_missing = _run_cli(["--json", "launch", str(tmp_path / "does_not_exist.exe"), "--dry-run"])
    assert res_missing.returncode == 2


def test_profile_bool_version_and_current_tab_guards(tmp_path: Path):
    with pytest.raises(ValueError):
        sc.validate_profile_payload(
            {
                "format": sc.PROFILE_FORMAT,
                "format_version": True,
                "tabs": [{"name": "Test", "view_mode": "tiles", "entries": []}],
            }
        )

    win = sc.MainWindow(settings=QSettings(str(tmp_path / "bool_tab.ini"), QSettings.Format.IniFormat))
    try:
        win.apply_profile_payload(
            {
                "format": sc.PROFILE_FORMAT,
                "format_version": 1,
                "current_tab": True,
                "tabs": [
                    {"name": "First", "view_mode": "tiles", "entries": []},
                    {"name": "Second", "view_mode": "list", "entries": []},
                ],
            }
        )
        assert win.tabs.currentIndex() == 0
    finally:
        win.close()


def test_p022_skill_and_llm_entrypoints_contract():
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    llm_text = (ROOT / "llm.txt").read_text(encoding="utf-8")

    assert 'version: "1.2.0"' in skill_text
    assert "llms.txt" in skill_text
    assert "--settings-file" in skill_text
    assert "--yes" in skill_text
    assert "C:\\Users\\" not in skill_text
    assert "OneDrive" not in skill_text

    assert "llms.txt" in llm_text
    assert "SKILL.md" in llm_text

    for readme_name in ("README.md", "README_de.md", "README.es.md"):
        readme_text = (ROOT / readme_name).read_text(encoding="utf-8")
        assert "SKILL.md" in readme_text
        assert "llm.txt" in readme_text
