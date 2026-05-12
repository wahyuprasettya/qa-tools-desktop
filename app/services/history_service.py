from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from app.core import paths


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
        paths.ensure_runtime_dirs()
        self.path = path or paths.DATA_DIR / "export_history.json"

    def list_records(self) -> list[ExportRecord]:
        if not self.path.exists():
            return []
        try:
            raw_records = json.loads(self.path.read_text(encoding="utf-8"))
            return [ExportRecord(**record) for record in raw_records]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def add_record(self, filename: str, path: Path, file_type: str, rows: int, columns: int) -> None:
        records = self.list_records()
        records.insert(
            0,
            ExportRecord(
                filename=filename,
                path=str(path),
                file_type=file_type,
                rows=rows,
                columns=columns,
                created_at=datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.path.write_text(
            json.dumps([asdict(record) for record in records[:100]], indent=2),
            encoding="utf-8",
        )

    def clear(self) -> None:
        self.path.write_text("[]", encoding="utf-8")
