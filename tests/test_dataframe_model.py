from __future__ import annotations

import unittest

import pandas as pd
from PySide6.QtCore import Qt

from app.models.dataframe_model import DataFrameModel


class DataFrameModelTests(unittest.TestCase):
    def test_editable_model_updates_source_dataframe(self) -> None:
        dataframe = pd.DataFrame({"Name": ["Andi"], "Status": ["Draft"]})
        model = DataFrameModel(dataframe, editable=True)
        index = model.index(0, 1)

        self.assertTrue(model.flags(index) & Qt.ItemIsEditable)
        self.assertTrue(model.setData(index, "Ready", Qt.EditRole))
        self.assertEqual("Ready", dataframe.iloc[0]["Status"])
        self.assertEqual("Ready", model.data(index, Qt.DisplayRole))

    def test_read_only_model_rejects_edits(self) -> None:
        dataframe = pd.DataFrame({"Name": ["Andi"], "Status": ["Draft"]})
        model = DataFrameModel(dataframe)
        index = model.index(0, 1)

        self.assertFalse(model.flags(index) & Qt.ItemIsEditable)
        self.assertFalse(model.setData(index, "Ready", Qt.EditRole))
        self.assertEqual("Draft", dataframe.iloc[0]["Status"])

    def test_max_rows_limits_visible_rows_without_truncating_dataframe(self) -> None:
        dataframe = pd.DataFrame({"Value": ["one", "two", "three"]})
        model = DataFrameModel(max_rows=2, editable=True)

        model.set_dataframe(dataframe)

        self.assertEqual(2, model.rowCount())
        self.assertEqual(3, len(model.dataframe()))
        self.assertTrue(model.setData(model.index(1, 0), "TWO", Qt.EditRole))
        self.assertEqual("TWO", dataframe.iloc[1]["Value"])


if __name__ == "__main__":
    unittest.main()
