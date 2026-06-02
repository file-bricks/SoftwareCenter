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
        settings_path = tmp / "softwarecenter-linux.ini"
        desktop_file = tmp / "org.example.toolbox.desktop"
        desktop_file.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Toolbox\n"
            "Name[de]=Werkzeugkasten\n"
            "Exec=/usr/bin/env printf toolbox %U\n",
            encoding="utf-8",
        )
        fallback_desktop_file = tmp / "org.example.viewer.desktop"
        fallback_desktop_file.write_text(
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Viewer\n",
            encoding="utf-8",
        )

        with mock.patch.object(module.sys, "platform", "linux"):
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
            window = MainWindow(settings=settings)
            try:
                page = window.current_page()
                require(page is not None, "MainWindow hat keine aktive Seite erzeugt.")

                page.add_paths([str(desktop_file)])
                require(page.list.count() == 1, "Desktop-Datei wurde nicht importiert.")
                item = page.list.item(0)
                require(item.text() == "Werkzeugkasten", "Lokalisierter Launcher-Name wurde nicht übernommen.")

                window.set_current_view("list")
                exported = profile_export_data(window)
                require(exported["format"] == "softwarecenter-profile-v1", "Falsches Exportformat.")
                require(
                    exported["tabs"][0]["entries"][0]["kind"] == "linux_desktop",
                    "Desktop-Eintrag wurde nicht als Linux-Launcher exportiert.",
                )

                with mock.patch.object(module.subprocess, "Popen") as popen:
                    module.open_file(str(desktop_file))
                popen.assert_called_once_with(["/usr/bin/env", "printf", "toolbox"])

                with mock.patch.object(module.subprocess, "Popen") as popen:
                    module.open_file(str(fallback_desktop_file))
                popen.assert_called_once_with(["xdg-open", str(fallback_desktop_file)])

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
                require(page.list.count() == 1, "Launcher wurde nach Reload nicht wiederhergestellt.")
                item = page.list.item(0)
                require(item.text() == "Werkzeugkasten", "Launcher-Name ging beim Reload verloren.")
                require(item.data(module.Qt.UserRole) == str(desktop_file), "Launcher-Pfad ging beim Reload verloren.")
            finally:
                restored.close()

    print(
        "Linux-Plattform-Smoke erfolgreich: .desktop-Import, Exec/Fallback, "
        "QSettings und Profil-Export geprüft."
    )


if __name__ == "__main__":
    main()
