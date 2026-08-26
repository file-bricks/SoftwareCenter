from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"
CONTRACT = ROOT / "CI_CONTRACT.md"


def test_ci_pins_node_and_runs_the_complete_web_companion_contract() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    assert "actions/setup-node@v4" in workflow
    assert 'node-version: "20.x"' in workflow
    assert "if [[ -d web_companion ]]" in workflow
    assert "npm --prefix web_companion ci" in workflow
    assert "npm --prefix web_companion test" in workflow
    for source in ("app.js", "library.js", "sw.js"):
        assert f"node --check web_companion/{source}" in workflow


def test_ci_declares_the_current_desktop_only_boundary() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if not (ROOT / "web_companion").exists():
        assert "web_companion is intentionally absent; PWA CI is not applicable." in workflow
        assert not (ROOT / "package.json").exists()


def test_ci_contract_records_the_current_remote_readback() -> None:
    contract = CONTRACT.read_text(encoding="utf-8")

    assert "e40f10fa5783b8c4291fe2614d37a05806f18845" in contract
    assert "actions/runs/32819291531" in contract
    assert "completed successfully" in contract
    assert "does not certify WACK" in contract
