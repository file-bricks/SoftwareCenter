#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""manage_translations.py - Multi-Language Scanner & Auditor für SoftwareCenter
================================================================================
Scannt Python-Dateien nach GUI-Texten und pflegt/auditiert locales/translations.json
gemäß dem 6-Sprachen Tier-2 Standard (Policy P-006: DE, EN, ES, ZH, JA, RU).

Verwendung:
    python manage_translations.py [--dir VERZEICHNIS] [--check] [--export-json DATEI]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SUPPORTED_LANGUAGES = ("de", "en", "es", "zh", "ja", "ru")
TRANSLATION_FILE = "locales/translations.json"

STRING_PATTERNS = [
    re.compile(r'text\s*=\s*["\']([^"\']+)["\']'),
    re.compile(r'setText\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'setWindowTitle\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'setToolTip\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'setPlaceholderText\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'QLabel\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'QPushButton\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'QCheckBox\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'QAction\s*\(\s*["\']([^"\']+)["\']'),
    re.compile(r'addAction\s*\(\s*["\']([^"\']+)["\']'),
    re.compile(r'addMenu\s*\(\s*["\']([^"\']+)["\']'),
    re.compile(r'QMessageBox\.\w+\s*\([^,]+,\s*["\']([^"\']+)["\']'),
    re.compile(r'QInputDialog\.\w+\s*\([^,]+,\s*["\']([^"\']+)["\']'),
    re.compile(r'QFileDialog\.\w+\s*\([^,]+,\s*["\']([^"\']+)["\']'),
    re.compile(r'tr\.t\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'translator\.t\s*\(\s*["\']([^"\']+)["\']\s*\)'),
    re.compile(r'\bt\s*\(\s*["\']([^"\']+)["\']\s*\)'),
]

GERMAN_HINTS = [
    "datei", "filter", "fehler", "laden", "speichern",
    "ansicht", "optionen", "zurück", "anzeigen", "export",
    "import", "einstellungen", "abbrechen", "hilfe", "bearbeiten",
    "öffnen", "schließen", "start", "aktualisieren", "löschen",
    "board", "leiste", "notiz", "bezeichnung", "suche", "verlauf",
    "favorit", "kacheln", "liste", "profil", "schließen",
]


def is_german(text: str) -> bool:
    """Erkennt, ob ein String deutsche Umlaute oder typische Signalworte enthält."""
    if any(ch in text for ch in "äöüÄÖÜß"):
        return True
    text_lower = text.lower()
    return any(w in text_lower for w in GERMAN_HINTS)


def find_german_strings(source_dir: str | Path) -> set[str]:
    """Durchsucht alle Python-Dateien nach deutschen GUI-Texten."""
    german_strings: set[str] = set()
    skip_dirs = {"build", "dist", "venv", ".venv", "__pycache__", "releases", ".git", "temp_test"}

    root_path = Path(source_dir)
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                try:
                    content = path.read_text(encoding="utf-8")
                except Exception:
                    continue
                for pattern in STRING_PATTERNS:
                    for match in pattern.findall(content):
                        cleaned = match.strip()
                        if len(cleaned) > 1 and not cleaned.startswith("http") and not cleaned.endswith((".ico", ".png")) and is_german(cleaned):
                            german_strings.add(cleaned)
    return german_strings


def manage_translations(
    source_dir: str | Path = ".",
    check_mode: bool = False,
    export_json: str | Path | None = None,
) -> int:
    """Verwaltet und validiert die Übersetzungsdatenbank.

    Returns:
        0 bei Erfolg, 1 bei Fehlern (z.B. fehlende Übersetzungen im check-Modus).
    """
    root_path = Path(source_dir)
    trans_file = root_path / TRANSLATION_FILE

    translations: dict[str, dict[str, str]] = {}
    if trans_file.exists():
        try:
            with open(trans_file, encoding="utf-8") as f:
                translations = json.load(f)
        except json.JSONDecodeError:
            translations = {}

    if check_mode:
        if not trans_file.exists():
            print(f"[ERROR] Translations file missing: {trans_file}", file=sys.stderr)
            return 1

        missing_by_lang: dict[str, list[str]] = {lang: [] for lang in SUPPORTED_LANGUAGES}
        for key, entry in translations.items():
            if not isinstance(entry, dict):
                missing_by_lang["de"].append(key)
                continue
            for lang in SUPPORTED_LANGUAGES:
                val = entry.get(lang)
                if not isinstance(val, str) or not val.strip():
                    missing_by_lang[lang].append(key)

        has_missing = any(len(lst) > 0 for lst in missing_by_lang.values())
        if has_missing:
            print("[ERROR] Missing translations found:", file=sys.stderr)
            for lang, keys in missing_by_lang.items():
                if keys:
                    print(f"  {lang} ({len(keys)} missing): {', '.join(keys[:5])}", file=sys.stderr)
            return 1

        print(f"[OK] Translation catalog check passed: {len(translations)} keys with 100% 6-language parity.")
        return 0

    found = find_german_strings(root_path)

    added = []
    for s in sorted(found):
        if s not in translations:
            translations[s] = {lang: (s if lang == "de" else "") for lang in SUPPORTED_LANGUAGES}
            added.append(s)

    # Sicherstellen, dass alle bestehenden Einträge das 6-Sprachen-Schema besitzen
    for _key, entry in translations.items():
        if isinstance(entry, dict):
            for lang in SUPPORTED_LANGUAGES:
                if lang not in entry:
                    entry[lang] = ""

    trans_file.parent.mkdir(parents=True, exist_ok=True)
    with open(trans_file, "w", encoding="utf-8") as f:
        json.dump(translations, f, indent=2, ensure_ascii=False)

    if added:
        print(f"[+] {len(added)} neue Eintraege hinzugefuegt:")
        for s in added[:10]:
            print(f"    - {s}")
        if len(added) > 10:
            print(f"    ... und {len(added) - 10} weitere")
    else:
        print("[i] Keine neuen deutschen Strings gefunden.")

    missing = {lang: [k for k, v in translations.items() if not v.get(lang)] for lang in SUPPORTED_LANGUAGES if lang != "de"}
    any_missing = any(len(lst) > 0 for lst in missing.values())
    if any_missing:
        print("\n[!] Fehlende Übersetzungen:")
        for lang, lst in missing.items():
            if lst:
                print(f"    - {lang}: {len(lst)} unübersetzt")
    else:
        print("\n[ok] Alle Strings haben vollständige Übersetzungen in allen 6 Sprachen.")

    print(f"\n[i] Gesamt: {len(translations)} Strings in {trans_file}")

    if export_json:
        out_path = Path(export_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(translations, f, indent=2, ensure_ascii=False)
        print(f"[i] Katalog exportiert nach {out_path}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage and audit multi-language catalogs")
    parser.add_argument("--dir", default=".", help="Project base directory")
    parser.add_argument("--check", action="store_true", help="Audit mode: exit non-zero if keys are missing")
    parser.add_argument("--export-json", default=None, help="Export catalog to specified path")
    args = parser.parse_args()

    return manage_translations(source_dir=args.dir, check_mode=args.check, export_json=args.export_json)


if __name__ == "__main__":
    sys.exit(main())
