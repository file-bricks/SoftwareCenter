# -*- coding: utf-8 -*-
"""Tests für SoftwareListWidgetDelegate (Listenansicht mit Notiz/Pfad & Fehlend-Indikator).

AUFGABEN.txt: Task R7 (Listenansicht horizontal füllen)
ROADMAP.md: Robustes Verhalten bei fehlenden Zielen
"""

import os
from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
        QApplication,
        QStyleOptionViewItem,
)

import SoftwareCenter as sc

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_APP = QApplication.instance() or QApplication([])


def _make_dummy_file(tmp_path: Path, name: str = "tool.exe") -> str:
        f = tmp_path / name
        f.write_text("dummy", encoding="utf-8")
        return str(f)


class TestSoftwareListItemDelegate:
        """Testet das Verhalten von SoftwareListItemDelegate in List- und Icon-Mode."""

        def test_delegate_attached_to_widget(self):
            widget = sc.SoftwareListWidget()
            delegate = widget.itemDelegate()
            assert isinstance(delegate, sc.SoftwareListItemDelegate)

        def test_delegate_size_hint_list_mode(self, tmp_path):
            f = _make_dummy_file(tmp_path, "tool.exe")
            widget = sc.SoftwareListWidget()
            widget.configure_as_list()
            widget.add_paths([f])

            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)
            opt = QStyleOptionViewItem()
            opt.widget = widget
            opt.rect = QRect(0, 0, 500, 32)

            size = delegate.sizeHint(opt, index)
            assert size.height() == 32
            assert size.width() == 500

        def test_delegate_size_hint_icon_mode(self, tmp_path):
            f = _make_dummy_file(tmp_path, "tool.exe")
            widget = sc.SoftwareListWidget()
            widget.configure_as_tiles()
            widget.add_paths([f])

            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)
            opt = QStyleOptionViewItem()
            opt.widget = widget

            size = delegate.sizeHint(opt, index)
            assert isinstance(size, QSize)

        def test_delegate_paint_list_mode_with_notes(self, tmp_path):
            f = _make_dummy_file(tmp_path, "calc.exe")
            widget = sc.SoftwareListWidget()
            widget.configure_as_list()
            widget.add_entries([{"path": f, "label": "Rechner", "notes": "Wichtiger Rechner"}])

            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)

            pixmap = QPixmap(800, 32)
            painter = QPainter(pixmap)
            try:
                opt = QStyleOptionViewItem()
                opt.widget = widget
                opt.rect = QRect(0, 0, 800, 32)
                opt.font = QFont()
                opt.palette = widget.palette()
                delegate.paint(painter, opt, index)
            finally:
                painter.end()

            assert widget.item(0).text() == "Rechner"
            assert widget.item(0).data(sc.ENTRY_METADATA_ROLE)["notes"] == "Wichtiger Rechner"

        def test_delegate_paint_list_mode_without_notes_shows_path(self, tmp_path):
            f = _make_dummy_file(tmp_path, "viewer.exe")
            widget = sc.SoftwareListWidget()
            widget.configure_as_list()
            widget.add_paths([f])

            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)

            pixmap = QPixmap(600, 32)
            painter = QPainter(pixmap)
            try:
                opt = QStyleOptionViewItem()
                opt.widget = widget
                opt.rect = QRect(0, 0, 600, 32)
                opt.font = QFont()
                opt.palette = widget.palette()
                delegate.paint(painter, opt, index)
            finally:
                painter.end()

            assert widget.item(0).text() == "viewer"
            assert widget.item(0).data(sc.ENTRY_METADATA_ROLE)["notes"] is None

        def test_delegate_paint_list_mode_missing_target(self):
            missing_path = "C:/nicht_vorhanden/verschollen.exe"
            widget = sc.SoftwareListWidget()
            widget.configure_as_list()
            widget.add_entries([{"path": missing_path, "label": "Verschollen"}])

            assert widget.count() == 1
            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)

            pixmap = QPixmap(700, 32)
            painter = QPainter(pixmap)
            try:
                opt = QStyleOptionViewItem()
                opt.widget = widget
                opt.rect = QRect(0, 0, 700, 32)
                opt.font = QFont()
                opt.palette = widget.palette()
                delegate.paint(painter, opt, index)
            finally:
                painter.end()

            assert widget.item(0).text() == "Verschollen"
            assert widget.item(0).data(Qt.ItemDataRole.UserRole) == missing_path

        def test_delegate_paint_selected_state(self, tmp_path):
            f = _make_dummy_file(tmp_path, "app.exe")
            widget = sc.SoftwareListWidget()
            widget.configure_as_list()
            widget.add_paths([f])

            item = widget.item(0)
            item.setSelected(True)

            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)

            pixmap = QPixmap(600, 32)
            painter = QPainter(pixmap)
            try:
                opt = QStyleOptionViewItem()
                opt.widget = widget
                opt.rect = QRect(0, 0, 600, 32)
                opt.font = QFont()
                opt.palette = widget.palette()
                opt.state = opt.state | widget.style().StateFlag.State_Selected
                delegate.paint(painter, opt, index)
            finally:
                painter.end()

        def test_delegate_paint_icon_mode_passthrough(self, tmp_path):
            f = _make_dummy_file(tmp_path, "app.exe")
            widget = sc.SoftwareListWidget()
            widget.configure_as_tiles()
            widget.add_paths([f])

            delegate = widget.itemDelegate()
            index = widget.model().index(0, 0)

            pixmap = QPixmap(100, 100)
            painter = QPainter(pixmap)
            try:
                opt = QStyleOptionViewItem()
                opt.widget = widget
                opt.rect = QRect(0, 0, 100, 100)
                opt.font = QFont()
                opt.palette = widget.palette()
                delegate.paint(painter, opt, index)
            finally:
                painter.end()
