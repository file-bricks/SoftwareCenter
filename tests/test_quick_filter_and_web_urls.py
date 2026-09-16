"""Tests für Schnellsuche/Live-Filter (Strg+F), Web-URL-Unterstützung und Board-Duplikation."""

from unittest.mock import MagicMock, patch

from PySide6.QtCore import QMimeData, QSettings, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication

from SoftwareCenter import (
    MainWindow,
    SoftwareListWidget,
    default_entry_label,
    detect_entry_kind,
    get_file_manager_action_title,
    is_supported_launch_target,
    is_web_url,
    open_file,
    show_in_file_manager,
)


def _get_qapp():
    return QApplication.instance() or QApplication([])


class TestWebUrlSupport:
    def test_is_web_url(self):
        assert is_web_url("https://github.com") is True
        assert is_web_url("http://example.com/page") is True
        assert is_web_url("HTTPS://SECURE.SITE.ORG") is True
        assert is_web_url("ftp://example.com") is False
        assert is_web_url("C:\\Windows\\notepad.exe") is False
        assert is_web_url("") is False
        assert is_web_url(None) is False  # type: ignore[arg-type]

    def test_is_supported_launch_target_for_urls(self):
        assert is_supported_launch_target("https://www.python.org") is True
        assert is_supported_launch_target("http://localhost:3000/app") is True

    def test_default_entry_label_for_urls(self):
        assert default_entry_label("https://github.com/user/repo/") == "github.com/user/repo"
        assert default_entry_label("http://example.com") == "example.com"

    def test_detect_entry_kind_for_urls(self):
        assert detect_entry_kind("https://example.com") == "url"
        assert detect_entry_kind("http://intranet/portal") == "url"

    def test_get_file_manager_action_title_for_urls(self):
        title = get_file_manager_action_title("https://example.com")
        from SoftwareCenter import t
        assert title == t("Im Browser öffnen")

    def test_open_file_launches_url(self):
        with patch("SoftwareCenter.QDesktopServices.openUrl") as mock_open_url:
            mock_open_url.return_value = True
            open_file("https://example.com/test")
            mock_open_url.assert_called_once()
            called_url = mock_open_url.call_args[0][0]
            assert isinstance(called_url, QUrl)
            assert called_url.toString() == "https://example.com/test"

    def test_show_in_file_manager_delegates_to_open_file_for_urls(self):
        with patch("SoftwareCenter.open_file") as mock_open:
            show_in_file_manager("https://example.com/page")
            mock_open.assert_called_once_with("https://example.com/page")


class TestSoftwareListWidgetFilterAndDrop:
    def test_filter_entries(self):
        _app = _get_qapp()
        widget = SoftwareListWidget()
        entries = [
            {"path": "https://github.com", "label": "GitHub Portal", "kind": "url", "notes": "Git Repos"},
            {"path": "https://python.org", "label": "Python Docs", "kind": "url", "notes": "Programming Reference"},
            {"path": "C:\\Tools\\Editor.exe", "label": "Code Editor", "kind": "file", "notes": "IDE"},
        ]
        widget.add_entries(entries)
        assert widget.count() == 3

        # Suche nach "git" (trifft GitHub Portal und Repos)
        count = widget.filter_entries("git")
        assert count == 1
        assert widget.get_visible_count() == 1
        first = widget.get_first_visible_entry()
        assert first is not None
        assert first["label"] == "GitHub Portal"

        # Suche nach Notiz "reference"
        count = widget.filter_entries("reference")
        assert count == 1
        first = widget.get_first_visible_entry()
        assert first is not None
        assert first["label"] == "Python Docs"

        # Leere Suche zeigt alle
        count = widget.filter_entries("")
        assert count == 3
        assert widget.get_visible_count() == 3

    def test_drag_drop_url(self):
        _app = _get_qapp()
        widget = SoftwareListWidget()
        mime = QMimeData()
        mime.setUrls([QUrl("https://example.com/docs")])
        event = MagicMock(spec=QDropEvent)
        event.mimeData.return_value = mime

        widget.dropEvent(event)
        assert widget.count() == 1
        entry = widget.get_all_entries()[0]
        assert entry["path"] == "https://example.com/docs"
        assert entry["kind"] == "url"


class TestMainWindowIntegration:
    def test_duplicate_board(self, tmp_path):
        _app = _get_qapp()
        settings_path = str(tmp_path / "test_settings.ini")
        settings = QSettings(settings_path, QSettings.Format.IniFormat)
        window = MainWindow(settings=settings)
        try:
            assert window.tabs.count() == 1
            page0 = window.tabs.widget(0)
            page0.add_entries([{"path": "https://python.org", "label": "Python", "kind": "url", "notes": "docs"}])

            window.duplicate_board(0)
            assert window.tabs.count() == 2
            from SoftwareCenter import t
            assert f"({t('Kopie')})" in window.tabs.tabText(1)
            page1 = window.tabs.widget(1)
            entries = page1.list.get_all_entries()
            assert len(entries) == 1
            assert entries[0]["path"] == "https://python.org"
        finally:
            window.close()

    def test_search_edit_and_return_pressed(self, tmp_path):
        _app = _get_qapp()
        settings_path = str(tmp_path / "test_settings.ini")
        settings = QSettings(settings_path, QSettings.Format.IniFormat)
        window = MainWindow(settings=settings)
        try:
            page = window.tabs.widget(0)
            page.add_entries([
                {"path": "https://example.com", "label": "Example Web", "kind": "url", "notes": ""},
                {"path": "https://other.com", "label": "Other Site", "kind": "url", "notes": ""},
            ])

            # Schnellsuche Text ändern
            window.search_edit.setText("Other")
            assert page.get_visible_count() == 1

            with patch("SoftwareCenter.open_file") as mock_open:
                window._on_search_return_pressed()
                mock_open.assert_called_once_with("https://other.com")

            # Esc leert Suche
            window._clear_search()
            assert window.search_edit.text() == ""
            assert page.get_visible_count() == 2
        finally:
            window.close()
