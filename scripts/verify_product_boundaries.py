"""Reproducible SoftwareCenter/LaunchBoards product-boundary verifier.

The process smoke uses temporary INI settings and task-specific local-server
names. It never reads or overwrites the user's real QSettings namespaces.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtNetwork import QLocalSocket
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import SoftwareCenter as sc  # noqa: E402


def _read_json(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def verify_static_contract() -> dict[str, str]:
    software_store = _read_json("store_package.json")
    launchboards_store = _read_json("store_package_launchboards.json")
    build_script = (ROOT / "build_exe_launchboards.bat").read_text(encoding="utf-8")
    software_store_docs = "\n".join(
        (ROOT / name).read_text(encoding="utf-8")
        for name in ("STORE_CONTRACT.md", "STORE_LISTING.md", "WINDOWS_STORE_PREP.md")
    )

    assert sc.PROFILE_SOFTWARECENTER.name == "SoftwareCenter"
    assert sc.PROFILE_LAUNCHBOARDS.name == "LaunchBoards"
    assert sc.PROFILE_SOFTWARECENTER.settings_app == "SoftwareCenter"
    assert sc.PROFILE_LAUNCHBOARDS.settings_app == "LaunchBoards"
    assert sc.PROFILE_SOFTWARECENTER.icon_file == "icon.ico"
    assert sc.PROFILE_LAUNCHBOARDS.icon_file == "launchboards.ico"
    assert sc.PROFILE_SOFTWARECENTER.instance_id != sc.PROFILE_LAUNCHBOARDS.instance_id

    assert software_store["app_name"] == "SoftwareCenter"
    assert software_store["identity_name"] == "Geiger.SoftwareCenter"
    assert software_store["executable"] == "SoftwareCenter.exe"
    assert "LaunchBoards" not in json.dumps(software_store)
    assert "LaunchBoards" not in software_store_docs

    assert launchboards_store["app_name"] == "LaunchBoards"
    assert launchboards_store["identity_name"] == "Geiger.LaunchBoards"
    assert launchboards_store["executable"] == "LaunchBoards.exe"
    assert launchboards_store["store_id"]
    assert launchboards_store["identity_name"] != software_store["identity_name"]

    for required in (
        "--name LaunchBoards",
        '"%PROJECT_ROOT%\\launchboards.py"',
        '"dist\\LaunchBoards.exe"',
        '"releases\\v1.0.0\\LaunchBoards-1.0.0-win64.exe"',
    ):
        assert required in build_script
    assert "SoftwareCenter.exe" not in build_script

    return {
        "softwarecenter_settings": sc.PROFILE_SOFTWARECENTER.settings_app,
        "launchboards_settings": sc.PROFILE_LAUNCHBOARDS.settings_app,
        "softwarecenter_instance": sc.PROFILE_SOFTWARECENTER.instance_id,
        "launchboards_instance": sc.PROFILE_LAUNCHBOARDS.instance_id,
        "softwarecenter_executable": software_store["executable"],
        "launchboards_executable": launchboards_store["executable"],
    }


def _isolated_profile(product: str, token: str) -> sc.AppProfile:
    base = {
        "SoftwareCenter": sc.PROFILE_SOFTWARECENTER,
        "LaunchBoards": sc.PROFILE_LAUNCHBOARDS,
    }[product]
    return replace(
        base,
        settings_app=f"{base.settings_app}_BoundaryCheck_{token}",
        instance_id=f"{base.instance_id}_boundary_check_{token}",
    )


def _wait_for_server(name: str, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        probe = QLocalSocket()
        probe.connectToServer(name)
        if probe.waitForConnected(200):
            probe.disconnectFromServer()
            return True
        probe.abort()
        time.sleep(0.05)
    return False


def verify_parallel_processes() -> dict[str, str]:
    """Start both product profiles concurrently without touching real settings."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    token = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
    profiles = {
        product: _isolated_profile(product, token)
        for product in ("SoftwareCenter", "LaunchBoards")
    }

    with tempfile.TemporaryDirectory(prefix="softwarecenter-boundary-") as settings_dir:
        common = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            "--token",
            token,
            "--settings-dir",
            settings_dir,
        ]
        primaries: list[subprocess.Popen] = []
        child_env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
        try:
            for product in profiles:
                primaries.append(
                    subprocess.Popen(
                        [*common, "--product", product],
                        cwd=ROOT,
                        env=child_env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                )
            for product, profile in profiles.items():
                assert _wait_for_server(profile.instance_id), f"{product} server did not start"
            assert all(process.poll() is None for process in primaries)

            for product in profiles:
                duplicate = subprocess.run(
                    [*common, "--product", product],
                    cwd=ROOT,
                    env=child_env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
                assert duplicate.returncode == 0
            assert all(process.poll() is None for process in primaries)
        finally:
            for process in primaries:
                if process.poll() is None:
                    process.terminate()
            for process in primaries:
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)

        assert app is not None

    return {
        "softwarecenter_server": profiles["SoftwareCenter"].instance_id,
        "launchboards_server": profiles["LaunchBoards"].instance_id,
        "parallel_processes": "passed",
        "settings_backend": "isolated temporary INI",
    }


def artifact_receipt(path: Path) -> dict[str, str | int]:
    resolved = path.resolve(strict=True)
    assert resolved.is_file() and resolved.stat().st_size > 0
    digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    return {"path": str(resolved), "bytes": resolved.stat().st_size, "sha256": digest}


def _child(product: str, token: str, settings_dir: Path) -> int:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    settings_dir.mkdir(parents=True, exist_ok=True)
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(settings_dir))
    result = sc.main(_isolated_profile(product, token))
    return 0 if result is None else int(result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path)
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--product", choices=("SoftwareCenter", "LaunchBoards"))
    parser.add_argument("--token")
    parser.add_argument("--settings-dir", type=Path)
    args = parser.parse_args()

    if args.child:
        if not args.product or not args.token or args.settings_dir is None:
            parser.error("child mode requires --product, --token and --settings-dir")
        return _child(args.product, args.token, args.settings_dir)

    report: dict[str, object] = {
        "static": verify_static_contract(),
        "parallel": verify_parallel_processes(),
    }
    if args.artifact is not None:
        report["artifact"] = artifact_receipt(args.artifact)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
