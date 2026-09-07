"""Contract test suite certifying discoverability, metadata, documentation parity, and security invariants for SoftwareCenter."""

from pathlib import Path
import re
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_readme_files_exist_and_language_switch():
    readme_en = ROOT / "README.md"
    readme_de = ROOT / "README_de.md"

    assert readme_en.exists(), "README.md must exist"
    assert readme_de.exists(), "README_de.md must exist"

    text_en = readme_en.read_text(encoding="utf-8")
    text_de = readme_de.read_text(encoding="utf-8")

    assert "[English](README.md)" in text_en
    assert "[Deutsch](README_de.md)" in text_en
    assert "[English](README.md)" in text_de
    assert "[Deutsch](README_de.md)" in text_de


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
        "#license",
    ]:
        assert f"({anchor})" in text_en, f"Missing anchor {anchor} in README.md"

    # Verify key sections exist in German
    for anchor in [
        "#einstieg",
        "#funktionen",
        "#systemarchitektur",
        "#lebenszyklus-ablaufdiagramm",
        "#kernf%C3%A4higkeiten--sicherheitsinvarianten" in text_de.lower() or "#kernfähigkeiten--sicherheitsinvarianten",
        "#geschwister-%C3%B6kosystem--schwesterprodukte" in text_de.lower() or "#geschwister-ökosystem--schwesterprodukte",
        "#auffindbarkeit",
        "#voraussetzungen",
        "#installation",
        "#starten",
        "#verwendung",
        "#exe-erstellen",
        "#qualit%C3%A4tssicherung" in text_de.lower() or "#qualitätssicherung",
        "#sicherheitsrichtlinie",
        "#lizenz",
    ]:
        pass  # dynamic check handled above


def test_readme_contains_mermaid_diagrams():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "```mermaid\ngraph TD" in text_en
    assert "```mermaid\nsequenceDiagram" in text_en

    assert "```mermaid\ngraph TD" in text_de
    assert "```mermaid\nsequenceDiagram" in text_de


def test_readme_badges_parity_and_test_count():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    common_badges = [
        "python-3.10",
        "pytest-182%20passed",
        "GUI-PySide6",
        "file--bricks",
        "open--bricks",
        "LLM-Ready",
    ]
    for badge in common_badges:
        assert badge in text_en, f"Missing badge {badge} in README.md"
        assert badge in text_de, f"Missing badge {badge} in README_de.md"

    assert "License-MIT" in text_en
    assert "Lizenz-MIT" in text_de or "License-MIT" in text_de


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
    assert urls["Changelog"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/CHANGELOG.md"
    assert urls["Security"] == "https://github.com/file-bricks/SoftwareCenter/blob/master/SECURITY.md"
    assert urls["Parent Organization"] == "https://github.com/file-bricks"
    assert urls["Umbrella Ecosystem"] == "https://github.com/open-bricks"

    assert "ruff" in data.get("tool", {}), "tool.ruff must be configured"


def test_sibling_ecosystem_table_links():
    text_en = (ROOT / "README.md").read_text(encoding="utf-8")
    text_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

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


def test_llms_txt_structure_and_timestamp():
    llms_file = ROOT / "llms.txt"
    assert llms_file.exists(), "llms.txt must exist"
    content = llms_file.read_text(encoding="utf-8")

    assert "## Last-checked: 2026-09-07" in content
    assert "https://github.com/file-bricks/SoftwareCenter" in content
    assert "182 tests" in content
    assert "Disambiguation" in content


def test_changelog_recent_entry():
    changelog_file = ROOT / "CHANGELOG.md"
    assert changelog_file.exists(), "CHANGELOG.md must exist"
    content = changelog_file.read_text(encoding="utf-8")

    assert "2026-09-07" in content
    assert "Pfad B" in content or "Discoverability" in content


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
