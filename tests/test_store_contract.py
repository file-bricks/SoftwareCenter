"""Regression contract for versioned SoftwareCenter Store metadata.

STORE_CONTRACT.md and _WARTUNG/msix_staging/ (staged MSIX build output) were
untracked as agent-internal / build-artifact material (T-20260926-510472849,
GITHUB-POLICY.md SS3). This contract now checks only files that stay public:
store_package.json, pyproject.toml, SoftwareCenter.py, and STORE_LISTING.md.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _runtime_version() -> str:
    source = (ROOT / "SoftwareCenter.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', source, re.MULTILINE)
    assert match, "__version__ nicht in SoftwareCenter.py gefunden"
    return match.group(1)


def _project_version() -> str:
    source = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', source, re.MULTILINE)
    assert match, "version nicht in pyproject.toml gefunden"
    return match.group(1)


def test_store_package_is_the_documented_canonical_contract():
    package = json.loads((ROOT / "store_package.json").read_text(encoding="utf-8"))
    listing = (ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")

    assert package["app_name"] == "SoftwareCenter"
    assert package["publisher"] == "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
    assert package["publisher_display"] == "Geiger"
    assert package["identity_name"] == "Geiger.SoftwareCenter"
    assert package["version"] == "1.2.0.0"
    assert package["executable"] == "SoftwareCenter.exe"
    assert package["capabilities"] == "runFullTrust"
    assert package["category"] == "Utilities & Tools"
    assert package["privacy_url"].endswith("/PRIVACY_POLICY.md")
    assert package["support_url"].endswith("/issues")

    assert "### Category\nUtilities & Tools" in listing


def test_version_is_identical_in_every_store_relevant_source():
    """Die Store-Einreichung 2026-08-11 lief als 1.2.0.0, waehrend die Runtime noch
    1.0.0 meldete. Dieser Test haelt die Quellen zusammen, damit die Luecke nicht
    unbemerkt wiederkommt."""
    package = json.loads((ROOT / "store_package.json").read_text(encoding="utf-8"))
    runtime = _runtime_version()
    project = _project_version()
    four_part = f"{runtime}.0"

    assert runtime == project, f"SoftwareCenter.py {runtime} != pyproject.toml {project}"
    assert package["version"] == four_part

    listing = (ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")
    assert f"| Version | {four_part} |" in listing
