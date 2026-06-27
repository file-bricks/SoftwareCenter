# -*- coding: utf-8 -*-
"""AppProfile: SoftwareCenter und LaunchBoards teilen Code, bleiben aber getrennt."""
import os
import sys

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import SoftwareCenter as sc  # noqa: E402

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
_app = QApplication.instance() or QApplication([])


def test_default_is_softwarecenter(tmp_path):
    w = sc.MainWindow(settings=QSettings(str(tmp_path / "sc.ini"), QSettings.Format.IniFormat))
    assert w.windowTitle() == "SoftwareCenter"
    assert w.profile.settings_app == "SoftwareCenter"
    assert w.profile.icon_file == "icon.ico"


def test_launchboards_profile(tmp_path):
    w = sc.MainWindow(settings=QSettings(str(tmp_path / "lb.ini"), QSettings.Format.IniFormat),
                      profile=sc.PROFILE_LAUNCHBOARDS)
    assert w.windowTitle() == "LaunchBoards"
    assert w.profile.settings_app == "LaunchBoards"
    assert w.profile.icon_file == "launchboards.ico"


def test_profiles_are_separate():
    # getrennte QSettings-Namespaces + Single-Instance -> parallel betreibbar
    assert sc.PROFILE_SOFTWARECENTER.settings_app != sc.PROFILE_LAUNCHBOARDS.settings_app
    assert sc.PROFILE_SOFTWARECENTER.instance_id != sc.PROFILE_LAUNCHBOARDS.instance_id
