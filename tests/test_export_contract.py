"""Redacted, real desktop export/import contract.

The web/PWA companion was removed from the source tree on 2026-07-23. This
test therefore proves the authoritative desktop contract and keeps the
optional web boundary explicit instead of inventing a second implementation.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

import SoftwareCenter as sc


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "profile_export_redacted.json"


def _app() -> QApplication:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def _secret_hits(text: str) -> list[str]:
    lowered = text.casefold()
    return [
        word
        for word in (
            "api_key",
            "authorization",
            "credential",
            "password",
            "secret",
            "token",
        )
        if word in lowered
    ]


def test_redacted_fixture_is_valid_json_and_has_no_secrets() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    payload = json.loads(text)
    assert sc.validate_profile_payload(payload)
    assert len(payload["tabs"]) == 2
    assert payload["tabs"][1]["entries"][0]["path"].startswith("Z:/NichtVorhanden")
    assert "Übergabe" in text and "Äußeres Werkzeug" in text
    assert _secret_hits(text) == []


def test_real_desktop_export_roundtrip_preserves_missing_path_and_unicode(tmp_path: Path) -> None:
    _app()
    source_dir = tmp_path / "source"
    export_dir = tmp_path / "export"
    source_dir.mkdir()
    export_dir.mkdir()
    source = source_dir / "Lokales Werkzeug.exe"
    source.write_bytes(b"redacted fixture payload")
    export_path = export_dir / "softwarecenter-profile-v1.json"

    first = sc.MainWindow(settings=QSettings(str(tmp_path / "first.ini"), QSettings.Format.IniFormat))
    try:
        page = first.current_page()
        assert page is not None
        page.add_paths([str(source)])
        first.add_new_tab(
            "Übergabe",
            "list",
            entries=[
                {
                    "path": "Z:/NichtVorhanden/Ä/Tool.exe",
                    "label": "Äußeres Werkzeug",
                    "kind": "file",
                    "notes": "Für den zweiten Rechner – Größe prüfen",
                }
            ],
        )
        first.tabs.setCurrentIndex(1)
        payload = sc.profile_export_data(first)
        export_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    finally:
        first.close()

    readback = json.loads(export_path.read_text(encoding="utf-8"))
    assert sc.validate_profile_payload(readback)
    assert len(readback["tabs"]) == 2
    assert readback["tabs"][1]["entries"][0]["path"] == "Z:/NichtVorhanden/Ä/Tool.exe"
    assert readback["tabs"][1]["entries"][0]["notes"] == "Für den zweiten Rechner – Größe prüfen"
    assert _secret_hits(export_path.read_text(encoding="utf-8")) == []
    assert [path.name for path in export_dir.iterdir()] == ["softwarecenter-profile-v1.json"]
    assert not (export_dir / source.name).exists()

    second = sc.MainWindow(settings=QSettings(str(tmp_path / "second.ini"), QSettings.Format.IniFormat))
    try:
        second.apply_profile_payload(readback)
        assert second.tabs.count() == 2
        assert second.tabs.currentIndex() == 1
        imported = second.current_page()
        assert imported is not None
        assert imported.list.count() == 1
        item = imported.list.item(0)
        assert item.text() == "Äußeres Werkzeug"
        assert item.data(sc.Qt.ItemDataRole.UserRole) == "Z:/NichtVorhanden/Ä/Tool.exe"
        assert "Größe prüfen" in item.toolTip()
    finally:
        second.close()


def test_web_companion_boundary_is_explicit() -> None:
    web_root = ROOT / "web_companion"
    if web_root.exists():
        assert (web_root / "package.json").exists()
    else:
        assert not (ROOT / "package.json").exists()
