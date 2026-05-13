from __future__ import annotations

from pathlib import Path
from app.core.database import DatabaseManager


class SessionService:
    def __init__(self, path: Path | None = None) -> None:
        self.db = DatabaseManager()

    def save_text(self, text: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO sessions (key, value) VALUES (?, ?)",
            ("last_input_text", text)
        )

    def load_text(self) -> str:
        row = self.db.fetch_one("SELECT value FROM sessions WHERE key = ?", ("last_input_text",))
        return row["value"] if row else ""
