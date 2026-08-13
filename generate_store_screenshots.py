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
from PySide6 import QtCore, QtWidgets

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


# Demo-Sammlung fuer die Store-Screenshots. Alle Namen sind frei erfunden und
# neutral: keine echten Nutzerpfade, keine Klarnamen, keine fremden
# Produktmarken. Die Dateiendung bestimmt Eintragstyp und damit das
# Windows-Symbol, deshalb sind die Endungen bewusst gemischt.
#
# Die Boards sind absichtlich gut gefuellt: ein zu 80 % leeres Fenster zeigt das
# Produkt nicht so, wie es benutzt wird, und laedt dieselbe Bewertung nach
# Policy 10.1.1.3 erneut ein wie die abgelehnten Tofu-Screenshots.
BOARD_CATALOGUE: dict[str, tuple[str, tuple[str, ...]]] = {
    "Arbeitsplatz": (
        "tiles",
        (
            "Projekt-Briefing.txt", "Redaktion.py", "Mail-Export.cmd", "PDF-Werkstatt.bat",
            "Recherche.url", "Sync-Ordner.lnk", "Backup-Lauf.cmd", "Rechnungen.bat",
            "Wochenplan.md", "Bildarchiv.lnk", "Haushaltsbuch.txt", "Handbuch.url",
            "Notizen.md", "Release-Check.ps1", "Texteditor.lnk", "Tabellen.lnk",
            "Präsentation.lnk", "Terminplaner.lnk", "Adressbuch.txt", "Aufgabenliste.md",
            "Zeiterfassung.bat", "Belegscanner.bat", "Archivsuche.py", "Dateimanager.lnk",
            "Bildbearbeitung.lnk", "Videoschnitt.lnk", "Tonaufnahme.lnk", "Bildschirmfoto.bat",
            "Farbwähler.py", "Schriftmuster.txt", "Diagramme.py", "Mindmap.lnk",
            "Kalkulation.txt", "Angebote.md", "Verträge.txt", "Protokolle.md",
            "Checklisten.md", "Vorlagen.lnk", "Serienbrief.bat", "Etiketten.bat",
            "Druckvorlagen.lnk", "Übersetzer.url", "Wörterbuch.url", "Rechtschreibung.py",
            "Lesezeichen.url", "Downloads.lnk", "Netzlaufwerk.lnk", "Druckerliste.ps1",
            "Systeminfo.ps1", "Datenträger.ps1", "Aufräumen.cmd", "Updates.ps1",
            "Ereignisse.ps1", "Dienste.ps1", "Aufgabenplanung.ps1", "Passworttresor.lnk",
            "Verschlüsselung.py", "Signaturen.txt", "Zertifikate.txt", "Firewall-Regeln.ps1",
            "Netzwerktest.cmd", "Ping-Werkzeug.cmd", "Portprüfung.py", "Fernwartung.lnk",
            "Terminalfenster.lnk", "Skriptsammlung.py", "Buildlauf.cmd", "Testlauf.cmd",
            "Auslieferung.ps1", "Changelog.md", "Fehlerliste.md", "Ideenspeicher.md",
            "Lernpfad.md", "Literatur.url", "Kursunterlagen.lnk", "Reisekosten.txt",
            "Urlaubsplan.md", "Inventar.txt", "Wartungsplan.md", "Kontakte.txt",
        ),
    ),
    "Office": (
        "tiles",
        (
            "Projekt-Notizen.md", "Freigabe-Briefing.txt", "Release-Check.ps1", "Post-Ausgang.cmd",
            "Scan-Ablage.bat", "Vorlagen.url", "Angebotsmappe.txt", "Auftragsbuch.txt",
            "Rechnungsausgang.bat", "Mahnwesen.bat", "Kassenbuch.txt", "Kostenstellen.txt",
            "Budgetplan.md", "Jahresabschluss.md", "Steuerordner.lnk", "Belegablage.lnk",
            "Lieferscheine.txt", "Bestellungen.txt", "Lagerliste.txt", "Preisliste.txt",
            "Kundenliste.txt", "Lieferanten.txt", "Serienmail.bat", "Newsletter.md",
            "Pressemappe.md", "Broschüre.lnk", "Visitenkarten.lnk", "Briefpapier.lnk",
            "Formulare.lnk", "Anträge.md", "Genehmigungen.md", "Fristenkalender.md",
            "Sitzungsplan.md", "Tagesordnung.md", "Sitzungsprotokoll.md", "Beschlüsse.md",
            "Aktenplan.txt", "Ablagestruktur.txt", "Archivierung.ps1", "Aktenvernichtung.md",
            "Datenschutz.md", "Verfahrensverzeichnis.md", "Löschkonzept.md", "Auskunftsersuchen.md",
            "Vertragsmappe.txt", "Vollmachten.txt", "Versicherungen.txt", "Mietunterlagen.txt",
            "Inventarliste.txt", "Wartungsverträge.txt", "Reisebuchung.url", "Fahrtenbuch.txt",
            "Spesenabrechnung.txt", "Stundenzettel.txt", "Urlaubsantrag.md", "Krankmeldung.md",
            "Personalakte.lnk", "Einarbeitung.md", "Schulungsplan.md", "Zeugnisse.lnk",
            "Bewerbungen.lnk", "Stellenausschreibung.md", "Organigramm.lnk", "Telefonliste.txt",
            "Kalenderwoche.md", "Raumbuchung.md", "Besucherliste.txt", "Poststelle.bat",
            "Frankierung.bat", "Materialbestellung.txt", "Büromaterial.txt", "Reinigungsplan.md",
            "Schlüsselliste.txt", "Notfallplan.md", "Brandschutz.md", "Ersthelfer.txt",
            "Unterweisungen.md", "Betriebsrat.md",
        ),
    ),
    "Review": (
        "list",
        (
            "Text-Review.py", "Mail-Status.cmd", "Dokumente.bat", "Layoutprüfung.md",
            "Bildrechte.md", "Quellenliste.txt", "Zitatprüfung.md", "Rechtschreibprüfung.py",
            "Terminologie.txt", "Übersetzungsabgleich.md", "Fußnoten.md", "Abbildungsverzeichnis.md",
            "Tabellenverzeichnis.md", "Inhaltsverzeichnis.md", "Seitenumbrüche.md", "Druckfreigabe.md",
            "Korrekturlauf.py", "Änderungsliste.md", "Freigabevermerk.txt", "Versionsvergleich.py",
            "Abnahmeprotokoll.md", "Restpunkte.md", "Nacharbeit.md", "Schlussabnahme.md",
        ),
    ),
    "Setup": (
        "tiles",
        (
            "Zielpfade.lnk", "Versionen.ps1", "Erstkonfiguration.md", "Pfadvorgaben.txt",
            "Standardordner.lnk", "Sicherungsziel.lnk", "Startverhalten.md", "Tastenkürzel.md",
            "Anzeigeoptionen.md", "Wiederherstellung.ps1",
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


def _write_demo_targets(workspace: Path) -> dict[str, list[Path]]:
    """Legt je Board einen Ordner mit den Demo-Zieldateien an."""
    targets: dict[str, list[Path]] = {}
    for board, (_view, filenames) in BOARD_CATALOGUE.items():
        board_dir = workspace / board
        board_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for filename in filenames:
            path = board_dir / filename
            template = _CONTENT_BY_SUFFIX[path.suffix]
            path.write_text(template.format(label=path.stem), encoding="utf-8")
            paths.append(path)
        targets[board] = paths
    return targets


def _entry(path: Path, label: str, kind: str, notes: str | None = None) -> dict[str, str | None]:
    return {
        "path": str(path),
        "label": label,
        "kind": kind,
        "notes": notes,
    }


def _board_entries(paths: list[Path]) -> list[dict[str, str | None]]:
    return [_entry(path, path.stem, _KIND_BY_SUFFIX[path.suffix]) for path in paths]


def _configure_demo_window(window: MainWindow, targets: dict[str, list[Path]]) -> None:
    default_page = window.current_page()
    if default_page is None:
        raise RuntimeError("SoftwareCenter konnte keine Startseite erzeugen")

    boards = list(BOARD_CATALOGUE.items())
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
    """Verwirft ein von aussen gesetztes Offscreen-Plugin nur fuer diesen Block.

    Qt liest ``QT_QPA_PLATFORM`` beim Erzeugen der QApplication. Die Variable
    darf nicht dauerhaft aus der Umgebung verschwinden, sonst verliert ein
    umgebender Testlauf sein Headless-Setup.
    """
    previous = os.environ.get("QT_QPA_PLATFORM")
    if previous in HEADLESS_PLATFORMS:
        del os.environ["QT_QPA_PLATFORM"]
    try:
        yield
    finally:
        if previous is not None:
            os.environ["QT_QPA_PLATFORM"] = previous


def _require_real_gui(app: QtWidgets.QApplication) -> None:
    """Bricht laut ab, statt lautlos unlesbare Screenshots zu erzeugen."""
    platform = app.platformName()
    if platform in HEADLESS_PLATFORMS:
        raise RuntimeError(
            "Store-Screenshots brauchen eine echte GUI-Session. Aktives Qt-Plattform-Plugin: "
            f"'{platform}'. Offscreen-Rendering erzeugt Tofu-Kaestchen statt Text und wurde vom "
            "Windows Store nach Policy 10.1.1.3 abgelehnt."
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
        _require_real_gui(app)

        ini_path = str(temp_root / "softwarecenter.ini")

        # Schritt 1: Demo-Profil aufbauen und speichern.
        builder_settings = QtCore.QSettings(ini_path, QtCore.QSettings.IniFormat)
        builder = MainWindow(settings=builder_settings)
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
