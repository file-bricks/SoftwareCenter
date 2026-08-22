"""Regressionstests für behobene Bugs in SoftwareCenter.

Bug A: QMessageBox.Yes statt QMessageBox.StandardButton.Yes — PySide6 6.4+ inkompatibel.
       on_request_delete (TabPage) und import_profile (MainWindow) verwendeten das
       veraltete Enum, sodass Bestätigungs-Dialoge in neueren PySide6-Versionen nicht
       korrekt ausgewertet wurden.

Batch #21 (2026-06-21):
  D2 — deprecated Qt-Enums (QListWidget.ExtendedSelection, ViewMode, ResizeMode, Qt.UserRole,
       Qt.CustomContextMenu)
  U2 — manage_translations.py json.load ohne JSONDecodeError-Handler
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


# ── Batch #21 D2: deprecated Qt-Enums ───────────────────────────────────────

class TestD2Batch21:
    """D2 — deprecated PySide6-Enums migriert (Batch #21)."""

    def _src(self):
        return Path(__file__).parent.parent.joinpath("SoftwareCenter.py").read_text(encoding="utf-8")

    def test_user_role_migrated(self):
        src = self._src()
        assert "Qt.ItemDataRole.UserRole" in src, "Qt.UserRole nicht migriert — BUG-D2"
        # Qt.UserRole ohne .ItemDataRole. darf nicht mehr vorkommen (außer als Teil von ItemDataRole)
        import re
        bare = re.findall(r'(?<!ItemDataRole\.)(?<!\w)Qt\.UserRole(?!\.)', src)
        assert not bare, f"Bare Qt.UserRole noch vorhanden: {bare} — BUG-D2"

    def test_selection_mode_migrated(self):
        src = self._src()
        assert "QAbstractItemView.SelectionMode.ExtendedSelection" in src, \
            "QListWidget.ExtendedSelection nicht migriert — BUG-D2"
        assert "QListWidget.ExtendedSelection" not in src, \
            "deprecated QListWidget.ExtendedSelection noch vorhanden — BUG-D2"

    def test_context_menu_policy_migrated(self):
        src = self._src()
        assert "Qt.ContextMenuPolicy.CustomContextMenu" in src, \
            "Qt.CustomContextMenu nicht migriert — BUG-D2"
        assert "Qt.CustomContextMenu\n" not in src and "Qt.CustomContextMenu)" not in src, \
            "deprecated Qt.CustomContextMenu noch vorhanden — BUG-D2"

    def test_view_mode_icon_migrated(self):
        src = self._src()
        assert "QListWidget.ViewMode.IconMode" in src, \
            "QListWidget.IconMode nicht migriert — BUG-D2"
        assert "QListWidget.IconMode" not in src.replace("QListWidget.ViewMode.IconMode", ""), \
            "deprecated QListWidget.IconMode noch vorhanden — BUG-D2"

    def test_view_mode_list_migrated(self):
        src = self._src()
        assert "QListWidget.ViewMode.ListMode" in src, \
            "QListWidget.ListMode nicht migriert — BUG-D2"
        assert "QListWidget.ListMode" not in src.replace("QListWidget.ViewMode.ListMode", ""), \
            "deprecated QListWidget.ListMode noch vorhanden — BUG-D2"

    def test_resize_mode_adjust_migrated(self):
        src = self._src()
        assert "QListWidget.ResizeMode.Adjust" in src, \
            "QListWidget.Adjust nicht migriert — BUG-D2"
        assert "QListWidget.Adjust" not in src.replace("QListWidget.ResizeMode.Adjust", ""), \
            "deprecated QListWidget.Adjust noch vorhanden — BUG-D2"

    def test_qabstractitemview_imported(self):
        src = self._src()
        assert "QAbstractItemView" in src, \
            "QAbstractItemView nicht importiert — für D2-Fix benötigt"


# ── Batch #21 U2: manage_translations ───────────────────────────────────────

class TestU2ManageTranslationsBatch21:
    """U2 — manage_translations.py json.load ohne JSONDecodeError-Handler (Batch #21)."""

    def _src(self):
        return Path(__file__).parent.parent.joinpath("manage_translations.py").read_text(encoding="utf-8")

    def test_json_load_has_json_decode_error_handler(self):
        src = self._src()
        assert "except json.JSONDecodeError" in src, \
            "manage_translations: json.load ohne JSONDecodeError-Handler — BUG-U2"

    def test_bare_json_load_wrapped(self):
        src = self._src()
        assert "JSONDecodeError" in src, \
            "manage_translations: JSONDecodeError-Handling fehlt — BUG-U2"


# ── BUGSWEEP-41: Non-string / None Path Guards ─────────────────────────────

class TestBugsweep41PathGuard:
    """BUGSWEEP-41: path helpers handle missing or malformed paths safely."""

    def test_detect_entry_kind_handles_none_and_non_string(self):
        from SoftwareCenter import detect_entry_kind
        assert detect_entry_kind(None) == "unknown"
        assert detect_entry_kind(123) == "unknown"
        assert detect_entry_kind("") == "unknown"

    def test_is_windows_shortcut_handles_none_and_non_string(self):
        from SoftwareCenter import is_windows_shortcut
        assert is_windows_shortcut(None) is False
        assert is_windows_shortcut(123) is False
        assert is_windows_shortcut("") is False

    def test_is_supported_launch_target_handles_none_and_non_string(self):
        from SoftwareCenter import is_supported_launch_target
        assert is_supported_launch_target(None) is False
        assert is_supported_launch_target(123) is False
        assert is_supported_launch_target("") is False

    def test_default_entry_label_handles_none_and_non_string(self):
        from SoftwareCenter import default_entry_label
        assert default_entry_label(None) == ""
        assert default_entry_label(123) == ""
        assert default_entry_label("") == ""

    def test_selected_entries_handles_items_without_userrole(self):
        from SoftwareCenter import SoftwareListWidget
        from PySide6.QtWidgets import QListWidgetItem
        widget = SoftwareListWidget()
        item = QListWidgetItem("Orphan Item")
        widget.addItem(item)
        widget.selectAll()
        assert widget._selected_entries() == []


# ── BUG R4: TabBar Orphan Close Buttons ────────────────────────────────────

class TestBugR4_TabBarOrphanCloseButtons:
    """R4 APP-BUG: _update_tab_closable_state hides orphan close buttons on QTabBar."""

    def test_update_tab_closable_state_hides_unassigned_buttons(self):
        from PySide6.QtWidgets import QPushButton
        tmp = Path(tempfile.mkdtemp())
        settings = QSettings(str(tmp / "test_r4.ini"), QSettings.Format.IniFormat)
        window = MainWindow(settings=settings)
        tab_bar = window.tabs.tabBar()

        # Simulate an orphan button child on QTabBar
        dummy = QPushButton("x", tab_bar)
        dummy.show()
        assert dummy.isHidden() is False

        window._update_tab_closable_state()
        assert dummy.isHidden() is True

