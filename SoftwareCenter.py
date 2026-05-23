# -*- coding: utf-8 -*-
"""SoftwareCenter - Desktop-Organizer für Software-Verknüpfungen."""

__version__ = "1.0.0"

import os
import sys
import platform
import subprocess
from PySide6.QtCore import Qt, QSize, QUrl, QFileInfo, Signal, QSettings
from PySide6.QtGui import QAction, QActionGroup, QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget,
    QListWidgetItem, QTabWidget, QFileIconProvider, QToolBar, QInputDialog,
    QMessageBox, QMenu
)

def is_supported_launch_target(path: str) -> bool:
    if os.path.isfile(path):
        return True
    return sys.platform == "darwin" and path.lower().endswith(".app") and os.path.isdir(path)

def open_file(path: str) -> None:
    if not os.path.exists(path):
        QMessageBox.warning(None, "Datei nicht gefunden", f"Pfad existiert nicht:\n{path}")
        return
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            if os.access(path, os.X_OK):
                subprocess.Popen([path])
            else:
                subprocess.Popen(["xdg-open", path])
    except Exception as e:
        QMessageBox.critical(None, "Fehler beim Starten", f"Konnte nicht starten:\n{path}\n\n{e}")

class SoftwareListWidget(QListWidget):
    requestDelete = Signal(list)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.itemActivated.connect(self._on_item_activated)
        self._icon_provider = QFileIconProvider()
        self.configure_as_tiles()

    def configure_as_tiles(self):
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setWrapping(True)
        self.setIconSize(QSize(64, 64))
        self.setGridSize(QSize(110, 100))
        self.setSpacing(8)
        self.setUniformItemSizes(False)

    def configure_as_list(self):
        self.setViewMode(QListWidget.ListMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setWrapping(False)
        self.setIconSize(QSize(24, 24))
        self.setGridSize(QSize())
        self.setSpacing(2)
        self.setUniformItemSizes(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return
        paths = []
        for url in urls:
            if url.isLocalFile():
                p = url.toLocalFile()
                if is_supported_launch_target(p):
                    paths.append(p)
        if paths:
            self.add_paths(paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_context_menu(self, pos):
        menu = QMenu(self)
        act_open = menu.addAction("Öffnen/Starten")
        act_del = menu.addAction("Löschen")
        global_pos = self.viewport().mapToGlobal(pos)
        action = menu.exec(global_pos)
        if action == act_open:
            for item in self.selectedItems():
                path = item.data(Qt.UserRole)
                open_file(path)
        elif action == act_del:
            paths = [it.data(Qt.UserRole) for it in self.selectedItems()]
            if paths:
                self.requestDelete.emit(paths)

    def _on_item_activated(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        open_file(path)

    def add_paths(self, paths: list[str]):
        for path in paths:
            if not is_supported_launch_target(path) or self._has_path(path):
                continue
            self._add_item(path)

    def _has_path(self, path: str) -> bool:
        for i in range(self.count()):
            it = self.item(i)
            if it.data(Qt.UserRole) == path:
                return True
        return False

    def _add_item(self, path: str):
        info = QFileInfo(path)
        icon = self._icon_provider.icon(info)
        name = os.path.splitext(os.path.basename(path))[0]
        item = QListWidgetItem(icon, name)
        item.setToolTip(path)
        item.setData(Qt.UserRole, path)
        self.addItem(item)

    def remove_paths(self, paths: list[str]):
        to_remove = set(paths)
        i = 0
        while i < self.count():
            it = self.item(i)
            if it.data(Qt.UserRole) in to_remove:
                self.takeItem(i)
            else:
                i += 1

    def get_all_paths(self) -> list[str]:
        return [self.item(i).data(Qt.UserRole) for i in range(self.count())]

    def set_all_paths(self, paths: list[str]):
        for p in paths:
            if os.path.exists(p):
                self._add_item(p)

class TabPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view_mode = "tiles"
        self.list = SoftwareListWidget()
        self.list.requestDelete.connect(self.on_request_delete)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.addWidget(self.list)

    def set_view_mode(self, mode: str):
        if mode == "tiles":
            self.list.configure_as_tiles()
            self.view_mode = "tiles"
        else:
            self.list.configure_as_list()
            self.view_mode = "list"

    def add_paths(self, paths: list[str]):
        self.list.add_paths(paths)

    def on_request_delete(self, paths: list[str]):
        if not paths:
            return
        if len(paths) == 1:
            msg = f"Diese Verknüpfung entfernen?\n\n{paths[0]}"
        else:
            msg = f"{len(paths)} Verknüpfungen aus dieser Ansicht entfernen?"
        ret = QMessageBox.question(self, "Löschen bestätigen", msg)
        if ret == QMessageBox.Yes:
            self.list.remove_paths(paths)

class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None):
        super().__init__()
        self.setWindowTitle("SoftwareCenter")
        self.resize(1000, 640)
        self.setAcceptDrops(True)
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.settings = settings or QSettings("LukasGeiger", "SoftwareCenter")
        self.tabs = QTabWidget(movable=True, tabsClosable=True)
        self.tabs.tabCloseRequested.connect(self.on_close_tab)
        self.tabs.tabBarDoubleClicked.connect(self.on_rename_tab)
        self.tabs.currentChanged.connect(self._sync_view_actions)
        self.setCentralWidget(self.tabs)
        self._build_toolbar()
        self.load_settings()

    def _build_toolbar(self):
        tb = QToolBar("Hauptleiste")
        tb.setMovable(False)
        self.addToolBar(tb)
        act_new_tab = QAction("Neuer Tab", self)
        act_new_tab.triggered.connect(self.on_new_tab)
        tb.addAction(act_new_tab)
        act_rename_tab = QAction("Tab umbenennen", self)
        act_rename_tab.triggered.connect(self.on_rename_tab_action)
        tb.addAction(act_rename_tab)
        tb.addSeparator()
        self.view_group = QActionGroup(self)
        self.view_group.setExclusive(True)
        self.act_view_tiles = QAction("Kacheln", self, checkable=True)
        self.act_view_list = QAction("Liste", self, checkable=True)
        self.view_group.addAction(self.act_view_tiles)
        self.view_group.addAction(self.act_view_list)
        self.act_view_tiles.setChecked(True)
        self.act_view_tiles.triggered.connect(lambda: self.set_current_view("tiles"))
        self.act_view_list.triggered.connect(lambda: self.set_current_view("list"))
        tb.addAction(self.act_view_tiles)
        tb.addAction(self.act_view_list)

    def current_page(self) -> TabPage | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, TabPage) else None

    def _sync_view_actions(self, index: int | None = None):
        page = self.current_page()
        if not page:
            return

        is_tiles = page.view_mode == "tiles"
        self.act_view_tiles.blockSignals(True)
        self.act_view_list.blockSignals(True)
        try:
            self.act_view_tiles.setChecked(is_tiles)
            self.act_view_list.setChecked(not is_tiles)
        finally:
            self.act_view_tiles.blockSignals(False)
            self.act_view_list.blockSignals(False)

    def add_new_tab(self, name: str | None = None, view_mode="tiles", paths=None):
        page = TabPage()
        page.set_view_mode(view_mode)
        if paths:
            page.list.set_all_paths(paths)
        idx = self.tabs.addTab(page, name or "Neuer Tab")
        self.tabs.setCurrentIndex(idx)

    def on_new_tab(self):
        name, ok = QInputDialog.getText(self, "Neuer Tab", "Tab-Name:")
        if ok:
            name = name.strip() or "Neuer Tab"
            self.add_new_tab(name)
            self.save_settings()  # BUG 6: Settings nach Tab-Erstellung sofort speichern

    def on_rename_tab(self, index: int):
        if index < 0:
            return
        current_name = self.tabs.tabText(index)
        name, ok = QInputDialog.getText(self, "Tab umbenennen", "Neuer Tab-Name:", text=current_name)
        if ok:
            name = name.strip() or current_name
            self.tabs.setTabText(index, name)
            self.save_settings()  # BUG 6: Settings nach Umbenennung sofort speichern

    def on_rename_tab_action(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.on_rename_tab(idx)

    def on_close_tab(self, index: int):
        if self.tabs.count() == 1:
            QMessageBox.information(self, "Nicht möglich", "Der letzte Tab kann nicht geschlossen werden.")
            return
        self.tabs.removeTab(index)
        self.save_settings()  # BUG 6: Settings nach Tab-Schließen sofort speichern

    def set_current_view(self, mode: str):
        page = self.current_page()
        if not page:
            return
        page.set_view_mode(mode)
        self._sync_view_actions()
        self.save_settings()

    # ----- Speicherfunktion -----
    def save_settings(self):
        settings = self.settings
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("current_tab", self.tabs.currentIndex())
        settings.beginWriteArray("tabs")
        for i in range(self.tabs.count()):
            settings.setArrayIndex(i)
            page = self.tabs.widget(i)
            settings.setValue("name", self.tabs.tabText(i))
            settings.setValue("view_mode", page.view_mode)
            settings.setValue("paths", page.list.get_all_paths())
        settings.endArray()

    def load_settings(self):
        settings = self.settings
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))
        current_tab = settings.value("current_tab", -1)
        if isinstance(current_tab, str):
            try:
                current_tab = int(current_tab)
            except ValueError:
                current_tab = -1

        size = settings.beginReadArray("tabs")
        if size > 0:
            self.tabs.clear()
            for i in range(size):
                settings.setArrayIndex(i)
                name = settings.value("name", "Tab")
                view_mode = settings.value("view_mode", "tiles")
                paths = settings.value("paths", [])
                if isinstance(paths, str):  # falls als einzelner String gespeichert
                    paths = [paths]
                self.add_new_tab(name, view_mode, paths)
            if isinstance(current_tab, int) and 0 <= current_tab < self.tabs.count():
                self.tabs.setCurrentIndex(current_tab)
            elif self.tabs.count() > 0:
                self.tabs.setCurrentIndex(0)
        else:
            self.add_new_tab("Allgemein")
        settings.endArray()
        self._sync_view_actions()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    # ----- Drag & Drop im Hauptfenster -----
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = []
        for url in urls:
            if url.isLocalFile():
                p = url.toLocalFile()
                if is_supported_launch_target(p):
                    paths.append(p)
        if paths:
            page = self.current_page()
            if page:
                page.add_paths(paths)
            self.save_settings()
            event.acceptProposedAction()
        else:
            event.ignore()

def main():
    app = QApplication(sys.argv)
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
