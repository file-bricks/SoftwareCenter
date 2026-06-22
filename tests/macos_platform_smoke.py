import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import SoftwareCenter as module
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from SoftwareCenter import MainWindow, profile_export_data


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        settings_path = tmp / "softwarecenter-macos.ini"
        app_bundle = tmp / "Notizbücher.app"
        executable = app_bundle / "Contents" / "MacOS" / "Notizbücher"
        executable.parent.mkdir(parents=True)
        executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        with mock.patch.object(module.sys, "platform", "darwin"):
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
            window = MainWindow(settings=settings)
            try:
                page = window.current_page()
                require(page is not None, "MainWindow hat keine aktive Seite erzeugt.")

                page.add_paths([str(app_bundle)])
                require(page.list.count() == 1, ".app-Bundle wurde nicht importiert.")
                item = page.list.item(0)
                require(item.text() == "Notizbücher", "Bundle-Name wurde nicht aus dem Pfad abgeleitet.")
                require(
                    item.data(module.Qt.ItemDataRole.UserRole) == str(app_bundle),
                    "Bundle-Pfad wurde nicht gespeichert.",
                )

                window.set_current_view("list")
                exported = profile_export_data(window)
                require(exported["format"] == "softwarecenter-profile-v1", "Falsches Exportformat.")
                require(
                    exported["tabs"][0]["entries"][0]["kind"] == "mac_app",
                    ".app-Bundle wurde nicht als mac_app exportiert.",
                )

                with mock.patch.object(module.subprocess, "Popen") as popen:
                    module.open_file(str(app_bundle))
                popen.assert_called_once_with(["open", str(app_bundle)])

                window.save_settings()
                settings.sync()
            finally:
                window.close()

            reloaded = QSettings(str(settings_path), QSettings.Format.IniFormat)
            restored = MainWindow(settings=reloaded)
            try:
                page = restored.current_page()
                require(page is not None, "Reloaded MainWindow hat keine aktive Seite.")
                require(page.view_mode == "list", "Ansichtsmodus wurde nicht aus QSettings wiederhergestellt.")
                require(page.list.count() == 1, ".app-Bundle wurde nach Reload nicht wiederhergestellt.")
                item = page.list.item(0)
                require(item.text() == "Notizbücher", "Bundle-Name ging beim Reload verloren.")
                require(
                    item.data(module.Qt.ItemDataRole.UserRole) == str(app_bundle),
                    "Bundle-Pfad ging beim Reload verloren.",
                )
            finally:
                restored.close()

    print(
        "macOS-Plattform-Smoke erfolgreich: .app-Import, open-Start, "
        "QSettings und Profil-Export geprüft."
    )


if __name__ == "__main__":
    main()
