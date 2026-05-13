from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.core import paths


@dataclass(slots=True)
class AppSettings:
    theme: str = "light"
    default_export_format: str = "xlsx"
    output_directory: str = ""
    autosave_session: bool = True
    open_after_export: bool = False
    max_preview_rows: int = 10000
    pagespeed_api_key: str = ""
    playwright_path: str = "npx playwright"


class ConfigManager:
    def __init__(self, path: Path | None = None) -> None:
        paths.ensure_runtime_dirs()
        self.path = path or paths.DATA_DIR / "settings.json"
        self.settings = self._load()

    def _load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return AppSettings(**{**asdict(AppSettings()), **data})
        except (OSError, json.JSONDecodeError, TypeError):
            return AppSettings()

    def save(self) -> None:
        self.path.write_text(json.dumps(asdict(self.settings), indent=2), encoding="utf-8")

    def update(self, **values: Any) -> AppSettings:
        for key, value in values.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.save()
        return self.settings
