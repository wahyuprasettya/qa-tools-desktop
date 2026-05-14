from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.core.paths import STYLES_DIR
from app.services.config_manager import ConfigManager


class ThemeManager:
    def __init__(self, app: QApplication, config: ConfigManager) -> None:
        self.app = app
        self.config = config
        self.apply(config.settings.theme)

    def apply(self, theme: str) -> None:
        theme_name = "light" if theme == "light" else "dark"
        qss_path = STYLES_DIR / f"{theme_name}.qss"
        self.app.setStyleSheet(_read_qss(qss_path))
        self.config.update(theme=theme_name)


def _read_qss(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""

