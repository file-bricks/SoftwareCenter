#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Store Readiness Preflight Check for SoftwareCenter.

Validates that all necessary metadata, documentation files, licenses,
icon assets, manifest resources, and staged 6-language Store listings
required for Windows Store release are present, valid, and policy-compliant
(Policy P-006 / Tier-2 / Microsoft Partner Center Policy 10.1.3).
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TIER2_LANGUAGES = ("de-DE", "en-US", "es-ES", "zh-CN", "ja-JP", "ru-RU")


def check_store_package_json(project_root: Path) -> list[str]:
    errors = []
    file_path = project_root / "store_package.json"
    if not file_path.exists():
        errors.append("store_package.json is missing.")
        return errors

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"store_package.json is invalid JSON: {e}")
        return errors

    required_fields = [
        "app_name",
        "publisher",
        "publisher_display",
        "identity_name",
        "version",
        "description",
        "executable",
        "capabilities",
        "category",
        "age_rating",
        "privacy_url",
        "support_url",
        "license",
        "languages",
    ]
    for field in required_fields:
        val = data.get(field)
        if not val or (isinstance(val, str) and not val.strip()):
            errors.append(f"store_package.json missing or empty required field: '{field}'")

    if data.get("app_name") != "SoftwareCenter":
        errors.append(f"store_package.json app_name expected 'SoftwareCenter', got '{data.get('app_name')}'")

    if data.get("publisher") != "CN=52596601-BAB4-4F3F-B182-E8F3F273B202":
        errors.append(f"store_package.json publisher CN unexpected: {data.get('publisher')}")

    if data.get("publisher_display") != "Geiger":
        errors.append(f"store_package.json publisher_display expected 'Geiger', got '{data.get('publisher_display')}'")

    if data.get("identity_name") != "Geiger.SoftwareCenter":
        errors.append(f"store_package.json identity_name expected 'Geiger.SoftwareCenter', got '{data.get('identity_name')}'")

    if data.get("version") != "1.2.0.0":
        errors.append(f"store_package.json version expected '1.2.0.0', got '{data.get('version')}'")

    if data.get("capabilities") != "runFullTrust":
        errors.append(f"store_package.json capabilities expected 'runFullTrust', got '{data.get('capabilities')}'")

    # Check 6 languages list
    languages = data.get("languages", [])
    for lang in TIER2_LANGUAGES:
        if lang not in languages:
            errors.append(f"store_package.json languages missing '{lang}'")

    # Check 6 localized descriptions (max 100 chars per Policy 10.1.3)
    desc_keys = ["description_de", "description_en", "description_es", "description_zh", "description_ja", "description_ru"]
    for dkey in desc_keys:
        dval = data.get(dkey)
        if not dval:
            errors.append(f"store_package.json missing localized description '{dkey}'")
        elif len(dval) > 100:
            errors.append(f"store_package.json '{dkey}' exceeds 100 characters: {len(dval)} chars ('{dval}')")

    # Check 6 keyword sets (exactly 7 keywords each, max 30 chars each)
    kw_keys = ["keywords_de", "keywords_en", "keywords_es", "keywords_zh", "keywords_ja", "keywords_ru"]
    for kkey in kw_keys:
        klist = data.get(kkey)
        if not isinstance(klist, list):
            errors.append(f"store_package.json missing keyword list '{kkey}'")
        elif len(klist) != 7:
            errors.append(f"store_package.json '{kkey}' must contain exactly 7 keywords (got {len(klist)})")
        else:
            for kw in klist:
                if len(kw) > 30:
                    errors.append(f"store_package.json keyword in '{kkey}' exceeds 30 characters: '{kw}'")

    # URLs
    priv_url = data.get("privacy_url", "")
    if not priv_url.startswith("https://") or not priv_url.endswith("/PRIVACY_POLICY.md"):
        errors.append(f"store_package.json privacy_url invalid: '{priv_url}'")

    supp_url = data.get("support_url", "")
    if not supp_url.startswith("https://"):
        errors.append(f"store_package.json support_url invalid: '{supp_url}'")

    return errors


def check_appx_manifest(manifest_path: Path, expected_identity: str, expected_version: str) -> list[str]:
    errors = []
    if not manifest_path.exists():
        errors.append(f"Manifest missing: {manifest_path}")
        return errors

    try:
        content = manifest_path.read_text(encoding="utf-8")
        root = ET.fromstring(content)
    except Exception as e:
        errors.append(f"Manifest XML parsing failed for {manifest_path}: {e}")
        return errors

    # Check namespaces
    ns = {"m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10"}

    # Identity
    identity_elem = root.find("m:Identity", ns)
    if identity_elem is None:
        identity_elem = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Identity")
    if identity_elem is None:
        errors.append(f"Identity element missing in {manifest_path}")
    else:
        name = identity_elem.attrib.get("Name")
        if name != expected_identity:
            errors.append(f"Identity Name mismatch in {manifest_path}: expected '{expected_identity}', got '{name}'")
        ver = identity_elem.attrib.get("Version")
        if ver != expected_version:
            errors.append(f"Identity Version mismatch in {manifest_path}: expected '{expected_version}', got '{ver}'")
        pub = identity_elem.attrib.get("Publisher")
        if pub != "CN=52596601-BAB4-4F3F-B182-E8F3F273B202":
            errors.append(f"Publisher mismatch in {manifest_path}: got '{pub}'")

    # Capabilities
    caps_elem = root.find("m:Capabilities", ns)
    if caps_elem is None:
        caps_elem = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Capabilities")
    if caps_elem is None:
        errors.append(f"Capabilities element missing in {manifest_path}")
    else:
        has_full_trust = False
        for child in caps_elem:
            if child.attrib.get("Name") == "runFullTrust" or (child.tag.endswith("Capability") and child.attrib.get("Name") == "runFullTrust"):
                has_full_trust = True
                break
        if not has_full_trust:
            errors.append(f"Missing runFullTrust capability in {manifest_path}")

    # Resources (must cover all 6 languages)
    res_elem = root.find("m:Resources", ns)
    if res_elem is None:
        res_elem = root.find("{http://schemas.microsoft.com/appx/manifest/foundation/windows10}Resources")
    if res_elem is None:
        errors.append(f"Resources element missing in {manifest_path}")
    else:
        found_langs = {r.attrib.get("Language", "").lower() for r in res_elem if "Language" in r.attrib}
        for lang in TIER2_LANGUAGES:
            if lang.lower() not in found_langs:
                errors.append(f"Manifest {manifest_path.name} missing Resource Language '{lang}' (found: {found_langs})")

    return errors


def check_store_assets(project_root: Path) -> list[str]:
    errors = []
    assets_dir = project_root / "store_assets"
    if not assets_dir.exists():
        errors.append("store_assets/ directory missing.")
        return errors

    required_assets = [
        "StoreLogo.png",
        "Square44x44Logo.png",
        "Square50x50Logo.png",
        "Square150x150Logo.png",
        "Wide310x150Logo.png",
        "Square310x310Logo.png",
    ]
    for asset in required_assets:
        p = assets_dir / asset
        if not p.exists():
            errors.append(f"store_assets missing required logo asset: '{asset}'")
        elif p.stat().st_size == 0:
            errors.append(f"store_assets logo asset is empty: '{asset}'")

    return errors


def check_store_listings_and_staging(project_root: Path) -> list[str]:
    errors = []
    # 1. Main STORE_LISTING.md
    listing_file = project_root / "STORE_LISTING.md"
    if not listing_file.exists():
        errors.append("STORE_LISTING.md is missing.")
    else:
        text = listing_file.read_text(encoding="utf-8")
        for lang_header in ["Deutsch", "English", "Español", "简体中文", "日本語", "Русский"]:
            if lang_header not in text:
                errors.append(f"STORE_LISTING.md missing section for '{lang_header}'")

    # 2. Staging directory releases/windowsstore/
    staging_dir = project_root / "releases" / "windowsstore"
    if not staging_dir.exists():
        errors.append("releases/windowsstore/ staging directory is missing.")
        return errors

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
        if not fpath.exists():
            errors.append(f"releases/windowsstore missing staged file: '{fname}'")
        elif fpath.stat().st_size == 0:
            errors.append(f"releases/windowsstore staged file is empty: '{fname}'")

    # Verify store_settings.json
    settings_file = staging_dir / "store_settings.json"
    if settings_file.exists():
        try:
            sdata = json.loads(settings_file.read_text(encoding="utf-8"))
            if sdata.get("identity_name") != "Geiger.SoftwareCenter":
                errors.append(f"store_settings.json identity_name mismatch: '{sdata.get('identity_name')}'")
            if sdata.get("version") != "1.2.0.0":
                errors.append(f"store_settings.json version mismatch: '{sdata.get('version')}'")
            if sdata.get("capabilities") != "runFullTrust":
                errors.append(f"store_settings.json capabilities mismatch: '{sdata.get('capabilities')}'")
        except Exception as e:
            errors.append(f"releases/windowsstore/store_settings.json invalid JSON: {e}")

    return errors


def check_translations_parity(project_root: Path) -> list[str]:
    errors = []
    trans_file = project_root / "locales" / "translations.json"
    if not trans_file.exists():
        errors.append("locales/translations.json is missing.")
        return errors

    try:
        data = json.loads(trans_file.read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"locales/translations.json is invalid JSON: {e}")
        return errors

    langs = ["de", "en", "es", "zh", "ja", "ru"]
    for key, val in data.items():
        if not isinstance(val, dict):
            errors.append(f"Translation entry for '{key}' is not a dict")
            continue
        for lang_code in langs:
            translated = val.get(lang_code) or (val.get("zh-Hans") if lang_code == "zh" else None)
            if not translated or not str(translated).strip():
                errors.append(f"Missing translation for key '{key}' in language '{lang_code}'")

    return errors


def run_all_checks(project_root: Path | None = None) -> tuple[int, list[str]]:
    if project_root is None:
        project_root = PROJECT_ROOT

    all_errors = []

    # 1. store_package.json
    all_errors.extend(check_store_package_json(project_root))

    # 2. Manifests
    manifest_sc = project_root / "store_package" / "SoftwareCenter" / "AppxManifest.xml"
    all_errors.extend(
        check_appx_manifest(
            manifest_sc,
            expected_identity="Geiger.SoftwareCenter",
            expected_version="1.2.0.0",
        )
    )
    manifest_wartung = project_root / "_WARTUNG" / "msix_staging" / "AppxManifest.xml"
    if manifest_wartung.exists():
        all_errors.extend(
            check_appx_manifest(
                manifest_wartung,
                expected_identity="Geiger.SoftwareCenter",
                expected_version="1.2.0.0",
            )
        )

    # 3. Store assets
    all_errors.extend(check_store_assets(project_root))

    # 4. Listings & Staging
    all_errors.extend(check_store_listings_and_staging(project_root))

    # 5. Translations parity
    all_errors.extend(check_translations_parity(project_root))

    return len(all_errors), all_errors


def main() -> int:
    error_count, errors = run_all_checks()
    if error_count == 0:
        print("[OK] STORE READINESS CHECK PASSED (0 findings).")
        print("     All metadata, Tier-2 6-language listings, manifests, and assets compliant.")
        return 0
    else:
        print(f"[FAIL] STORE READINESS CHECK FAILED ({error_count} findings):")
        for err in errors:
            print(f"  - {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
