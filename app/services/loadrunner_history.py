from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.database import DatabaseManager


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
        self.db = DatabaseManager()

    def list_records(self) -> list[LRHistoryRecord]:
        rows = self.db.fetch_all("SELECT timestamp, scenario_path, status, duration_sec, total_transactions, passed_transactions, failed_transactions FROM lr_history ORDER BY id DESC LIMIT 100")
        return [LRHistoryRecord(**row) for row in rows]

    def add_record(self, record: LRHistoryRecord) -> None:
        self.db.execute(
            "INSERT INTO lr_history (timestamp, scenario_path, status, duration_sec, total_transactions, passed_transactions, failed_transactions) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record.timestamp, record.scenario_path, record.status, record.duration_sec, record.total_transactions, record.passed_transactions, record.failed_transactions)
        )

    def clear(self) -> None:
        self.db.execute("DELETE FROM lr_history")
