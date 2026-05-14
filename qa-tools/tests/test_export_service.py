from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

from app.services.export_service import ExportService


class ExportServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.exporter = ExportService()
        self.dataframe = pd.DataFrame(
            {
                "Focus": ["Verify client", "Verify report"],
                "Result": ["Pending", "Pass"],
            }
        )

    def test_csv_export_reports_progress(self) -> None:
        events: list[tuple[int, str]] = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "table.csv"

            result = self.exporter.export(self.dataframe, path, "csv", lambda percent, message: events.append((percent, message)))

            self.assertEqual(path, result)
            self.assertTrue(path.exists())
            self.assertEqual(0, events[0][0])
            self.assertEqual(100, events[-1][0])
            self.assertIn("Focus,Result", path.read_text(encoding="utf-8"))

    def test_xlsx_export_reports_progress(self) -> None:
        events: list[tuple[int, str]] = []
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "table.xlsx"

            result = self.exporter.export(self.dataframe, path, "xlsx", lambda percent, message: events.append((percent, message)))

            self.assertEqual(path, result)
            self.assertTrue(path.exists())
            self.assertEqual(0, events[0][0])
            self.assertEqual(100, events[-1][0])
            workbook = load_workbook(path)
            sheet = workbook.active
            self.assertEqual("Focus", sheet["A1"].value)
            self.assertEqual("Pending", sheet["B2"].value)


if __name__ == "__main__":
    unittest.main()
