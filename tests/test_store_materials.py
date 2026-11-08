"""
Tests for Windows Store materials and release readiness contract in SoftwareCenter.
Prüft Vollständigkeit, Tier-2 6-Sprachen-Harmonisierung (Policy P-006),
Partner-Center-Richtlinie 10.1.3 Keyword-Compliance und Staging-Konsistenz.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TIER2_LANGUAGES = ("de-DE", "en-US", "es-ES", "zh-CN", "ja-JP", "ru-RU")


def test_store_package_json_exists_and_valid():
    store_json_path = PROJECT_ROOT / "store_package.json"
    assert store_json_path.exists(), "store_package.json must exist in project root"

    with open(store_json_path, encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("app_name") == "SoftwareCenter"
    assert data.get("publisher") == "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
    assert data.get("publisher_display") == "Geiger"
    assert data.get("identity_name") == "Geiger.SoftwareCenter"
    assert data.get("executable") == "SoftwareCenter.exe"
    assert data.get("capabilities") == "runFullTrust"
    assert data.get("category") == "Utilities & Tools"
    assert data.get("license") == "MIT"
    assert data.get("pricing") == "Free"
    assert data.get("store_id") == "9NHZN7S3FD5F"
    assert data.get("privacy_url", "").startswith("https://")
    assert data.get("privacy_url", "").endswith("/PRIVACY_POLICY.md")
    assert data.get("support_url", "").startswith("https://")


def test_store_package_tier2_languages_and_char_limits():
    store_json_path = PROJECT_ROOT / "store_package.json"
    with open(store_json_path, encoding="utf-8") as f:
        data = json.load(f)

    # 1. Languages list
    languages = data.get("languages", [])
    for lang in TIER2_LANGUAGES:
        assert lang in languages, f"Missing language '{lang}' in store_package.json"

    # 2. Localized short descriptions (max 100 characters per Policy 10.1.3)
    desc_keys = ["description_de", "description_en", "description_es", "description_zh", "description_ja", "description_ru"]
    for dkey in desc_keys:
        assert dkey in data, f"Missing '{dkey}' in store_package.json"
        val = data[dkey]
        assert isinstance(val, str) and len(val) > 0, f"'{dkey}' is empty"
        assert len(val) <= 100, f"'{dkey}' exceeds 100 characters ({len(val)} chars)"

    # 3. Localized keywords (exactly 7 keywords per language, each <= 30 chars)
    kw_keys = ["keywords_de", "keywords_en", "keywords_es", "keywords_zh", "keywords_ja", "keywords_ru"]
    for kkey in kw_keys:
        assert kkey in data, f"Missing '{kkey}' in store_package.json"
        klist = data[kkey]
        assert isinstance(klist, list), f"'{kkey}' must be a list"
        assert len(klist) == 7, f"'{kkey}' must contain exactly 7 keywords, got {len(klist)}"
        for kw in klist:
            assert isinstance(kw, str) and len(kw) > 0, f"Empty keyword in '{kkey}'"
            assert len(kw) <= 30, f"Keyword '{kw}' in '{kkey}' exceeds 30 characters"


def test_appx_manifest_resources_contain_all_six_languages():
    manifest_path = PROJECT_ROOT / "store_package" / "SoftwareCenter" / "AppxManifest.xml"
    assert manifest_path.exists(), f"AppxManifest.xml missing at {manifest_path}"
    root = ET.fromstring(manifest_path.read_text(encoding="utf-8"))
    res_elem = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Resources")
    assert res_elem is not None, f"Resources element missing in {manifest_path}"
    found_langs = {r.attrib.get("Language", "").lower() for r in res_elem if "Language" in r.attrib}
    for lang in TIER2_LANGUAGES:
        assert lang.lower() in found_langs, f"AppxManifest.xml missing Resource Language '{lang}' (found: {found_langs})"


def test_store_documentation_and_icon_assets_exist():
    required_files = [
        "store_package.json",
        "WINDOWS_STORE_PREP.md",
        "STORE_LISTING.md",
        "PRIVACY_POLICY.md",
        "SUPPORT.md",
        "SoftwareCenter.py",
        "icon.ico",
        "store_assets/StoreLogo.png",
        "store_assets/Square44x44Logo.png",
        "store_assets/Square50x50Logo.png",
        "store_assets/Square150x150Logo.png",
        "store_assets/Wide310x150Logo.png",
        "store_assets/Square310x310Logo.png",
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
    # Verify all 6 Tier-2 languages are represented
    for lang_header in ["Deutsch", "English", "Español", "简体中文", "日本語", "Русский"]:
        assert lang_header in content, f"STORE_LISTING.md missing section for '{lang_header}'"


def test_staging_directory_and_store_settings_parity():
    staging_dir = PROJECT_ROOT / "releases" / "windowsstore"
    assert staging_dir.exists(), "releases/windowsstore/ missing"

    required_staging_files = [
        "BUILD.md",
        "WACK_PROTOCOL.md",
        "store_settings.json",
        "StoreLogo.png",
        "store_listing_de.md",
        "store_listing_en.md",
        "store_listing_es.md",
        "store_listing_zh.md",
        "store_listing_ja.md",
        "store_listing_ru.md",
    ]
    for fname in required_staging_files:
        fpath = staging_dir / fname
        assert fpath.exists(), f"Missing staging file: {fname}"
        assert fpath.stat().st_size > 0, f"Empty staging file: {fname}"

    settings_file = staging_dir / "store_settings.json"
    with open(settings_file, encoding="utf-8") as f:
        sdata = json.load(f)
    assert sdata.get("identity_name") == "Geiger.SoftwareCenter"
    assert sdata.get("version") == "1.2.0.0"
    assert sdata.get("capabilities") == "runFullTrust"
    assert sdata.get("store_id") == "9NHZN7S3FD5F"


def test_check_store_readiness_script_passes():
    import sys
    scripts_dir = PROJECT_ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import check_store_readiness

    error_count, errors = check_store_readiness.run_all_checks(PROJECT_ROOT)
    assert error_count == 0, f"check_store_readiness reported {error_count} findings: {errors}"
