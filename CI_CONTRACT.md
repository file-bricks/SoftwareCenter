# Continuous-integration contract

The authoritative workflow is `.github/workflows/tests.yml`.

## Desktop contract

Every push and pull request to `master` or `main` runs the Python regression
suite on Python 3.10, 3.11, and 3.12, compiles the Python entry points,
validates tracked JSON metadata, and runs the Linux and macOS platform smokes.

## Optional web-companion boundary

The former `web_companion/` was intentionally removed on 2026-07-23. CI pins
Node 20.x nevertheless. If the directory is reintroduced, the same workflow
requires all of the following and fails when any file or command is missing:

```text
web_companion/package.json
npm --prefix web_companion ci
npm --prefix web_companion test
node --check web_companion/app.js
node --check web_companion/library.js
node --check web_companion/sw.js
```

While the directory is absent, CI prints the explicit desktop-only boundary;
it does not claim PWA coverage. `tests/test_ci_contract.py` prevents either the
Node pin or the future-reintroduction checks from disappearing silently.

## Current remote readback

The public `SoftwareCenter smoke tests` workflow completed successfully for
the current `master` commit `e40f10fa5783b8c4291fe2614d37a05806f18845` on
2026-08-25: [GitHub Actions run 32819291531](https://github.com/file-bricks/SoftwareCenter/actions/runs/32819291531).

This proves the hosted CI contract for that commit. It does not certify WACK,
signing, Store publication, or physical mobile-device behavior.
