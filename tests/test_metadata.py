"""Contract test suite certifying discoverability, metadata, documentation parity, and security invariants for SoftwareCenter."""

import re
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[1]


def test_readme_files_exist_and_language_switch():
    readme_en = ROOT / "README.md"
    readme_de = ROOT / "README_de.md"
    readme_es = ROOT / "README.es.md"

    assert readme_en.exists(), "README.md must exist"
    assert readme_de.exists(), "README_de.md must exist"
    assert readme_es.exists(), "README.es.md must exist"

    text_en = readme_en.read_text(encoding="utf-8")
    text_de = readme_de.read_text(encoding="utf-8")
    text_es = readme_es.read_text(encoding="utf-8")

    assert "[English](README.md)" in text_en
    assert "[Deutsch](README_de.md)" in text_en
    assert "[Español](README.es.md)" in text_en
    assert "[English](README.md)" in text_de
    assert "[Deutsch](README_de.md)" in text_de
    assert "[Español](README.es.md)" in text_de
    assert "[English](README.md)" in text_es
    assert "[Deutsch](README_de.md)" in text_es
    assert "[Español](README.es.md)" in text_es


def test_readme_quick_navigation_anchors():
    readme_en = ROOT / "README.md"
    readme_de = ROOT / "README_de.md"

    text_en = readme_en.read_text(encoding="utf-8")
    text_de = readme_de.read_text(encoding="utf-8")

    assert "## Quick Navigation" in text_en
    assert "## Schnellnavigation" in text_de

    # Verify key sections exist in English
    for anchor in [
        "#quick-reference",
        "#features",
        "#target-personas--discoverability",
        "#comparative-matrix-vs-alternatives",
        "#system-architecture",
        "#lifecycle-sequence-flow",
        "#core-capabilities--safety-invariants",
        "#sibling-ecosystem--sister-products",
        "#discovery-context",
        "#requirements",
        "#installation",
        "#run",
        "#usage",
        "#build-executable",
        "#quality-checks",
        "#security-policy",
        "#third-party-licenses--governance",
        "#license",
    ]:
        assert f"({anchor})" in text_en, f"Missing anchor {anchor} in README.md"

    # Verify key sections exist in German
    for anchor in [
        "#einstieg",
        "#funktionen",
        "#zielgruppen--auffindbarkeit",
        "#vergleichsmatrix-gegenüber-alternativen",
        "#systemarchitektur",
        "#lebenszyklus-ablaufdiagramm",
        "#kernfähigkeiten--sicherheitsinvarianten",
        "#geschwister-ökosystem--schwesterprodukte",
        "#auffindbarkeit",
        "#voraussetzungen",
        "#installation",
        "#starten",
        "#verwendung",
        "#exe-erstellen",
        "#qualitätssicherung",
        "#sicherheitsrichtlinie",
        "#drittanbieter-lizenzen--governance",
        "#lizenz",
    ]:
        assert f"({anchor})" in text_de, f"Missing anchor {anchor} in README_de.md"

    # Verify key sections exist in Spanish
    readme_es = ROOT / "README.es.md"
    text_es = readme_es.read_text(encoding="utf-8")
    assert "## Navegación rápida" in text_es
    for anchor in [
        "#referencia-rápida",
        "#características",
        "#personas-objetivo-y-descubribilidad",
        "#matriz-comparativa-frente-a-alternativas",
        "#arquitectura-del-sistema",
        "#flujo-del-ciclo-de-vida",
        "#capacidades-centrales-e-invariantes-de-seguridad",
        "#ecosistema-hermano-y-productos-relacionados",
        "#contexto-de-descubrimiento",
        "#requisitos",
        "#instalación",
        "#ejecución",
        "#uso",
        "#compilar-ejecutable",
        "#controles-de-calidad",
        "#política-de-seguridad",
        "#licencias-de-terceros-y-gobernanza",
        "#licencia",
    ]:
        assert f"({anchor})" in text_es, f"Missing anchor {anchor} in README.es.md"


def test_readme_contains_mermaid_diagrams():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")

    assert "```mermaid\ngraph TD" in text_en
    assert "```mermaid\nsequenceDiagram" in text_en

    assert "```mermaid\ngraph TD" in text_de
    assert "```mermaid\nsequenceDiagram" in text_de

    assert "```mermaid\ngraph TD" in text_es
    assert "```mermaid\nsequenceDiagram" in text_es


def test_readme_badges_parity_and_test_count():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")

    common_badges = [
        "python-3.10",
        "GUI-PySide6",
        "file--bricks",
        "open--bricks",
        "LLM-Ready",
    ]
    for badge in common_badges:
        assert badge in text_en, f"Missing badge {badge} in README.md"
        assert badge in text_de, f"Missing badge {badge} in README_de.md"
        assert badge in text_es, f"Missing badge {badge} in README.es.md"

    for text in [text_en, text_de, text_es]:
        assert "pytest-" in text

    assert "License-MIT" in text_en
    assert "Lizenz-MIT" in text_de or "License-MIT" in text_de
    assert "Licencia-MIT" in text_es or "License-MIT" in text_es


def test_security_policy_bilingual_and_sla_invariants():
    security_file = ROOT / "SECURITY.md"
    assert security_file.exists(), "SECURITY.md must exist"
    content = security_file.read_text(encoding="utf-8")

    # English & German sections
    assert "## English" in content
    assert "## Deutsch" in content

    # Supported versions
    assert "`1.2.x`" in content
    assert "`1.1.x`" in content

    # Response SLA & contacts
    assert "48 hours" in content or "48 Stunden" in content
    assert "security@open-bricks.org" in content
    assert "support@lukasgeiger.com" in content
    assert "lukas@open-bricks.org" in content

    # Security Invariants
    assert "Local-First" in content
    assert "Zero Network Egress" in content or "Zero Egress" in content
    assert "Non-Elevation" in content or "Unprivileged" in content


def test_pyproject_pep621_metadata_and_urls():
    pyproject_file = ROOT / "pyproject.toml"
    assert pyproject_file.exists(), "pyproject.toml must exist"

    data = tomllib.loads(pyproject_file.read_text(encoding="utf-8"))
    project = data["project"]

    assert project["name"] == "file-bricks-softwarecenter"
    assert project["version"] == "1.2.0"
    assert project["license"]["text"] == "MIT"

    urls = project["urls"]
    assert urls["Homepage"] == "https://github.com/file-bricks/SoftwareCenter"
    assert urls["Repository"] == "https://github.com/file-bricks/SoftwareCenter"
    assert urls["Documentation"] == "https://github.com/file-bricks/SoftwareCenter#readme"
    assert urls["Issues"] == "https://github.com/file-bricks/SoftwareCenter/issues"
    assert urls["Bug Tracker"] == "https://github.com/file-bricks/SoftwareCenter/issues"
    assert urls["Changelog"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/CHANGELOG.md"
    assert urls["Security"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/SECURITY.md"
    assert urls["Parent Organization"] == "https://github.com/file-bricks"
    assert urls["Umbrella Ecosystem"] == "https://github.com/open-bricks"
    assert urls["LLM Ready"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/llms.txt"
    assert urls["Marketing Log"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/MARKETING-LOG.txt"
    assert urls["Third-Party Licenses"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/THIRD_PARTY_LICENSES.md"

    classifiers = project["classifiers"]
    assert "Programming Language :: Python :: 3.13" in classifiers
    assert "Operating System :: OS Independent" in classifiers
    assert "Operating System :: Microsoft :: Windows" in classifiers
    assert "Operating System :: POSIX :: Linux" in classifiers
    assert "Operating System :: MacOS" in classifiers

    assert "ruff" in data.get("tool", {}), "tool.ruff must be configured"
    assert "lint" in data["tool"]["ruff"], "tool.ruff.lint must be configured"
    assert "select" in data["tool"]["ruff"]["lint"], "tool.ruff.lint.select must be defined"


def test_sibling_ecosystem_table_links():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")

    for sibling in [
        "https://github.com/file-bricks/ProFiler",
        "https://github.com/file-bricks/ExplorerPro",
        "https://github.com/file-bricks/CloudLockFixer",
        "https://github.com/file-bricks/knowledgedigest",
        "https://github.com/doc-bricks/FormularErstellen",
        "https://github.com/doc-bricks/USR_PDFunlock",
        "https://github.com/dev-bricks/safe-start-for-codex",
        "https://github.com/dev-bricks/MethodenAnalyser",
        "https://github.com/ellmos-ai/connectors",
        "https://github.com/open-bricks",
    ]:
        assert sibling in text_en, f"Missing sibling {sibling} in README.md"
        assert sibling in text_de, f"Missing sibling {sibling} in README_de.md"
        assert sibling in text_es, f"Missing sibling {sibling} in README.es.md"


def test_llms_txt_structure_and_timestamp():
    llms_file = ROOT / "llms.txt"
    assert llms_file.exists(), "llms.txt must exist"
    content = llms_file.read_text(encoding="utf-8")

    assert "## Last-checked: 2026-09-23" in content
    assert "https://github.com/file-bricks/SoftwareCenter" in content
    assert "THIRD_PARTY_LICENSES.md" in content
    assert "Disambiguation" in content
    assert "MARKETING-LOG.txt" in content


def test_changelog_recent_entry():
    changelog_file = ROOT / "CHANGELOG.md"
    assert changelog_file.exists(), "CHANGELOG.md must exist"
    content = changelog_file.read_text(encoding="utf-8")

    assert "2026-09-23" in content
    assert "2026-09-14" in content
    assert "Pfad B" in content
    assert "2026-09-11" in content
    assert "Pfad A" in content


def test_ci_workflow_guardrails():
    workflow_file = ROOT / ".github" / "workflows" / "tests.yml"
    assert workflow_file.exists(), "tests.yml must exist"
    content = workflow_file.read_text(encoding="utf-8")

    assert "concurrency:" in content
    assert "cancel-in-progress: true" in content
    assert "timeout-minutes: 15" in content
    assert "ruff check ." in content


def test_gitignore_multi_host_and_lock_hardening():
    gitignore_file = ROOT / ".gitignore"
    assert gitignore_file.exists(), ".gitignore must exist"
    content = gitignore_file.read_text(encoding="utf-8")

    assert "*-WORKSTATION*" in content
    assert "*-ASUS-GEI*" in content
    assert "*.sync-conflict-*" in content
    assert "LOCK.*" in content
    assert "uv.lock" in content
    assert ".coverage.*" in content


def test_marketing_log_contract_and_invariants():
    mkt_file = ROOT / "MARKETING-LOG.txt"
    assert mkt_file.exists(), "MARKETING-LOG.txt must exist"
    content = mkt_file.read_text(encoding="utf-8")

    assert "file-bricks/SoftwareCenter" in content
    assert "2026-09-23" in content
    assert "2026-09-14" in content
    assert "INV-LOCAL-01" in content
    assert "INV-SEC-02" in content
    assert "INV-PROFILE-03" in content
    assert "INV-LAUNCH-04" in content
    assert "INV-DUAL-05" in content
    assert "INV-PARITY-09" in content
    assert "INV-ZEROCOPY-10" in content


def test_target_personas_present_in_all_readmes():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")

    assert "Persona 1:" in text_en and "Persona 2:" in text_en and "Persona 3:" in text_en and "Persona 4:" in text_en
    assert "Persona 1:" in text_de and "Persona 2:" in text_de and "Persona 3:" in text_de and "Persona 4:" in text_de
    assert "Persona 1:" in text_es and "Persona 2:" in text_es and "Persona 3:" in text_es and "Persona 4:" in text_es


def test_comparative_matrix_present_in_all_readmes():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")

    for text in [text_en, text_de, text_es]:
        assert "Stardock Fences" in text
        assert "SyMenu" in text
        assert "Launchy / Flow Launcher" in text


def test_third_party_licenses_md_contract_and_invariants():
    tpl_file = ROOT / "THIRD_PARTY_LICENSES.md"
    assert tpl_file.exists(), "THIRD_PARTY_LICENSES.md must exist"
    content = tpl_file.read_text(encoding="utf-8")

    assert "PySide6" in content
    assert "shiboken6" in content
    assert "PyInstaller" in content
    assert "LGPL-3.0" in content
    assert "RunAsInvoker" in content

    # All 10 invariants verified
    for inv_id in [
        "INV-LOCAL-01",
        "INV-SEC-02",
        "INV-PROFILE-03",
        "INV-LAUNCH-04",
        "INV-DUAL-05",
        "INV-A11Y-06",
        "INV-HYGIENE-07",
        "INV-SLA-08",
        "INV-PARITY-09",
        "INV-ZEROCOPY-10",
    ]:
        assert inv_id in content, f"Missing {inv_id} in THIRD_PARTY_LICENSES.md"


def test_third_party_licenses_referenced_in_all_readmes():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")

    for text in [text_en, text_de, text_es]:
        assert "[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)" in text


def test_git_hygiene_no_sync_conflicts():
    patterns = [
        re.compile(r".*\.sync-conflict-.*", re.IGNORECASE),
        re.compile(r".*\.conflict$", re.IGNORECASE),
        re.compile(r".*-CONFLIT-.*", re.IGNORECASE),
    ]

    for item in ROOT.rglob("*"):
        if ".git" in item.parts or "__pycache__" in item.parts or ".pytest_cache" in item.parts:
            continue
        for pattern in patterns:
            assert not pattern.match(item.name), f"Detected sync conflict artifact: {item}"


def test_notice_attribution_contract():
    notice_file = ROOT / "NOTICE"
    assert notice_file.exists(), "NOTICE file must exist"
    content = notice_file.read_text(encoding="utf-8")

    assert "SoftwareCenter" in content
    assert "Lukas Geiger" in content
    assert "file-bricks" in content
    assert "open-bricks" in content
    assert "MIT License" in content


def test_notice_referenced_in_readmes_and_pyproject():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")
    text_es = (ROOT / "README.es.md").read_text(encoding="utf-8")
    for text in [text_en, text_de, text_es]:
        assert "(NOTICE)" in text

    pyproject_file = ROOT / "pyproject.toml"
    assert pyproject_file.exists(), "pyproject.toml must exist"
    pyproject_text = pyproject_file.read_text(encoding="utf-8")
    pyproject_data = tomllib.loads(pyproject_text)

    license_files = pyproject_data.get("project", {}).get("license-files", [])
    assert "NOTICE" in license_files
    urls = pyproject_data.get("project", {}).get("urls", {})
    assert "Notice" in urls


def test_ci_lifecycle_workflows():
    stale_file = ROOT / ".github" / "workflows" / "stale.yml"
    assert stale_file.exists(), "stale.yml must exist"
    stale_content = stale_file.read_text(encoding="utf-8")
    assert "concurrency:" in stale_content
    assert "cancel-in-progress: true" in stale_content
    assert "timeout-minutes: 10" in stale_content

    welcome_file = ROOT / ".github" / "workflows" / "welcome.yml"
    assert welcome_file.exists(), "welcome.yml must exist"
    welcome_content = welcome_file.read_text(encoding="utf-8")
    assert "concurrency:" in welcome_content
    assert "cancel-in-progress: true" in welcome_content
    assert "timeout-minutes: 5" in welcome_content


def test_extended_gitignore_multi_host_and_lock_defense():
    gitignore_file = ROOT / ".gitignore"
    assert gitignore_file.exists(), ".gitignore must exist"
    content = gitignore_file.read_text(encoding="utf-8")

    required_patterns = [
        "*conflicted copy*",
        "*-ASUS*",
        "*-LAPTOP*",
        "*-Mac Studio*",
        "*-MacBook*",
        "*.rej",
        "*.orig",
        "LOCK.user.*",
        "LOCK.until.*",
        "LOCK.condition.*",
        ".automation-lock",
        "!package-lock.json",
    ]
    for pat in required_patterns:
        assert pat in content, f"Missing pattern {pat} in .gitignore"
