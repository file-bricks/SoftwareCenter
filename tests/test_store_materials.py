"""
Tests for Windows Store materials and release readiness contract in SoftwareCenter.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_store_package_json_exists_and_valid():
    store_json_path = PROJECT_ROOT / "store_package.json"
    assert store_json_path.exists(), "store_package.json must exist in project root"

    with open(store_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("app_name") == "SoftwareCenter"
    assert data.get("publisher") == "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
    assert data.get("publisher_display") == "Geiger"
    assert data.get("identity_name") == "Geiger.SoftwareCenter"
    assert data.get("executable") == "SoftwareCenter.exe"
    assert data.get("capabilities") == "runFullTrust"
    assert data.get("category") == "Utilities & Tools"
    assert data.get("privacy_url", "").startswith("https://")
    assert data.get("support_url", "").startswith("https://")


def test_store_documentation_and_icon_assets_exist():
    required_files = [
        "store_package.json",
        "WINDOWS_STORE_PREP.md",
        "STORE_LISTING.md",
        "PRIVACY_POLICY.md",
        "SUPPORT.md",
        "SoftwareCenter.py",
        "icon.ico",
    ]
    for rel_path in required_files:
        path = PROJECT_ROOT / rel_path
        assert path.exists(), f"Required store release asset {rel_path} is missing"


def test_store_listing_content():
    store_listing_path = PROJECT_ROOT / "STORE_LISTING.md"
    assert store_listing_path.exists()
    content = store_listing_path.read_text(encoding="utf-8")
    assert "SoftwareCenter" in content
    assert "Features" in content or "Funktionen" in content
