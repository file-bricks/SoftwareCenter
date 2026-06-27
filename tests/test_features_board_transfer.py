"""Feature-Tests: Eintraege zwischen Boards (Tabs) verschieben / duplizieren.

User-Wunsch 2026-06-27:
  - Kontextmenue "Senden an" = Eintrag auf anderes Board verschieben (move).
  - Kontextmenue "Duplizieren auf" = Eintrag zusaetzlich auf weiterem Board zeigen (copy).

Getestet wird die reine Handler-Logik (ohne modales menu.exec()), analog zu den
bestehenden Regressionstests fuer on_request_delete.
"""

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from SoftwareCenter import MainWindow

_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)


def _make_window(tmpdir):
    settings = QSettings(str(Path(tmpdir) / "s.ini"), QSettings.Format.IniFormat)
    return MainWindow(settings=settings)


def _make_tool(tmpdir, name="tool.bat"):
    f = Path(tmpdir) / name
    f.write_text("@echo off\n", encoding="utf-8")
    return str(f)


class TestMoveToBoard:
    def test_move_removes_from_source_and_adds_to_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                tool = _make_tool(tmp)
                src = win.current_page()
                src.add_paths([tool])
                win.add_new_tab("Ziel")
                target_index = win.tabs.indexOf(win.current_page())
                target = win.current_page()
                assert src.list.count() == 1 and target.list.count() == 0

                entries = src.list.get_all_entries()
                win.move_entries_to_board(src, entries, target_index)

                assert src.list.count() == 0, "Quelle muss den Eintrag nach Move verlieren"
                assert target.list.count() == 1, "Ziel muss den Eintrag nach Move erhalten"
                assert target.list.get_all_paths() == [tool]
            finally:
                win.close()

    def test_move_to_same_board_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                tool = _make_tool(tmp)
                src = win.current_page()
                src.add_paths([tool])
                same_index = win.tabs.indexOf(src)
                win.move_entries_to_board(src, src.list.get_all_entries(), same_index)
                assert src.list.count() == 1, "Move auf dasselbe Board darf nichts loeschen"
            finally:
                win.close()

    def test_move_preserves_label_and_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                tool = _make_tool(tmp)
                src = win.current_page()
                src.list.add_entries([{"path": tool, "label": "Mein Tool", "notes": "Wichtig"}])
                win.add_new_tab("Ziel")
                target = win.current_page()
                target_index = win.tabs.indexOf(target)

                win.move_entries_to_board(src, src.list.get_all_entries(), target_index)

                moved = target.list.get_all_entries()
                assert len(moved) == 1
                assert moved[0]["label"] == "Mein Tool"
                assert moved[0]["notes"] == "Wichtig"
            finally:
                win.close()


class TestCopyToBoard:
    def test_copy_keeps_in_source_and_adds_to_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                tool = _make_tool(tmp)
                src = win.current_page()
                src.add_paths([tool])
                win.add_new_tab("Ziel")
                target = win.current_page()
                target_index = win.tabs.indexOf(target)

                win.copy_entries_to_board(src.list.get_all_entries(), target_index)

                assert src.list.count() == 1, "Quelle muss den Eintrag nach Copy behalten"
                assert target.list.count() == 1, "Ziel muss eine Kopie erhalten"
            finally:
                win.close()

    def test_copy_dedup_when_path_already_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                tool = _make_tool(tmp)
                src = win.current_page()
                src.add_paths([tool])
                win.add_new_tab("Ziel")
                target = win.current_page()
                target.add_paths([tool])
                target_index = win.tabs.indexOf(target)
                assert target.list.count() == 1

                win.copy_entries_to_board(src.list.get_all_entries(), target_index)
                assert target.list.count() == 1, "Bereits vorhandener Pfad darf nicht doppelt erscheinen"
            finally:
                win.close()


class TestBoardProvider:
    def test_provider_excludes_own_board(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                first = win.current_page()
                win.add_new_tab("Zweites")
                win.add_new_tab("Drittes")

                provider = first.list.board_provider
                assert callable(provider), "board_provider muss gesetzt sein"
                boards = provider()
                names = [name for _idx, name in boards]
                assert "Zweites" in names and "Drittes" in names
                # Das eigene Board darf nicht in der Liste auftauchen.
                own_index = win.tabs.indexOf(first)
                assert all(idx != own_index for idx, _name in boards)
            finally:
                win.close()


class TestSignalsExist:
    def test_widget_exposes_transfer_signals(self):
        with tempfile.TemporaryDirectory() as tmp:
            win = _make_window(tmp)
            try:
                lst = win.current_page().list
                assert hasattr(lst, "requestMoveToBoard")
                assert hasattr(lst, "requestCopyToBoard")
            finally:
                win.close()
