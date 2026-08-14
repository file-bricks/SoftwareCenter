from __future__ import annotations

import contextlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_SCALE_FACTOR", "1")

# Import bewusst erst hier: QT_SCALE_FACTOR muss vor dem Qt-Import stehen.
from PySide6 import QtCore, QtGui, QtWidgets

from SoftwareCenter import MainWindow

MIN_STORE_WIDTH = 1366
MIN_STORE_HEIGHT = 768

# Bewusst kompakt gehalten: ein sehr breites Fenster laesst denselben Inhalt
# verloren wirken. 1440x900 liegt mit Reserve ueber der Store-Mindestgroesse.
WINDOW_SIZE = (1440, 900)

# Qt-Plattformen ohne echtes Fenstersystem. Sie rendern auf diesem System keine
# Glyphen (Tofu-Kaestchen statt Text) und haben 2026-08-11 zur Store-Ablehnung
# nach Policy 10.1.1.3 ("Inaccurate Representation") gefuehrt.
HEADLESS_PLATFORMS = frozenset({"offscreen", "minimal", "vnc"})

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "README" / "screenshots" / "store"

SCREENSHOT_FILES = {
    "main": "main-window.png",
    "tabs": "tab-organization.png",
    "tiles": "tiles-view.png",
    "list": "list-view.png",
}


def _process_events(app: QtWidgets.QApplication, duration: float = 0.08) -> None:
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)


def _configure_runtime_dirs(temp_root: Path) -> Path:
    home_dir = temp_root / "home"
    home_dir.mkdir(parents=True, exist_ok=True)

    os.environ["HOME"] = str(home_dir)
    os.environ["USERPROFILE"] = str(home_dir)
    os.environ["APPDATA"] = str(home_dir / "AppData" / "Roaming")
    os.environ["LOCALAPPDATA"] = str(home_dir / "AppData" / "Local")
    os.environ["XDG_CONFIG_HOME"] = str(home_dir / ".config")

    settings_root = temp_root / "qsettings"
    settings_root.mkdir(parents=True, exist_ok=True)
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    QtCore.QSettings.setPath(
        QtCore.QSettings.IniFormat,
        QtCore.QSettings.UserScope,
        str(settings_root),
    )
    QtCore.QSettings.setPath(
        QtCore.QSettings.IniFormat,
        QtCore.QSettings.SystemScope,
        str(settings_root),
    )
    return home_dir


# Demo-Sammlung fuer die Store-Screenshots.
#
# WICHTIG: Hier stehen ECHTE, installierte Programme - keine Demo-Textdateien.
# Grund: SoftwareCenter ist ein Software-Organizer. Zeigte der Screenshot
# Dokumente statt Programme, erzaehlte er die Produktgeschichte eines anderen
# Produkts und fiele unter Policy 10.1.1.3 "Inaccurate Representation" - genau
# der Ablehnungsgrund vom 2026-08-11. Echte EXEs liefern echte Icons;
# generische Platzhalter-Symbole lassen die App unfertig wirken.
#
# Die Gruppierung folgt der realen Installation des Nutzers.
# Fehlende Programme werden beim Aufbau uebersprungen.
#
# Format: Board -> (Ansicht, ((absoluter Pfad, Anzeigename), ...))
PROGRAM_CATALOGUE: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
    "Dev": (
        "list",
        (
            (r"C:\Program Files\Git\git-bash.exe", "git-bash"),
            (r"C:\Users\User\AppData\Local\Programs\Microsoft VS Code\Code.exe", "Code"),
            (r"C:\Users\User\AppData\Local\GitHubDesktop\GitHubDesktop.exe", "GitHubDesktop"),
            (r"C:\Program Files (x86)\Thonny\thonny.exe", "thonny"),
            (r"C:\Program Files\Python312\python.exe", "Python"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\CODING\REL-PUB_WinStorePackager\releases\v2.3.1\WinStorePackager-2.3.1-win64.exe", "WinStorePackager"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\CODING\REL-PUB_MethodenAnalyser\MethodenAnalyser.exe", "MethodenAnalyser"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL-PUB_ProSync\releases\v3.2.0\ProSyncReader.exe", "ProSyncReader"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL-PUB_SQLiteViewer\releases\v2.0.0\SQLiteViewer-2.0.0-win64.exe", "SQLiteViewer"),
            (r"C:\Program Files\Notepad++\notepad++.exe", "Notepad++"),
            (r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe", "PowerShell"),
            (r"C:\Windows\System32\cmd.exe", "Eingabeaufforderung"),
        ),
    ),
    "data": (
        "tiles",
        (
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL-PUB_ProFiler\ProFiler.exe", "ProFiler"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL_AmpelClip\AmpelClip.exe", "AmpelClip"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL_SoftwareCenter\SoftwareCenter.exe", "SoftwareCenter"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\BIO\REL-PUB_23andMe_to_VCF\releases\v1.0.2\23toVCF_Pro-1.0.2-win64.exe", "23toVCF"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\ASSISTENT\FAST_HausLagerist_V4\HausLagerist.exe", "HausLagerist"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\ASSISTENT\RDY_FAST_UpToday_SOCIAL\UpToday.exe", "UpToday"),
            (r"C:\Windows\System32\taskmgr.exe", "Task-Manager"),
            (r"C:\Windows\System32\msinfo32.exe", "Systeminformation"),
            (r"C:\Windows\System32\cleanmgr.exe", "Datenträgerbereinigung"),
            (r"C:\Windows\System32\resmon.exe", "Ressourcenmonitor"),
        ),
    ),
    "office": (
        "tiles",
        (
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DOCS\DEV_DokuZen\releases\v1.0.0\DokuZen-Pro-1.0.0-win64.exe", "DokuZen"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DOCS\DEV_CleanMarkdown\releases\v0.3.2\CleanMarkdown-0.3.2-win64.exe", "CleanMarkdown"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DOCS\DEV_FormularErstellen\FormConstructor.exe", "Formulare"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DOCS\DEV_TextBrain\TextBrain.exe", "TextBrain"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DATA\REL-PUB_PromptBoard\releases\v1.1.1\PromptBoard-1.1.1-win64.exe", "PromptBoard"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\DOCS\REL-PUB_LitZentrum_SUITE\releases\v1.0.0\LitZentrum-1.0.0-win64.exe", "LitZen"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\AUTISMO\DEV_Foerderplaner_Autismo_pro\releases\v4.0.0\Foerderplaner-4.0.0-win64.exe", "Förderplaner"),
            (r"C:\Windows\System32\notepad.exe", "Editor"),
            (r"C:\Windows\System32\calc.exe", "Rechner"),
            (r"C:\Windows\System32\charmap.exe", "Zeichentabelle"),
        ),
    ),
    "web": (
        "tiles",
        (
            (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "Chrome"),
            (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "Edge"),
            (r"C:\Users\User\AppData\Local\GitHubDesktop\GitHubDesktop.exe", "GitHubDesktop"),
            (r"C:\Windows\System32\mstsc.exe", "Remotedesktop"),
        ),
    ),
    "Production": (
        "tiles",
        (
            (r"C:\Program Files\Blender Foundation\Blender 5.1\blender-launcher.exe", "blender-launcher"),
            (r"C:\Users\User\OneDrive\.TOPICS\.SOFTWARE\ASSISTENT\RDY_FAST_UpToday_SOCIAL\UpToday.exe", "UpToday"),
        ),
    ),
}

_KIND_BY_SUFFIX = {
    ".txt": "file",
    ".md": "file",
    ".py": "script",
    ".bat": "script",
    ".cmd": "script",
    ".ps1": "script",
    ".url": "url",
    ".lnk": "windows_shortcut",
}

_CONTENT_BY_SUFFIX = {
    ".txt": "{label} – lokale Demo-Datei mit echten Umlauten: äöüß.\n",
    ".md": "# {label}\n\nDemo-Inhalt. Desktop-Profile bleiben lokal.\n",
    ".py": "print('{label}: lokale Demo mit Umlauten äöü')\n",
    ".bat": "@echo off\r\necho {label} starten\r\n",
    ".cmd": "@echo off\r\necho {label} starten\r\n",
    ".ps1": "Write-Output '{label} vorbereiten'\n",
    ".url": "[InternetShortcut]\nURL=https://example.invalid/demo\n",
    ".lnk": "Demo-Verknüpfung: {label}\n",
}


def _write_demo_targets(workspace: Path) -> dict[str, list[tuple[Path, str]]]:
    """Liefert je Board die echten Programme mit ihrem Anzeigenamen.

    Legt bewusst NICHTS mehr an: Die Eintraege verweisen auf tatsaechlich
    installierte Programme, damit SoftwareCenter deren echte Icons zieht.
    Fehlende Programme werden still uebersprungen, damit der Generator auch
    auf einem anders bestueckten Rechner durchlaeuft.
    """
    del workspace  # keine Demo-Dateien mehr noetig
    targets: dict[str, list[tuple[Path, str]]] = {}
    for board, (_view, programs) in PROGRAM_CATALOGUE.items():
        found = [(Path(p), label) for p, label in programs if Path(p).is_file()]
        if found:
            targets[board] = found
    return targets


def _entry(path: Path, label: str, kind: str, notes: str | None = None) -> dict[str, str | None]:
    return {
        "path": str(path),
        "label": label,
        "kind": kind,
        "notes": notes,
    }


def _board_entries(items: list[tuple[Path, str]]) -> list[dict[str, str | None]]:
    # "file" ist der Typ, den detect_entry_kind() fuer eine existierende .exe
    # liefert; das Icon zieht SoftwareCenter dann aus der Datei selbst.
    return [_entry(path, label, "file") for path, label in items]


def _configure_demo_window(window: MainWindow, targets: dict[str, list[Path]]) -> None:
    default_page = window.current_page()
    if default_page is None:
        raise RuntimeError("SoftwareCenter konnte keine Startseite erzeugen")

    boards = list(PROGRAM_CATALOGUE.items())
    first_name, (first_view, _first_files) = boards[0]
    default_page.set_view_mode(first_view)
    default_page.add_entries(_board_entries(targets[first_name]))

    for board_name, (view_mode, _files) in boards[1:]:
        window.add_new_tab(board_name, view_mode, entries=_board_entries(targets[board_name]))

    # Erst umbenennen, wenn alle Tabs stehen: Solange nur ein Tab existiert, ist die
    # Tab-Leiste noch ohne Schliessen-Knopf bemessen; ein spaeter eingeblendeter Knopf
    # laege sonst ueber dem laengeren Namen.
    window.tabs.setTabText(0, first_name)


def real_gui_available() -> bool:
    """Kann dieser Prozess ein echtes Fenster zeichnen?

    Laeuft bereits eine QApplication (z. B. unter pytest mit
    ``QT_QPA_PLATFORM=offscreen``), entscheidet deren Plattform-Plugin -- ein
    zweites laesst sich nicht daneben starten.
    """
    app = QtWidgets.QApplication.instance()
    if app is not None:
        return app.platformName() not in HEADLESS_PLATFORMS
    forced = os.environ.get("QT_QPA_PLATFORM", "")
    if forced in HEADLESS_PLATFORMS:
        # Wird beim Erzeugen der QApplication verworfen, siehe _native_qt_platform().
        forced = ""
    if sys.platform.startswith("win") or sys.platform == "darwin":
        return True
    return bool(forced or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


@contextlib.contextmanager
def _native_qt_platform():
    """Verwirft ein von aussen gesetztes Headless-Plugin nur fuer diesen Block.

    Root-Cause des Tofu-Bugs: Unter ``QT_QPA_PLATFORM=offscreen`` rendert Qt auf
    Windows KEINE echten Glyphen -- das Textlayout stimmt, aber jede Glyphe wird
    als .notdef-Kaestchen gerastert, und ``grab()`` liefert ein Bild voller
    Kaestchen. Die native Plattform muss aktiv sein; das Fenster bleibt trotzdem
    unsichtbar (``Qt.WA_DontShowOnScreen``).

    Qt liest die Variable beim Erzeugen der QApplication. Existiert bereits eine,
    ist ein Wechsel ohnehin nicht mehr moeglich. Danach wird der vorherige Wert
    wiederhergestellt, damit ein umgebender Testlauf sein Headless-Setup behaelt.
    """
    previous = os.environ.get("QT_QPA_PLATFORM")
    if previous in HEADLESS_PLATFORMS and QtWidgets.QApplication.instance() is None:
        del os.environ["QT_QPA_PLATFORM"]
    try:
        yield
    finally:
        if previous is not None:
            os.environ["QT_QPA_PLATFORM"] = previous


def _render_char(ch: str, font: QtGui.QFont, size: QtCore.QSize) -> bytes:
    pixmap = QtGui.QPixmap(size)
    pixmap.fill(QtCore.Qt.white)
    painter = QtGui.QPainter(pixmap)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), QtCore.Qt.AlignCenter, ch)
    painter.end()
    return bytes(pixmap.toImage().constBits())


def font_rendering_works(app: QtWidgets.QApplication) -> bool:
    """True, wenn die aktuelle Plattform echte Glyphen rendert.

    Rendert mehrere unterschiedliche Zeichen einzeln. Bei echtem Rendering sehen
    sie verschieden aus; bei Tofu ist jedes das gleiche .notdef-Kaestchen -> alle
    Renderings identisch.
    """
    font = app.font()
    size = QtCore.QSize(48, 48)
    probes = ["A", "B", "g", "8", "M"]
    renders = [_render_char(ch, font, size) for ch in probes]
    blank = _render_char(" ", font, size)
    distinct = len(set(renders))
    non_blank = sum(1 for render in renders if render != blank)
    return distinct >= 3 and non_blank >= len(probes) - 1


def _assert_font_rendering(app: QtWidgets.QApplication) -> None:
    """Bricht laut ab, statt lautlos unlesbare Screenshots zu erzeugen.

    Zwei Stufen: erst das Plattform-Plugin, dann eine echte Glyphen-Probe. Ein
    reiner Plattform-Check wuerde fehlende Schriften auf nativer Plattform nicht
    bemerken.
    """
    platform = app.platformName()
    if platform in HEADLESS_PLATFORMS:
        raise RuntimeError(
            f"Qt laeuft unter der '{platform}'-Plattform -- Screenshots wuerden Tofu "
            "(Kaestchen statt Text) enthalten. QT_QPA_PLATFORM=offscreen nicht setzen; "
            "der Generator nutzt WA_DontShowOnScreen auf der nativen Plattform."
        )
    if not font_rendering_works(app):
        raise RuntimeError(
            f"Font-Rendering-Selbsttest fehlgeschlagen (Plattform '{platform}'): "
            "gerenderte Glyphen sind nicht unterscheidbar (Tofu-Verdacht). "
            "Abbruch, um kein defektes Screenshot-Set zu erzeugen."
        )


def _save_widget(widget: QtWidgets.QWidget, target: Path) -> None:
    widget.show()
    widget.raise_()
    widget.activateWindow()
    app = QtWidgets.QApplication.instance()
    if app is not None:
        _process_events(app, duration=0.4)
    pixmap = widget.grab()
    if pixmap.isNull():
        raise RuntimeError(f"Screenshot für {target.name} konnte nicht erzeugt werden")
    if pixmap.width() < MIN_STORE_WIDTH or pixmap.height() < MIN_STORE_HEIGHT:
        raise RuntimeError(
            f"Screenshot {target.name} ist mit {pixmap.width()}x{pixmap.height()} kleiner als die "
            f"Store-Mindestgroesse {MIN_STORE_WIDTH}x{MIN_STORE_HEIGHT}"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    if not pixmap.save(str(target)):
        raise RuntimeError(f"Screenshot {target} konnte nicht gespeichert werden")
    print(f"{target.name}: {pixmap.width()}x{pixmap.height()}")


def _write_summary(targets: list[Path]) -> Path:
    summary_path = targets[0].parent / "summary.json"
    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "screenshots": [
            {"name": "main", "file": SCREENSHOT_FILES["main"], "caption": "Hauptfenster mit lokalen Launcher-Kacheln"},
            {"name": "tabs", "file": SCREENSHOT_FILES["tabs"], "caption": "Mehrere Workflow-Tabs im selben Profil"},
            {"name": "tiles", "file": SCREENSHOT_FILES["tiles"], "caption": "Kachelansicht für schnellen Zugriff"},
            {"name": "list", "file": SCREENSHOT_FILES["list"], "caption": "Listenansicht für größere Sammlungen"},
        ],
    }
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary_path


def generate_store_screenshots(output_dir: Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="softwarecenter-store-shots-") as temp_dir:
        temp_root = Path(temp_dir)
        home_dir = _configure_runtime_dirs(temp_root)
        targets = _write_demo_targets(home_dir / "workspace")

        QtCore.QStandardPaths.setTestModeEnabled(True)
        with _native_qt_platform():
            app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        app.setApplicationName("SoftwareCenter Store Screenshots")
        app.setQuitOnLastWindowClosed(False)
        _assert_font_rendering(app)

        ini_path = str(temp_root / "softwarecenter.ini")

        # Schritt 1: Demo-Profil aufbauen und speichern.
        builder_settings = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        builder = MainWindow(settings=builder_settings)
        builder.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
        builder.resize(*WINDOW_SIZE)
        _configure_demo_window(builder, targets)
        builder.save_settings()
        builder_settings.sync()
        builder.close()
        _process_events(app)

        # Schritt 2: Fenster frisch aus dem gespeicherten Profil starten. Genau so
        # sieht die App ein wiederkehrender Nutzer -- und nur so ist die Board-Leiste
        # von Anfang an korrekt bemessen.
        settings = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        window = MainWindow(settings=settings)
        # Nie sichtbar zeigen, aber echtes Rendering auf der nativen Plattform.
        window.setAttribute(QtCore.Qt.WA_DontShowOnScreen, True)
        window.resize(*WINDOW_SIZE)
        _process_events(app)

        result_paths = [
            output_dir / SCREENSHOT_FILES["main"],
            output_dir / SCREENSHOT_FILES["tabs"],
            output_dir / SCREENSHOT_FILES["tiles"],
            output_dir / SCREENSHOT_FILES["list"],
        ]

        def show(tab_index: int, view: str, message: str) -> str:
            """Board wechseln, Ansicht setzen, Statuszeile aus echten Zahlen bilden."""
            window.tabs.setCurrentIndex(tab_index)
            window.set_current_view(view)
            page = window.current_page()
            text = message.format(
                board=window.tabs.tabText(tab_index),
                count=page.list.count(),
                boards=window.tabs.count(),
            )
            window.statusBar().showMessage(text, 0)
            return text

        try:
            show(0, "tiles", "Lokale Sammlung »{board}« · {count} Einträge · Offline")
            _save_widget(window, result_paths[0])

            show(2, "list", "Board »{board}« · {count} Einträge · {boards} Boards im Profil")
            _save_widget(window, result_paths[1])

            # Bewusst ein anderes Board als bei "main", sonst waeren zwei der vier
            # Store-Screenshots dasselbe Bild.
            show(1, "tiles", "Kachelansicht · Board »{board}« · {count} Einträge")
            _save_widget(window, result_paths[2])

            show(0, "list", "Listenansicht für größere Sammlungen · {count} Einträge")
            _save_widget(window, result_paths[3])
        finally:
            window.close()
            _process_events(app)

    _write_summary(result_paths)
    return result_paths


def main() -> None:
    targets = generate_store_screenshots(OUTPUT_DIR)
    for target in targets:
        print(target.name)


if __name__ == "__main__":
    main()
