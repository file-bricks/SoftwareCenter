from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from scripts.project_version import read_project_version


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_version_reader_matches_pyproject() -> None:
    pyproject = PROJECT_ROOT / "pyproject.toml"

    assert read_project_version(pyproject) == "1.2.0"
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "project_version.py"), str(pyproject)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "1.2.0"


def test_build_script_uses_current_version_for_release_artifact() -> None:
    script = (PROJECT_ROOT / "build_exe.bat").read_text(encoding="utf-8")

    assert "scripts\\project_version.py" in script
    assert "releases\\v%APP_VERSION%" in script
    assert "SoftwareCenter-%APP_VERSION%-win64.exe" in script
    assert "releases\\v1.0.0" not in script
    assert "%SOFTWARE_ROOT%\\_tools\\build_exclude_scanner.py" in script
    assert "%OneDrive%\\.TOPICS\\.SOFTWARE\\_tools\\build_exclude_scanner.py" in script
    assert "%PROJECT_ROOT%\\..\\..\\_tools" not in script
