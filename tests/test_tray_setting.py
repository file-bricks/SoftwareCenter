# -*- coding: utf-8 -*-
"""Systemtray-Einstellung: an/aus wird in QSettings gespeichert und gelesen."""
import os
import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import SoftwareCenter as sc  # noqa: E402

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_app = QApplication.instance() or QApplication([])


def _window(tmp_path):
    s = QSettings(str(tmp_path / "tray.ini"), QSettings.Format.IniFormat)
    return sc.MainWindow(settings=s)


def test_tray_default_off(tmp_path):
    w = _window(tmp_path)
    assert w._tray_enabled() is False


def test_tray_toggle_persists(tmp_path):
    w = _window(tmp_path)
    w._on_toggle_tray(True)
    assert w._tray_enabled() is True
    w._on_toggle_tray(False)
    assert w._tray_enabled() is False


def test_tray_setting_read_from_existing(tmp_path):
    s = QSettings(str(tmp_path / "pre.ini"), QSettings.Format.IniFormat)
    s.setValue("minimize_to_tray", True)
    s.sync()
    w = sc.MainWindow(settings=s)
    assert w._tray_enabled() is True
    # Menü-Häkchen spiegelt die gespeicherte Einstellung
    assert w.act_minimize_to_tray.isChecked() is True
