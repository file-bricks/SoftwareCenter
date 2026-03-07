# SoftwareCenter

A lightweight, cross-platform desktop organizer for managing software shortcuts with tab-based categorization.

## Features

- **Tab Organization** - Group programs into renamable, rearrangeable tabs
- **Drag & Drop** - Add files via drag & drop
- **Two View Modes** - Tiles (large icons) and list
- **Auto-Save** - Tabs, contents, and window position are preserved
- **Context Menu** - Right-click to open or remove
- **Cross-Platform** - Windows, macOS, and Linux
- **Native Icons** - Automatic display of system application icons

## Installation

### Requirements

- Python 3.10+
- PySide6

```bash
pip install -r requirements.txt
```

### Run

```bash
python SoftwareCenter.py
```

On Windows, also via `START.bat` or the precompiled `SoftwareCenter.exe` from the [Releases](https://github.com/lukisch/SoftwareCenter/releases).

## Usage

| Action | Instructions |
|--------|-------------|
| Add programs | Drag files (EXE, scripts, etc.) into the window |
| Organize tabs | Toolbar > "New Tab", double-click to rename |
| Switch view | Toolbar > Tiles / List |
| Launch programs | Double-click or right-click > Open/Run |
| Remove entries | Right-click > Delete (removes only the shortcut) |

## Build Executable

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name=SoftwareCenter SoftwareCenter.py
```

The EXE will be located in `dist/`.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| GUI Framework | PySide6 (Qt for Python) |
| Storage | QSettings (Windows Registry / INI) |
| Codebase | ~350 lines |

## License

This project is licensed under the [MIT License](LICENSE).

**Note:** This application uses [PySide6](https://doc.qt.io/qtforpython-6/), licensed under LGPLv3. PySide6 is dynamically linked and not included in this repository.

---

Deutsche Version: [README.de.md](README.de.md)
