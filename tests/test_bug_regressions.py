"""Regressionstests für behobene Bugs in SoftwareCenter.

Bug A: QMessageBox.Yes statt QMessageBox.StandardButton.Yes — PySide6 6.4+ inkompatibel.
       on_request_delete (TabPage) und import_profile (MainWindow) verwendeten das
       veraltete Enum, sodass Bestätigungs-Dialoge in neueren PySide6-Versionen nicht
       korrekt ausgewertet wurden.
"""

import inspect
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import SoftwareCenter as module
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox
from SoftwareCenter import TabPage, MainWindow

_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)


class TestBugA_QMessageBoxStandardButton:
    """Bug A: QMessageBox.Yes → QMessageBox.StandardButton.Yes"""

    def test_on_request_delete_uses_standard_button_yes(self):
        """on_request_delete darf nicht QMessageBox.Yes verwenden."""
        source = inspect.getsource(TabPage.on_request_delete)
        assert "QMessageBox.StandardButton.Yes" in source, (
            "on_request_delete verwendet QMessageBox.Yes statt "
            "QMessageBox.StandardButton.Yes (Bug A nicht behoben)"
        )
        assert "QMessageBox.Yes" not in source.replace(
            "QMessageBox.StandardButton.Yes", ""
        ), "QMessageBox.Yes (altes Enum) noch vorhanden in on_request_delete (Bug A)"

    def test_import_profile_uses_standard_button_yes(self):
        """import_profile darf nicht QMessageBox.Yes verwenden."""
        source = inspect.getsource(MainWindow.import_profile)
        assert "QMessageBox.StandardButton.Yes" in source, (
            "import_profile verwendet QMessageBox.Yes statt "
            "QMessageBox.StandardButton.Yes (Bug A nicht behoben)"
        )
        assert "QMessageBox.Yes" not in source.replace(
            "QMessageBox.StandardButton.Yes", ""
        ), "QMessageBox.Yes (altes Enum) noch vorhanden in import_profile (Bug A)"

    def test_on_request_delete_respects_yes_confirmation(self):
        """on_request_delete entfernt Einträge wenn StandardButton.Yes zurückgegeben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "tool.bat"
            f.write_text("@echo off\n", encoding="utf-8")
            settings = QSettings(str(Path(tmpdir) / "s.ini"), QSettings.Format.IniFormat)
            win = MainWindow(settings=settings)
            try:
                page = win.current_page()
                page.add_paths([str(f)])
                assert page.list.count() == 1
                with patch.object(QMessageBox, "question",
                                  return_value=QMessageBox.StandardButton.Yes):
                    page.on_request_delete([str(f)])
                assert page.list.count() == 0, (
                    "Eintrag wurde nicht gelöscht obwohl StandardButton.Yes zurückgegeben (Bug A)"
                )
            finally:
                win.close()

    def test_on_request_delete_respects_no_cancellation(self):
        """on_request_delete behält Einträge wenn StandardButton.No zurückgegeben wird."""
        with tempfile.TemporaryDirectory() as tmpdir:
            f = Path(tmpdir) / "tool.bat"
            f.write_text("@echo off\n", encoding="utf-8")
            settings = QSettings(str(Path(tmpdir) / "s.ini"), QSettings.Format.IniFormat)
            win = MainWindow(settings=settings)
            try:
                page = win.current_page()
                page.add_paths([str(f)])
                assert page.list.count() == 1
                with patch.object(QMessageBox, "question",
                                  return_value=QMessageBox.StandardButton.No):
                    page.on_request_delete([str(f)])
                assert page.list.count() == 1, (
                    "Eintrag wurde gelöscht obwohl Abbruch (No) gewählt wurde (Bug A)"
                )
            finally:
                win.close()
