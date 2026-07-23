# -*- coding: utf-8 -*-
"""Regressionstests fuer den Board-Lebenszyklus (Ticket T-20260721-01).

Finale Spezifikation (LG, 2026-07-23, AUFGABEN.txt "ENTSCHEIDUNG GETROFFEN"):
Jedes Board ist eine feste Identitaet. "Schliessen" entfernt es nur aus der
Tab-Leiste und setzt `closed_at`; Name, Eintraege, Reihenfolge, Ansicht und
Favorit bleiben erhalten. Endgueltiges Loeschen verlangt eine Bestaetigung
NUR bei Favoriten. Simple Mode zeigt nur den Verlauf und bietet "Verlauf
leeren" (loescht geschlossene Nicht-Favoriten, Favoriten ueberleben).

Deckt ab: schliessen -> Persistenz -> Neustart-Simulation -> reaktivieren
(gleiche Identitaet, kein Duplikat); endgueltiges Loeschen (Favorit mit
Bestaetigung, Nicht-Favorit ohne); Reihenfolge/Eintraege/Ansicht bleiben
erhalten; Migration alter QSettings-Daten (nur "tabs" ohne neue Felder);
Verlaufssortierung; Simple-Mode "Verlauf leeren" verschont Favoriten;
Persistenz der zuletzt gewaehlten Panel-Ansicht; gemeinsamer Kern fuer
SoftwareCenter UND LaunchBoards.
"""
import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import SoftwareCenter as sc
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QMessageBox

_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)


def _make_window(tmp_path, name="s.ini", profile=sc.PROFILE_SOFTWARECENTER):
    settings = QSettings(str(tmp_path / name), QSettings.Format.IniFormat)
    return sc.MainWindow(settings=settings, profile=profile)


def _tool(tmp_path, name="tool.bat"):
    f = tmp_path / name
    f.write_text("@echo off\n", encoding="utf-8")
    return str(f)


class TestCloseReactivateIdentity:
    def test_close_persists_then_reactivate_restores_same_identity(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tool = _tool(tmp_path)
            win.current_page().add_paths([tool])
            first_board_id = win.current_page().board_id

            win.add_new_tab("Zweites")
            win.on_close_tab(0)  # "Allgemein" schliessen, "Zweites" bleibt als letzter Tab aktiv
            assert win.tabs.count() == 1
            assert first_board_id in win.closed_boards
            win.save_settings()
            win.settings.sync()
        finally:
            win.close()

        # Neustart-Simulation: frisches MainWindow auf demselben QSettings-Pfad.
        reloaded = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
        win2 = sc.MainWindow(settings=reloaded)
        try:
            assert first_board_id in win2.closed_boards, "Geschlossenes Board ueberlebt Neustart nicht"
            assert win2.tabs.count() == 1

            win2.reactivate_board(first_board_id)

            assert first_board_id not in win2.closed_boards, "Reaktiviertes Board darf nicht mehr geschlossen sein"
            active_ids = [win2.tabs.widget(i).board_id for i in range(win2.tabs.count())]
            assert active_ids.count(first_board_id) == 1, "Reaktivierung darf kein Duplikat erzeugen"
            page = win2.current_page()
            assert page.board_id == first_board_id
            assert page.list.get_all_paths() == [tool]
        finally:
            win2.close()

    def test_reclosing_same_board_moves_to_top_without_duplicate(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("A")
            board_id = win.current_page().board_id
            idx = win.tabs.indexOf(win.current_page())
            win.on_close_tab(idx)

            win.reactivate_board(board_id)
            idx2 = win.tabs.indexOf(win.current_page())
            win.on_close_tab(idx2)

            snapshot = win.all_boards_snapshot()
            assert sum(1 for b in snapshot if b["id"] == board_id) == 1, \
                "Erneutes Schliessen desselben Boards darf kein Duplikat erzeugen"
            assert board_id in win.closed_boards
        finally:
            win.close()


class TestOrderEntriesViewPreserved:
    def test_close_and_reactivate_preserves_order_entries_and_view(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tool_a = _tool(tmp_path, "a.bat")
            tool_b = _tool(tmp_path, "b.bat")
            tool_c = _tool(tmp_path, "c.bat")
            page = win.current_page()
            page.add_paths([tool_a, tool_b, tool_c])
            page.set_view_mode("list")
            board_id = page.board_id
            expected_order = page.list.get_all_paths()

            win.add_new_tab("Zweites")
            win.on_close_tab(0)
            win.reactivate_board(board_id)

            restored = win.current_page()
            assert restored.board_id == board_id
            assert restored.list.get_all_paths() == expected_order
            assert restored.view_mode == "list"
        finally:
            win.close()


class TestPermanentDelete:
    def test_delete_non_favorite_closed_board_without_confirmation(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Wird geschlossen")
            page = win.current_page()
            board_id = page.board_id
            win.on_close_tab(win.tabs.indexOf(page))
            assert board_id in win.closed_boards

            with patch.object(QMessageBox, "question") as mock_question:
                win.request_delete_board(board_id)
            mock_question.assert_not_called()
            assert board_id not in win.closed_boards
            assert win._find_board(board_id) is None

        finally:
            win.close()

    def test_delete_favorite_requires_confirmation_and_cancel_keeps_it(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Favorit-Board")
            page = win.current_page()
            board_id = page.board_id
            win.on_close_tab(win.tabs.indexOf(page))
            win.toggle_board_favorite(board_id)
            assert board_id in win.favorites

            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q:
                win.request_delete_board(board_id)
            mock_q.assert_called_once()
            assert board_id in win.closed_boards, "Abbruch (No) darf das Board nicht loeschen"

            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as mock_q2:
                win.request_delete_board(board_id)
            mock_q2.assert_called_once()
            assert board_id not in win.closed_boards
            assert board_id not in win.favorites
        finally:
            win.close()

    def test_deleting_last_active_board_creates_fallback_board(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            board_id = win.current_page().board_id  # einziges Board ("Allgemein")
            with patch.object(QMessageBox, "question") as mock_q:
                win.request_delete_board(board_id)
            mock_q.assert_not_called()
            assert win.tabs.count() == 1, "Die App darf nie ohne aktives Board dastehen"
            assert win.current_page().board_id != board_id
        finally:
            win.close()


class TestMigrationLegacySettings:
    def test_legacy_tabs_without_new_fields_load_as_active_boards(self, tmp_path):
        settings_path = tmp_path / "legacy.ini"
        legacy = QSettings(str(settings_path), QSettings.Format.IniFormat)
        legacy.setValue("current_tab", 0)
        legacy.beginWriteArray("tabs")
        legacy.setArrayIndex(0)
        legacy.setValue("name", "Altbestand")
        legacy.setValue("view_mode", "list")
        legacy.setValue(
            "entries_json",
            '[{"path": "C:/Tools/Old.exe", "label": "Old", "kind": "file", "notes": null}]',
        )
        legacy.setValue("paths", ["C:/Tools/Old.exe"])
        legacy.endArray()
        legacy.sync()

        reloaded = QSettings(str(settings_path), QSettings.Format.IniFormat)
        win = sc.MainWindow(settings=reloaded)
        try:
            assert win.tabs.count() == 1
            page = win.current_page()
            assert page.view_mode == "list"
            assert page.list.get_all_paths() == ["C:/Tools/Old.exe"]
            assert page.board_id, "Migration muss eine neue, feste Board-Identitaet vergeben"
            assert win.closed_boards == {}, "Alte Datenstaende kennen keinen Verlauf -> leer, nicht fehlerhaft"
            assert win.favorites == set()
        finally:
            win.close()


class TestHistorySorting:
    def test_sort_boards_history_orders_closed_desc_then_active(self):
        boards = [
            {"id": "active-1", "name": "Aktiv", "closed_at": "", "favorite": False},
            {"id": "closed-old", "name": "Alt", "closed_at": "2026-07-20T10:00:00Z", "favorite": False},
            {"id": "closed-new", "name": "Neu", "closed_at": "2026-07-23T09:00:00Z", "favorite": False},
        ]
        ordered = sc.sort_boards_history(boards)
        assert [b["id"] for b in ordered] == ["closed-new", "closed-old", "active-1"]

    def test_sort_boards_alphabetical_is_case_insensitive(self):
        boards = [
            {"id": "1", "name": "zeta"},
            {"id": "2", "name": "Alpha"},
            {"id": "3", "name": "beta"},
        ]
        ordered = sc.sort_boards_alphabetical(boards)
        assert [b["id"] for b in ordered] == ["2", "3", "1"]


class TestFavoriteToggle:
    def test_toggle_board_favorite(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            board_id = win.current_page().board_id
            assert board_id not in win.favorites
            win.toggle_board_favorite(board_id)
            assert board_id in win.favorites
            win.toggle_board_favorite(board_id)
            assert board_id not in win.favorites
        finally:
            win.close()

    def test_favorite_persists_across_restart_for_active_and_closed_boards(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Aktiv-Favorit")
            active_fav_id = win.current_page().board_id
            win.toggle_board_favorite(active_fav_id)

            win.add_new_tab("Geschlossen-Favorit")
            page = win.current_page()
            closed_fav_id = page.board_id
            win.on_close_tab(win.tabs.indexOf(page))
            win.toggle_board_favorite(closed_fav_id)

            win.save_settings()
            win.settings.sync()
        finally:
            win.close()

        reloaded = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
        win2 = sc.MainWindow(settings=reloaded)
        try:
            assert active_fav_id in win2.favorites
            assert closed_fav_id in win2.favorites
        finally:
            win2.close()


class TestSimpleModeClearHistory:
    def test_clear_history_deletes_non_favorites_but_spares_favorites(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Fav")
            fav_page = win.current_page()
            fav_id = fav_page.board_id
            win.on_close_tab(win.tabs.indexOf(fav_page))
            win.toggle_board_favorite(fav_id)

            win.add_new_tab("NichtFav")
            other_page = win.current_page()
            other_id = other_page.board_id
            win.on_close_tab(win.tabs.indexOf(other_page))

            assert fav_id in win.closed_boards and other_id in win.closed_boards

            win.act_simple_mode.setChecked(True)
            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
                deleted = win.clear_board_history()

            assert deleted is True
            assert other_id not in win.closed_boards, "Nicht-Favorit muss durch 'Verlauf leeren' geloescht werden"
            assert fav_id in win.closed_boards, "Favorit muss 'Verlauf leeren' ueberleben"
        finally:
            win.close()

    def test_clear_history_confirmation_names_board_and_entry_count(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tool = _tool(tmp_path)
            win.add_new_tab("X")
            page = win.current_page()
            page.add_paths([tool])
            win.on_close_tab(win.tabs.indexOf(page))

            with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as mock_q:
                win.clear_board_history()
            _obj, _title, message = mock_q.call_args[0][:3]
            assert "1" in message  # 1 Board, 1 Eintrag
        finally:
            win.close()

    def test_clear_history_with_nothing_to_delete_does_not_prompt(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(QMessageBox, "question") as mock_q:
                deleted = win.clear_board_history()
            mock_q.assert_not_called()
            assert deleted is False
        finally:
            win.close()


class TestPanelViewPersistence:
    def test_default_panel_view_is_history(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            assert win._boards_panel_view == "history"
        finally:
            win.close()

    def test_last_chosen_panel_view_persists_across_restart(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win._set_boards_panel_view("alphabetical")
            win.save_settings()
            win.settings.sync()
        finally:
            win.close()

        reloaded = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
        win2 = sc.MainWindow(settings=reloaded)
        try:
            assert win2._boards_panel_view == "alphabetical"
        finally:
            win2.close()


class TestBoardsPanelUI:
    def test_hamburger_toggle_shows_and_hides_dock(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.show()
            assert win.boards_dock.isVisible() is False
            win.act_toggle_boards_panel.setChecked(True)
            assert win.boards_dock.isVisible() is True
            win.act_toggle_boards_panel.setChecked(False)
            assert win.boards_dock.isVisible() is False
        finally:
            win.close()

    def test_simple_mode_removes_alphabetical_tab_from_panel(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win._refresh_boards_panel()
            assert win.boards_panel.view_tabs.indexOf(win.boards_panel.alpha_list) != -1, \
                "Normal-Modus zeigt beide Reiter"

            win.act_simple_mode.setChecked(True)
            assert win.boards_panel.view_tabs.indexOf(win.boards_panel.alpha_list) == -1, \
                "Simple Mode darf keinen Alphabetisch-Reiter zeigen"
            assert win.boards_panel.view_tabs.count() == 1

            win.act_simple_mode.setChecked(False)
            assert win.boards_panel.view_tabs.indexOf(win.boards_panel.alpha_list) != -1, \
                "Zurueck im Normal-Modus muss der zweite Reiter wieder erscheinen"
        finally:
            win.close()

    def test_panel_snapshot_reflects_closed_and_favorite_state(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Board2")
            page = win.current_page()
            board_id = page.board_id
            win.on_close_tab(win.tabs.indexOf(page))
            win.toggle_board_favorite(board_id)

            win._refresh_boards_panel()
            entry = next(b for b in win.all_boards_snapshot() if b["id"] == board_id)
            assert entry["closed_at"] != ""
            assert entry["favorite"] is True
        finally:
            win.close()


class TestSharedAcrossProfiles:
    def test_board_lifecycle_works_for_launchboards_profile(self, tmp_path):
        win = _make_window(tmp_path, name="lb.ini", profile=sc.PROFILE_LAUNCHBOARDS)
        try:
            win.add_new_tab("LB-Board")
            page = win.current_page()
            board_id = page.board_id
            win.on_close_tab(win.tabs.indexOf(page))
            assert board_id in win.closed_boards

            win.reactivate_board(board_id)
            assert win.current_page().board_id == board_id
        finally:
            win.close()
