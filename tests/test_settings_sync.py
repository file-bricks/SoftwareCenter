import os
import tempfile
import unittest
import json
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import SoftwareCenter as module
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from SoftwareCenter import MainWindow


class SoftwareCenterSettingsSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._app = QApplication.instance() or QApplication([])
        cls._app.setQuitOnLastWindowClosed(False)

    def test_restores_active_tab_and_syncs_view_actions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

            first = MainWindow(settings=settings)
            try:
                self.assertEqual(first.tabs.count(), 1)
                self.assertFalse(first.tabs.tabsClosable())

                first.set_current_view("list")
                first.add_new_tab("Tools", "tiles")
                self.assertTrue(first.tabs.tabsClosable())
                first.tabs.setCurrentIndex(0)
                first.save_settings()
                settings.sync()
            finally:
                first.close()

            reloaded = QSettings(str(settings_path), QSettings.Format.IniFormat)
            second = MainWindow(settings=reloaded)
            try:
                self.assertEqual(second.tabs.count(), 2)
                self.assertTrue(second.tabs.tabsClosable())
                self.assertEqual(second.tabs.currentIndex(), 0)
                self.assertEqual(second.current_page().view_mode, "list")
                self.assertTrue(second.act_view_list.isChecked())
                self.assertFalse(second.act_view_tiles.isChecked())

                second.tabs.setCurrentIndex(1)
                self.assertTrue(second.act_view_tiles.isChecked())
                self.assertFalse(second.act_view_list.isChecked())
            finally:
                second.close()

    def test_legacy_settings_without_current_tab_default_to_first_tab(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

            first = MainWindow(settings=settings)
            try:
                first.set_current_view("list")
                first.add_new_tab("Tools", "tiles")
                first.tabs.setCurrentIndex(1)
                first.save_settings()
            finally:
                first.close()

            legacy = QSettings(str(settings_path), QSettings.Format.IniFormat)
            legacy.remove("current_tab")
            legacy.sync()

            reloaded = QSettings(str(settings_path), QSettings.Format.IniFormat)
            second = MainWindow(settings=reloaded)
            try:
                self.assertEqual(second.tabs.count(), 2)
                self.assertTrue(second.tabs.tabsClosable())
                self.assertEqual(second.tabs.currentIndex(), 0)
                self.assertEqual(second.current_page().view_mode, "list")
                self.assertTrue(second.act_view_list.isChecked())
                self.assertFalse(second.act_view_tiles.isChecked())
            finally:
                second.close()

    def test_last_remaining_tab_hides_close_button_again(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

            window = MainWindow(settings=settings)
            try:
                self.assertEqual(window.tabs.count(), 1)
                self.assertFalse(window.tabs.tabsClosable())

                window.add_new_tab("Tools", "tiles")
                self.assertEqual(window.tabs.count(), 2)
                self.assertTrue(window.tabs.tabsClosable())

                window.on_close_tab(1)

                self.assertEqual(window.tabs.count(), 1)
                self.assertFalse(window.tabs.tabsClosable())
            finally:
                window.close()

    def test_accepts_macos_app_bundles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_bundle = Path(tmpdir) / "Notizen.app"
            app_bundle.mkdir()
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

            with mock.patch.object(module.sys, "platform", "darwin"):
                window = MainWindow(settings=settings)
                try:
                    page = window.current_page()
                    self.assertIsNotNone(page)
                    page.add_paths([str(app_bundle)])

                    self.assertEqual(page.list.count(), 1)
                    item = page.list.item(0)
                    self.assertEqual(item.text(), "Notizen")
                    self.assertEqual(item.data(module.Qt.UserRole), str(app_bundle))
                finally:
                    window.close()

    def test_linux_desktop_entries_use_translated_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desktop_file = Path(tmpdir) / "org.example.editor.desktop"
            desktop_file.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Editor\n"
                "Name[de]=Texteditor\n"
                "Exec=/usr/bin/editor %U\n",
                encoding="utf-8",
            )
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)

            with mock.patch.object(module.sys, "platform", "linux"):
                window = MainWindow(settings=settings)
                try:
                    page = window.current_page()
                    self.assertIsNotNone(page)
                    page.add_paths([str(desktop_file)])

                    self.assertEqual(page.list.count(), 1)
                    item = page.list.item(0)
                    self.assertEqual(item.text(), "Texteditor")
                    self.assertEqual(item.data(module.Qt.UserRole), str(desktop_file))
                finally:
                    window.close()

    def test_linux_desktop_entries_launch_exec_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desktop_file = Path(tmpdir) / "org.example.editor.desktop"
            desktop_file.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Editor\n"
                "Exec=/usr/bin/editor --new-window %U\n",
                encoding="utf-8",
            )

            with mock.patch.object(module.sys, "platform", "linux"), \
                 mock.patch.object(module.subprocess, "Popen") as popen:
                module.open_file(str(desktop_file))

            popen.assert_called_once_with(["/usr/bin/editor", "--new-window"])

    def test_linux_desktop_entries_drop_embedded_field_code_arguments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            desktop_file = Path(tmpdir) / "org.example.editor.desktop"
            desktop_file.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=Editor\n"
                "Exec=/usr/bin/editor --mode=edit --open=%f --profile=%u --literal=%%f %U\n",
                encoding="utf-8",
            )

            with mock.patch.object(module.sys, "platform", "linux"), \
                 mock.patch.object(module.subprocess, "Popen") as popen:
                module.open_file(str(desktop_file))

            popen.assert_called_once_with(["/usr/bin/editor", "--mode=edit", "--literal=%f"])

    def test_add_paths_ignores_plain_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "NurEinOrdner"
            folder.mkdir()
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
            window = MainWindow(settings=settings)
            try:
                page = window.current_page()
                self.assertIsNotNone(page)
                page.add_paths([str(folder)])

                self.assertEqual(page.list.count(), 0)
            finally:
                window.close()

    def test_profile_export_contains_tab_entry_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            script_file = Path(tmpdir) / "Start Tool.bat"
            script_file.write_text("@echo off\n", encoding="utf-8")

            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
            window = MainWindow(settings=settings)
            try:
                page = window.current_page()
                self.assertIsNotNone(page)
                page.add_paths([str(script_file)])
                window.add_new_tab("Referenzen", "list", entries=[
                    {
                        "path": "Z:/Portable/Editor.exe",
                        "label": "Portable Editor",
                        "kind": "file",
                        "notes": "Auf Zweitrechner nachinstallieren",
                    }
                ])
                window.tabs.setCurrentIndex(1)

                exported = module.profile_export_data(window)

                self.assertEqual(exported["format"], "softwarecenter-profile-v1")
                self.assertEqual(exported["format_version"], 1)
                self.assertEqual(exported["current_tab"], 1)
                self.assertEqual(len(exported["tabs"]), 2)
                self.assertEqual(exported["tabs"][0]["entries"][0]["kind"], "script")
                self.assertEqual(exported["tabs"][1]["entries"][0]["label"], "Portable Editor")
                self.assertEqual(exported["tabs"][1]["entries"][0]["notes"], "Auf Zweitrechner nachinstallieren")
            finally:
                window.close()

    def test_profile_import_replaces_tabs_and_persists_entry_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
            payload = {
                "format": "softwarecenter-profile-v1",
                "format_version": 1,
                "app_version": "1.0.0",
                "source_platform": "win32",
                "exported_at": "2026-05-24T08:00:00Z",
                "current_tab": 1,
                "tabs": [
                    {
                        "name": "Werkzeuge",
                        "view_mode": "tiles",
                        "entries": [
                            {
                                "path": "C:/Tools/Analyzer.exe",
                                "label": "Analyzer",
                                "kind": "file",
                                "notes": None,
                            }
                        ],
                    },
                    {
                        "name": "Referenzen",
                        "view_mode": "list",
                        "entries": [
                            {
                                "path": "Z:/Portable/Editor.exe",
                                "label": "Portable Editor",
                                "kind": "file",
                                "notes": "Auf Zweitrechner nachinstallieren",
                            }
                        ],
                    },
                ],
            }

            first = MainWindow(settings=settings)
            try:
                first.apply_profile_payload(payload)
                self.assertEqual(first.tabs.count(), 2)
                self.assertEqual(first.tabs.currentIndex(), 1)
                imported_page = first.current_page()
                self.assertIsNotNone(imported_page)
                self.assertEqual(imported_page.view_mode, "list")
                imported_item = imported_page.list.item(0)
                self.assertEqual(imported_item.text(), "Portable Editor")
                self.assertIn("Auf Zweitrechner nachinstallieren", imported_item.toolTip())
                first.save_settings()
                settings.sync()
            finally:
                first.close()

            reloaded = QSettings(str(settings_path), QSettings.Format.IniFormat)
            second = MainWindow(settings=reloaded)
            try:
                self.assertEqual(second.tabs.count(), 2)
                self.assertEqual(second.tabs.currentIndex(), 1)
                imported_page = second.current_page()
                self.assertIsNotNone(imported_page)
                self.assertEqual(imported_page.list.item(0).text(), "Portable Editor")
                self.assertIn("Auf Zweitrechner nachinstallieren", imported_page.list.item(0).toolTip())

                second.settings.beginReadArray("tabs")
                second.settings.setArrayIndex(1)
                entries_json = second.settings.value("entries_json", "")
                second.settings.endArray()
                entries = json.loads(entries_json)
                self.assertEqual(entries[0]["label"], "Portable Editor")
                self.assertEqual(entries[0]["notes"], "Auf Zweitrechner nachinstallieren")
            finally:
                second.close()

    def test_profile_import_ignores_non_list_entries_container(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            settings_path = Path(tmpdir) / "softwarecenter.ini"
            settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
            payload = {
                "format": "softwarecenter-profile-v1",
                "format_version": 1,
                "tabs": [
                    {
                        "name": "Broken",
                        "view_mode": "tiles",
                        "entries": {
                            "path": "C:/Tools/App.exe",
                            "label": "Analyzer",
                        },
                    }
                ],
            }

            window = MainWindow(settings=settings)
            try:
                window.apply_profile_payload(payload)
                page = window.current_page()
                self.assertIsNotNone(page)
                self.assertEqual(page.list.count(), 0)
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
