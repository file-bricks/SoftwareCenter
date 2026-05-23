import os
import tempfile
import unittest
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

                first.set_current_view("list")
                first.add_new_tab("Tools", "tiles")
                first.tabs.setCurrentIndex(0)
                first.save_settings()
                settings.sync()
            finally:
                first.close()

            reloaded = QSettings(str(settings_path), QSettings.Format.IniFormat)
            second = MainWindow(settings=reloaded)
            try:
                self.assertEqual(second.tabs.count(), 2)
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
                self.assertEqual(second.tabs.currentIndex(), 0)
                self.assertEqual(second.current_page().view_mode, "list")
                self.assertTrue(second.act_view_list.isChecked())
                self.assertFalse(second.act_view_tiles.isChecked())
            finally:
                second.close()

    def test_accepts_macos_app_bundles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app_bundle = Path(tmpdir) / "Notizen.app"
            app_bundle.mkdir()

            with mock.patch.object(module.sys, "platform", "darwin"):
                window = MainWindow()
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


if __name__ == "__main__":
    unittest.main()
