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
    s1 = QSettings(ini_path, QSettings.Format.IniFormat)
    win1 = sc.MainWindow(settings=s1)
    win1.set_language("es")
    win1.save_settings()
    win1.close()

    s2 = QSettings(ini_path, QSettings.Format.IniFormat)
    win2 = sc.MainWindow(settings=s2)
    try:
        assert win2.translator.get_language() == "es"
        assert win2.act_quit.text() == "Salir"
    finally:
        win2.close()

