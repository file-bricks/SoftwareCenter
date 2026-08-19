# -*- coding: utf-8 -*-
"""Regressionstest: kein verwaister Schliessen-Knopf in der Board-Leiste (R4).

Befund 2026-08-14: `QTabWidget(tabsClosable=True)` im Konstruktor liess Qt schon
fuer den ersten Tab einen Schliessen-Knopf anlegen. `_update_tab_closable_state()`
schaltet `tabsClosable` bei nur einem Board wieder ab, doch dieser eine Knopf
blieb als Kind der Tab-Leiste an fester Position (x=71) liegen. Sobald ein
zweites Board dazukam, zeichnete Qt die regulaeren Knoepfe zusaetzlich -- der
Alt-Knopf lag dann ueber der Beschriftung des Nachbartabs. Im Store-Screenshot
vom 2026-08-14 war das sichtbar: der Tab "data" erschien als "Xata".

Der Test misst die tatsaechlich sichtbaren Knoepfe der Tab-Leiste gegen die per
`tabButton()` einem Tab zugeordneten. Die Differenz muss leer sein.

Bewusst mit nativem Qt-Plattform-Plugin: Unter `offscreen` tritt der Defekt
nicht auf (dort war kein Knopf sichtbar), er waere also nicht nachweisbar.
"""
import os
import sys
import tempfile
from pathlib import Path

import pytest

from PySide6 import QtCore, QtWidgets
from PySide6.QtWidgets import QAbstractButton, QTabBar

_HEADLESS = {"offscreen", "minimal", "vnc"}


def _native_gui_available() -> bool:
    app = QtWidgets.QApplication.instance()
    if app is not None:
        return app.platformName() not in _HEADLESS
    return sys.platform.startswith("win") or sys.platform == "darwin"


pytestmark = pytest.mark.skipif(
    not _native_gui_available(),
    reason="Der Defekt ist nur mit nativem Qt-Plattform-Plugin messbar.",
)


def _visible_orphan_buttons(window) -> list[QAbstractButton]:
    """Sichtbare Knoepfe der Tab-Leiste, die zu keinem Tab gehoeren."""
    tab_bar = window.tabs.tabBar()
    assigned: set[int] = set()
    for index in range(window.tabs.count()):
        for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
            button = tab_bar.tabButton(index, side)
            if button is not None:
                assigned.add(id(button))
    visible = [
        child
        for child in tab_bar.children()
        if isinstance(child, QAbstractButton) and child.isVisible()
    ]
    return [button for button in visible if id(button) not in assigned]


@pytest.fixture(scope="module")
def _app():
    os.environ.setdefault("QT_SCALE_FACTOR", "1")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def _window(_app):
    import SoftwareCenter as sc

    tmp = Path(tempfile.mkdtemp())
    settings = QtCore.QSettings(str(tmp / "s.ini"), QtCore.QSettings.Format.IniFormat)
    window = sc.MainWindow(settings=settings)
    # Unsichtbar rendern: die Tab-Leiste braucht ein Layout, aber kein Fenster
    # auf dem Desktop (gleiches Vorgehen wie im Screenshot-Generator).
    window.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
    window.resize(1440, 900)
    window.show()
    return window


def test_single_board_has_no_visible_close_button(_app):
    window = _window(_app)
    assert window.tabs.count() == 1
    assert window.tabs.tabsClosable() is False
    assert _visible_orphan_buttons(window) == []


def test_no_orphan_button_after_adding_boards(_app):
    window = _window(_app)
    for name, view in (("data", "tiles"), ("office", "tiles"), ("web", "tiles")):
        window.add_new_tab(name, view, entries=[])
    _app.processEvents()

    assert window.tabs.count() == 4
    assert window.tabs.tabsClosable() is True
    orphans = _visible_orphan_buttons(window)
    assert orphans == [], (
        f"{len(orphans)} verwaiste(r) Schliessen-Knopf/Knoepfe an Position(en) "
        f"{[(b.x(), b.y()) for b in orphans]}"
    )


def test_no_orphan_button_after_closing_back_to_one_board(_app):
    """Auch der Rueckweg darf nichts liegen lassen."""
    window = _window(_app)
    window.add_new_tab("zweitboard", "tiles", entries=[])
    _app.processEvents()
    window.on_close_tab(1)
    _app.processEvents()

    assert window.tabs.count() == 1
    assert _visible_orphan_buttons(window) == []


def test_every_close_button_stays_inside_its_own_tab(_app):
    """Kein Knopf darf in die Beschriftung eines Nachbartabs ragen."""
    window = _window(_app)
    for name, view in (("data", "tiles"), ("office", "tiles"), ("Production", "tiles")):
        window.add_new_tab(name, view, entries=[])
    _app.processEvents()

    tab_bar = window.tabs.tabBar()
    for index in range(window.tabs.count()):
        rect = tab_bar.tabRect(index)
        for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
            button = tab_bar.tabButton(index, side)
            if button is None:
                continue
            assert rect.x() <= button.x(), (
                f"Knopf von Tab {index} beginnt links ausserhalb des Tabs"
            )
            assert button.x() + button.width() <= rect.x() + rect.width(), (
                f"Knopf von Tab {index} ragt rechts aus dem Tab heraus"
            )
