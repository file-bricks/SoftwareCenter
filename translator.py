"""TranslationSystem - Multi-Language Support für Anwendungen
============================================================
Version: 2.1.0 (Tier-2 6-Sprachen-Ausbau P-006)
Quelle: _LANG/translator.py v2.0 & SoftwareCenter
Referenz: _LANG/LANGUAGE_CODES.md

Verwendung:
-----------
from translator import TranslationSystem, get_translator, t

translator = get_translator()
label.setText(t('Datei'))
translator.set_language('en')
"""

from __future__ import annotations

import json
import locale
import re
from pathlib import Path

SUPPORTED_LANGUAGES = ("de", "en", "es", "zh", "ja", "ru")
DEFAULT_LANGUAGE = "de"
FALLBACK_CHAIN = ("en", "de")

LANGUAGE_NAMES: dict[str, str] = {
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "zh": "简体中文",
    "ja": "日本語",
    "ru": "Русский",
}

LANGUAGE_DISPLAY_NAMES: dict[str, str] = {
    "de": "Deutsch (de)",
    "en": "English (en)",
    "es": "Español (es)",
    "zh": "简体中文 (zh)",
    "ja": "日本語 (ja)",
    "ru": "Русский (ru)",
}


def detect_system_language() -> str:
    """Ermittelt die Systemsprache, Fallback auf 'de'."""
    try:
        loc = locale.getlocale()[0]
        if loc:
            code = loc.split("_")[0].lower()
            if code in SUPPORTED_LANGUAGES:
                return code
    except Exception:
        pass
    return DEFAULT_LANGUAGE


class TranslationSystem:
    """Multi-Language Support System v2.1 mit deterministischer Fallback-Kette."""

    SUPPORTED_LANGUAGES = SUPPORTED_LANGUAGES
    FALLBACK_LANGUAGES = FALLBACK_CHAIN
    LANGUAGE_NAMES = LANGUAGE_NAMES
    LANGUAGE_DISPLAY_NAMES = LANGUAGE_DISPLAY_NAMES

    def __init__(self, default_lang: str = DEFAULT_LANGUAGE, app_dir: Path | None = None):
        """Initialisiert Translation-System.

        Args:
            default_lang: Standard-Sprache ('de', 'en', 'es', 'zh', 'ja', 'ru')
            app_dir: Verzeichnis der Anwendung (default: Verzeichnis dieser Datei)
        """
        self.current_lang = default_lang if default_lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

        if app_dir is None:
            self.app_dir = Path(__file__).resolve().parent
        else:
            self.app_dir = Path(app_dir)

        self.translations_file = self.app_dir / "locales" / "translations.json"

        self.string_patterns = [
            re.compile(r'setText\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'setWindowTitle\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'setToolTip\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'setPlaceholderText\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'QLabel\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'QPushButton\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'QCheckBox\s*\(\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'addAction\s*\([^,]*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'addMenu\s*\([^,]*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'addTab\s*\([^,]+,\s*["\']([^"\']+)["\']\s*\)'),
            re.compile(r'text\s*=\s*"([^"]+)"'),
        ]

        self.german_hints = [
            "datei", "bearbeiten", "ansicht", "hilfe", "öffnen", "speichern",
            "schließen", "einstellungen", "abbrechen", "ok", "ja", "nein",
            "start", "stop", "pause", "fortsetzen", "laden", "aktualisieren",
            "filter", "fehler", "export", "import", "optionen", "anzeigen",
            "löschen", "board", "leiste", "notiz", "bezeichnung", "suche",
            "verlauf", "favorit", "kacheln", "liste",
        ]

        self.translations: dict[str, dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        if self.translations_file.exists():
            try:
                with open(self.translations_file, encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception:
                self.translations = {}
        else:
            self.translations = {}

    def _save_translations(self):
        self.translations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.translations_file, "w", encoding="utf-8") as f:
            json.dump(self.translations, f, indent=2, ensure_ascii=False)

    def t(self, key: str) -> str:
        """Übersetzt einen Key in die aktuelle Sprache.
        Fallback-Kette: aktuelle Sprache -> en -> de -> Key selbst.
        """
        if not key:
            return ""

        entry = self.translations.get(key)
        if isinstance(entry, dict):
            value = entry.get(self.current_lang)
            if isinstance(value, str) and value.strip():
                return value
            for fb in FALLBACK_CHAIN:
                value = entry.get(fb)
                if isinstance(value, str) and value.strip():
                    return value
            return key

        if self._is_german(key):
            self.translations[key] = self._new_translation_entry(key, "")
            self._save_translations()

        return key

    def set_language(self, lang: str):
        """Setzt die aktive Zielsprache."""
        if lang in SUPPORTED_LANGUAGES:
            self.current_lang = lang

    def get_language(self) -> str:
        """Liefert die aktive Zielsprache zurück."""
        return self.current_lang

    @classmethod
    def get_supported_languages(cls) -> list[str]:
        """Liefert die Liste aller 6 unterstützten Sprachcodes."""
        return list(SUPPORTED_LANGUAGES)

    @classmethod
    def get_language_names(cls) -> dict[str, str]:
        """Liefert Mapping von Sprachcode auf nativer Sprachname."""
        return dict(LANGUAGE_NAMES)

    @classmethod
    def get_language_display_names(cls) -> dict[str, str]:
        """Liefert Mapping von Sprachcode auf UI-Display-Name."""
        return dict(LANGUAGE_DISPLAY_NAMES)

    @classmethod
    def _new_translation_entry(cls, de: str, en: str = "", **kwargs) -> dict[str, str]:
        """Erzeugt einen neuen Eintrag mit vollständigem 6-Sprachen-Schema."""
        entry = dict.fromkeys(SUPPORTED_LANGUAGES, "")
        entry["de"] = de
        entry["en"] = en
        for lang, val in kwargs.items():
            if lang in SUPPORTED_LANGUAGES:
                entry[lang] = val
        return entry

    def add_translation(self, key: str, **translations: str):
        """Fügt eine Übersetzung manuell hinzu oder aktualisiert sie."""
        if key not in self.translations:
            self.translations[key] = dict.fromkeys(SUPPORTED_LANGUAGES, "")
        for lang, value in translations.items():
            if lang in SUPPORTED_LANGUAGES:
                self.translations[key][lang] = value
        self._save_translations()

    def scan_and_update(self, project_dir: Path | None = None) -> dict:
        """Scannt Projekt-Dateien nach deutschen Strings und aktualisiert translations.json."""
        if project_dir is None:
            project_dir = self.app_dir

        found_strings = self._find_german_strings(Path(project_dir))

        added = []
        for string in sorted(found_strings):
            if string not in self.translations:
                self.translations[string] = self._new_translation_entry(string, "")
                added.append(string)

        if added:
            self._save_translations()

        missing = {lang: [] for lang in SUPPORTED_LANGUAGES if lang != "de"}
        for k, v in self.translations.items():
            for lang in SUPPORTED_LANGUAGES:
                if lang != "de" and not v.get(lang):
                    missing[lang].append(k)

        return {"added": added, "missing": missing, "total": len(self.translations)}

    def _find_german_strings(self, directory: Path) -> set[str]:
        german_strings = set()
        skip_dirs = {"build", "dist", "venv", ".venv", "__pycache__", "releases", ".git"}

        for py_file in directory.rglob("*.py"):
            if any(folder in py_file.parts for folder in skip_dirs):
                continue
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue

            for pattern in self.string_patterns:
                for match in pattern.findall(content):
                    if match and self._is_german(match):
                        german_strings.add(match.strip())

        return german_strings

    def _is_german(self, text: str) -> bool:
        if any(ch in text for ch in "äöüÄÖÜß"):
            return True
        text_lower = text.lower()
        return any(hint in text_lower for hint in self.german_hints)

    def get_missing_translations(self, lang: str | None = None) -> dict[str, list[str]] | list[str]:
        """Gibt fehlende Übersetzungen zurück. Wenn lang gesetzt ist, nur für diese Sprache."""
        if lang:
            if lang not in SUPPORTED_LANGUAGES:
                raise ValueError(f"Unsupported language: {lang}")
            return [k for k, v in self.translations.items() if not v.get(lang)]

        missing = {}
        for lang_code in SUPPORTED_LANGUAGES:
            if lang_code == "de":
                continue
            m = [k for k, v in self.translations.items() if not v.get(lang_code)]
            if m:
                missing[lang_code] = m
        return missing


_default_translator: TranslationSystem | None = None


def get_translator(default_lang: str | None = None) -> TranslationSystem:
    """Gibt die anwendungsweite TranslationSystem-Instanz zurück (Singleton-Muster)."""
    global _default_translator
    if _default_translator is None:
        _default_translator = TranslationSystem(default_lang or DEFAULT_LANGUAGE)
    elif default_lang and default_lang in SUPPORTED_LANGUAGES:
        _default_translator.set_language(default_lang)
    return _default_translator


def t(key: str) -> str:
    """Übersetzt den angegebenen Schlüssel mit der Standard-Instanz."""
    return get_translator().t(key)


if __name__ == "__main__":
    tr = TranslationSystem()
    print(f"Sprache: {tr.get_language()}")
    print(f"Unterstützt: {', '.join(SUPPORTED_LANGUAGES)}")
    result = tr.scan_and_update()
    print(f"Scan: {result['total']} Strings, {len(result['added'])} neu")
    for lang_code, keys in result["missing"].items():
        print(f"  {lang_code}: {len(keys)} fehlend")
