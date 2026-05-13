from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core.database import DatabaseManager


@dataclass(slots=True)
class ExportRecord:
    filename: str
    path: str
    file_type: str
    rows: int
    columns: int
    created_at: str


class HistoryService:
    def __init__(self, path: Path | None = None) -> None:
        self.db = DatabaseManager()

    def list_records(self) -> list[ExportRecord]:
        rows = self.db.fetch_all("SELECT filename, path, file_type, rows, columns, created_at FROM export_history ORDER BY id DESC LIMIT 100")
        return [ExportRecord(**row) for row in rows]

    def add_record(self, filename: str, path: Path, file_type: str, rows: int, columns: int) -> None:
        created_at = datetime.now().isoformat(timespec="seconds")
        self.db.execute(
            "INSERT INTO export_history (filename, path, file_type, rows, columns, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (filename, str(path), file_type, rows, columns, created_at)
        )

    def clear(self) -> None:
        self.db.execute("DELETE FROM export_history")
