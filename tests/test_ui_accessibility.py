# -*- coding: utf-8 -*-
"""Tests für UX- und Barrierefreiheitsfunktionen (WCAG 2.1 AA / BITV 2.0).

Prüft:
- Tastaturbedienung in SoftwareListWidget (Entf, Backspace, F2, Strg+C)
- Formular-Zugänglichkeit und Mnemonic-Buddies in EditEntryDialog
- Barrierefreiheits-Attribute und Tooltips in BoardsPanel und Hauptleiste
- Tastaturkürzel- und Barrierefreiheits-Übersichtsdialog (F1)
"""
import os
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QTextEdit

import SoftwareCenter as sc
import pytest

_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)


@pytest.fixture(autouse=True)
def _ensure_german_locale():
    """Stellt sicher, dass fuer Barrierefreiheitstests die deutsche Sprache aktiv ist."""
    translator = sc.get_translator()
    prev = translator.get_language()
    translator.set_language("de")
    yield
    translator.set_language(prev)


def test_software_list_widget_accessibility_metadata():
    """Prüft accessibleName und accessibleDescription der Liste."""
    widget = sc.SoftwareListWidget()
    assert widget.accessibleName() == "Software- und Dokumentenliste"
    assert "Pfeiltasten" in widget.accessibleDescription()
    assert "F2" in widget.accessibleDescription()
    assert "Entf" in widget.accessibleDescription()


def test_software_list_widget_keyboard_delete(tmp_path):
    """Prüft, ob Entf und Backspace requestDelete mit den ausgewählten Pfaden auslösen."""
    f1 = tmp_path / "app1.exe"
    f2 = tmp_path / "app2.exe"
    f1.write_text("dummy", encoding="utf-8")
    f2.write_text("dummy", encoding="utf-8")

    widget = sc.SoftwareListWidget()
    widget.add_paths([str(f1), str(f2)])

    received_paths = []
    widget.requestDelete.connect(lambda paths: received_paths.extend(paths))

    # Nichts ausgewählt -> keine Löschung
    key_del = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Delete, Qt.KeyboardModifier.NoModifier)
    widget.keyPressEvent(key_del)
    assert received_paths == []

    # Erstes Element auswählen und Entf drücken
    widget.item(0).setSelected(True)
    widget.keyPressEvent(key_del)
    assert received_paths == [str(f1)]

    # Zweites Element mit Backspace löschen
    received_paths.clear()
    widget.item(0).setSelected(False)
    widget.item(1).setSelected(True)
    key_back = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Backspace, Qt.KeyboardModifier.NoModifier)
    widget.keyPressEvent(key_back)
    assert received_paths == [str(f2)]


def test_software_list_widget_keyboard_f2_edits_entry(tmp_path):
    """Prüft, ob F2 die Eintragsbearbeitung für das ausgewählte Element öffnet."""
    f1 = tmp_path / "app.exe"
    f1.write_text("dummy", encoding="utf-8")

    widget = sc.SoftwareListWidget()
    widget.add_paths([str(f1)])
    widget.item(0).setSelected(True)

    with patch.object(widget, "_edit_entry") as mock_edit:
        key_f2 = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F2, Qt.KeyboardModifier.NoModifier)
        widget.keyPressEvent(key_f2)
        mock_edit.assert_called_once_with(widget.item(0))


def test_software_list_widget_keyboard_copy_path_to_clipboard(tmp_path):
    """Prüft, ob Strg+C die Pfade der markierten Einträge in die Zwischenablage kopiert."""
    f1 = tmp_path / "app1.exe"
    f2 = tmp_path / "app2.exe"
    f1.write_text("dummy", encoding="utf-8")
    f2.write_text("dummy", encoding="utf-8")

    widget = sc.SoftwareListWidget()
    widget.add_paths([str(f1), str(f2)])

    widget.item(0).setSelected(True)
    widget.item(1).setSelected(True)

    clipboard = QApplication.clipboard()
    clipboard.clear()

    key_copy = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
    widget.keyPressEvent(key_copy)

    assert clipboard.text() == f"{f1}\n{f2}"


def test_edit_entry_dialog_accessibility_and_buddies():
    """Prüft Formular-Buddies, barrierefreie Namen und Tooltips im Bearbeitungsdialog."""
    entry = {"path": "C:/demo/tool.exe", "label": "Demo Tool", "notes": "Notiz"}
    dlg = sc.EditEntryDialog(entry)

    assert dlg.accessibleName() == "Eintrag bearbeiten"
    assert "Notizen des Eintrags" in dlg.accessibleDescription()

    # Felder prüfen
    assert dlg.lbl_path.accessibleName() == "Pfad oder Web-Adresse"
    assert dlg.lbl_path.toolTip() != ""
    assert dlg.edit_label.accessibleName() == "Bezeichnung"
    assert dlg.edit_label.toolTip() != ""
    assert dlg.edit_notes.accessibleName() == "Notiz"
    assert dlg.edit_notes.toolTip() != ""

    # Buddy-Verknüpfungen für Tastatur-Navigation (Alt+P, Alt+B, Alt+N) prüfen
    labels = dlg.findChildren(QLabel)
    buddy_targets = [lbl.buddy() for lbl in labels if lbl.buddy() is not None]
    assert dlg.lbl_path in buddy_targets
    assert dlg.edit_label in buddy_targets
    assert dlg.edit_notes in buddy_targets


def test_boards_panel_accessibility():
    """Prüft accessibleName und Beschreibungen im BoardsPanel."""
    win = sc.MainWindow()
    try:
        panel = win.boards_panel
        assert panel.view_tabs.accessibleName() == "Board-Katalog"
        assert panel.history_list.accessibleName() == "Zuletzt geschlossene und aktive Boards"
        assert panel.alpha_list.accessibleName() == "Alphabetische Board-Liste"
        assert panel.clear_history_btn.accessibleName() == "Verlauf leeren"
        assert panel.clear_history_btn.toolTip() != ""
    finally:
        win.close()


def test_toolbar_accessibility_and_shortcuts():
    """Prüft Shortcuts und barrierefreie Attribute der Schnellfilter- und Toolbar-Aktionen."""
    win = sc.MainWindow()
    try:
        assert win.search_edit.accessibleName() == "Schnellsuche"
        assert "Filtert" in win.search_edit.accessibleDescription()
        assert "Strg+F" in win.search_edit.toolTip()

        # Shortcuts prüfen
        assert win.act_new_tab.shortcut() == QKeySequence("Ctrl+T")
        assert "Strg+T" in win.act_new_tab.toolTip()

        assert win.act_toggle_boards_panel.shortcut() == QKeySequence("Ctrl+B")
        assert "Strg+B" in win.act_toggle_boards_panel.toolTip()

        assert win.act_quit.shortcut() == QKeySequence("Ctrl+Q")
        assert win.act_shortcuts.shortcut() == QKeySequence("F1")
    finally:
        win.close()


def test_shortcuts_dialog_content():
    """Prüft, ob der Tastaturkürzel-Dialog alle relevanten Aktionen aufführt."""
    win = sc.MainWindow()
    try:
        title, shortcuts = win.show_shortcuts_dialog()
        assert "Tastaturkürzel & Barrierefreiheit" in title
        shortcut_dict = dict(shortcuts)
        assert "Strg+F" in shortcut_dict
        assert "Strg+T" in shortcut_dict
        assert "Strg+B" in shortcut_dict
        assert "F1" in shortcut_dict
        assert "F2" in shortcut_dict
        assert "Entf / Backspace" in shortcut_dict
        assert "Strg+C" in shortcut_dict
    finally:
        win.close()
