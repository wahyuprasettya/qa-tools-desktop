from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication

from app.core.logging_config import configure_logging, get_logger
from app.core.paths import ICONS_DIR
from app.services.config_manager import ConfigManager
from app.services.history_service import HistoryService
from app.services.session_service import SessionService
from app.services.theme_manager import ThemeManager
from app.ui.main_window import MainWindow


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("QA Generator")
    app.setOrganizationName("QA Generator")
    app.setWindowIcon(QIcon(str(ICONS_DIR / "qa-generator.png")))

    configure_logging()
    logger = get_logger(__name__)
    logger.info("Application starting")

    config = ConfigManager()
    theme = ThemeManager(app, config)
    history = HistoryService()
    session = SessionService()

    window = MainWindow(config=config, theme=theme, history=history, session=session)
    window.setWindowIcon(QIcon(str(ICONS_DIR / "qa-generator.png")))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
