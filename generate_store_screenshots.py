from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "1")

from PySide6 import QtCore, QtGui, QtWidgets

import SoftwareCenter as module
from SoftwareCenter import MainWindow


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "README" / "screenshots" / "store"

SCREENSHOT_FILES = {
    "main": "main-window.png",
    "tabs": "tab-organization.png",
    "tiles": "tiles-view.png",
    "list": "list-view.png",
}


def _process_events(app: QtWidgets.QApplication, duration: float = 0.08) -> None:
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)


def _configure_runtime_dirs(temp_root: Path) -> Path:
    home_dir = temp_root / "home"
    home_dir.mkdir(parents=True, exist_ok=True)

    os.environ["HOME"] = str(home_dir)
    os.environ["USERPROFILE"] = str(home_dir)
    os.environ["APPDATA"] = str(home_dir / "AppData" / "Roaming")
    os.environ["LOCALAPPDATA"] = str(home_dir / "AppData" / "Local")
    os.environ["XDG_CONFIG_HOME"] = str(home_dir / ".config")

    settings_root = temp_root / "qsettings"
    settings_root.mkdir(parents=True, exist_ok=True)
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    QtCore.QSettings.setPath(
        QtCore.QSettings.IniFormat,
        QtCore.QSettings.UserScope,
        str(settings_root),
    )
    QtCore.QSettings.setPath(
        QtCore.QSettings.IniFormat,
        QtCore.QSettings.SystemScope,
        str(settings_root),
    )
    return home_dir


def _write_demo_targets(workspace: Path) -> dict[str, Path]:
    workspace.mkdir(parents=True, exist_ok=True)

    targets = {
        "briefing": workspace / "Projekt-Briefing.txt",
        "editor": workspace / "Redaktion.py",
        "mail": workspace / "Mail-Export.cmd",
        "ocr": workspace / "PDF-Werkstatt.bat",
        "research": workspace / "Recherche.url",
        "sync": workspace / "Sync-Ordner.lnk",
        "release": workspace / "Release-Check.ps1",
        "notes": workspace / "Notizen.md",
    }
    demo_text = {
        "briefing": "Projekt-Briefing für lokale Software-Sammlungen.\n",
        "editor": "print('Lokale Redaktion mit echten Umlauten: äöü')\n",
        "mail": "@echo off\r\necho Mail-Export vorbereiten\r\n",
        "ocr": "@echo off\r\necho PDF-Werkstatt starten\r\n",
        "research": "[InternetShortcut]\nURL=https://example.invalid/recherche\n",
        "sync": "Demo-Verknüpfung für lokale Synchronisation\n",
        "release": "Write-Output 'Release-Check vorbereiten'\n",
        "notes": "# Notizen\n\nDesktop-Profile bleiben lokal.\n",
    }
    for key, path in targets.items():
        path.write_text(demo_text[key], encoding="utf-8")
    return targets


def _entry(path: Path, label: str, kind: str, notes: str | None = None) -> dict[str, str | None]:
    return {
        "path": str(path),
        "label": label,
        "kind": kind,
        "notes": notes,
    }


def _apply_consistent_icons(list_widget: module.SoftwareListWidget, icon: QtGui.QIcon) -> None:
    for index in range(list_widget.count()):
        item = list_widget.item(index)
        item.setIcon(icon)


def _configure_demo_window(window: MainWindow, targets: dict[str, Path]) -> None:
    default_page = window.current_page()
    if default_page is None:
        raise RuntimeError("SoftwareCenter konnte keine Startseite erzeugen")

    workspace_entries = [
        _entry(targets["briefing"], "Projekt-Briefing", "file", "Startpunkt für lokale Arbeitsplätze"),
        _entry(targets["editor"], "Redaktion", "script", "Bearbeitung und Review"),
        _entry(targets["mail"], "Mail-Export", "script", "Regelbasierte Übergabe"),
        _entry(targets["ocr"], "PDF-Werkstatt", "script", "OCR und PDF-Werkzeuge"),
        _entry(targets["research"], "Recherche", "url", "Schneller Sprung zu Referenzen"),
        _entry(targets["sync"], "Sync-Ordner", "windows_shortcut", "Lokale Zielpfade im Blick"),
    ]
    office_entries = [
        _entry(targets["notes"], "Projekt-Notizen", "file", "Besprechungen und offene Punkte"),
        _entry(targets["briefing"], "Freigabe-Briefing", "file", "Kompakte Zusammenfassung"),
        _entry(targets["release"], "Release-Check", "script", "Vor dem Versand prüfen"),
    ]
    review_entries = [
        _entry(targets["editor"], "Text-Review", "script", "Korrektur und Endabnahme"),
        _entry(targets["mail"], "Mail-Status", "script", "Letzten Export kontrollieren"),
        _entry(targets["ocr"], "Dokumente", "script", "Neue PDFs prüfen"),
    ]

    default_page.add_entries(workspace_entries)
    window.tabs.setTabText(0, "Arbeitsplatz")
    window.add_new_tab("Office", "tiles", entries=office_entries)
    window.add_new_tab("Review", "list", entries=review_entries)
    window.add_new_tab(
        "Setup",
        "tiles",
        entries=[
            _entry(targets["sync"], "Zielpfade", "windows_shortcut", "Nur Referenz, kein Upload"),
            _entry(targets["release"], "Versionen", "script", "Checks für die Übergabe"),
        ],
    )

    app_icon = window.windowIcon()
    if app_icon.isNull():
        app_icon = QtGui.QIcon(str(PROJECT_ROOT / "icon.ico"))
    for index in range(window.tabs.count()):
        page = window.tabs.widget(index)
        if isinstance(page, module.TabPage):
            _apply_consistent_icons(page.list, app_icon)


def _save_widget(widget: QtWidgets.QWidget, target: Path) -> None:
    widget.show()
    widget.raise_()
    widget.activateWindow()
    app = QtWidgets.QApplication.instance()
    if app is not None:
        _process_events(app)
    pixmap = widget.grab()
    if pixmap.isNull():
        raise RuntimeError(f"Screenshot für {target.name} konnte nicht erzeugt werden")
    target.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(target)):
        raise RuntimeError(f"Screenshot {target} konnte nicht gespeichert werden")


def _write_summary(targets: list[Path]) -> Path:
    summary_path = targets[0].parent / "summary.json"
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "screenshots": [
            {"name": "main", "file": SCREENSHOT_FILES["main"], "caption": "Hauptfenster mit lokalen Launcher-Kacheln"},
            {"name": "tabs", "file": SCREENSHOT_FILES["tabs"], "caption": "Mehrere Workflow-Tabs im selben Profil"},
            {"name": "tiles", "file": SCREENSHOT_FILES["tiles"], "caption": "Kachelansicht für schnellen Zugriff"},
            {"name": "list", "file": SCREENSHOT_FILES["list"], "caption": "Listenansicht für größere Sammlungen"},
        ],
    }
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary_path


def generate_store_screenshots(output_dir: Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="softwarecenter-store-shots-") as temp_dir:
        temp_root = Path(temp_dir)
        home_dir = _configure_runtime_dirs(temp_root)
        targets = _write_demo_targets(home_dir / "workspace")

        QtCore.QStandardPaths.setTestModeEnabled(True)
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        app.setApplicationName("SoftwareCenter Store Screenshots")
        app.setQuitOnLastWindowClosed(False)

        settings = QtCore.QSettings(str(temp_root / "softwarecenter.ini"), QtCore.QSettings.IniFormat)
        window = MainWindow(settings=settings)
        window.resize(1600, 960)
        _configure_demo_window(window, targets)

        result_paths = [
            output_dir / SCREENSHOT_FILES["main"],
            output_dir / SCREENSHOT_FILES["tabs"],
            output_dir / SCREENSHOT_FILES["tiles"],
            output_dir / SCREENSHOT_FILES["list"],
        ]

        try:
            window.tabs.setCurrentIndex(0)
            window.set_current_view("tiles")
            window.statusBar().showMessage("Lokale Sammlung · 6 Einträge · Offline", 0)
            _save_widget(window, result_paths[0])

            window.tabs.setCurrentIndex(2)
            window.statusBar().showMessage("Tabs für Arbeitsplatz, Office, Review und Setup", 0)
            _save_widget(window, result_paths[1])

            window.tabs.setCurrentIndex(0)
            window.set_current_view("tiles")
            window.statusBar().showMessage("Kachelansicht für schnellen Programmzugriff", 0)
            _save_widget(window, result_paths[2])

            window.set_current_view("list")
            window.statusBar().showMessage("Listenansicht für größere Sammlungen", 0)
            _save_widget(window, result_paths[3])
        finally:
            window.close()
            _process_events(app)

    _write_summary(result_paths)
    return result_paths


def main() -> None:
    targets = generate_store_screenshots(OUTPUT_DIR)
    for target in targets:
        print(target.name)


if __name__ == "__main__":
    main()
