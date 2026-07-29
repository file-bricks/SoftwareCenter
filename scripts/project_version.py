"""Read the application version from pyproject.toml using only the stdlib."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


_SAFE_VERSION = re.compile(r"^[A-Za-z0-9]+(?:[._+-][A-Za-z0-9]+)*$")


def read_project_version(path: Path) -> str:
    """Return ``project.version`` and reject values unsafe for artifact paths."""

    in_project = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_project = line == "[project]"
            continue
        if not in_project or not line.startswith("version"):
            continue

        match = re.fullmatch(r"""version\s*=\s*["']([^"']+)["']\s*(?:#.*)?""", line)
        if not match:
            raise ValueError(f"Ungültige project.version-Zeile in {path}")
        version = match.group(1)
        if not _SAFE_VERSION.fullmatch(version):
            raise ValueError(f"Unsichere project.version in {path}: {version!r}")
        return version

    raise ValueError(f"project.version fehlt in {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pyproject", type=Path)
    args = parser.parse_args()
    print(read_project_version(args.pyproject))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
