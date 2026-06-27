# -*- coding: utf-8 -*-
"""Windows: open_file/_startfile_in_dir startet Ziele mit cwd = Ordner der Datei.

Hintergrund: Aus SoftwareCenter gestartete Apps sollen ihr Arbeitsverzeichnis
auf den Ordner der Ziel-Datei gesetzt bekommen (wie "Ausfuehren in:" einer
Verknuepfung), damit Apps Ressourcen relativ zur cwd finden. os.startfile() allein
wuerde die cwd des SoftwareCenter-Prozesses vererben.
"""
import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import SoftwareCenter as sc  # noqa: E402

pytestmark = pytest.mark.skipif(not sys.platform.startswith("win"),
                                reason="cwd-Start via ShellExecuteW ist Windows-spezifisch")


def test_startfile_sets_working_directory(tmp_path):
    out = tmp_path / "probe_out.txt"
    ziel = tmp_path / "ziel"
    ziel.mkdir()
    bat = tmp_path / "probe.bat"
    bat.write_text('@echo off\r\ncd > "%s"\r\n' % out, encoding="ascii")

    old = os.getcwd()
    os.chdir(os.environ.get("SystemRoot", r"C:\Windows"))  # fremde cwd
    try:
        sc._startfile_in_dir(str(bat), str(ziel))
        for _ in range(30):
            if out.exists():
                break
            time.sleep(0.2)
    finally:
        os.chdir(old)

    assert out.exists(), "Probe-Batch wurde nicht ausgefuehrt"
    got = out.read_text(encoding="utf-8", errors="replace").strip()
    assert os.path.normcase(got) == os.path.normcase(str(ziel)), (
        f"cwd nicht gesetzt: erwartet {ziel}, war {got}")
