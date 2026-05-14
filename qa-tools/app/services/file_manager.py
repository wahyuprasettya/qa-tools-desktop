from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.core import paths


class FileManager:
    @staticmethod
    def default_output_dir(configured: str = "") -> Path:
        paths.ensure_runtime_dirs()
        if configured:
            path = Path(configured).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            return path
        return paths.EXPORTS_DIR

    @staticmethod
    def open_in_file_manager(path: Path) -> None:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
