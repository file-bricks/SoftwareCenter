"""Tests für das Multi-Language System (Tier-2 6-Sprachen-Standard P-006) in SoftwareCenter."""

import json
from pathlib import Path

from manage_translations import manage_translations
from translator import (
    DEFAULT_LANGUAGE,
    FALLBACK_CHAIN,
    LANGUAGE_DISPLAY_NAMES,
    LANGUAGE_NAMES,
    SUPPORTED_LANGUAGES,
    TranslationSystem,
    detect_system_language,
    get_translator,
    t,
)

ROOT = Path(__file__).resolve().parents[1]


def test_supported_languages_tier2():
    assert len(SUPPORTED_LANGUAGES) == 6
    assert set(SUPPORTED_LANGUAGES) == {"de", "en", "es", "zh", "ja", "ru"}
    assert DEFAULT_LANGUAGE == "de"
    assert FALLBACK_CHAIN == ("en", "de")


def test_language_names_and_display_mappings():
    for lang in SUPPORTED_LANGUAGES:
        assert lang in LANGUAGE_NAMES
        assert lang in LANGUAGE_DISPLAY_NAMES
        assert lang in LANGUAGE_DISPLAY_NAMES[lang]


def test_translation_system_initialization(tmp_path):
    tr = TranslationSystem(app_dir=tmp_path)
    assert tr.get_language() == "de"
    assert tr.get_supported_languages() == list(SUPPORTED_LANGUAGES)


def test_fallback_chain(tmp_path):
    locales_dir = tmp_path / "locales"
    locales_dir.mkdir(parents=True)
    catalog = {
        "Full": {
            "de": "Voll",
            "en": "Full",
            "es": "Lleno",
            "zh": "全",
            "ja": "満",
            "ru": "Полный",
        },
        "OnlyEn": {
            "de": "",
            "en": "EnglishOnly",
            "es": "",
            "zh": "",
            "ja": "",
            "ru": "",
        },
        "OnlyDe": {
            "de": "NurDeutsch",
            "en": "",
            "es": "",
            "zh": "",
            "ja": "",
            "ru": "",
        },
    }
    with open(locales_dir / "translations.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f)

    tr = TranslationSystem(app_dir=tmp_path)

    # 1. Exact match in target language
    tr.set_language("es")
    assert tr.t("Full") == "Lleno"

    # 2. Fallback to EN if missing in target
    assert tr.t("OnlyEn") == "EnglishOnly"

    # 3. Fallback to DE if missing in target and EN
    assert tr.t("OnlyDe") == "NurDeutsch"

    # 4. Fallback to key if missing everywhere
    assert tr.t("MissingKey") == "MissingKey"


def test_invalid_language_handling(tmp_path):
    tr = TranslationSystem(app_dir=tmp_path)
    tr.set_language("de")
    tr.set_language("invalid_lang_code")
    assert tr.get_language() == "de"


def test_detect_system_language():
    lang = detect_system_language()
    assert lang in SUPPORTED_LANGUAGES


def test_singleton_get_translator():
    tr1 = get_translator()
    tr2 = get_translator()
    assert tr1 is tr2


def test_global_t_helper():
    res = t("Datei")
    assert isinstance(res, str)
    assert len(res) > 0


def test_translations_catalog_exists_and_is_valid():
    catalog_path = ROOT / "locales" / "translations.json"
    assert catalog_path.exists(), "locales/translations.json must exist"

    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert len(data) >= 80


def test_translations_catalog_100_percent_parity():
    catalog_path = ROOT / "locales" / "translations.json"
    with open(catalog_path, encoding="utf-8") as f:
        data = json.load(f)

    missing = []
    for key, entry in data.items():
        assert isinstance(entry, dict), f"Key {key} must be a dict"
        for lang in SUPPORTED_LANGUAGES:
            val = entry.get(lang)
            if not isinstance(val, str) or not val.strip():
                missing.append((key, lang))

    assert len(missing) == 0, f"Missing translations in catalog: {missing}"


def test_manage_translations_check_mode():
    exit_code = manage_translations(source_dir=ROOT, check_mode=True)
    assert exit_code == 0


def test_new_translation_entry_helper():
    entry = TranslationSystem._new_translation_entry("Speichern", "Save", es="Guardar")
    assert entry["de"] == "Speichern"
    assert entry["en"] == "Save"
    assert entry["es"] == "Guardar"
    for lang in SUPPORTED_LANGUAGES:
        assert lang in entry


def test_mainwindow_language_switching_and_retranslate(tmp_path):
    import os

    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    import SoftwareCenter as sc

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QApplication.instance() or QApplication([])

    s = QSettings(str(tmp_path / "i18n_test.ini"), QSettings.Format.IniFormat)
    win = sc.MainWindow(settings=s)

    try:
        # Default starts in German
        win.set_language("de")
        assert win.translator.get_language() == "de"
        assert win.act_quit.text() == "Beenden"
        assert win.act_view_tiles.text() == "Kacheln"
        assert win.act_view_list.text() == "Liste"

        # Switch to English
        win.set_language("en")
        assert win.translator.get_language() == "en"
        assert win.act_quit.text() == "Quit"
        assert win.act_view_tiles.text() == "Tiles"
        assert win.act_view_list.text() == "List"
        assert win.act_export_profile.text() == "Export profile"

        # Switch to Spanish
        win.set_language("es")
        assert win.translator.get_language() == "es"
        assert win.act_quit.text() == "Salir"
        assert win.act_view_tiles.text() == "Mosaicos"
        assert win.act_view_list.text() == "Lista"

        # Switch to Chinese
        win.set_language("zh")
        assert win.translator.get_language() == "zh"
        assert win.act_quit.text() == "退出"

        # Switch back to German
        win.set_language("de")
        assert win.translator.get_language() == "de"
        assert win.act_quit.text() == "Beenden"
    finally:
        win.close()


def test_mainwindow_language_persists_in_settings(tmp_path):
    import os

    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication

    import SoftwareCenter as sc

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QApplication.instance() or QApplication([])

    ini_path = str(tmp_path / "persist_test.ini")
    tr = get_translator()
    original_lang = tr.get_language()
    try:
        s1 = QSettings(ini_path, QSettings.Format.IniFormat)
        win1 = sc.MainWindow(settings=s1)
        try:
            win1.set_language("es")
            win1.save_settings()
        finally:
            win1.close()

        s2 = QSettings(ini_path, QSettings.Format.IniFormat)
        win2 = sc.MainWindow(settings=s2)
        try:
            assert win2.translator.get_language() == "es"
            assert win2.act_quit.text() == "Salir"
        finally:
            win2.close()
    finally:
        tr.set_language(original_lang)


def test_context_menu_translates_with_active_language(tmp_path):
    import os
    from unittest.mock import patch

    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QApplication

    import SoftwareCenter as sc

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QApplication.instance() or QApplication([])

    f = tmp_path / "app.exe"
    f.write_text("dummy", encoding="utf-8")

    widget = sc.SoftwareListWidget()
    widget.board_provider = lambda: [(1, "Board 2")]
    widget.add_paths([str(f)])
    widget.item(0).setSelected(True)

    tr = get_translator()
    original_lang = tr.get_language()

    expected_by_lang = {
        "de": ("Öffnen/Starten", "Pfad kopieren", "Eintrag bearbeiten...", "Alphabetisch sortieren (A-Z)", "Löschen", "Senden an", "Duplizieren auf"),
        "en": ("Open/Launch", "Copy path", "Edit entry...", "Sort alphabetically (A-Z)", "Delete", "Send to", "Duplicate to"),
        "es": ("Abrir/Iniciar", "Copiar ruta", "Editar entrada...", "Ordenar alfabéticamente (A-Z)", "Eliminar", "Enviar a", "Duplicar en"),
        "ja": ("開く/起動", "パスをコピー", "エントリを編集...", "アルファベット順に並べ替え (A-Z)", "削除", "送信先", "次に複製"),
        "ru": ("Открыть/Запустить", "Копировать путь", "Редактировать запись...", "Сортировать по алфавиту (А-Я)", "Удалить", "Отправить в", "Дублировать в"),
        "zh": ("打开/启动", "复制路径", "编辑条目...", "按字母排序 (A-Z)", "删除", "发送到", "复制到"),
    }

    try:
        for lang, expected_labels in expected_by_lang.items():
            tr.set_language(lang)
            captured = []

            def intercept_exec(menu_self, pos=None, target=captured):
                for act in menu_self.actions():
                    if not act.isSeparator():
                        target.append(act.text())
                return None

            with patch.object(sc.SoftwareListWidget, "_exec_context_menu", side_effect=intercept_exec):
                widget._on_context_menu(QPoint(10, 10))

            for label in expected_labels:
                assert label in captured, f"{label!r} missing in {lang} context menu: {captured}"
    finally:
        tr.set_language(original_lang)
        widget.close()


def test_file_manager_titles_and_error_dialogs_translate(tmp_path):
    from unittest.mock import patch

    from PySide6.QtWidgets import QMessageBox

    import SoftwareCenter as sc

    tr = get_translator()
    original_lang = tr.get_language()
    try:
        tr.set_language("en")
        with patch("sys.platform", "win32"):
            assert sc.get_file_manager_action_title() == "Show in Explorer"
        with patch("sys.platform", "darwin"):
            assert sc.get_file_manager_action_title() == "Show in Finder"
        with patch("sys.platform", "linux"):
            assert sc.get_file_manager_action_title() == "Show in file manager"
        assert sc.get_file_manager_action_title("https://example.com") == "Open in browser"

        missing = str(tmp_path / "missing_tool.exe")
        with patch.object(QMessageBox, "warning") as mock_warn:
            sc.open_file(missing)
            assert mock_warn.call_args[0][1] == "File not found"
            assert "Path does not exist:" in mock_warn.call_args[0][2]

        with patch.object(QMessageBox, "warning") as mock_warn_fm:
            sc.show_in_file_manager(missing)
            assert mock_warn_fm.call_args[0][1] == "File not found"
            assert "Path does not exist:" in mock_warn_fm.call_args[0][2]
    finally:
        tr.set_language(original_lang)


def test_retranslate_ui_updates_sidebar_toolbar_tooltips_and_tray(tmp_path):
    import os
    from unittest.mock import patch

    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QApplication, QLineEdit, QSystemTrayIcon, QWidgetAction

    import SoftwareCenter as sc

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QApplication.instance() or QApplication([])

    tr = get_translator()
    original_lang = tr.get_language()
    tool = tmp_path / "demo.exe"
    tool.write_text("x", encoding="utf-8")

    s = QSettings(str(tmp_path / "retranslate_full.ini"), QSettings.Format.IniFormat)
    s.setValue("minimize_to_tray", True)
    with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
        win = sc.MainWindow(settings=s)

    try:
        win.current_page().list.add_entries([{"path": str(tool), "label": "Demo", "notes": "My note"}])
        win.add_new_tab("Second")
        win.on_close_tab(1)
        win.set_language("en")

        # Sidebar (BoardsPanel) + Dock
        panel = win.boards_panel
        assert win.boards_dock.windowTitle() == "Boards"
        assert panel.view_tabs.tabText(panel.view_tabs.indexOf(panel.history_list)) == "History"
        assert panel.view_tabs.tabText(panel.view_tabs.indexOf(panel.alpha_list)) == "Alphabetical"
        assert panel.view_tabs.accessibleName() == "Board Catalog"
        assert panel.history_list.accessibleName() == "Recently closed and active boards"
        assert panel.alpha_list.accessibleName() == "Alphabetical board list"
        assert panel.clear_history_btn.text() == "Clear history"
        assert panel.clear_history_btn.accessibleName() == "Clear history"
        assert "closed boards" in panel.clear_history_btn.toolTip().lower()
        hist_tooltips = [panel.history_list.item(i).toolTip() for i in range(panel.history_list.count())]
        assert any(tt.startswith("Closed:") for tt in hist_tooltips)
        assert "Active" in hist_tooltips

        # Toolbar, Tooltips, Search, Board Bar & List Item Tooltips
        assert win.main_toolbar.windowTitle() == "Main Toolbar"
        assert win.act_rename_tab.toolTip() == "Rename current board"
        assert win.act_duplicate_tab.toolTip() == "Duplicate current board (create copy)"
        assert win.act_view_tiles.toolTip() == "Tile view with large icons"
        assert win.act_view_list.toolTip() == "Compact list view"
        assert win.act_export_profile.toolTip() == "Export boards and entries as JSON profile"
        assert win.act_import_profile.toolTip() == "Import boards and entries from JSON profile"
        assert win.act_toggle_boards_panel.iconText() == "Board Management"
        assert win.act_toggle_boards_panel.toolTip() == "Toggle board management (Ctrl+B)"
        if win.btn_toggle_boards_panel is not None:
            assert win.btn_toggle_boards_panel.accessibleName() == "Board Management"
        assert win.search_edit.accessibleName() == "Quick search"
        assert "Filters entries" in win.search_edit.accessibleDescription()
        assert win.search_edit.placeholderText() == "Filter entries in board… (Ctrl+F)"
        assert "Ctrl+F" in win.search_edit.toolTip()
        assert win.tabs.tabBar().accessibleName() == "Board Bar"
        assert "Notes: My note" in win.current_page().list.item(0).toolTip()
        assert win.current_page().list.accessibleName() == "Software and document list"

        # Live Tray Menu
        assert win.tray is not None
        tray_menu = win.tray.contextMenu()
        assert tray_menu is not None
        tray_texts = [a.text() for a in tray_menu.actions() if not a.isSeparator()]
        assert "Open/Show" in tray_texts
        assert "Quit" in tray_texts
        widget_actions = [a for a in tray_menu.actions() if isinstance(a, QWidgetAction)]
        search_widgets = [a.defaultWidget() for a in widget_actions if isinstance(a.defaultWidget(), QLineEdit)]
        assert search_widgets and search_widgets[0].placeholderText() == "Search board or entry …"
        assert win._tray_dynamic_actions[0].menu() is not None
        assert win._tray_dynamic_actions[0].menu().actions()[0].text() == "Open board"
    finally:
        tr.set_language(original_lang)
        win.close()


def test_dialogs_and_panel_context_menu_translate_in_english(tmp_path):
    import os
    from unittest.mock import patch

    from PySide6.QtCore import QPoint, QSettings
    from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMenu, QMessageBox

    import SoftwareCenter as sc

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    _ = QApplication.instance() or QApplication([])

    tr = get_translator()
    original_lang = tr.get_language()
    s = QSettings(str(tmp_path / "dialogs_en.ini"), QSettings.Format.IniFormat)
    win = sc.MainWindow(settings=s)
    try:
        win.set_language("en")

        with patch.object(QMessageBox, "information") as mock_info:
            win.on_close_tab(0)
            assert mock_info.call_args[0][1] == "Not possible"
            assert mock_info.call_args[0][2] == "The last tab cannot be closed."

        with patch.object(QInputDialog, "getText", return_value=("", False)) as mock_new:
            win.on_new_tab()
            assert mock_new.call_args[0][1] == "New tab"
            assert mock_new.call_args[0][2] == "Tab name:"

        with patch.object(QInputDialog, "getText", return_value=("", False)) as mock_ren:
            win.on_rename_tab(0)
            assert mock_ren.call_args[0][1] == "Rename tab"
            assert mock_ren.call_args[0][2] == "New tab name:"

        with patch.object(QFileDialog, "getSaveFileName", return_value=("", "")) as mock_exp:
            win.export_profile()
            assert mock_exp.call_args[0][1] == "Export profile"
            assert mock_exp.call_args[0][3] == "JSON files (*.json)"

        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_del:
            win.current_page().on_request_delete(["C:/a.exe", "C:/b.exe"])
            assert mock_del.call_args[0][1] == "Confirm deletion"
            assert "Remove 2 shortcuts from this view?" in mock_del.call_args[0][2]

        # BoardsPanel context menu
        win.boards_panel.refresh()
        captured_panel_actions = []

        def intercept_panel_menu(menu_self, pos=None):
            captured_panel_actions.extend(a.text() for a in menu_self.actions() if not a.isSeparator())
            return None

        with patch.object(QMenu, "exec", side_effect=intercept_panel_menu):
            win.boards_panel._on_context_menu(win.boards_panel.history_list, QPoint(5, 5))
        assert "Favorite" in captured_panel_actions
        assert "Delete" in captured_panel_actions
    finally:
        tr.set_language(original_lang)
        win.close()
