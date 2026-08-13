from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_SCALE_FACTOR", "1")

MIN_STORE_WIDTH = 1366
MIN_STORE_HEIGHT = 768

# Qt-Plattformen ohne echtes Fenstersystem. Sie rendern auf diesem System keine
# Glyphen (Tofu-Kaestchen statt Text) und haben 2026-08-11 zur Store-Ablehnung
# nach Policy 10.1.1.3 ("Inaccurate Representation") gefuehrt.
HEADLESS_PLATFORMS = frozenset({"offscreen", "minimal", "vnc"})

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
        "backup": workspace / "Backup-Lauf.cmd",
        "invoice": workspace / "Rechnungen.bat",
        "calendar": workspace / "Wochenplan.md",
        "photos": workspace / "Bildarchiv.lnk",
        "budget": workspace / "Haushaltsbuch.txt",
        "manual": workspace / "Handbuch.url",
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
        "backup": "@echo off\r\necho Backup-Lauf starten\r\n",
        "invoice": "@echo off\r\necho Rechnungen sortieren\r\n",
        "calendar": "# Wochenplan\n\nTermine und Aufgaben der Woche.\n",
        "photos": "Demo-Verknüpfung für das lokale Bildarchiv\n",
        "budget": "Haushaltsbuch – lokale Übersicht der Ausgaben.\n",
        "manual": "[InternetShortcut]\nURL=https://example.invalid/handbuch\n",
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
        _entry(targets["backup"], "Backup-Lauf", "script", "Sicherung der Arbeitsdaten"),
        _entry(targets["invoice"], "Rechnungen", "script", "Belege sortieren"),
        _entry(targets["calendar"], "Wochenplan", "file", "Termine und Aufgaben"),
        _entry(targets["photos"], "Bildarchiv", "windows_shortcut", "Fotos und Grafiken"),
        _entry(targets["budget"], "Haushaltsbuch", "file", "Ausgaben im Blick"),
        _entry(targets["manual"], "Handbuch", "url", "Nachschlagewerk öffnen"),
        _entry(targets["notes"], "Notizen", "file", "Schnelle Gedächtnisstütze"),
        _entry(targets["release"], "Release-Check", "script", "Vor dem Versand prüfen"),
    ]
    office_entries = [
        _entry(targets["notes"], "Projekt-Notizen", "file", "Besprechungen und offene Punkte"),
        _entry(targets["briefing"], "Freigabe-Briefing", "file", "Kompakte Zusammenfassung"),
        _entry(targets["release"], "Release-Check", "script", "Vor dem Versand prüfen"),
        _entry(targets["mail"], "Post-Ausgang", "script", "Versand vorbereiten"),
        _entry(targets["ocr"], "Scan-Ablage", "script", "Belege einsortieren"),
        _entry(targets["research"], "Vorlagen", "url", "Verweise auf Musterdokumente"),
    ]
    review_entries = [
        _entry(targets["editor"], "Text-Review", "script", "Korrektur und Endabnahme"),
        _entry(targets["mail"], "Mail-Status", "script", "Letzten Export kontrollieren"),
        _entry(targets["ocr"], "Dokumente", "script", "Neue PDFs prüfen"),
    ]

    default_page.add_entries(workspace_entries)
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

    # Erst umbenennen, wenn alle Tabs stehen: Solange nur ein Tab existiert, ist die
    # Tab-Leiste noch ohne Schliessen-Knopf bemessen; ein spaeter eingeblendeter Knopf
    # laege sonst ueber dem laengeren Namen.
    window.tabs.setTabText(0, "Arbeitsplatz")

    app_icon = window.windowIcon()
    if app_icon.isNull():
        app_icon = QtGui.QIcon(str(PROJECT_ROOT / "icon.ico"))
    for index in range(window.tabs.count()):
        page = window.tabs.widget(index)
        if isinstance(page, module.TabPage):
            _apply_consistent_icons(page.list, app_icon)


def real_gui_available() -> bool:
    """Kann dieser Prozess ein echtes Fenster zeichnen?

    Laeuft bereits eine QApplication (z. B. unter pytest mit
    ``QT_QPA_PLATFORM=offscreen``), entscheidet deren Plattform-Plugin -- ein
    zweites laesst sich nicht daneben starten.
    """
    app = QtWidgets.QApplication.instance()
    if app is not None:
        return app.platformName() not in HEADLESS_PLATFORMS
    forced = os.environ.get("QT_QPA_PLATFORM", "")
    if forced in HEADLESS_PLATFORMS:
        # Wird beim Erzeugen der QApplication verworfen, siehe _native_qt_platform().
        forced = ""
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(forced or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


@contextlib.contextmanager
def _native_qt_platform():
    """Verwirft ein von aussen gesetztes Offscreen-Plugin nur fuer diesen Block.

    Qt liest ``QT_QPA_PLATFORM`` beim Erzeugen der QApplication. Die Variable
    darf nicht dauerhaft aus der Umgebung verschwinden, sonst verliert ein
    umgebender Testlauf sein Headless-Setup.
    """
    previous = os.environ.get("QT_QPA_PLATFORM")
    if previous in HEADLESS_PLATFORMS:
        del os.environ["QT_QPA_PLATFORM"]
    try:
        yield
    finally:
        if previous is not None:
            os.environ["QT_QPA_PLATFORM"] = previous


def _require_real_gui(app: QtWidgets.QApplication) -> None:
    """Bricht laut ab, statt lautlos unlesbare Screenshots zu erzeugen."""
    platform = app.platformName()
    if platform in HEADLESS_PLATFORMS:
        raise RuntimeError(
            "Store-Screenshots brauchen eine echte GUI-Session. Aktives Qt-Plattform-Plugin: "
            f"'{platform}'. Offscreen-Rendering erzeugt Tofu-Kaestchen statt Text und wurde vom "
            "Windows Store nach Policy 10.1.1.3 abgelehnt."
        )


def _save_widget(widget: QtWidgets.QWidget, target: Path) -> None:
    widget.show()
    widget.raise_()
    widget.activateWindow()
    app = QtWidgets.QApplication.instance()
    if app is not None:
        _process_events(app, duration=0.4)
    pixmap = widget.grab()
    if pixmap.isNull():
        raise RuntimeError(f"Screenshot für {target.name} konnte nicht erzeugt werden")
    if pixmap.width() < MIN_STORE_WIDTH or pixmap.height() < MIN_STORE_HEIGHT:
        raise RuntimeError(
            f"Screenshot {target.name} ist mit {pixmap.width()}x{pixmap.height()} kleiner als die "
            f"Store-Mindestgroesse {MIN_STORE_WIDTH}x{MIN_STORE_HEIGHT}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(target)):
        raise RuntimeError(f"Screenshot {target} konnte nicht gespeichert werden")
    print(f"{target.name}: {pixmap.width()}x{pixmap.height()}")


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
        with _native_qt_platform():
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        app.setApplicationName("SoftwareCenter Store Screenshots")
        app.setQuitOnLastWindowClosed(False)
        _require_real_gui(app)

        ini_path = str(temp_root / "softwarecenter.ini")

        # Schritt 1: Demo-Profil aufbauen und speichern.
        builder_settings = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        builder = MainWindow(settings=builder_settings)
        builder.resize(1600, 960)
        _configure_demo_window(builder, targets)
        builder.save_settings()
        builder_settings.sync()
        builder.close()
        _process_events(app)

        # Schritt 2: Fenster frisch aus dem gespeicherten Profil starten. Genau so
        # sieht die App ein wiederkehrender Nutzer -- und nur so ist die Board-Leiste
        # von Anfang an korrekt bemessen.
        settings = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        window = MainWindow(settings=settings)
        window.resize(1600, 960)
        _process_events(app)

        result_paths = [
            output_dir / SCREENSHOT_FILES["main"],
            output_dir / SCREENSHOT_FILES["tabs"],
            output_dir / SCREENSHOT_FILES["tiles"],
            output_dir / SCREENSHOT_FILES["list"],
        ]

        try:
            window.tabs.setCurrentIndex(0)
            window.set_current_view("tiles")
            entry_count = window.current_page().list.count()
            window.statusBar().showMessage(
                f"Lokale Sammlung · {entry_count} Einträge · Offline", 0
            )
            _save_widget(window, result_paths[0])

            window.tabs.setCurrentIndex(2)
            window.statusBar().showMessage("Tabs für Arbeitsplatz, Office, Review und Setup", 0)
            _save_widget(window, result_paths[1])

            # Bewusst ein anderes Board als bei "main", sonst waeren zwei der vier
            # Store-Screenshots dasselbe Bild.
            window.tabs.setCurrentIndex(1)
            window.set_current_view("tiles")
            window.statusBar().showMessage("Kachelansicht für schnellen Programmzugriff", 0)
            _save_widget(window, result_paths[2])

            window.tabs.setCurrentIndex(0)
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
