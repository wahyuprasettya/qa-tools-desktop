from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.services.pagespeed_service import AuditResult


class PageSpeedTableModel(QAbstractTableModel):
    """Model to display Accessibility Audit Results."""

    def __init__(self) -> None:
        super().__init__()
        self._data: list[AuditResult] = []
        self._headers = ["Status", "Audit Title", "Description", "Value"]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < self.rowCount()):
            return None

        audit = self._data[index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                # Interpret score: 1.0 is Pass, 0 is Fail, null means Not Applicable or Manual
                if audit.score_display_mode == "notApplicable":
                    return "N/A"
                elif audit.score_display_mode == "manual":
                    return "Manual Check"
                elif audit.score is not None:
                    return "Pass" if audit.score >= 0.9 else "Fail"
                return audit.score_display_mode
            elif index.column() == 1:
                return audit.title
            elif index.column() == 2:
                # Remove markdown links if any, simple truncate
                desc = audit.description.split("[")[0].strip()
                return desc if len(desc) < 100 else desc[:97] + "..."
            elif index.column() == 3:
                return audit.display_value
                
        elif role == Qt.ToolTipRole:
            if index.column() == 2:
                return audit.description

        elif role == Qt.ForegroundRole:
            # Color coding for status
            if index.column() == 0:
                from PySide6.QtGui import QColor
                if audit.score_display_mode == "notApplicable" or audit.score_display_mode == "manual":
                    return QColor("#9ca3af") # Gray
                elif audit.score is not None:
                    return QColor("#10b981") if audit.score >= 0.9 else QColor("#ef4444") # Green/Red

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def set_audits(self, audits: list[AuditResult]) -> None:
        """Set audits in the model."""
        self.beginResetModel()
        # Sort by score ascending (Fails first)
        def sort_key(a: AuditResult) -> float:
            if a.score_display_mode in ("notApplicable", "manual"):
                return 2.0 # Put these at the end
            return a.score if a.score is not None else 1.0
            
        self._data = sorted(audits, key=sort_key)
        self.endResetModel()

    def clear(self) -> None:
        """Clear all audits."""
        self.beginResetModel()
        self._data.clear()
        self.endResetModel()
