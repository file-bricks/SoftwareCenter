"""Automated security, dependency floor, and third-party license contract tests for SoftwareCenter."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dependency_vulnerability_floors() -> None:
    """Verify requirements.txt and pyproject.toml enforce patched dependency floors against CVEs."""
    req_file = ROOT / "requirements.txt"
    assert req_file.is_file(), "requirements.txt must exist"
    req_text = req_file.read_text(encoding="utf-8")

    assert re.search(r"^PySide6\s*>=\s*6\.5\.0", req_text, re.MULTILINE), (
        "requirements.txt must enforce PySide6>=6.5.0 floor"
    )

    pyproject_file = ROOT / "pyproject.toml"
    assert pyproject_file.is_file(), "pyproject.toml must exist"
    pyproject_text = pyproject_file.read_text(encoding="utf-8")

    # PEP 621 dependencies section
    assert "dependencies = [" in pyproject_text, "pyproject.toml must define project.dependencies"
    assert "PySide6>=6.5.0" in pyproject_text, "pyproject.toml must specify PySide6>=6.5.0"

    # Optional dependencies with hardened floors
    assert "[project.optional-dependencies]" in pyproject_text, "pyproject.toml must define optional-dependencies"
    # pytest >= 9.1.1 protects against CVE-2025-7117 / GHSA-6w46-j5rx-g56g
    assert "pytest>=9.1.1" in pyproject_text, "pyproject.toml test dependencies must require pytest>=9.1.1"
    assert "ruff>=0.9.0" in pyproject_text, "pyproject.toml test dependencies must require ruff>=0.9.0"
    # Pillow >= 12.3.0 protects icon & asset generators against known Pillow CVEs
    assert "Pillow>=12.3.0" in pyproject_text, "pyproject.toml test dependencies must require Pillow>=12.3.0"
    assert "PyInstaller>=6.10.0" in pyproject_text, "pyproject.toml build dependencies must require PyInstaller>=6.10.0"
    assert "altgraph>=0.17.4" in pyproject_text, "pyproject.toml build dependencies must require altgraph>=0.17.4"
    assert "support@lukasgeiger.com" in pyproject_text, "pyproject.toml must specify official maintainer support email"


def test_third_party_licenses_complete_and_accurate() -> None:
    """Verify THIRD_PARTY_LICENSES.txt comprehensively covers runtime, transitive, build, and test packages."""
    license_file = ROOT / "THIRD_PARTY_LICENSES.txt"
    assert license_file.is_file(), "THIRD_PARTY_LICENSES.txt must exist"
    content = license_file.read_text(encoding="utf-8")

    required_packages = [
        ("PySide6", "LGPL-3.0-only"),
        ("PySide6_Addons", "LGPL-3.0-only"),
        ("PySide6_Essentials", "LGPL-3.0-only"),
        ("shiboken6", "LGPL-3.0-only"),
        ("pywin32", "PSF-2.0"),
        ("pytest", "MIT"),
        ("pluggy", "MIT"),
        ("iniconfig", "MIT"),
        ("ruff", "MIT OR Apache-2.0"),
        ("Pillow", "HPND-sell-variant"),
        ("PyInstaller", "GPL-2.0-or-later WITH Bootloader-exception"),
        ("pyinstaller-hooks-contrib", "Apache-2.0"),
        ("altgraph", "MIT"),
        ("packaging", "Apache-2.0 OR BSD-2-Clause"),
    ]

    for pkg, spdx in required_packages:
        assert pkg in content, f"Package {pkg} missing from THIRD_PARTY_LICENSES.txt"
        assert spdx in content, f"SPDX identifier {spdx} for {pkg} missing from THIRD_PARTY_LICENSES.txt"

    # Ensure structured schema fields exist
    assert "License:" in content, "License: field missing in THIRD_PARTY_LICENSES.txt"
    assert "URL:" in content, "URL: field missing in THIRD_PARTY_LICENSES.txt"
    assert "SPDX:" in content, "SPDX: field missing in THIRD_PARTY_LICENSES.txt"
    assert "Notice:" in content, "Notice: field missing in THIRD_PARTY_LICENSES.txt"
    assert "MIT Compatibility" in content, "MIT compatibility section missing in THIRD_PARTY_LICENSES.txt"


def test_gitignore_security_and_multi_host_hardening() -> None:
    """Verify .gitignore blocks private secrets, test run artifacts, and multi-host conflict files."""
    gitignore_file = ROOT / ".gitignore"
    assert gitignore_file.is_file(), ".gitignore must exist"
    content = gitignore_file.read_text(encoding="utf-8")

    # Secrets and certificate protection
    for pat in ["credentials.json", "*.pfx", "*.p12", "*.cer", "*.crt", "*.pem", "*.key", "keyring/", "secrets.*"]:
        assert pat in content, f"Secret pattern {pat} missing in .gitignore"

    # Multi-host sync hardening
    for host_pat in ["*-WORKSTATION-LG*", "*-ASUS-GEI*", "*.sync-conflict-*", "*.conflict", "*-conflict-*"]:
        assert host_pat in content, f"Sync conflict pattern {host_pat} missing in .gitignore"

    # Multi-agent lock system fail-closed patterns
    for lock_pat in ["LOCK.*", "*.lock", "LOCK*.txt"]:
        assert lock_pat in content, f"Lock pattern {lock_pat} missing in .gitignore"

    # Test runner output protection
    for test_pat in [".pytest_cache/", "pytest_out.txt", "pytest*.txt"]:
        assert test_pat in content, f"Test output pattern {test_pat} missing in .gitignore"


def test_no_hardcoded_user_paths_in_python_code() -> None:
    """Verify no hardcoded personal user profile paths (e.g. C:\\Users\\lukas) exist in active Python source."""
    disallowed_regex = re.compile(r"""(?i)C:[/\\]Users[/\\](?:lukas|admin|administrator)[/\\]""", re.VERBOSE)

    # Collect Python files across the codebase
    python_files = list(ROOT.glob("*.py"))
    for sub in ["tests", "tools", "scripts"]:
        sub_path = ROOT / sub
        if sub_path.is_dir():
            python_files.extend(sub_path.rglob("*.py"))

    assert len(python_files) >= 15, f"Expected >=15 Python files to scan, found {len(python_files)}"

    violating_lines = []
    for py_file in python_files:
        if not py_file.is_file():
            continue
        try:
            text = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        for idx, line in enumerate(text.splitlines(), 1):
            if disallowed_regex.search(line):
                violating_lines.append(f"{py_file.name}:{idx}: {line.strip()}")

    assert not violating_lines, "Found hardcoded user paths in Python code:\n" + "\n".join(violating_lines)


def test_security_policy_bilingual_and_sla() -> None:
    """Verify SECURITY.md maintains strict SLA, non-elevation guarantees, and designated response channels."""
    sec_file = ROOT / "SECURITY.md"
    assert sec_file.is_file(), "SECURITY.md must exist"
    content = sec_file.read_text(encoding="utf-8")

    # Bilingual structure
    assert "## English" in content, "SECURITY.md must have English section"
    assert "## Deutsch" in content, "SECURITY.md must have Deutsch section"

    # Designated response channels
    assert "security@file-bricks.org" in content, "security@file-bricks.org contact missing"
    assert "security@open-bricks.org" in content, "security@open-bricks.org contact missing"
    assert "security@ellmos.ai" in content, "security@ellmos.ai contact missing"
    assert "support@lukasgeiger.com" in content, "support@lukasgeiger.com contact missing"

    # Strict SLA commitments
    assert "48" in content, "48h initial acknowledgment SLA missing"
    assert "5" in content, "5-day triage commitment missing"

    # GitHub advisories link
    assert "security/advisories/new" in content, "Private vulnerability reporting link missing"


def test_local_first_and_offline_invariants() -> None:
    """Verify SoftwareCenter preserves offline, zero-egress, and non-elevation guarantees."""
    sec_file = ROOT / "SECURITY.md"
    assert sec_file.is_file()
    content = sec_file.read_text(encoding="utf-8")

    assert "Local-First" in content or "lokal" in content
    assert "Zero" in content or "Null Datenausleitung" in content or "Zero-Egress" in content
    assert "Non-Elevation" in content or "Unprivilegierter Betrieb" in content

    # Check that production source files don't reference unauthorized third-party telemetry services
    disallowed_endpoints = [
        "google-analytics.com",
        "segment.io",
        "mixpanel.com",
        "sentry.io",
        "amplitude.com",
    ]

    prod_files = list(ROOT.glob("*.py"))
    for sub in ["tools", "scripts"]:
        sub_path = ROOT / sub
        if sub_path.is_dir():
            prod_files.extend(sub_path.rglob("*.py"))

    for f in prod_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for ep in disallowed_endpoints:
            assert ep not in text.lower(), f"Unauthorized telemetry endpoint {ep} found in {f.name}"


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main(["-v", __file__]))
