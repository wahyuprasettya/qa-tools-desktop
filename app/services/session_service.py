from __future__ import annotations

import json
from pathlib import Path

from app.core import paths


class SessionService:
    def __init__(self, path: Path | None = None) -> None:
        paths.ensure_runtime_dirs()
        self.path = path or paths.DATA_DIR / "last_session.json"

    def save_text(self, text: str) -> None:
        self.path.write_text(json.dumps({"raw_text": text}), encoding="utf-8")

    def load_text(self) -> str:
        if not self.path.exists():
            return ""
        try:
            return str(json.loads(self.path.read_text(encoding="utf-8")).get("raw_text", ""))
        except (OSError, json.JSONDecodeError):
            return ""
