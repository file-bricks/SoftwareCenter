from __future__ import annotations

import json
import tempfile
from pathlib import Path

from generate_store_screenshots import SCREENSHOT_FILES, generate_store_screenshots


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def test_generate_store_screenshots_creates_expected_pngs_and_summary() -> None:
    with tempfile.TemporaryDirectory(prefix="softwarecenter-store-shots-test-") as tmp_dir:
        targets = generate_store_screenshots(Path(tmp_dir))

        expected = {Path(tmp_dir) / name for name in SCREENSHOT_FILES.values()}
        assert set(targets) == expected

        for target in targets:
            data = target.read_bytes()
            assert data.startswith(b"\x89PNG\r\n\x1a\n")
            assert len(data) > 2048
            width, height = _png_dimensions(target)
            assert width >= 1200
            assert height >= 700

        summary_path = Path(tmp_dir) / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert [item["file"] for item in summary["screenshots"]] == list(SCREENSHOT_FILES.values())
