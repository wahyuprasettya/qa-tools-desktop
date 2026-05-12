from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.core import paths


def configure_logging() -> None:
    paths.ensure_runtime_dirs()
    log_file = paths.LOGS_DIR / "tableforge.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
