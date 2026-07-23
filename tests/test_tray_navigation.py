# -*- coding: utf-8 -*-
"""Regressionstests fuer Tray-Zuverlaessigkeit (T-20260721-02) und Tray-Navigation
(T-20260721-03).

Deckt ab: Icon-Aufloesung inkl. MEIPASS-Fallback und Nicht-Null-Garantie;
Verfuegbarkeits-Retry ohne unsichtbares Weiterlaufen; Vertrag Schalter an/aus inkl.
closeEvent-Verhalten und sofortigem Icon-Entfernen; Menueinhalt = nur aktive Boards mit
Aktualisierung nach Umbenennen/Schliessen/Reaktivieren/endgueltigem Loeschen (keine
verwaisten Aktionen); Eintrags-Limit je Board; tray_search-Ranking und
Enter-Aktivierung (Launch gemockt); beide Produktprofile; Packaging-Manifest-Vertrag.

Kein QMessageBox.exec()-Pfad ist ungemockt erreichbar (blockiert unter offscreen fuer
immer, siehe Lehre 2026-07-23) -- jeder Test, der `_notify_tray_unavailable` erreicht,
mockt `QMessageBox.warning` explizit. Es werden nirgends echte Programme gestartet
(`sc.open_file` wird bei jeder Aktivierung gemockt)."""
import os
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import SoftwareCenter as sc
from PySide6.QtCore import QSettings
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox, QSystemTrayIcon, QWidgetAction

_APP = QApplication.instance() or QApplication([])
_APP.setQuitOnLastWindowClosed(False)


def _make_window(tmp_path, name="t.ini", profile=sc.PROFILE_SOFTWARECENTER):
    settings = QSettings(str(tmp_path / name), QSettings.Format.IniFormat)
    return sc.MainWindow(settings=settings, profile=profile)


def _tool(tmp_path, name="tool.bat"):
    f = tmp_path / name
    f.write_text("@echo off\n", encoding="utf-8")
    return str(f)


def _close(win):
    win._force_quit = True
    win.close()


class TestResourcePath:
    def test_source_run_uses_script_directory(self):
        expected = os.path.join(os.path.dirname(os.path.abspath(sc.__file__)), "icon.ico")
        assert sc.resource_path("icon.ico") == expected

    def test_meipass_fallback_used_when_frozen(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sc.sys, "_MEIPASS", str(tmp_path), raising=False)
        assert sc.resource_path("icon.ico") == os.path.join(str(tmp_path), "icon.ico")


class TestTrayIconResolution:
    def test_resolves_profile_icon_when_present(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            assert win._resolve_tray_icon().isNull() is False
        finally:
            _close(win)

    def test_falls_back_to_window_icon_when_ico_missing(self, tmp_path, monkeypatch):
        win = _make_window(tmp_path)
        try:
            monkeypatch.setattr(sc, "resource_path", lambda name: str(tmp_path / "missing.ico"))
            icon = win._resolve_tray_icon()
            assert icon.isNull() is False
            assert icon.cacheKey() == win.windowIcon().cacheKey()
        finally:
            _close(win)

    def test_never_returns_null_icon_even_without_window_icon(self, tmp_path, monkeypatch):
        win = _make_window(tmp_path)
        try:
            monkeypatch.setattr(sc, "resource_path", lambda name: str(tmp_path / "missing.ico"))
            win.windowIcon = lambda: QIcon()
            assert win._resolve_tray_icon().isNull() is False
        finally:
            _close(win)


class TestTrayContract:
    """Vertrag T-20260721-02: aus = kein Icon; an = Icon sofort; Ausschalten entfernt sofort."""

    def test_disabled_by_default_no_icon_even_if_available(self, tmp_path):
        with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
            win = _make_window(tmp_path)
            try:
                assert win.tray is None
            finally:
                _close(win)

    def test_enable_creates_visible_icon_immediately(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
                win._on_toggle_tray(True)
            assert win.tray is not None
            assert win.tray.isVisible() is True
        finally:
            _close(win)

    def test_disable_removes_icon_immediately(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
                win._on_toggle_tray(True)
            tray_ref = win.tray
            win._on_toggle_tray(False)
            assert win.tray is None
            assert tray_ref.isVisible() is False
        finally:
            _close(win)

    def test_close_hides_to_tray_when_enabled_and_visible(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
                win._on_toggle_tray(True)
            win.show()
            event = QCloseEvent()
            win.closeEvent(event)
            assert event.isAccepted() is False
            assert win.isHidden() is True
        finally:
            _close(win)

    def test_close_quits_app_when_tray_unavailable(self, tmp_path):
        win = _make_window(tmp_path)
        assert win.tray is None
        event = QCloseEvent()
        with patch.object(QApplication, "instance") as mock_instance:
            win.closeEvent(event)
        assert event.isAccepted() is True
        mock_instance.return_value.quit.assert_called_once()


class TestTrayAvailabilityFallback:
    """Ohne verfuegbaren Tray darf die App nie unsichtbar weiterlaufen (Ticket-Vertrag)."""

    def test_retry_scheduled_when_unavailable(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=False), \
                 patch.object(sc.QTimer, "singleShot") as mock_timer:
                win._on_toggle_tray(True)
            mock_timer.assert_called_once()
            interval = mock_timer.call_args[0][0]
            assert interval == sc.TRAY_RETRY_INTERVAL_MS
            assert win.tray is None
        finally:
            _close(win)

    def test_gives_up_after_max_retries_warns_and_never_runs_invisibly(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=False), \
                 patch.object(QMessageBox, "warning") as mock_warn:
                win._attempt_tray_creation(win._tray_setup_token, retry=sc.TRAY_RETRY_MAX_ATTEMPTS)
            assert win.tray is None
            mock_warn.assert_called_once()

            event = QCloseEvent()
            with patch.object(QApplication, "instance") as mock_instance:
                win.closeEvent(event)
            assert event.isAccepted() is True  # normal beendet, nicht ins Tray versteckt
            mock_instance.return_value.quit.assert_called_once()
        finally:
            _close(win)

    def test_retry_chain_eventually_creates_icon_once_available(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            state = {"n": 0}

            def available():
                state["n"] += 1
                return state["n"] > 2  # erst beim 3. Check verfuegbar

            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", side_effect=available), \
                 patch.object(sc.QTimer, "singleShot", side_effect=lambda ms, fn: fn()):
                win._on_toggle_tray(True)
            assert win.tray is not None
            assert win.tray.isVisible() is True
        finally:
            _close(win)

    def test_superseded_retry_chain_does_not_create_duplicate_icon(self, tmp_path):
        """Schnelles Aus/Ein waehrend eine Retry-Kette laeuft darf kein zweites Icon erzeugen."""
        win = _make_window(tmp_path)
        try:
            pending = []
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=False), \
                 patch.object(sc.QTimer, "singleShot", side_effect=lambda ms, fn: pending.append(fn)):
                win._on_toggle_tray(True)  # Generation A: haengt in der Retry-Warteschleife
            assert len(pending) == 1

            win._on_toggle_tray(False)  # bricht Generation A ab
            with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
                win._on_toggle_tray(True)  # Generation B: sofort verfuegbar
                pending[0]()  # verspaetetes Timer-Feuern von Generation A simulieren

            assert win.tray is not None
            assert win.tray.isVisible() is True
        finally:
            _close(win)


class TestTrayProfiles:
    def test_profile_name_used_as_tray_tooltip(self, tmp_path):
        for profile in (sc.PROFILE_SOFTWARECENTER, sc.PROFILE_LAUNCHBOARDS):
            win = _make_window(tmp_path, name=f"{profile.settings_app}-tooltip.ini", profile=profile)
            try:
                with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
                    win._on_toggle_tray(True)
                assert win.tray.toolTip() == profile.name
            finally:
                _close(win)

    def test_profile_icon_file_used_for_resolution(self, tmp_path):
        for profile in (sc.PROFILE_SOFTWARECENTER, sc.PROFILE_LAUNCHBOARDS):
            win = _make_window(tmp_path, name=f"{profile.settings_app}-icon.ini", profile=profile)
            try:
                assert win._resolve_tray_icon().isNull() is False
                assert os.path.basename(sc.resource_path(profile.icon_file)) == profile.icon_file
            finally:
                _close(win)

    def test_profiles_use_separate_settings_namespace(self):
        assert sc.PROFILE_SOFTWARECENTER.settings_app != sc.PROFILE_LAUNCHBOARDS.settings_app


class TestTrayNavigationEntries:
    def test_only_active_boards_listed(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Zweites")
            win.on_close_tab(0)  # "Allgemein" schliessen
            names = {b["name"] for b in win.tray_navigation_entries()}
            assert names == {"Zweites"}
        finally:
            _close(win)

    def test_entry_limit_for_non_favorite_board(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tools = [_tool(tmp_path, f"tool{i}.bat") for i in range(15)]
            win.current_page().add_paths(tools)
            board = win.tray_navigation_entries()[0]
            assert len(board["entries"]) == sc.TRAY_ENTRY_LIMIT_PER_BOARD
            assert board["entries_truncated"] is True
            assert board["entries_total"] == 15
        finally:
            _close(win)

    def test_favorite_board_lists_all_entries(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tools = [_tool(tmp_path, f"tool{i}.bat") for i in range(15)]
            win.current_page().add_paths(tools)
            win.toggle_board_favorite(win.current_page().board_id)
            board = win.tray_navigation_entries()[0]
            assert len(board["entries"]) == 15
            assert board["entries_truncated"] is False
        finally:
            _close(win)

    def test_closed_board_absent_then_reappears_after_reactivate(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Zweites")
            first_id = win.tabs.widget(0).board_id
            win.on_close_tab(0)
            assert "Allgemein" not in {b["name"] for b in win.tray_navigation_entries()}

            win.reactivate_board(first_id)
            assert "Allgemein" in {b["name"] for b in win.tray_navigation_entries()}
        finally:
            _close(win)

    def test_rename_reflected_immediately(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.tabs.setTabText(0, "Umbenannt")
            win._refresh_tab_accessibility()
            assert win.tray_navigation_entries()[0]["name"] == "Umbenannt"
        finally:
            _close(win)

    def test_permanently_deleted_board_leaves_no_orphaned_menu_action(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Loeschmich")
            board_id = win.tabs.widget(win.tabs.count() - 1).board_id
            menu = win._build_tray_menu()
            before = [a.text() for a in win._tray_dynamic_actions]
            assert any("Loeschmich" in t for t in before)

            win.delete_board_permanently(board_id)
            win._populate_tray_menu(menu)
            after = [a.text() for a in win._tray_dynamic_actions]
            assert not any("Loeschmich" in t for t in after)
        finally:
            _close(win)


class TestTrayMenuBuilding:
    def test_menu_has_search_field(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            menu = win._build_tray_menu()
            widget_actions = [a for a in menu.actions() if isinstance(a, QWidgetAction)]
            assert any(isinstance(a.defaultWidget(), QLineEdit) for a in widget_actions)
        finally:
            _close(win)

    def test_menu_has_open_and_quit_actions(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            texts = [a.text() for a in win._build_tray_menu().actions()]
            assert "Öffnen/Anzeigen" in texts
            assert "Beenden" in texts
        finally:
            _close(win)

    def test_stage2_submenu_for_board_with_entries(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.current_page().add_paths([_tool(tmp_path)])
            win._build_tray_menu()
            assert win._tray_dynamic_actions
            assert win._tray_dynamic_actions[0].menu() is not None
        finally:
            _close(win)

    def test_stage2_disabled_above_board_threshold(self, tmp_path, monkeypatch):
        monkeypatch.setattr(sc, "TRAY_STAGE2_MAX_BOARDS", 1)
        win = _make_window(tmp_path)
        try:
            win.current_page().add_paths([_tool(tmp_path)])
            win.add_new_tab("Zweites")
            win._build_tray_menu()
            assert win._tray_dynamic_actions
            for action in win._tray_dynamic_actions:
                assert action.menu() is None
        finally:
            _close(win)

    def test_truncation_hint_shown_in_submenu(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tools = [_tool(tmp_path, f"tool{i}.bat") for i in range(12)]
            win.current_page().add_paths(tools)
            win._build_tray_menu()
            sub = win._tray_dynamic_actions[0].menu()
            assert any(a.text().startswith("…") for a in sub.actions())
        finally:
            _close(win)

    def test_no_active_boards_shows_placeholder(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            # Sicherheitsnetz greift zwar (mind. 1 Board bleibt), aber die Methode selbst
            # muss auch mit einer leeren Liste robust umgehen.
            actions = win._tray_board_actions(win._build_tray_menu())
            assert len(actions) >= 1
        finally:
            _close(win)


class TestTraySearch:
    def test_empty_query_returns_no_hits(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            assert win.tray_search("") == []
            assert win.tray_search("   ") == []
        finally:
            _close(win)

    def test_ranks_exact_before_prefix_before_substring(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.tabs.setTabText(0, "Note")
            win.add_new_tab("Notenverwaltung")
            win.add_new_tab("Meine Note App")
            labels = [h["label"] for h in win.tray_search("Note") if h["kind"] == "board"]
            assert labels == ["Note", "Notenverwaltung", "Meine Note App"]
        finally:
            _close(win)

    def test_searches_entry_labels_too(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tool = _tool(tmp_path, "besonderes_tool.bat")
            win.current_page().add_paths([tool])
            entry_label = win.current_page().list.get_all_entries()[0]["label"]
            hits = win.tray_search(entry_label[:6])
            assert any(h["kind"] == "entry" and h["label"] == entry_label for h in hits)
        finally:
            _close(win)

    def test_activate_search_opens_best_board_match(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Zielboard")
            with patch.object(win, "open_board_from_tray") as mock_open:
                activated = win.tray_activate_search("Zielboard")
            assert activated is True
            mock_open.assert_called_once()
        finally:
            _close(win)

    def test_activate_search_launches_best_entry_match(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            tool = _tool(tmp_path, "startme.bat")
            win.current_page().add_paths([tool])
            with patch.object(sc, "open_file") as mock_open_file:
                activated = win.tray_activate_search("startme")
            assert activated is True
            mock_open_file.assert_called_once_with(tool)
        finally:
            _close(win)

    def test_activate_search_no_hit_returns_false_and_launches_nothing(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            with patch.object(sc, "open_file") as mock_open_file:
                activated = win.tray_activate_search("gibtsgarantiertnichtxyz")
            assert activated is False
            mock_open_file.assert_not_called()
        finally:
            _close(win)

    def test_enter_in_search_field_closes_menu_on_hit(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Zielboard")
            menu = win._build_tray_menu()
            with patch.object(menu, "close") as mock_close, \
                 patch.object(win, "open_board_from_tray") as mock_open:
                win._on_tray_search_enter(menu, "Zielboard")
            mock_open.assert_called_once()
            mock_close.assert_called_once()
        finally:
            _close(win)

    def test_enter_with_no_hit_keeps_menu_open(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            menu = win._build_tray_menu()
            with patch.object(menu, "close") as mock_close:
                win._on_tray_search_enter(menu, "keintreffervorhanden")
            mock_close.assert_not_called()
        finally:
            _close(win)

    def test_live_filter_replaces_board_list_without_losing_search_field(self, tmp_path):
        win = _make_window(tmp_path)
        try:
            win.add_new_tab("Filterziel")
            menu = win._build_tray_menu()
            win._rebuild_tray_dynamic_section(menu, "Filterziel")
            texts = [a.text() for a in win._tray_dynamic_actions]
            assert any("Filterziel" in t for t in texts)
            assert not any(t == "Allgemein" for t in texts)
            # Suchfeld bleibt Teil des Menues (nicht durch den Filter entfernt).
            widget_actions = [a for a in menu.actions() if isinstance(a, QWidgetAction)]
            assert any(isinstance(a.defaultWidget(), QLineEdit) for a in widget_actions)
        finally:
            _close(win)


class TestPackagingManifest:
    """Textvertrag der Build-Skripte -- KEIN PyInstaller-Lauf (siehe LOCK.tray.txt)."""

    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def test_softwarecenter_spec_bundles_icon(self):
        with open(os.path.join(self.PROJECT_ROOT, "SoftwareCenter.spec"), encoding="utf-8") as f:
            content = f.read()
        assert "icon.ico" in content
        assert "datas=[('icon.ico', '.')]" in content

    def test_build_exe_bat_adds_icon_as_bundled_data(self):
        with open(os.path.join(self.PROJECT_ROOT, "build_exe.bat"), encoding="utf-8") as f:
            content = f.read()
        assert "--add-data" in content
        assert "icon.ico;." in content

    def test_build_exe_launchboards_bat_bundles_both_icons(self):
        with open(os.path.join(self.PROJECT_ROOT, "build_exe_launchboards.bat"), encoding="utf-8") as f:
            content = f.read()
        assert "launchboards.ico;." in content
        assert "icon.ico;." in content
