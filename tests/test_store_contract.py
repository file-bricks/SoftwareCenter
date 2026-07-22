"""Regression contract for versioned SoftwareCenter Store metadata."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_store_package_is_the_documented_canonical_contract():
    package = json.loads((ROOT / "store_package.json").read_text(encoding="utf-8"))
    listing = (ROOT / "STORE_LISTING.md").read_text(encoding="utf-8")
    contract = (ROOT / "STORE_CONTRACT.md").read_text(encoding="utf-8")

    assert package["app_name"] == "SoftwareCenter"
    assert package["publisher"] == "CN=52596601-BAB4-4F3F-B182-E8F3F273B202"
    assert package["publisher_display"] == "Geiger"
    assert package["identity_name"] == "Geiger.SoftwareCenter"
    assert package["version"] == "1.0.0.0"
    assert package["executable"] == "SoftwareCenter.exe"
    assert package["capabilities"] == "runFullTrust"
    assert package["category"] == "Utilities & Tools"
    assert package["privacy_url"].endswith("/PRIVACY_POLICY.md")
    assert package["support_url"].endswith("/issues")

    assert "### Category\nUtilities & Tools" in listing
    assert "`store_package.json` ist die kanonische" in contract
    assert "`runFullTrust`" in contract
