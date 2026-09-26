# Third-Party Licenses & Governance Statement

> **Project:** `file-bricks/SoftwareCenter`<br>
> **Audited:** 2026-09-23<br>
> **Repository License:** [MIT License](LICENSE)<br>
> **Attribution:** [NOTICE](NOTICE)<br>
> **Architecture & Privacy:** 100% Local-First, Zero-Egress, Unprivileged User-Mode (`RunAsInvoker`)<br>
> **Umbrella:** [open-bricks](https://github.com/open-bricks)

---

## Executive Summary & Compliance Assurance

`file-bricks/SoftwareCenter` is engineered as a lightweight, privacy-first, local-first desktop application organizer and launcher.

All runtime and development dependencies utilized in SoftwareCenter are distributed under well-established, permissive or reciprocal open-source licenses (MIT, PSF-2.0, LGPL-3.0, GPL-2.0-or-later with Exception, Apache-2.0).

SoftwareCenter strictly guarantees:
1. **100% Local-First & Zero Egress (INV-LOCAL-01):** All UI rendering, shortcut resolution, icon caching, and profile parsing execute strictly offline on the local workstation. The application initiates zero external network requests and contains no tracking or telemetry.
2. **Unprivileged Execution (`RunAsInvoker` / INV-SEC-02):** SoftwareCenter and launched applications run strictly in standard user mode without requesting administrative (UAC) elevation.
3. **Dynamic Linking & Zero-Copyleft Compliance (LGPL-3.0):** PySide6 (Qt for Python) is dynamically linked in compliance with LGPLv3 Section 4. The application source code is licensed under permissive MIT and is not affected by copyleft obligations. Users are free to replace Qt runtime shared libraries.
4. **Standalone PyInstaller Exemption:** Executable packaging via PyInstaller uses the standard PyInstaller exception to GPL-2.0-or-later, permitting independent binary distribution without licensing contagion.
5. **Non-Destructive Operations (INV-LAUNCH-04):** Managing or removing shortcuts never touches, modifies, or deletes the underlying executable or filesystem files.
6. **Machine-Readable Metadata & Internationalization Parity:** Complete metadata alignment across `llms.txt`, `CHANGELOG.md`, and Tier-2 6-language translations (`de`, `en`, `es`, `zh`, `ja`, `ru`).

---

## Runtime Dependency Matrix

| Package | Role / Functional Scope | License (SPDX) | Upstream Repository / Source |
|:---|:---|:---|:---|
| **PySide6** (>=6.0.0) | Cross-platform Qt6 GUI widgets, list/tile views, system tray integration, and event loop | [LGPL-3.0-only](https://www.gnu.org/licenses/lgpl-3.0.html) | [The Qt Company / PySide6](https://wiki.qt.io/Qt_for_Python) |
| **shiboken6** (>=6.0.0) | CPython/C++ binding generator and runtime bindings for PySide6 | [LGPL-3.0-only](https://www.gnu.org/licenses/lgpl-3.0.html) | [The Qt Company / Shiboken](https://wiki.qt.io/Qt_for_Python) |
| **Python Standard Library** | Core persistence (`json`, `configparser`), process execution (`subprocess`), path resolution (`pathlib`, `os`), and typing (`typing`) | [PSF-2.0](https://docs.python.org/3/license.html) | [Python Software Foundation](https://github.com/python/cpython) |

---

## Build & Quality Assurance Tooling

| Package | Usage & Purpose | License (SPDX) | Upstream Repository / Source |
|:---|:---|:---|:---|
| **PyInstaller** (>=6.0.0) | Standalone single-file executable packaging (`build_exe.bat` / `SoftwareCenter.spec`) | [GPL-2.0-or-later WITH PyInstaller-exception](https://pyinstaller.org/en/stable/license.html) | [PyInstaller Development Team](https://github.com/pyinstaller/pyinstaller) |
| **setuptools** (>=61.0) | PEP 517 / PEP 621 build backend and metadata specification | [MIT](https://github.com/pypa/setuptools/blob/main/LICENSE) | [Python Packaging Authority (PyPA)](https://github.com/pypa/setuptools) |
| **pytest** (>=8.0.0) | Automated test suite execution across unit, platform smoke, and contract tests | [MIT](https://github.com/pytest-dev/pytest/blob/main/LICENSE) | [pytest-dev / pytest](https://github.com/pytest-dev/pytest) |
| **ruff** (>=0.4.0) | Fast static analysis, linting, and Python code style enforcement | [MIT](https://github.com/astral-sh/ruff/blob/main/LICENSE-MIT) / [Apache-2.0](https://github.com/astral-sh/ruff/blob/main/LICENSE-APACHE) | [Astral / ruff](https://github.com/astral-sh/ruff) |

---

## Governance & Runtime Invariants

| ID | Invariant Name | Specification & Guarantee |
|:---|:---|:---|
| **INV-LOCAL-01** | **100% Local-First & Zero Egress** | Execution, icon extraction, and configuration parsing run strictly offline without outbound network calls or background telemetry. |
| **INV-SEC-02** | **Unprivileged Execution (`RunAsInvoker`)** | All operations and launched applications execute under standard unprivileged user security descriptors without requesting UAC elevation. |
| **INV-PROFILE-03** | **Portable Profile Redaction** | Profile exports (`softwarecenter-profile-v1.json`) serialize only user-defined board structures, paths, and labels, strictly excluding machine credentials or tokens. |
| **INV-LAUNCH-04** | **Working Directory Integrity** | Applications launched via `_startfile_in_dir` explicitly set target parent directory as CWD, preventing relative path breakages. |
| **INV-DUAL-05** | **Multi-Identity Boundary Isolation** | Absolute isolation between `SoftwareCenter` and sister profile `LaunchBoards` across QSettings namespaces, mutex names, and store packages. |
| **INV-A11Y-06** | **Accessibility & Navigation Parity** | Standard keyboard navigation, visible focus indicators, and accessible widget labels across both Tile and List modes. |
| **INV-HYGIENE-07** | **Multi-Host Conflict Guard** | Multi-host synchronization artifacts (`*-WORKSTATION*`, `*-ASUS-GEI*`, `*.sync-conflict-*`) are ignored and blocked by gitignore. |
| **INV-SLA-08** | **Security Response SLA** | Committed 48-hour response SLA and 5-business-day triage commitment for reported security vulnerabilities (`SECURITY.md`). |
| **INV-PARITY-09** | **Tier-2 Multi-Language Parity** | Complete 6-language translation catalog parity (`de`, `en`, `es`, `zh`, `ja`, `ru`) with deterministic 4-stage fallback and tri-lingual docs. |
| **INV-ZEROCOPY-10** | **Permissive Licensing & Zero Copyleft** | Permissive MIT codebase with dynamically linked LGPL-3.0 Qt components; clean separation of build-only tools under PyInstaller exception. |

---

## License Texts & Excerpts

### 1. GNU Lesser General Public License Version 3 (LGPL-3.0)
Used dynamically by `PySide6` and `shiboken6`. Under Section 4 of the LGPLv3, dynamic linking to unmodified shared libraries is permitted in proprietary and permissively licensed applications.

### 2. MIT License
Used by `file-bricks/SoftwareCenter`, `pytest`, `ruff`, and `setuptools`.

> Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### 3. GPL-2.0-or-later with PyInstaller Exception
Used by `PyInstaller` build tooling.
Under the PyInstaller exception, output executables produced by PyInstaller containing bundled user Python scripts and runtime interpreters are exempt from GPL copyleft requirements and can be distributed under the user's choice of license (MIT).

### 4. Python Software Foundation License Version 2 (PSF-2.0)
Used by the Python Standard Library.
