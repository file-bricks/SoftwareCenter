import os

# Headless Qt for local pytest runs (mirrors CI job-level env var).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

collect_ignore_glob = ["*-ASUS-GEI.py"]
