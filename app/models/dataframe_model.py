from __future__ import annotations

import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DataFrameModel(QAbstractTableModel):
    def __init__(
        self,
        dataframe: pd.DataFrame | None = None,
        max_rows: int = 10000,
        editable: bool = False,
    ) -> None:
        super().__init__()
        self._dataframe = dataframe if dataframe is not None else pd.DataFrame()
        self._max_rows = max_rows
        self._editable = editable

    def set_dataframe(self, dataframe: pd.DataFrame) -> None:
        self.beginResetModel()
        self._dataframe = dataframe
        self.endResetModel()

    def dataframe(self) -> pd.DataFrame:
        return self._dataframe

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else min(len(self._dataframe.index), self._max_rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._dataframe.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> object:
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole):
            return None
        value = self._dataframe.iat[index.row(), index.column()]
        return "" if pd.isna(value) else str(value)

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:
        if not self._editable or role != Qt.EditRole or not index.isValid():
            return False
        if index.row() >= len(self._dataframe.index) or index.column() >= len(self._dataframe.columns):
            return False

        text = "" if value is None else str(value)
        self._dataframe.iat[index.row(), index.column()] = text
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        flags = super().flags(index)
        if self._editable and index.isValid():
            flags |= Qt.ItemIsEditable
        return flags

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> object:
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._dataframe.columns[section])
        return str(section + 1)
