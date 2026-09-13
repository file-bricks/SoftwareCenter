"""Tests for Empty-Board UI placeholder and Universal Organizer communication."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

import SoftwareCenter as sc
from translator import SUPPORTED_LANGUAGES, get_translator


def _ensure_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_empty_board_paint_event_renders_safely():
    _ensure_app()
    widget = sc.SoftwareListWidget()
    widget.resize(500, 400)
    assert widget.count() == 0

    pixmap = QPixmap(500, 400)
    pixmap.fill(Qt.GlobalColor.white)
    widget.render(pixmap)
    assert not pixmap.isNull()


def test_populated_board_paint_event_renders_safely(tmp_path):
    _ensure_app()
    widget = sc.SoftwareListWidget()
    widget.resize(500, 400)

    f1 = tmp_path / "sample_doc.txt"
    f1.write_text("content", encoding="utf-8")
    f2 = tmp_path / "sample_script.py"
    f2.write_text("print(1)", encoding="utf-8")

    widget.add_paths([str(f1), str(f2)])
    assert widget.count() == 2

    pixmap = QPixmap(500, 400)
    pixmap.fill(Qt.GlobalColor.white)
    widget.render(pixmap)
    assert not pixmap.isNull()


def test_placeholder_translations_available_in_all_tier2_languages():
    tr = get_translator()
    keys = [
        "Dieses Board ist noch leer",
        "Ziehen Sie beliebige Apps, Dokumente, Ordner oder Verknüpfungen hierher.",
        "Über SoftwareCenter",
        "Über LaunchBoards",
    ]

    for key in keys:
        assert key in tr.translations, f"Missing key {key} in translations catalog"
        for lang in SUPPORTED_LANGUAGES:
            val = tr.translations[key].get(lang)
            assert val and len(val.strip()) > 0, f"Missing translation for {key} in {lang}"


def test_main_window_help_menu_and_about_dialog(tmp_path):
    _ensure_app()
    s = sc.QSettings(str(tmp_path / "settings.ini"), sc.QSettings.Format.IniFormat)
    win = sc.MainWindow(settings=s, profile=sc.PROFILE_SOFTWARECENTER)
    try:
        assert hasattr(win, "help_menu")
        assert hasattr(win, "act_about")
        assert "Hilfe" in win.help_menu.title()

        title, desc = win.show_about_dialog()
        assert sc.__version__ in title
        assert "SoftwareCenter" in title
        assert "Ordnungslayer" in desc

        win.set_language("en")
        assert win.help_menu.title() == "Help"
        assert win.act_about.text() == "About SoftwareCenter"
    finally:
        win.close()
