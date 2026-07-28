# -*- coding: utf-8 -*-
"""SoftwareCenter - Desktop-Organizer für Software-Verknüpfungen."""

__version__ = "1.0.0"

import configparser
import json
import os
import shlex
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from PySide6.QtCore import Qt, QSize, QFileInfo, Signal, QSettings, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDockWidget, QMainWindow, QPushButton, QSizePolicy,
    QStyle, QWidget, QVBoxLayout, QListWidget,
    QListWidgetItem, QTabWidget, QFileIconProvider, QToolBar, QInputDialog,
    QMessageBox, QMenu, QFileDialog, QSystemTrayIcon, QTabBar, QLineEdit, QWidgetAction
)
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from dataclasses import dataclass

_USER_SUFFIX = os.environ.get("USERNAME") or "user"


@dataclass(frozen=True)
class AppProfile:
    """Produkt-Profil: mehrere Produkte aus EINEM Code (SoftwareCenter, LaunchBoards).

    Jedes Produkt hat eigenen Namen, Icon, QSettings-Namespace und Single-Instance,
    damit beide parallel und mit getrennten Profilen laufen können.
    """
    name: str          # Fenstertitel / Tray-Tooltip / Tray-Meldungen
    settings_app: str  # QSettings-AppName (eigenes Profil je Produkt)
    icon_file: str     # Icon-Dateiname relativ zum Skript
    instance_id: str   # Single-Instance-Servername


PROFILE_SOFTWARECENTER = AppProfile(
    "SoftwareCenter", "SoftwareCenter", "icon.ico", "SoftwareCenter_singleton_" + _USER_SUFFIX)
PROFILE_LAUNCHBOARDS = AppProfile(
    "LaunchBoards", "LaunchBoards", "launchboards.ico", "LaunchBoards_singleton_" + _USER_SUFFIX)

PROFILE_FORMAT = "softwarecenter-profile-v1"
PROFILE_FORMAT_VERSION = 1
ENTRY_METADATA_ROLE = Qt.ItemDataRole.UserRole + 1
DESKTOP_FIELD_CODES = set("fFuUicck")

# Tray-Verfuegbarkeits-Retry (T-20260721-02): manche Umgebungen (z.B. Explorer-Neustart
# beim Login) melden den Tray kurzzeitig als nicht verfuegbar -- lieber ein paar Sekunden
# nachfragen als sofort dauerhaft aufzugeben.
TRAY_RETRY_INTERVAL_MS = 1500
TRAY_RETRY_MAX_ATTEMPTS = 5

# Tray-Navigation (T-20260721-03): Grenzen, damit das Tray-Menue nicht unbounded waechst.
TRAY_ENTRY_LIMIT_PER_BOARD = 10
TRAY_STAGE2_MAX_BOARDS = 20
TRAY_SEARCH_RESULT_LIMIT = 15


def resource_path(filename: str) -> str:
    """Loest einen mitgelieferten Ressourcenpfad (Icons etc.) robust auf.

    Im PyInstaller-Onefile-Build entpackt der Bootloader ueber `--add-data` gebuendelte
    Dateien zur Laufzeit nach `sys._MEIPASS`; im Sourcelauf liegt die Datei einfach neben
    diesem Skript. Ohne diese Unterscheidung wuerde das Tray-Icon in der gefrorenen EXE
    einen Pfad relativ zum (fluechtigen) Skriptort suchen, der dort nicht existiert."""
    base_dir = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def _tray_match_score(query: str, text: str) -> int | None:
    """Einfaches Praefix-Ranking fuer die Tray-Suche: 0=exakt, 1=Praefix, 2=Substring, sonst None."""
    text_cf = (text or "").casefold()
    if text_cf == query:
        return 0
    if text_cf.startswith(query):
        return 1
    if query in text_cf:
        return 2
    return None


def iso_now() -> str:
    """UTC-Zeitstempel im ISO-8601-Format (z.B. fuer `closed_at`, Profil-Export)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_board_id() -> str:
    """Neue, stabile Board-Identitaet (ueberlebt Schliessen/Reaktivieren/Neustart)."""
    return uuid.uuid4().hex


def _settings_bool(value) -> bool:
    """QSettings liefert Bools je nach Backend als str oder bool zurueck -- vereinheitlichen."""
    return str(value).strip().lower() in ("true", "1", "yes")


def _parse_entries_json(value) -> list[dict]:
    if isinstance(value, str) and value.strip():
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            loaded = []
        if isinstance(loaded, list):
            return loaded
    return []


def sort_boards_history(boards: list[dict]) -> list[dict]:
    """Verlaufs-Sortierung: zuletzt geschlossenes Board zuerst, danach aktive Boards.

    Wird ein Board erneut geschlossen, ueberschreibt das denselben Datensatz
    (gleiche `id`) -- dadurch entsteht nie ein Duplikat, es wandert nur nach oben."""
    closed = sorted((b for b in boards if b.get("closed_at")), key=lambda b: b["closed_at"], reverse=True)
    active = [b for b in boards if not b.get("closed_at")]
    return closed + active


def sort_boards_alphabetical(boards: list[dict]) -> list[dict]:
    return sorted(boards, key=lambda b: (b.get("name") or "").casefold())

def is_windows_shortcut(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False
    return os.path.isfile(path) and path.lower().endswith(".lnk")

def is_linux_desktop_entry(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False
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
    if not isinstance(path, str) or not path:
        return False
    if os.path.isfile(path) or os.path.isdir(path):
        return True
    return False

def is_supported_windows_shortcut_target(path: str) -> bool:
    if not isinstance(path, str) or not path:
        return False
    if path.lower().endswith(".exe") and os.path.isfile(path):
        return True
    return os.path.isdir(path)

def resolve_windows_shortcut_target(path: str) -> str | None:
    if not sys.platform.startswith("win") or not is_windows_shortcut(path):
        return None

    target = _resolve_windows_shortcut_target_com(path) or _resolve_windows_shortcut_target_powershell(path)
    if not target:
        return None
    target = os.path.normpath(target.strip().strip('"'))
    if is_supported_windows_shortcut_target(target):
        return target
    return None

def _resolve_windows_shortcut_target_com(path: str) -> str | None:
    try:
        import win32com.client  # type: ignore[import-not-found]

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(path)
        target = getattr(shortcut, "TargetPath", "")
    except Exception:
        return None
    return target.strip() or None

def _resolve_windows_shortcut_target_powershell(path: str) -> str | None:
    env = os.environ.copy()
    env["SOFTWARECENTER_SHORTCUT_PATH"] = path
    command = (
        "$ErrorActionPreference='Stop'; "
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
        "$shortcut=(New-Object -ComObject WScript.Shell)."
        "CreateShortcut($env:SOFTWARECENTER_SHORTCUT_PATH); "
        "$shortcut.TargetPath"
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=5,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None

def normalize_new_launch_path(path: str) -> str:
    return resolve_windows_shortcut_target(path) or path

def default_entry_label(path: str) -> str:
    if not isinstance(path, str) or not path:
        return ""
    name = desktop_entry_display_name(path) if is_linux_desktop_entry(path) else None
    if name:
        return name
    basename = os.path.basename(path.rstrip("\\/"))
    label, _ext = os.path.splitext(basename)
    return label or basename or path

def detect_entry_kind(path: str) -> str:
    if not isinstance(path, str) or not path:
        return "unknown"
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
    if os.path.isdir(path):
        return "directory"
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
        # BUGSWEEP-40: Nicht-String-Pfad (z.B. None aus manuell editiertem Profil) -> leer, damit der
        # `if not path: return None`-Guard greift; str(None) ergäbe sonst den Literal-String "None".
        path = raw_path.strip() if isinstance(raw_path, str) else ""
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
        "exported_at": iso_now(),
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

def _startfile_in_dir(path: str, workdir: str | None) -> None:
    """Startet eine Datei unter Windows mit gesetztem Arbeitsverzeichnis.

    Viele gebuendelte Apps suchen Ressourcen/Module relativ zum Arbeitsverzeichnis
    (cwd). Eine Desktop-Verknuepfung setzt dafuer "Ausfuehren in:"; os.startfile()
    erbt dagegen die cwd des SoftwareCenter-Prozesses, was solche Apps brechen kann.
    Daher hier explizit das Verzeichnis der Ziel-Datei als cwd setzen.
    """
    # Python 3.13+: os.startfile akzeptiert cwd direkt.
    try:
        os.startfile(path, cwd=workdir)  # type: ignore[call-arg]
        return
    except TypeError:
        pass  # aelteres Python ohne cwd-Parameter -> ShellExecuteW
    except OSError:
        raise
    import ctypes
    # ShellExecuteW(hwnd, lpVerb, lpFile, lpParameters, lpDirectory, nShowCmd)
    # lpDirectory = Arbeitsverzeichnis (wie "Ausfuehren in" einer Verknuepfung).
    rc = ctypes.windll.shell32.ShellExecuteW(None, None, path, None, workdir, 1)
    if rc <= 32:  # ShellExecute meldet Fehler als Wert <= 32
        os.startfile(path)  # letzter Fallback ohne Arbeitsverzeichnis


def open_file(path: str) -> None:
    if not os.path.exists(path):
        QMessageBox.warning(None, "Datei nicht gefunden", f"Pfad existiert nicht:\n{path}")
        return
    try:
        if sys.platform.startswith("win"):
            # Windows: Arbeitsverzeichnis = Ordner der Ziel-Datei (wie "Ausfuehren in"
            # einer Verknuepfung), damit Apps ihre Ressourcen relativ zur cwd finden.
            workdir = os.path.dirname(os.path.abspath(path)) or None
            _startfile_in_dir(path, workdir)
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
    # Transfer zwischen Boards (Tabs): jeweils (entries: list[dict], target_index: int)
    requestMoveToBoard = Signal(list, int)
    requestCopyToBoard = Signal(list, int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.itemActivated.connect(self._on_item_activated)
        self._icon_provider = QFileIconProvider()
        # Callable -> list[(index, name)] der ANDEREN Boards (ohne dieses).
        # Wird von MainWindow.add_new_tab gesetzt; ohne Provider bleiben die
        # Transfer-Submenues ausgeblendet (z. B. bei isolierter Nutzung in Tests).
        self.board_provider = None
        self.configure_as_tiles()

    def configure_as_tiles(self):
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.setWrapping(True)
        self.setIconSize(QSize(64, 64))
        self.setGridSize(QSize(110, 100))
        self.setSpacing(8)
        self.setUniformItemSizes(False)

    def configure_as_list(self):
        self.setViewMode(QListWidget.ViewMode.ListMode)
        self.setResizeMode(QListWidget.ResizeMode.Adjust)
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

        # "Senden an" (verschieben) / "Duplizieren auf" (kopieren) nur anbieten,
        # wenn etwas ausgewählt ist UND mindestens ein anderes Board existiert.
        move_actions: dict = {}
        copy_actions: dict = {}
        boards = self.board_provider() if callable(self.board_provider) else []
        if self.selectedItems() and boards:
            menu.addSeparator()
            move_menu = menu.addMenu("Senden an")
            copy_menu = menu.addMenu("Duplizieren auf")
            for index, name in boards:
                move_actions[move_menu.addAction(name)] = index
                copy_actions[copy_menu.addAction(name)] = index

        global_pos = self.viewport().mapToGlobal(pos)
        action = menu.exec(global_pos)
        if action is None:
            return
        if action == act_open:
            for item in self.selectedItems():
                path = item.data(Qt.ItemDataRole.UserRole)
                open_file(path)
        elif action == act_del:
            paths = [it.data(Qt.ItemDataRole.UserRole) for it in self.selectedItems()]
            if paths:
                self.requestDelete.emit(paths)
        elif action in move_actions:
            entries = self._selected_entries()
            if entries:
                self.requestMoveToBoard.emit(entries, move_actions[action])
        elif action in copy_actions:
            entries = self._selected_entries()
            if entries:
                self.requestCopyToBoard.emit(entries, copy_actions[action])

    def _selected_entries(self) -> list[dict]:
        """Vollständige Eintrags-Dicts (Pfad, Label, Typ, Notizen) der Auswahl.

        Spiegelt den Fallback aus get_all_entries(), falls ein Item kein
        ENTRY_METADATA_ROLE-Dict trägt (z. B. Alt-Daten)."""
        entries = []
        for item in self.selectedItems():
            metadata = item.data(ENTRY_METADATA_ROLE)
            if isinstance(metadata, dict):
                entries.append(normalize_entry(metadata))
            else:
                path = item.data(Qt.ItemDataRole.UserRole)
                entries.append(
                    normalize_entry(
                        {
                            "path": path,
                            "label": item.text(),
                            "kind": detect_entry_kind(path),
                            "notes": None,
                        }
                    )
                )
        return [entry for entry in entries if entry]

    def _on_item_activated(self, item: QListWidgetItem):
        path = item.data(Qt.ItemDataRole.UserRole)
        open_file(path)

    def add_paths(self, paths: list[str]):
        self.add_entries(paths)

    def add_entries(self, entries: list[str | dict]):
        for entry in entries:
            if isinstance(entry, str):
                original_entry = entry
                entry = normalize_new_launch_path(entry)
                if (
                    entry != original_entry
                    and is_windows_shortcut(original_entry)
                    and not is_supported_windows_shortcut_target(entry)
                ):
                    entry = original_entry
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
            if it.data(Qt.ItemDataRole.UserRole) == path:
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
        item.setData(Qt.ItemDataRole.UserRole, path)
        item.setData(ENTRY_METADATA_ROLE, entry)
        self.addItem(item)

    def remove_paths(self, paths: list[str]):
        to_remove = set(paths)
        i = 0
        while i < self.count():
            it = self.item(i)
            if it.data(Qt.ItemDataRole.UserRole) in to_remove:
                self.takeItem(i)
            else:
                i += 1

    def get_all_paths(self) -> list[str]:
        return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]

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
                            "path": item.data(Qt.ItemDataRole.UserRole),
                            "label": item.text(),
                            "kind": detect_entry_kind(item.data(Qt.ItemDataRole.UserRole)),
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

class BoardsPanel(QWidget):
    """Rechtes Seitenfenster: verwaltet ALLE Boards (aktiv + geschlossen).

    Zwei Ansichten als Reiter ("Verlauf"/"Alphabetisch"); im Simple Mode nur
    "Verlauf" ohne Favoriten. Die eigentliche Lebenszyklus-Logik (schliessen,
    reaktivieren, endgueltig loeschen, favorisieren) lebt bewusst auf
    MainWindow, damit sie unabhaengig von diesem Widget testbar bleibt.
    """
    def __init__(self, window: "MainWindow", parent=None):
        super().__init__(parent)
        self.window = window
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        self.view_tabs = QTabWidget()
        self.history_list = QListWidget()
        self.alpha_list = QListWidget()
        for lst in (self.history_list, self.alpha_list):
            lst.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            lst.customContextMenuRequested.connect(lambda pos, w=lst: self._on_context_menu(w, pos))
            lst.itemClicked.connect(self._on_item_activated)
            lst.itemActivated.connect(self._on_item_activated)
        self.history_tab_index = self.view_tabs.addTab(self.history_list, "Verlauf")
        self.alpha_tab_index = self.view_tabs.addTab(self.alpha_list, "Alphabetisch")
        self.view_tabs.currentChanged.connect(self._on_view_changed)
        layout.addWidget(self.view_tabs)

        self.clear_history_btn = QPushButton("Verlauf leeren")
        self.clear_history_btn.clicked.connect(lambda: self.window.clear_board_history())
        layout.addWidget(self.clear_history_btn)

    def refresh(self):
        simple = self.window._simple_mode_enabled()
        boards = self.window.all_boards_snapshot()

        # Simple Mode: nur der Verlauf-Reiter, kein zweiter Reiter, kein Favoriten-Menue.
        alpha_present = self.view_tabs.indexOf(self.alpha_list) != -1
        if simple and alpha_present:
            self.view_tabs.removeTab(self.view_tabs.indexOf(self.alpha_list))
        elif not simple and not alpha_present:
            self.view_tabs.addTab(self.alpha_list, "Alphabetisch")
        self.view_tabs.tabBar().setVisible(not simple)
        self.clear_history_btn.setVisible(simple)

        wanted_view = "history" if simple else self.window._boards_panel_view
        alpha_index = self.view_tabs.indexOf(self.alpha_list)
        target_index = alpha_index if (wanted_view == "alphabetical" and alpha_index != -1) else \
            self.view_tabs.indexOf(self.history_list)
        if target_index != -1 and self.view_tabs.currentIndex() != target_index:
            self.view_tabs.blockSignals(True)
            self.view_tabs.setCurrentIndex(target_index)
            self.view_tabs.blockSignals(False)

        self._populate(self.history_list, sort_boards_history(boards), simple)
        if not simple:
            self._populate(self.alpha_list, sort_boards_alphabetical(boards), simple)

    def _populate(self, list_widget: QListWidget, boards: list[dict], simple: bool):
        list_widget.clear()
        for board in boards:
            prefix = "★ " if (not simple and board["favorite"]) else ""
            item = QListWidgetItem(f"{prefix}{board['name']}")
            item.setData(Qt.ItemDataRole.UserRole, board["id"])
            if board["closed_at"]:
                item.setForeground(QColor(Qt.GlobalColor.gray))
                item.setToolTip(f"Geschlossen: {board['closed_at']}")
            else:
                item.setToolTip("Aktiv")
            list_widget.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem):
        board_id = item.data(Qt.ItemDataRole.UserRole)
        if board_id:
            self.window.activate_board(board_id)

    def _on_view_changed(self, index: int):
        widget = self.view_tabs.widget(index)
        mode = "alphabetical" if widget is self.alpha_list else "history"
        self.window._set_boards_panel_view(mode)

    def _on_context_menu(self, list_widget: QListWidget, pos):
        item = list_widget.itemAt(pos)
        if item is None:
            return
        board_id = item.data(Qt.ItemDataRole.UserRole)
        simple = self.window._simple_mode_enabled()
        menu = QMenu(self)
        act_fav = None
        if not simple:
            is_fav = board_id in self.window.favorites
            act_fav = menu.addAction("Favorit entfernen" if is_fav else "Favorit")
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        act_del = menu.addAction(icon, "Löschen")
        action = menu.exec(list_widget.viewport().mapToGlobal(pos))
        if action is None:
            return
        if act_fav is not None and action == act_fav:
            self.window.toggle_board_favorite(board_id)
        elif action == act_del:
            self.window.request_delete_board(board_id)

class MainWindow(QMainWindow):
    def __init__(self, settings: QSettings | None = None,
                 profile: AppProfile = PROFILE_SOFTWARECENTER):
        super().__init__()
        self.profile = profile
        self.setWindowTitle(profile.name)
        self.resize(1000, 640)
        self.setAcceptDrops(True)
        icon_path = resource_path(profile.icon_file)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.settings = settings or QSettings("LukasGeiger", profile.settings_app)
        # Board-Lebenszyklus: geschlossene Boards leben hier (id -> Board-Dict), aktive Boards
        # sind die aktuellen self.tabs-Seiten. Favoriten gelten fuer beide Gruppen gleichermassen.
        self.closed_boards: dict[str, dict] = {}
        self.favorites: set[str] = set()
        self._boards_panel_view = "history"
        self.tabs = QTabWidget(movable=True, tabsClosable=True)
        self.tabs.tabCloseRequested.connect(self.on_close_tab)
        self.tabs.tabBarDoubleClicked.connect(self.on_rename_tab)
        self.tabs.currentChanged.connect(self._sync_view_actions)
        self.setCentralWidget(self.tabs)
        self._force_quit = False
        self.tray = None
        self._tray_setup_token = 0
        self._tray_dynamic_actions: list = []
        self._tray_footer_marker = None
        self._build_menu()
        self._build_toolbar()
        self._build_boards_panel()
        self.load_settings()
        self._setup_tray()
        self._refresh_tab_accessibility()
        self._refresh_boards_panel()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Datei")
        self.act_export_profile = QAction("Profil exportieren", self)
        self.act_import_profile = QAction("Profil importieren", self)
        self.act_export_profile.triggered.connect(self.export_profile)
        self.act_import_profile.triggered.connect(self.import_profile)
        file_menu.addAction(self.act_export_profile)
        file_menu.addAction(self.act_import_profile)
        file_menu.addSeparator()
        # Systemtray-Einstellung: bei aktiviert wandert die App beim Schließen in den Tray.
        self.act_minimize_to_tray = QAction("Beim Schließen in Systemtray minimieren", self, checkable=True)
        self.act_minimize_to_tray.setChecked(self._tray_enabled())
        self.act_minimize_to_tray.toggled.connect(self._on_toggle_tray)
        file_menu.addAction(self.act_minimize_to_tray)
        # Simple Mode: Board-Panel zeigt nur den Verlauf, keine Favoriten (siehe BoardsPanel).
        self.act_simple_mode = QAction("Einfacher Modus (Board-Verlauf ohne Favoriten)", self, checkable=True)
        self.act_simple_mode.setChecked(self._simple_mode_enabled())
        self.act_simple_mode.toggled.connect(self._on_toggle_simple_mode)
        file_menu.addAction(self.act_simple_mode)
        file_menu.addSeparator()
        self.act_quit = QAction("Beenden", self)
        self.act_quit.triggered.connect(self.quit_app)
        file_menu.addAction(self.act_quit)

    def _build_toolbar(self):
        tb = QToolBar("Hauptleiste")
        # BUGSWEEP-40: objectName setzen — saveState()/restoreState() (unten genutzt) brauchen einen
        # eindeutigen objectName je Toolbar, sonst Qt-Warnung + windowState wird nicht zuverlässig restauriert.
        tb.setObjectName("Hauptleiste")
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
        # Spacer schiebt den Hamburger-Button (Board-Verwaltung) an den rechten Rand.
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb.addWidget(spacer)
        self.act_toggle_boards_panel = QAction("☰", self, checkable=True)
        self.act_toggle_boards_panel.setToolTip("Board-Verwaltung ein-/ausblenden")
        self.act_toggle_boards_panel.toggled.connect(self._on_toggle_boards_panel)
        tb.addAction(self.act_toggle_boards_panel)

    def _build_boards_panel(self):
        self.boards_dock = QDockWidget("Boards", self)
        self.boards_dock.setObjectName("BoardsDock")
        self.boards_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.boards_panel = BoardsPanel(self)
        self.boards_dock.setWidget(self.boards_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.boards_dock)
        self.boards_dock.setVisible(False)
        self.boards_dock.visibilityChanged.connect(self._on_boards_dock_visibility_changed)

    def _on_toggle_boards_panel(self, checked: bool):
        self.boards_dock.setVisible(checked)
        if checked:
            self._refresh_boards_panel()

    def _on_boards_dock_visibility_changed(self, visible: bool):
        self.act_toggle_boards_panel.blockSignals(True)
        self.act_toggle_boards_panel.setChecked(visible)
        self.act_toggle_boards_panel.blockSignals(False)

    def _refresh_boards_panel(self):
        if hasattr(self, "boards_panel"):
            self.boards_panel.refresh()

    def _set_boards_panel_view(self, mode: str):
        self._boards_panel_view = mode if mode in ("history", "alphabetical") else "history"
        self.settings.setValue("boards_panel_view", self._boards_panel_view)

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
        self._refresh_tab_accessibility()

    def _refresh_tab_accessibility(self):
        tab_bar = self.tabs.tabBar()
        tab_bar.setAccessibleName("Board-Leiste")
        tab_bar.setAccessibleDescription(
            "Wechselt zwischen Boards. Tabs lassen sich per Doppelklick umbenennen."
        )
        closable = self.tabs.tabsClosable() and self.tabs.count() > 1
        for index in range(self.tabs.count()):
            tab_name = self.tabs.tabText(index).strip() or f"Board {index + 1}"
            self.tabs.setTabToolTip(index, f'Board "{tab_name}"')
            for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
                button = tab_bar.tabButton(index, side)
                if button is None:
                    continue
                if closable:
                    button.setToolTip(f'Board "{tab_name}" schließen')
                    button.setAccessibleName(f'Board "{tab_name}" schließen')
                    button.setAccessibleDescription("Schließt dieses Board.")
                else:
                    button.setToolTip("")
                    button.setAccessibleName("")
                    button.setAccessibleDescription("")

    def add_new_tab(self, name: str | None = None, view_mode="tiles", paths=None, entries=None,
                     board_id: str | None = None):
        page = TabPage()
        # Feste Board-Identitaet: neu -> frische id; reaktiviert/geladen -> uebergebene id
        # bleibt erhalten, damit Verlauf/Favoriten dasselbe Board wiedererkennen.
        page.board_id = board_id or new_board_id()
        page.set_view_mode(view_mode)
        if entries:
            page.list.set_all_entries(entries)
        elif paths:
            page.list.set_all_paths(paths)
        # Board-Transfer verdrahten: Provider liefert zur Menü-Zeit die anderen
        # Boards, die Signale lösen Verschieben/Duplizieren aus.
        page.list.board_provider = self._board_provider_for(page)
        page.list.requestMoveToBoard.connect(
            lambda transfer, target_index, source=page: self.move_entries_to_board(source, transfer, target_index)
        )
        page.list.requestCopyToBoard.connect(self.copy_entries_to_board)
        idx = self.tabs.addTab(page, name or "Neuer Tab")
        self._update_tab_closable_state()
        self.tabs.setCurrentIndex(idx)
        self._refresh_tab_accessibility()
        self._refresh_boards_panel()

    def _board_provider_for(self, page: "TabPage"):
        """Closure: liefert zur Aufrufzeit (index, name) aller Boards außer `page`.

        Dynamisch, damit verschobene/umbenannte/geschlossene Tabs korrekt
        berücksichtigt werden."""
        def provider():
            result = []
            for i in range(self.tabs.count()):
                if self.tabs.widget(i) is page:
                    continue
                result.append((i, self.tabs.tabText(i)))
            return result
        return provider

    def move_entries_to_board(self, source_page: "TabPage", entries: list, target_index: int):
        target_page = self.tabs.widget(target_index)
        if not isinstance(target_page, TabPage) or target_page is source_page:
            return
        if not entries:
            return
        target_page.list.add_entries(entries)
        source_page.list.remove_paths([e["path"] for e in entries if isinstance(e, dict) and e.get("path")])
        self.save_settings()
        self._refresh_boards_panel()

    def copy_entries_to_board(self, entries: list, target_index: int):
        target_page = self.tabs.widget(target_index)
        if not isinstance(target_page, TabPage):
            return
        if not entries:
            return
        target_page.list.add_entries(entries)
        self.save_settings()
        self._refresh_boards_panel()

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
            self._refresh_tab_accessibility()
            self.save_settings()  # BUG 6: Settings nach Umbenennung sofort speichern
            self._refresh_boards_panel()

    def on_rename_tab_action(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.on_rename_tab(idx)

    def on_close_tab(self, index: int):
        """Schliesst ein Board: entfernt nur den Tab, die Daten bleiben im Verlauf erhalten.

        Feste Board-Identitaet (T-20260721-01): Name, Eintraege, Ansicht und Reihenfolge
        werden unveraendert unter derselben `board_id` in self.closed_boards abgelegt und
        `closed_at` gesetzt. Ein spaeteres Reaktivieren (siehe reactivate_board) stellt genau
        diesen Stand wieder her -- Schliessen loescht niemals Daten."""
        if self.tabs.count() == 1:
            QMessageBox.information(self, "Nicht möglich", "Der letzte Tab kann nicht geschlossen werden.")
            return
        page = self.tabs.widget(index)
        if isinstance(page, TabPage):
            board_id = getattr(page, "board_id", None) or new_board_id()
            self.closed_boards[board_id] = {
                "id": board_id,
                "name": self.tabs.tabText(index),
                "view_mode": page.view_mode,
                "entries": page.list.get_all_entries(),
                "closed_at": iso_now(),
            }
        self.tabs.removeTab(index)
        self._update_tab_closable_state()
        self.save_settings()  # BUG 6: Settings nach Tab-Schließen sofort speichern
        self._refresh_boards_panel()

    # ----- Board-Lebenszyklus (T-20260721-01) -----
    def all_boards_snapshot(self) -> list[dict]:
        """Einheitliche Sicht auf ALLE Boards (aktiv + geschlossen) fuer das Panel/Tests."""
        boards = []
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if not isinstance(page, TabPage):
                continue
            board_id = getattr(page, "board_id", None) or new_board_id()
            boards.append({
                "id": board_id,
                "name": self.tabs.tabText(i),
                "closed_at": "",
                "favorite": board_id in self.favorites,
                "entry_count": page.list.count(),
            })
        for board in self.closed_boards.values():
            boards.append({
                "id": board["id"],
                "name": board["name"],
                "closed_at": board["closed_at"],
                "favorite": board["id"] in self.favorites,
                "entry_count": len(board["entries"]),
            })
        return boards

    def _find_board(self, board_id: str) -> dict | None:
        for board in self.all_boards_snapshot():
            if board["id"] == board_id:
                return board
        return None

    def activate_board(self, board_id: str):
        """Wechselt zu einem aktiven Board oder reaktiviert es, falls geschlossen."""
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if isinstance(page, TabPage) and getattr(page, "board_id", None) == board_id:
                self.tabs.setCurrentIndex(i)
                return
        self.reactivate_board(board_id)

    def reactivate_board(self, board_id: str):
        """Stellt ein geschlossenes Board mit unveraenderter Identitaet als Tab wieder her."""
        board = self.closed_boards.pop(board_id, None)
        if board is None:
            return
        self.add_new_tab(board["name"], board["view_mode"], entries=board["entries"], board_id=board["id"])
        self.save_settings()
        self._refresh_boards_panel()

    def delete_board_permanently(self, board_id: str):
        """Loescht ein Board (aktiv oder geschlossen) endgueltig -- keine Wiederherstellung."""
        removed_active = False
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if isinstance(page, TabPage) and getattr(page, "board_id", None) == board_id:
                self.tabs.removeTab(i)
                removed_active = True
                break
        if not removed_active:
            self.closed_boards.pop(board_id, None)
        self.favorites.discard(board_id)
        if self.tabs.count() == 0:
            # Sicherheitsnetz: die App braucht immer mindestens ein aktives Board.
            self.add_new_tab("Allgemein")
        self._update_tab_closable_state()
        self.save_settings()
        self._refresh_boards_panel()

    def request_delete_board(self, board_id: str):
        """Endgueltiges Loeschen ueber das Panel: Bestaetigung NUR bei Favoriten."""
        board = self._find_board(board_id)
        if board is None:
            return
        if board["favorite"]:
            ret = QMessageBox.question(
                self, "Board endgültig löschen",
                f'Board "{board["name"]}" ist als Favorit markiert und wird ENDGÜLTIG gelöscht '
                f'(inkl. {board["entry_count"]} Einträgen). Dieser Vorgang kann nicht rückgängig '
                f'gemacht werden. Fortfahren?'
            )
            if ret != QMessageBox.StandardButton.Yes:
                return
        self.delete_board_permanently(board_id)

    def toggle_board_favorite(self, board_id: str):
        if board_id in self.favorites:
            self.favorites.discard(board_id)
        else:
            self.favorites.add(board_id)
        self.save_settings()
        self._refresh_boards_panel()

    def clear_board_history(self) -> bool:
        """Simple Mode: loescht alle geschlossenen NICHT-Favoriten endgueltig.

        Im Normal-Modus gesetzte Favoriten ueberleben das Leeren (Favorit = Schutzmarke,
        siehe request_delete_board). Rueckgabe zeigt an, ob tatsaechlich geloescht wurde
        (fuer Tests ohne QMessageBox-Interaktion)."""
        victims = [b for b in self.closed_boards.values() if b["id"] not in self.favorites]
        if not victims:
            return False
        entry_count = sum(len(b["entries"]) for b in victims)
        ret = QMessageBox.question(
            self, "Verlauf leeren",
            f'{len(victims)} geschlossene Boards mit insgesamt {entry_count} Einträgen endgültig löschen?'
        )
        if ret != QMessageBox.StandardButton.Yes:
            return False
        for b in victims:
            self.closed_boards.pop(b["id"], None)
            self.favorites.discard(b["id"])
        self.save_settings()
        self._refresh_boards_panel()
        return True

    def _simple_mode_enabled(self) -> bool:
        return _settings_bool(self.settings.value("simple_mode", False))

    def _on_toggle_simple_mode(self, checked: bool):
        self.settings.setValue("simple_mode", bool(checked))
        self._refresh_boards_panel()

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
        # BUGSWEEP-40: altes Array vorher entfernen — sonst bleiben bei weniger Tabs als zuvor
        # verwaiste Schlüssel höherer Indizes als Registry-Müll liegen.
        settings.remove("tabs")
        settings.beginWriteArray("tabs")
        for i in range(self.tabs.count()):
            settings.setArrayIndex(i)
            page = self.tabs.widget(i)
            board_id = getattr(page, "board_id", None) or new_board_id()
            settings.setValue("name", self.tabs.tabText(i))
            settings.setValue("view_mode", page.view_mode)
            settings.setValue("entries_json", json.dumps(page.list.get_all_entries(), ensure_ascii=False))
            settings.setValue("paths", page.list.get_all_paths())
            settings.setValue("board_id", board_id)
            settings.setValue("favorite", board_id in self.favorites)
        settings.endArray()

        # Board-Lebenszyklus: geschlossene Boards bleiben ueber Neustarts hinweg erhalten
        # (eigenes Array, damit "tabs"/current_tab weiterhin exakt die offenen Tabs abbildet).
        settings.remove("closed_boards")
        settings.beginWriteArray("closed_boards")
        for i, board in enumerate(self.closed_boards.values()):
            settings.setArrayIndex(i)
            settings.setValue("board_id", board["id"])
            settings.setValue("name", board["name"])
            settings.setValue("view_mode", board["view_mode"])
            settings.setValue("entries_json", json.dumps(board["entries"], ensure_ascii=False))
            settings.setValue("favorite", board["id"] in self.favorites)
            settings.setValue("closed_at", board["closed_at"])
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

        # Board-Lebenszyklus: geschlossene Boards laden (fehlt das Array bei alten
        # Datenstaenden komplett, ist size==0 -> verlustfrei leer, kein Fehler).
        self.closed_boards = {}
        self.favorites = set()
        closed_size = settings.beginReadArray("closed_boards")
        for i in range(closed_size):
            settings.setArrayIndex(i)
            board_id = settings.value("board_id") or new_board_id()
            name = settings.value("name", "Board")
            view_mode = settings.value("view_mode", "tiles")
            entries = _parse_entries_json(settings.value("entries_json", ""))
            favorite = _settings_bool(settings.value("favorite", False))
            closed_at = settings.value("closed_at", "") or iso_now()
            self.closed_boards[board_id] = {
                "id": board_id,
                "name": name,
                "view_mode": view_mode,
                "entries": entries,
                "closed_at": closed_at,
            }
            if favorite:
                self.favorites.add(board_id)
        settings.endArray()

        size = settings.beginReadArray("tabs")
        if size > 0:
            self.tabs.clear()
            for i in range(size):
                settings.setArrayIndex(i)
                name = settings.value("name", "Tab")
                view_mode = settings.value("view_mode", "tiles")
                entries = _parse_entries_json(settings.value("entries_json", ""))
                paths = settings.value("paths", [])
                if isinstance(paths, str):  # falls als einzelner String gespeichert
                    paths = [paths]
                # Migration: fehlt board_id (alter Datenstand) -> neue feste Identitaet vergeben.
                board_id = settings.value("board_id") or new_board_id()
                favorite = _settings_bool(settings.value("favorite", False))
                self.add_new_tab(name, view_mode, paths=paths, entries=entries, board_id=board_id)
                if favorite:
                    self.favorites.add(board_id)
            if isinstance(current_tab, int) and 0 <= current_tab < self.tabs.count():
                self.tabs.setCurrentIndex(current_tab)
            elif self.tabs.count() > 0:
                self.tabs.setCurrentIndex(0)
        else:
            self.add_new_tab("Allgemein")
        settings.endArray()
        self._update_tab_closable_state()
        self._sync_view_actions()

        panel_view = settings.value("boards_panel_view", "history")
        self._boards_panel_view = panel_view if panel_view in ("history", "alphabetical") else "history"

    def closeEvent(self, event):
        self.save_settings()
        # Bei aktiviertem Systemtray: Fenster nur verstecken statt die App zu beenden.
        if (not self._force_quit and self._tray_enabled()
                and self.tray is not None and self.tray.isVisible()):
            event.ignore()
            self.hide()
            self.tray.showMessage(
                self.profile.name, "Läuft weiter im Systemtray. Zum Beenden: Tray-Menü > Beenden.",
                QSystemTrayIcon.MessageIcon.Information, 2500)
            return
        if self.tray is not None:
            self.tray.hide()
        super().closeEvent(event)
        QApplication.instance().quit()

    # ----- Systemtray (T-20260721-02) -----
    def _tray_enabled(self) -> bool:
        return _settings_bool(self.settings.value("minimize_to_tray", False))

    def _on_toggle_tray(self, checked: bool):
        self.settings.setValue("minimize_to_tray", bool(checked))
        if checked:
            self._setup_tray()
        else:
            self._teardown_tray()

    def _setup_tray(self):
        """Baut das Tray-Icon auf -- Vertrag: Schalter aus = kein Icon, Schalter an = Icon
        sofort erzeugen (mit Verfuegbarkeits-Retry).

        Jeder Aufruf startet eine neue "Generation" (`_tray_setup_token`); eine noch laufende
        Retry-Kette einer vorherigen Generation (z.B. nach schnellem Aus/Ein-Toggle) bricht sich
        beim naechsten Versuch selbst ab, damit nie zwei Tray-Icons gleichzeitig entstehen."""
        self._tray_setup_token += 1
        if not self._tray_enabled():
            self.tray = None
            return
        self._attempt_tray_creation(self._tray_setup_token, retry=0)

    def _attempt_tray_creation(self, token: int, retry: int):
        if token != self._tray_setup_token:
            return  # ueberholt durch neueren _setup_tray()/Toggle-Aufruf
        if not QSystemTrayIcon.isSystemTrayAvailable():
            if retry < TRAY_RETRY_MAX_ATTEMPTS:
                QTimer.singleShot(
                    TRAY_RETRY_INTERVAL_MS,
                    lambda: self._attempt_tray_creation(token, retry + 1),
                )
                return
            # Ohne verfuegbaren Tray darf die App nie unsichtbar weiterlaufen (siehe closeEvent):
            # self.tray bleibt None, Schliessen beendet die App dann normal.
            self.tray = None
            self._notify_tray_unavailable()
            return
        self._create_tray_icon()

    def _create_tray_icon(self):
        self.tray = QSystemTrayIcon(self._resolve_tray_icon(), self)
        self.tray.setToolTip(self.profile.name)
        self.tray.setContextMenu(self._build_tray_menu())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def _teardown_tray(self):
        """Entfernt das Tray-Icon sofort (Vertrag: Ausschalten entfernt das Icon sofort)."""
        self._tray_setup_token += 1  # bricht eine evtl. laufende Retry-Kette ab
        if self.tray is not None:
            self.tray.hide()
            self.tray.setContextMenu(None)
            self.tray.deleteLater()
        self.tray = None

    def _resolve_tray_icon(self) -> QIcon:
        """Liefert IMMER ein nicht-leeres Icon: Profil-ICO -> Fenster-Icon -> Qt-Standardicon.

        Nie stillschweigend ein Null-Icon setzen (siehe Ticket-Diagnose T-20260721-02)."""
        icon_path = resource_path(self.profile.icon_file)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                return icon
        window_icon = self.windowIcon()
        if not window_icon.isNull():
            return window_icon
        return self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

    def _notify_tray_unavailable(self):
        QMessageBox.warning(
            self, self.profile.name,
            f"Der Systemtray ist auf diesem System nicht verfügbar. {self.profile.name} läuft "
            "ohne Tray-Symbol -- Schließen beendet die App vollständig.",
        )

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger,
                      QSystemTrayIcon.ActivationReason.DoubleClick):
            self._show_from_tray()

    def _show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self):
        self._force_quit = True
        self.close()

    # ----- Tray-Navigation (T-20260721-03) -----
    def tray_navigation_entries(self) -> list[dict]:
        """Aktive Boards fuers Tray-Menue (geschlossene Boards erscheinen nie, siehe Ticket).

        Pro Board hoechstens TRAY_ENTRY_LIMIT_PER_BOARD Eintraege, ausser bei Favoriten
        (vollstaendige Liste). `entries_truncated` zeigt an, ob weitere Eintraege existieren."""
        boards = []
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if not isinstance(page, TabPage):
                continue
            board_id = getattr(page, "board_id", None)
            is_favorite = board_id in self.favorites
            all_entries = page.list.get_all_entries()
            shown = all_entries if is_favorite else all_entries[:TRAY_ENTRY_LIMIT_PER_BOARD]
            boards.append({
                "id": board_id,
                "name": self.tabs.tabText(i),
                "favorite": is_favorite,
                "entries": shown,
                "entries_total": len(all_entries),
                "entries_truncated": len(shown) < len(all_entries),
            })
        return boards

    def _tray_stage2_enabled(self, board_count: int) -> bool:
        """Bei sehr vielen Boards keine Eintrags-Untermenues aufblasen -- nur Stufe 1."""
        return board_count <= TRAY_STAGE2_MAX_BOARDS

    def _tray_board_label(self, board: dict) -> str:
        return f'★ {board["name"]}' if board["favorite"] else board["name"]

    def open_board_from_tray(self, board_id: str):
        """Stufe 1: Board aus dem Tray direkt anwaehlen und Hauptfenster zeigen."""
        self.activate_board(board_id)
        self._show_from_tray()

    def launch_entry_from_tray(self, board_id: str, path: str):
        """Stufe 2: hinterlegten Eintrag ueber denselben sicheren Launch-Pfad wie im
        Hauptfenster starten (open_file). Wechselt zusaetzlich das aktive Board, zeigt das
        Hauptfenster aber bewusst NICHT erzwungen -- ein Tray-Quick-Launch soll nicht jedes
        Mal das Fenster aufreissen."""
        self.activate_board(board_id)
        open_file(path)

    def tray_search(self, query: str) -> list[dict]:
        """UI-freie Such-/Ranking-Logik: Boards + Eintraege ueber alle AKTIVEN Boards.

        Liefert eine nach Trefferguete sortierte Liste von Treffer-Dicts
        {"kind": "board"|"entry", "board_id", "board_name", "label", "path"}.
        Leere/Whitespace-Anfrage liefert eine leere Liste (keine Sondersicht im Menue)."""
        needle = (query or "").strip().casefold()
        if not needle:
            return []
        hits = []
        for i in range(self.tabs.count()):
            page = self.tabs.widget(i)
            if not isinstance(page, TabPage):
                continue
            board_id = getattr(page, "board_id", None)
            board_name = self.tabs.tabText(i)
            board_score = _tray_match_score(needle, board_name)
            if board_score is not None:
                hits.append({"kind": "board", "board_id": board_id, "board_name": board_name,
                             "label": board_name, "path": None, "_score": board_score})
            for entry in page.list.get_all_entries():
                label = entry.get("label") or ""
                entry_score = _tray_match_score(needle, label)
                if entry_score is not None:
                    hits.append({"kind": "entry", "board_id": board_id, "board_name": board_name,
                                 "label": label, "path": entry.get("path"), "_score": entry_score})
        hits.sort(key=lambda h: (h["_score"], h["kind"] != "board", h["label"].casefold()))
        for hit in hits:
            del hit["_score"]
        return hits

    def tray_activate_search(self, query: str) -> bool:
        """Fuehrt tray_search() aus und aktiviert den besten Treffer (Enter im Suchfeld).

        Board -> Board oeffnen (wie Stufe 1); Eintrag -> starten (wie Stufe 2). Rueckgabe zeigt
        an, ob ueberhaupt ein Treffer aktiviert wurde (fuer Tests ohne Menue-Interaktion)."""
        hits = self.tray_search(query)
        if not hits:
            return False
        best = hits[0]
        if best["kind"] == "board":
            self.open_board_from_tray(best["board_id"])
        else:
            self.launch_entry_from_tray(best["board_id"], best["path"])
        return True

    def _build_tray_menu(self) -> QMenu:
        menu = QMenu()
        menu.aboutToShow.connect(lambda m=menu: self._populate_tray_menu(m))
        self._populate_tray_menu(menu)
        return menu

    def _populate_tray_menu(self, menu: QMenu):
        """Baut das Tray-Menue komplett neu auf -- immer aus dem LIVE-Board-Zustand.

        Dadurch bleiben nach Umbenennen/Schliessen/Reaktivieren/endgueltigem Loeschen nie
        verwaiste Aktionen im Menue haengen (Menue wird per aboutToShow on-demand neu befuellt)."""
        menu.clear()

        search_edit = QLineEdit()
        search_edit.setPlaceholderText("Board oder Eintrag suchen …")
        search_edit.textChanged.connect(lambda text, m=menu: self._rebuild_tray_dynamic_section(m, text))
        search_edit.returnPressed.connect(
            lambda m=menu, e=search_edit: self._on_tray_search_enter(m, e.text()))
        search_action = QWidgetAction(menu)
        search_action.setDefaultWidget(search_edit)
        menu.addAction(search_action)
        menu.addSeparator()

        # Marker-Trenner: dynamischer Board-/Suchtreffer-Block wird VOR diesen Marker eingefuegt,
        # die Fuss-Aktionen danach bleiben Menue-weit stabil (keine Neuanlage pro Tastendruck).
        self._tray_footer_marker = menu.addSeparator()
        act_open = menu.addAction("Öffnen/Anzeigen")
        act_open.triggered.connect(self._show_from_tray)
        menu.addAction("Beenden", self.quit_app)

        self._tray_dynamic_actions = []
        self._rebuild_tray_dynamic_section(menu, "")

    def _on_tray_search_enter(self, menu: QMenu, query: str):
        if self.tray_activate_search(query):
            menu.close()

    def _rebuild_tray_dynamic_section(self, menu: QMenu, query: str):
        """Ersetzt nur den dynamischen Block (Boards ODER Suchtreffer) -- das Suchfeld selbst
        bleibt dabei unangetastet, damit Fokus/Cursor beim Tippen erhalten bleiben."""
        for action in self._tray_dynamic_actions:
            menu.removeAction(action)

        marker = self._tray_footer_marker
        query = (query or "").strip()
        actions = self._tray_search_result_actions(menu, query) if query else self._tray_board_actions(menu)
        for action in actions:
            menu.insertAction(marker, action)
        self._tray_dynamic_actions = actions

    def _tray_board_actions(self, menu: QMenu) -> list:
        boards = self.tray_navigation_entries()
        if not boards:
            act = QAction("Keine aktiven Boards", menu)
            act.setEnabled(False)
            return [act]

        stage2 = self._tray_stage2_enabled(len(boards))
        actions = []
        for board in boards:
            label = self._tray_board_label(board)
            if stage2 and board["entries"]:
                sub = QMenu(label, menu)
                open_act = sub.addAction("Board öffnen")
                open_act.triggered.connect(
                    lambda checked=False, bid=board["id"]: self.open_board_from_tray(bid))
                sub.addSeparator()
                for entry in board["entries"]:
                    entry_act = sub.addAction(entry["label"])
                    entry_act.triggered.connect(
                        lambda checked=False, bid=board["id"], p=entry["path"]:
                        self.launch_entry_from_tray(bid, p))
                if board["entries_truncated"]:
                    remaining = board["entries_total"] - len(board["entries"])
                    more_act = sub.addAction(f"… {remaining} weitere")
                    more_act.setEnabled(False)
                actions.append(sub.menuAction())
            else:
                act = QAction(label, menu)
                act.triggered.connect(lambda checked=False, bid=board["id"]: self.open_board_from_tray(bid))
                actions.append(act)
        return actions

    def _tray_search_result_actions(self, menu: QMenu, query: str) -> list:
        hits = self.tray_search(query)[:TRAY_SEARCH_RESULT_LIMIT]
        if not hits:
            act = QAction("Keine Treffer", menu)
            act.setEnabled(False)
            return [act]
        actions = []
        for hit in hits:
            if hit["kind"] == "board":
                act = QAction(hit["label"], menu)
                act.triggered.connect(
                    lambda checked=False, bid=hit["board_id"]: self.open_board_from_tray(bid))
            else:
                act = QAction(f'{hit["label"]} — {hit["board_name"]}', menu)
                act.triggered.connect(
                    lambda checked=False, bid=hit["board_id"], p=hit["path"]:
                    self.launch_entry_from_tray(bid, p))
            actions.append(act)
        return actions

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

def main(profile: AppProfile = PROFILE_SOFTWARECENTER):
    app = QApplication(sys.argv)
    # Systemtray: App nicht automatisch beenden, wenn das Fenster (in den Tray)
    # versteckt wird. Das Beenden steuert MainWindow.closeEvent/quit_app explizit.
    app.setQuitOnLastWindowClosed(False)

    # Single-Instance: Laeuft bereits dieses Produkt (auch versteckt im Tray)?
    # Dann die bestehende Instanz nach vorne holen statt eine zweite zu starten.
    probe = QLocalSocket()
    probe.connectToServer(profile.instance_id)
    if probe.waitForConnected(300):
        probe.write(b"show")
        probe.flush()
        probe.waitForBytesWritten(500)
        probe.disconnectFromServer()
        return 0
    probe.abort()

    icon_path = resource_path(profile.icon_file)
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    win = MainWindow(profile=profile)

    # Lokalen Server starten, der bei Start einer zweiten Instanz benachrichtigt wird.
    QLocalServer.removeServer(profile.instance_id)  # evtl. verwaisten Socket aufraeumen
    server = QLocalServer()
    server.listen(profile.instance_id)

    def _on_second_instance():
        conn = server.nextPendingConnection()
        win._show_from_tray()
        if conn is not None:
            conn.close()

    server.newConnection.connect(_on_second_instance)
    win._local_server = server  # Referenz halten, damit der Server nicht aufgeraeumt wird

    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
