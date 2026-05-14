from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = APP_DIR.parent
ASSETS_DIR = APP_DIR / "assets"
STYLES_DIR = ASSETS_DIR / "styles"
ICONS_DIR = ASSETS_DIR / "icons"

if getattr(sys, "frozen", False):
    if os.environ.get("SNAP_REAL_HOME"):
        runtime_root = Path(os.environ["SNAP_REAL_HOME"]) / ".local" / "share" / "qa-generator"
    else:
        runtime_root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "qa-generator"
else:
    runtime_root = APP_DIR

EXPORTS_DIR = runtime_root / "exports"
LOGS_DIR = runtime_root / "logs"
DATA_DIR = runtime_root / "data"
PLAYWRIGHT_DIR = runtime_root / "playwright"
DB_PATH = DATA_DIR / "app_database.db"


def ensure_runtime_dirs() -> None:
    global DATA_DIR, EXPORTS_DIR, LOGS_DIR, PLAYWRIGHT_DIR

    try:
        for path in (EXPORTS_DIR, LOGS_DIR, DATA_DIR, PLAYWRIGHT_DIR):
            path.mkdir(parents=True, exist_ok=True)
    except OSError:
        runtime_root = Path(os.environ.get("TMPDIR", "/tmp")) / "qa-generator"
        EXPORTS_DIR = runtime_root / "exports"
        LOGS_DIR = runtime_root / "logs"
        DATA_DIR = runtime_root / "data"
        for path in (EXPORTS_DIR, LOGS_DIR, DATA_DIR):
            path.mkdir(parents=True, exist_ok=True)
