from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from app.core.paths import DATA_DIR


@dataclass
class LRHistoryRecord:
    timestamp: str
    scenario_path: str
    status: str
    duration_sec: float
    total_transactions: int
    passed_transactions: int
    failed_transactions: int

    @property
    def created_at(self) -> str:
        try:
            return datetime.fromisoformat(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return self.timestamp


class LoadRunnerHistoryService:
    def __init__(self) -> None:
        self.history_file = DATA_DIR / "lr_history.json"
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            self.history_file.write_text("[]", encoding="utf-8")

    def list_records(self) -> list[LRHistoryRecord]:
        try:
            content = self.history_file.read_text(encoding="utf-8")
            data = json.loads(content)
            return [LRHistoryRecord(**item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_record(self, record: LRHistoryRecord) -> None:
        records = self.list_records()
        records.insert(0, record)
        # Keep only the last 100 records
        records = records[:100]
        data = [asdict(r) for r in records]
        self.history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def clear(self) -> None:
        self.history_file.write_text("[]", encoding="utf-8")
