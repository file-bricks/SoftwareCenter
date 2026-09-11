# -*- coding: utf-8 -*-
"""Tests fuer Dateimanager-Aktionen, Notiz-/Eintragsbearbeitung und Sortierung.

ROADMAP / AUFGABEN:
- Kontextmenue: "Im Explorer anzeigen" (bzw. Finder/Dateimanager)
- Kontextmenue: "Pfad kopieren"
- Kontextmenue: "Eintrag bearbeiten..." (Bezeichnung & Notizen)
- Kontextmenue: "Alphabetisch sortieren (A-Z)"
- Signal-Kette: entriesChanged -> persistente Speicherung
"""
import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPoint, QSettings
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

import SoftwareCenter as sc

_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)


def _make_dummy_file(tmp_path: Path, name: str = "app.exe") -> str:
    f = tmp_path / name
    f.write_text("dummy", encoding="utf-8")
    return str(f)


class TestFileManagerIntegration:
    """Prueft die plattformspezifische Dateimanager-Integration."""

    def test_get_file_manager_action_title(self):
        with patch("sys.platform", "win32"):
            assert sc.get_file_manager_action_title() == "Im Explorer anzeigen"
        with patch("sys.platform", "darwin"):
            assert sc.get_file_manager_action_title() == "Im Finder anzeigen"
        with patch("sys.platform", "linux"):
            assert sc.get_file_manager_action_title() == "Im Dateimanager anzeigen"

    def test_show_in_file_manager_missing_file_shows_warning(self):
        with patch.object(QMessageBox, "warning") as mock_warn:
            sc.show_in_file_manager("C:/gibts/nicht/wirklich.exe")
            mock_warn.assert_called_once()
            assert "Datei nicht gefunden" in mock_warn.call_args[0][1]

    def test_show_in_file_manager_file_windows(self, tmp_path):
        f = _make_dummy_file(tmp_path, "test.exe")
        with patch("sys.platform", "win32"), patch("subprocess.Popen") as mock_popen:
            sc.show_in_file_manager(f)
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args[0][0]
            assert cmd[0] == "explorer"
            assert cmd[1].startswith("/select,")
            assert os.path.normpath(f) in cmd[1]

    def test_show_in_file_manager_dir_windows(self, tmp_path):
        d = str(tmp_path)
        with patch("sys.platform", "win32"), patch("subprocess.Popen") as mock_popen:
            sc.show_in_file_manager(d)
            mock_popen.assert_called_once()
            cmd = mock_popen.call_args[0][0]
            assert cmd == ["explorer", os.path.normpath(d)]

    def test_show_in_file_manager_darwin(self, tmp_path):
        f = _make_dummy_file(tmp_path, "test.app")
        with patch("sys.platform", "darwin"), patch("subprocess.Popen") as mock_popen:
            sc.show_in_file_manager(f)
            mock_popen.assert_called_once()
            assert mock_popen.call_args[0][0] == ["open", "-R", os.path.normpath(f)]

    def test_show_in_file_manager_linux(self, tmp_path):
        f = _make_dummy_file(tmp_path, "test.desktop")
        with patch("sys.platform", "linux"), patch("subprocess.Popen") as mock_popen:
            sc.show_in_file_manager(f)
            mock_popen.assert_called_once()
            assert mock_popen.call_args[0][0] == ["xdg-open", os.path.normpath(str(tmp_path))]


class TestEditEntryDialog:
    """Prueft den Dialog zur Bearbeitung von Bezeichnung und Notizen."""

    def test_dialog_loads_and_updates_data(self):
        entry = {
            "path": "C:/app.exe",
            "label": "Alte Bezeichnung",
            "notes": "Bestehende Notiz",
        }
        dlg = sc.EditEntryDialog(entry)
        assert dlg.lbl_path.text() == "C:/app.exe"
        assert dlg.edit_label.text() == "Alte Bezeichnung"
        assert dlg.edit_notes.toPlainText() == "Bestehende Notiz"

        dlg.edit_label.setText("Neue Bezeichnung")
        dlg.edit_notes.setPlainText("Aktualisierte Notiz")
        lbl, notes = dlg.get_data()
        assert lbl == "Neue Bezeichnung"
        assert notes == "Aktualisierte Notiz"

    def test_dialog_empty_notes_returns_none(self):
        entry = {"path": "C:/app.exe", "label": "Test", "notes": "Vorhanden"}
        dlg = sc.EditEntryDialog(entry)
        dlg.edit_notes.setPlainText("   ")
        _lbl, notes = dlg.get_data()
        assert notes is None


class TestSoftwareListWidgetEnhancements:
    """Prueft Sortierung, Notizen-Bearbeitung, Kontextmenue und Signale in SoftwareListWidget."""

    def test_sort_entries_alphabetical(self, tmp_path):
        f1 = _make_dummy_file(tmp_path, "zebra.exe")
        f2 = _make_dummy_file(tmp_path, "alpha.exe")
        f3 = _make_dummy_file(tmp_path, "beta.exe")

        widget = sc.SoftwareListWidget()
        signal_spy = []
        widget.entriesChanged.connect(lambda: signal_spy.append(True))

        widget.add_paths([f1, f2, f3])
        # Zuruecksetzen nach Hinzufuegen
        signal_spy.clear()

        # Vor Sortierung
        labels_before = [widget.item(i).text().lower() for i in range(widget.count())]
        assert labels_before == ["zebra", "alpha", "beta"]

        # Alphabetisch sortieren
        widget.sort_entries(ascending=True)

        labels_after = [widget.item(i).text().lower() for i in range(widget.count())]
        assert labels_after == ["alpha", "beta", "zebra"]
        assert len(signal_spy) == 1

    def test_edit_entry_updates_item_and_tooltip(self, tmp_path):
        f = _make_dummy_file(tmp_path, "app.exe")
        widget = sc.SoftwareListWidget()
        signal_spy = []
        widget.entriesChanged.connect(lambda: signal_spy.append(True))

        widget.add_paths([f])
        signal_spy.clear()
        item = widget.item(0)

        # Simuliere Dialog-Bestaetigung mit neuer Bezeichnung und Notiz
        with patch.object(sc.EditEntryDialog, "exec", return_value=QDialog.DialogCode.Accepted),              patch.object(sc.EditEntryDialog, "get_data", return_value=("Super Tool", "Wichtige Notiz")):
            widget._edit_entry(item)

        assert item.text() == "Super Tool"
        assert "Notizen: Wichtige Notiz" in item.toolTip()
        metadata = item.data(sc.ENTRY_METADATA_ROLE)
        assert metadata["label"] == "Super Tool"
        assert metadata["notes"] == "Wichtige Notiz"
        assert len(signal_spy) == 1

    def test_context_menu_contains_all_actions(self, tmp_path):
        f = _make_dummy_file(tmp_path, "app.exe")
        widget = sc.SoftwareListWidget()
        widget.add_paths([f])

        item = widget.item(0)
        widget.setCurrentItem(item)

        created_actions = []

        def intercept_exec(menu_self, pos=None):
            for act in menu_self.actions():
                if act.isSeparator():
                    continue
                created_actions.append(act.text())
            return None

        with patch.object(sc.SoftwareListWidget, "_exec_context_menu", side_effect=intercept_exec):
            widget._on_context_menu(QPoint(10, 10))

        assert "Öffnen/Starten" in created_actions
        assert sc.get_file_manager_action_title() in created_actions
        assert "Pfad kopieren" in created_actions
        assert "Eintrag bearbeiten..." in created_actions
        assert "Alphabetisch sortieren (A-Z)" in created_actions
        assert "Löschen" in created_actions

    def test_copy_path_to_clipboard(self, tmp_path):
        f = _make_dummy_file(tmp_path, "app.exe")
        widget = sc.SoftwareListWidget()
        widget.add_paths([f])

        item = widget.item(0)
        item.setSelected(True)

        clipboard = QApplication.clipboard()
        clipboard.clear()

        def intercept_exec(menu_self, pos=None):
            for act in menu_self.actions():
                if act.text() == "Pfad kopieren":
                    return act
            return None

        with patch.object(sc.SoftwareListWidget, "_exec_context_menu", side_effect=intercept_exec):
            widget._on_context_menu(QPoint(5, 5))

        assert clipboard.text() == f


class TestSettingsPersistenceIntegration:
    """Prueft, ob Aenderungen via entriesChanged direkt in QSettings gespeichert werden."""

    def test_sort_and_edit_persisted_to_settings(self, tmp_path):
        settings_file = tmp_path / "settings.ini"
        settings = QSettings(str(settings_file), QSettings.Format.IniFormat)

        f1 = _make_dummy_file(tmp_path, "z_app.bat")
        f2 = _make_dummy_file(tmp_path, "a_app.bat")

        win = sc.MainWindow(settings=settings)
        try:
            page = win.current_page()
            page.add_paths([f1, f2])
            win.save_settings()

            # Sortieren
            page.list.sort_entries(ascending=True)

            # Zweites MainWindow laden zur Pruefung der Persistenz
            settings2 = QSettings(str(settings_file), QSettings.Format.IniFormat)
            win2 = sc.MainWindow(settings=settings2)
            try:
                page2 = win2.current_page()
                labels = [page2.list.item(i).text() for i in range(page2.list.count())]
                assert labels == ["a_app", "z_app"]
            finally:
                win2.close()
        finally:
            win.close()
