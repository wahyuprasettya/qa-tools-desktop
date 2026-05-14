from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.services.loadrunner_service import TransactionStatus


class LoadRunnerTableModel(QAbstractTableModel):
    """Model to display real-time transaction data during a scenario run."""

    def __init__(self) -> None:
        super().__init__()
        self._data: list[TransactionStatus] = []
        self._headers = ["Transaction Name", "Response Time (s)", "Status"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        tx = self._data[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                return tx.name
            elif index.column() == 1:
                return f"{tx.response_time:.2f}"
            elif index.column() == 2:
                return tx.status
                
        elif role == Qt.ForegroundRole:
            # Color coding for status
            if index.column() == 2:
                from PySide6.QtGui import QColor
                if tx.status.lower() == "pass":
                    return QColor("#10b981") # Green
                elif tx.status.lower() == "fail":
                    return QColor("#ef4444") # Red

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def add_transaction(self, tx: TransactionStatus) -> None:
        """Add a transaction to the model."""
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._data.append(tx)
        self.endInsertRows()

    def clear(self) -> None:
        """Clear all transactions from the model."""
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()

    def get_stats(self) -> dict[str, int]:
        passed = sum(1 for tx in self._data if tx.status.lower() == "pass")
        failed = sum(1 for tx in self._data if tx.status.lower() == "fail")
        return {"total": len(self._data), "passed": passed, "failed": failed}
