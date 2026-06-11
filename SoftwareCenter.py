# -*- coding: utf-8 -*-
"""SoftwareCenter - Desktop-Organizer für Software-Verknüpfungen."""

__version__ = "1.0.0"

import configparser
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from PySide6.QtCore import Qt, QSize, QFileInfo, Signal, QSettings
from PySide6.QtGui import QAction, QActionGroup, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QListWidget,
    QListWidgetItem, QTabWidget, QFileIconProvider, QToolBar, QInputDialog,
    QMessageBox, QMenu, QFileDialog
)

PROFILE_FORMAT = "softwarecenter-profile-v1"
PROFILE_FORMAT_VERSION = 1
ENTRY_METADATA_ROLE = Qt.UserRole + 1
DESKTOP_FIELD_CODES = set("fFuUicck")

def is_linux_desktop_entry(path: str) -> bool:
    return sys.platform.startswith("linux") and os.path.isfile(path) and path.lower().endswith(".desktop")

def read_desktop_entry(path: str) -> dict[str, str]:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.optionxform = str
    try:
        with open(path, "r", encoding="utf-8") as handle:
            parser.read_file(handle)
    except (OSError, configparser.Error, UnicodeDecodeError):
        return {}
    if not parser.has_section("Desktop Entry"):
        return {}
    return {key: value for key, value in parser.items("Desktop Entry")}

def desktop_entry_display_name(path: str) -> str | None:
    entry = read_desktop_entry(path)
    if not entry:
        return None

    for key in ("Name[de_DE]", "Name[de]", "Name"):
        value = entry.get(key)
        if value:
            return value.strip()
    return None

def desktop_entry_icon(path: str) -> QIcon | None:
    entry = read_desktop_entry(path)
    icon_name = entry.get("Icon", "").strip()
    if not icon_name:
        return None

    if os.path.isabs(icon_name) and os.path.exists(icon_name):
        return QIcon(icon_name)

    icon = QIcon.fromTheme(icon_name)
    if not icon.isNull():
        return icon
    return None

def desktop_entry_exec_command(path: str) -> list[str] | None:
    entry = read_desktop_entry(path)
    exec_line = entry.get("Exec", "").strip()
    if not exec_line:
        return None

    cleaned = []
    for token in shlex.split(exec_line, posix=True):
        normalized_token = _sanitize_desktop_exec_token(token)
        if normalized_token:
            cleaned.append(normalized_token)
    return cleaned or None

def _sanitize_desktop_exec_token(token: str) -> str | None:
    if "%" not in token:
        return token

    normalized = []
    saw_field_code = False
    index = 0
    while index < len(token):
        char = token[index]
        if char != "%":
            normalized.append(char)
            index += 1
            continue

        if index + 1 >= len(token):
            normalized.append(char)
            index += 1
            continue

        code = token[index + 1]
        if code == "%":
            normalized.append("%")
            index += 2
            continue

        if code in DESKTOP_FIELD_CODES:
            saw_field_code = True
            index += 2
            continue

        normalized.append(char)
        index += 1

    sanitized = "".join(normalized).strip()
    if not sanitized:
        return None

    # SoftwareCenter startet Desktop-Dateien ohne Datei-/URL-Kontext.
    # Argumente mit Desktop-Feldcodes werden deshalb komplett verworfen.
    if saw_field_code and sanitized != token:
        return None
    return sanitized

def is_supported_launch_target(path: str) -> bool:
    if os.path.isfile(path):
        return True
    return sys.platform == "darwin" and path.lower().endswith(".app") and os.path.isdir(path)

def default_entry_label(path: str) -> str:
    name = desktop_entry_display_name(path) if is_linux_desktop_entry(path) else None
    if name:
        return name
    basename = os.path.basename(path.rstrip("\\/"))
    label, _ext = os.path.splitext(basename)
    return label or basename or path

def detect_entry_kind(path: str) -> str:
    lower_path = path.lower()
    if lower_path.endswith(".url"):
        return "url"
    if lower_path.endswith(".lnk"):
        return "windows_shortcut"
    if lower_path.endswith(".app"):
        return "mac_app"
    if lower_path.endswith(".desktop"):
        return "linux_desktop"
    if lower_path.endswith((".bat", ".cmd", ".ps1", ".sh", ".py")):
        return "script"
    if os.path.isfile(path):
        return "file"
    return "unknown"

def normalize_entry(entry: str | dict) -> dict | None:
    if isinstance(entry, str):
        path = entry.strip()
        label = None
        kind = None
        notes = None
    elif isinstance(entry, dict):
        raw_path = entry.get("path", "")
        path = raw_path.strip() if isinstance(raw_path, str) else str(raw_path).strip()
        label = entry.get("label")
        kind = entry.get("kind")
        notes = entry.get("notes")
    else:
        return None

    if not path:
        return None

    if label is not None:
        label = str(label).strip() or None
    if kind is not None:
        kind = str(kind).strip() or None
    if notes is not None:
        notes = str(notes).strip() or None

    return {
        "path": path,
        "label": label or default_entry_label(path),
        "kind": kind or detect_entry_kind(path),
        "notes": notes,
    }

def profile_export_data(window: "MainWindow") -> dict:
    tabs = []
    for index in range(window.tabs.count()):
        page = window.tabs.widget(index)
        tabs.append(
            {
                "name": window.tabs.tabText(index),
                "view_mode": page.view_mode,
                "entries": page.list.get_all_entries(),
            }
        )
    return {
        "format": PROFILE_FORMAT,
        "format_version": PROFILE_FORMAT_VERSION,
        "app_version": __version__,
        "source_platform": sys.platform,
        "exported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "current_tab": max(window.tabs.currentIndex(), 0),
        "tabs": tabs,
    }

def validate_profile_payload(payload: dict) -> list[dict]:
    if not isinstance(payload, dict):
        raise ValueError("Das Profil ist kein JSON-Objekt.")

    payload_format = payload.get("format")
    payload_version = payload.get("format_version")
    if payload_format != PROFILE_FORMAT or payload_version != PROFILE_FORMAT_VERSION:
        raise ValueError("Unbekanntes Profilformat.")

    raw_tabs = payload.get("tabs")
    if not isinstance(raw_tabs, list) or not raw_tabs:
        raise ValueError("Das Profil enthält keine Tabs.")

    tabs = []
    for raw_tab in raw_tabs:
        if not isinstance(raw_tab, dict):
            continue
        name = str(raw_tab.get("name") or "Tab").strip() or "Tab"
        view_mode = "list" if str(raw_tab.get("view_mode")).strip().lower() == "list" else "tiles"
        entries = []
        raw_entries = raw_tab.get("entries", [])
        if not isinstance(raw_entries, list):
            raw_entries = []
        for raw_entry in raw_entries:
            normalized = normalize_entry(raw_entry)
            if normalized:
                entries.append(normalized)
        tabs.append({"name": name, "view_mode": view_mode, "entries": entries})

    if not tabs:
        raise ValueError("Das Profil enthält keine lesbaren Tabs.")
    return tabs

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
            if is_linux_desktop_entry(path):
                command = desktop_entry_exec_command(path)
                if command:
                    subprocess.Popen(command)
                else:
                    subprocess.Popen(["xdg-open", path])
            elif os.access(path, os.X_OK):
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
        self.add_entries(paths)

    def add_entries(self, entries: list[str | dict]):
        for entry in entries:
            normalized = normalize_entry(entry)
            if not normalized:
                continue
            if isinstance(entry, str) and not is_supported_launch_target(normalized["path"]):
                continue
            if self._has_path(normalized["path"]):
                continue
            self._add_item(normalized)

    def _has_path(self, path: str) -> bool:
        for i in range(self.count()):
            it = self.item(i)
            if it.data(Qt.UserRole) == path:
                return True
        return False

    def _add_item(self, entry: dict):
        path = entry["path"]
        info = QFileInfo(path)
        icon = desktop_entry_icon(path) if is_linux_desktop_entry(path) else None
        if icon is None or icon.isNull():
            icon = self._icon_provider.icon(info)
        name = entry["label"]
        item = QListWidgetItem(icon, name)
        notes = entry.get("notes")
        item.setToolTip(f"{path}\n\nNotizen: {notes}" if notes else path)
        item.setData(Qt.UserRole, path)
        item.setData(ENTRY_METADATA_ROLE, entry)
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

    def get_all_entries(self) -> list[dict]:
        entries = []
        for i in range(self.count()):
            item = self.item(i)
            metadata = item.data(ENTRY_METADATA_ROLE)
            if isinstance(metadata, dict):
                entries.append(normalize_entry(metadata))
            else:
                entries.append(
                    normalize_entry(
                        {
                            "path": item.data(Qt.UserRole),
                            "label": item.text(),
                            "kind": detect_entry_kind(item.data(Qt.UserRole)),
                            "notes": None,
                        }
                    )
                )
        return [entry for entry in entries if entry]

    def set_all_paths(self, paths: list[str]):
        self.add_entries(paths)

    def set_all_entries(self, entries: list[str | dict]):
        self.add_entries(entries)

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

    def add_entries(self, entries: list[str | dict]):
        self.list.add_entries(entries)

    def on_request_delete(self, paths: list[str]):
        if not paths:
            return
        if len(paths) == 1:
            msg = f"Diese Verknüpfung entfernen?\n\n{paths[0]}"
        else:
            msg = f"{len(paths)} Verknüpfungen aus dieser Ansicht entfernen?"
        ret = QMessageBox.question(self, "Löschen bestätigen", msg)
        if ret == QMessageBox.StandardButton.Yes:
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
        self._build_menu()
        self._build_toolbar()
        self.load_settings()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Datei")
        self.act_export_profile = QAction("Profil exportieren", self)
        self.act_import_profile = QAction("Profil importieren", self)
        self.act_export_profile.triggered.connect(self.export_profile)
        self.act_import_profile.triggered.connect(self.import_profile)
        file_menu.addAction(self.act_export_profile)
        file_menu.addAction(self.act_import_profile)

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
        tb.addSeparator()
        tb.addAction(self.act_export_profile)
        tb.addAction(self.act_import_profile)

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

    def _update_tab_closable_state(self):
        self.tabs.setTabsClosable(self.tabs.count() > 1)

    def add_new_tab(self, name: str | None = None, view_mode="tiles", paths=None, entries=None):
        page = TabPage()
        page.set_view_mode(view_mode)
        if entries:
            page.list.set_all_entries(entries)
        elif paths:
            page.list.set_all_paths(paths)
        idx = self.tabs.addTab(page, name or "Neuer Tab")
        self._update_tab_closable_state()
        self.tabs.setCurrentIndex(idx)

    def export_profile(self):
        default_name = os.path.join(os.path.expanduser("~"), f"{PROFILE_FORMAT}.json")
        target, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Profil exportieren",
            default_name,
            "JSON-Dateien (*.json)",
        )
        if not target:
            return
        try:
            with open(target, "w", encoding="utf-8") as handle:
                json.dump(profile_export_data(self), handle, ensure_ascii=False, indent=2)
                handle.write("\n")
        except OSError as exc:
            QMessageBox.critical(self, "Export fehlgeschlagen", f"Profil konnte nicht gespeichert werden:\n{exc}")
            return
        QMessageBox.information(self, "Export abgeschlossen", f"Profil gespeichert:\n{target}")

    def import_profile(self):
        source, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Profil importieren",
            "",
            "JSON-Dateien (*.json)",
        )
        if not source:
            return
        replace = QMessageBox.question(
            self,
            "Profil importieren",
            "Das aktuelle Profil wird durch den Import ersetzt. Fortfahren?",
        )
        if replace != QMessageBox.StandardButton.Yes:
            return
        try:
            with open(source, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.apply_profile_payload(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            QMessageBox.critical(self, "Import fehlgeschlagen", f"Profil konnte nicht importiert werden:\n{exc}")
            return
        QMessageBox.information(self, "Import abgeschlossen", f"Profil geladen:\n{source}")

    def apply_profile_payload(self, payload: dict):
        tabs = validate_profile_payload(payload)
        current_tab = payload.get("current_tab", 0)
        if not isinstance(current_tab, int):
            try:
                current_tab = int(current_tab)
            except (TypeError, ValueError):
                current_tab = 0

        self.tabs.clear()
        for tab in tabs:
            self.add_new_tab(tab["name"], tab["view_mode"], entries=tab["entries"])

        if 0 <= current_tab < self.tabs.count():
            self.tabs.setCurrentIndex(current_tab)
        elif self.tabs.count() > 0:
            self.tabs.setCurrentIndex(0)

        self._sync_view_actions()
        self.save_settings()

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
        self._update_tab_closable_state()
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
            settings.setValue("entries_json", json.dumps(page.list.get_all_entries(), ensure_ascii=False))
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
                entries_json = settings.value("entries_json", "")
                paths = settings.value("paths", [])
                entries = []
                if isinstance(entries_json, str) and entries_json.strip():
                    try:
                        loaded_entries = json.loads(entries_json)
                    except json.JSONDecodeError:
                        loaded_entries = []
                    if isinstance(loaded_entries, list):
                        entries = loaded_entries
                if isinstance(paths, str):  # falls als einzelner String gespeichert
                    paths = [paths]
                self.add_new_tab(name, view_mode, paths=paths, entries=entries)
            if isinstance(current_tab, int) and 0 <= current_tab < self.tabs.count():
                self.tabs.setCurrentIndex(current_tab)
            elif self.tabs.count() > 0:
                self.tabs.setCurrentIndex(0)
        else:
            self.add_new_tab("Allgemein")
        settings.endArray()
        self._update_tab_closable_state()
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
