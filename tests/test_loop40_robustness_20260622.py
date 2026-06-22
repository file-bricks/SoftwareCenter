# -*- coding: utf-8 -*-
"""Regressionstests — SoftwareCenter Desktop-Bugsweep 2026-06-22 (Bugsweep-Loop-Lauf 40).

normalize_entry ist GUI-frei -> echter Test. Rest statisch (red-on-revert via SC_SRC -> PRE-Backup).

  BUG-40 normalize_entry: Nicht-String-Pfad (None) -> leer -> Eintrag verworfen (statt Literal "None").
  BUG-40 _build_toolbar: QToolBar.setObjectName (saveState/restoreState-tauglich).
  BUG-40 save_settings: settings.remove("tabs") vor beginWriteArray (keine Registry-Reste).
"""
import os
import sys
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJ))

_SRC = Path(os.environ.get("SC_SRC", _PROJ))


def read(rel):
    return (_SRC / rel).read_text(encoding="utf-8")


# --- echter Test ---
def test_bug40_normalize_entry_none_path_dropped():
    import SoftwareCenter as m
    # dict-Eintrag mit path=None (manuell editiertes Profil) -> vor Fix str(None)="None" -> gespeichert
    assert m.normalize_entry({"path": None}) is None, "Nicht-String-Pfad (None) muss verworfen werden"
    # gültiger Pfad bleibt erhalten
    ok = m.normalize_entry({"path": "C:/x/y.exe"})
    assert ok is not None and ok.get("path")


# --- statische Assertions (red-on-revert via SC_SRC -> PRE) ---
def test_bug40_static_toolbar_objectname():
    src = read("SoftwareCenter.py")
    assert 'tb.setObjectName("Hauptleiste")' in src, "BUG-40 QToolBar objectName fehlt"


def test_bug40_static_settings_remove_array():
    src = read("SoftwareCenter.py")
    assert 'settings.remove("tabs")' in src, "BUG-40 settings.remove vor beginWriteArray fehlt"


def test_bug40_static_normalize_entry_nonstr_empty():
    src = read("SoftwareCenter.py")
    assert "if isinstance(raw_path, str) else \"\"" in src, "BUG-40 normalize_entry Nicht-String-Guard fehlt"
    assert "else str(raw_path).strip()" not in src, "BUG-40 alter str(None)-Pfad noch da"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
