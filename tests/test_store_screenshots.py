from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from generate_store_screenshots import (
    MIN_STORE_HEIGHT,
    MIN_STORE_WIDTH,
    SCREENSHOT_FILES,
    generate_store_screenshots,
    real_gui_available,
)


def _png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    width = int.from_bytes(data[16:20], "big")
    height = int.from_bytes(data[20:24], "big")
    return width, height


def test_generate_store_screenshots_creates_expected_pngs_and_summary() -> None:
    if not real_gui_available():
        pytest.skip(
            "Store-Screenshots brauchen eine echte GUI-Session; headless (offscreen) "
            "entstehen unlesbare Tofu-Kaestchen statt Text."
        )
    with tempfile.TemporaryDirectory(prefix="softwarecenter-store-shots-test-") as tmp_dir:
        targets = generate_store_screenshots(Path(tmp_dir))

        expected = {Path(tmp_dir) / name for name in SCREENSHOT_FILES.values()}
        assert set(targets) == expected

        for target in targets:
            data = target.read_bytes()
            assert data.startswith(b"\x89PNG\r\n\x1a\n")
            assert len(data) > 2048
            width, height = _png_dimensions(target)
            assert width >= MIN_STORE_WIDTH
            assert height >= MIN_STORE_HEIGHT

        summary_path = Path(tmp_dir) / "summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        assert [item["file"] for item in summary["screenshots"]] == list(SCREENSHOT_FILES.values())
