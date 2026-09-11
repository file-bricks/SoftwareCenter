# -*- coding: utf-8 -*-
"""Regressionstests fuer Bug-Sweep: QMenu.exec Delegation und Clipboard-Robustheit."""
import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication

import SoftwareCenter as sc

_APP = QApplication.instance() or QApplication([])


def test_context_menu_exec_delegates_to_class_mock(tmp_path: Path):
    f = tmp_path / "app.exe"
    f.write_text("dummy", encoding="utf-8")

    widget = sc.SoftwareListWidget()
    widget.add_paths([str(f)])
    item = widget.item(0)
    widget.setCurrentItem(item)

    mock_invocations = []

    def intercept_exec(menu_self, pos=None):
        mock_invocations.append(menu_self)
        return None

    with patch.object(sc.QMenu, "exec", side_effect=intercept_exec, autospec=True):
        widget._on_context_menu(QPoint(10, 10))

    assert len(mock_invocations) == 1


def test_context_menu_copy_path_null_clipboard_guarded(tmp_path: Path):
    f = tmp_path / "test.exe"
    f.write_text("dummy", encoding="utf-8")

    widget = sc.SoftwareListWidget()
    widget.add_paths([str(f)])
    item = widget.item(0)
    item.setSelected(True)

    def intercept_exec(menu_self, pos=None):
        for act in menu_self.actions():
            if act.text() == "Pfad kopieren":
                return act
        return None

    with patch.object(sc.QMenu, "exec", side_effect=intercept_exec, autospec=True), \
         patch.object(QApplication, "clipboard", return_value=None):
        widget._on_context_menu(QPoint(5, 5))
