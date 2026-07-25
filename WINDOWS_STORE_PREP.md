# Windows Store Release Preparation — SoftwareCenter

**App Name:** SoftwareCenter  
**Package Identity:** Geiger.SoftwareCenter  
**Publisher:** CN=52596601-BAB4-4F3F-B182-E8F3F273B202  
**Publisher Display Name:** Geiger  
**Executable:** SoftwareCenter.exe  
**Capabilities:** runFullTrust  
**Category:** Utilities & Tools  
**Age Rating:** 3+  

---

## 1. Store Materials Overview

- `store_package.json`: Canonical Store package configuration file.
- `STORE_LISTING.md`: Store description (German & English), feature list, and keywords.
- `PRIVACY_POLICY.md`: Public privacy policy link required by Microsoft Store.
- `SUPPORT.md`: Support contact and issue reporting links.
- `tests/test_store_materials.py`: Automated contract tests for store assets, package config, and listings.

## 2. Store Assets & Icons

- Primary App Icon: `icon.ico` (512x512 / multi-resolution ICO)
- Desktop Icon: `DesktopIcon.ico`
- Store Listing Screenshots: `README/screenshots/store/` (generated via `generate_store_screenshots.py`)

## 3. Verification & Compliance

- Package schema: `store_package.json`
- WACK Preflight: `scripts/run_windows_wack.py`
- Test Coverage: `tests/test_store_materials.py`
