from pathlib import Path

from scripts.verify_product_boundaries import (
    artifact_receipt,
    verify_parallel_processes,
    verify_static_contract,
)


def test_static_product_contract_is_separate() -> None:
    report = verify_static_contract()

    assert report["softwarecenter_executable"] == "SoftwareCenter.exe"
    assert report["launchboards_executable"] == "LaunchBoards.exe"


def test_product_profiles_can_run_in_parallel_isolated_processes() -> None:
    report = verify_parallel_processes()

    assert report["parallel_processes"] == "passed"
    assert report["softwarecenter_server"] != report["launchboards_server"]
    assert report["settings_backend"] == "isolated temporary INI"


def test_artifact_receipt_is_deterministic(tmp_path: Path) -> None:
    artifact = tmp_path / "LaunchBoards.exe"
    artifact.write_bytes(b"synthetic launchboards artifact")

    first = artifact_receipt(artifact)
    second = artifact_receipt(artifact)

    assert first == second
    assert first["bytes"] == 31
    assert len(first["sha256"]) == 64


def test_documented_external_spec_build_uses_absolute_project_resources() -> None:
    documentation = (Path(__file__).resolve().parents[1] / "PRODUCT_BOUNDARIES.md").read_text(
        encoding="utf-8"
    )

    assert '$PROJECT_ROOT = (Get-Location).Path' in documentation
    assert '--icon "$PROJECT_ROOT\\launchboards.ico"' in documentation
    assert '--add-data "$PROJECT_ROOT\\launchboards.ico;."' in documentation
    assert '--add-data "$PROJECT_ROOT\\icon.ico;."' in documentation
    assert '"$PROJECT_ROOT\\launchboards.py"' in documentation
