from __future__ import annotations

import unittest

from app.services.table_parser import TableParser


class TableParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = TableParser()

    def test_markdown_table_columns(self) -> None:
        result = self.parser.parse(
            "| No | Name | Status |\n"
            "| --- | --- | --- |\n"
            "| 1 | Login | Pass |\n"
        )

        self.assertEqual(["No", "Name", "Status"], list(result.dataframe.columns))
        self.assertEqual((1, 3), result.dataframe.shape)

    def test_numbered_markdown_table_does_not_create_extra_prefix_column(self) -> None:
        result = self.parser.parse(
            "1. | No | Name | Status |\n"
            "2. | --- | --- | --- |\n"
            "3. | 1 | Login | Pass |\n"
        )

        self.assertEqual(["No", "Name", "Status"], list(result.dataframe.columns))
        self.assertEqual((1, 3), result.dataframe.shape)
        self.assertEqual("Login", result.dataframe.iloc[0]["Name"])

    def test_extra_markdown_cells_are_merged_into_last_column(self) -> None:
        result = self.parser.parse(
            "| No | Name | Notes |\n"
            "| --- | --- | --- |\n"
            "| 1 | Login | Needs check | urgent |\n"
        )

        self.assertEqual(["No", "Name", "Notes"], list(result.dataframe.columns))
        self.assertEqual("Needs check | urgent", result.dataframe.iloc[0]["Notes"])

    def test_markdown_header_separator_defines_columns_for_incomplete_rows(self) -> None:
        result = self.parser.parse(
            "| Focus | Type | ID | Pre-Condition | Scenario | Test Steps | Expected Result | Result | Notes / Issue |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            "| ini harus jadi nama kolom soalnya ada kejadian issue dan notes tidak jadi nama kolom tapi jadi data\n"
        )

        self.assertEqual(
            [
                "Focus",
                "Type",
                "ID",
                "Pre-Condition",
                "Scenario",
                "Test Steps",
                "Expected Result",
                "Result",
                "Notes / Issue",
            ],
            list(result.dataframe.columns),
        )
        self.assertEqual((1, 9), result.dataframe.shape)
        self.assertEqual(
            "ini harus jadi nama kolom soalnya ada kejadian issue dan notes tidak jadi nama kolom tapi jadi data",
            result.dataframe.iloc[0]["Focus"],
        )

    def test_tsv_columns(self) -> None:
        result = self.parser.parse("No\tName\tStatus\n1\tLogin\tPass\n")

        self.assertEqual(["No", "Name", "Status"], list(result.dataframe.columns))
        self.assertEqual((1, 3), result.dataframe.shape)

    def test_csv_is_not_misread_as_flattened_table(self) -> None:
        result = self.parser.parse("No,Name,Status\n1,Login,Pass\n2,Export,Pending\n")

        self.assertEqual(["No", "Name", "Status"], list(result.dataframe.columns))
        self.assertEqual((2, 3), result.dataframe.shape)
        self.assertEqual("Pending", result.dataframe.iloc[1]["Status"])

    def test_padded_markdown_table_with_dates_and_comma_numbers(self) -> None:
        result = self.parser.parse(
            "| Name          | Role              | Platform | Status     | Last Export      | Rows Processed |\n"
            "| ------------- | ----------------- | -------- | ---------- | ---------------- | -------------- |\n"
            "| Andi Pratama  | Data Analyst      | Windows  | Success    | 2026-05-09 14:21 | 1,245          |\n"
            "| Siti Rahma    | QA Engineer       | Linux    | Success    | 2026-05-09 13:40 | 842            |\n"
            "| Budi Santoso  | Project Manager   | macOS    | Failed     | 2026-05-09 12:15 | 0              |\n"
            "| Dewi Lestari  | Business Analyst  | Windows  | Success    | 2026-05-09 11:02 | 2,310          |\n"
            "| Rian Saputra  | Backend Developer | Linux    | Processing | 2026-05-09 10:58 | 560            |\n"
            "| Maya Putri    | UI/UX Designer    | Windows  | Success    | 2026-05-08 18:44 | 978            |\n"
            "| Fajar Nugroho | DevOps Engineer   | Linux    | Success    | 2026-05-08 17:20 | 1,502          |\n"
            "| Kevin Wijaya  | Security Engineer | macOS    | Success    | 2026-05-08 16:35 | 3,020          |\n"
            "| Intan Permata | Product Owner     | Windows  | Failed     | 2026-05-08 15:50 | 0              |\n"
            "| Rizky Hidayat | Data Engineer     | Linux    | Success    | 2026-05-08 14:12 | 4,115          |\n"
        )

        self.assertEqual(
            ["Name", "Role", "Platform", "Status", "Last Export", "Rows Processed"],
            list(result.dataframe.columns),
        )
        self.assertEqual((10, 6), result.dataframe.shape)
        self.assertEqual("1,245", result.dataframe.iloc[0]["Rows Processed"])
        self.assertEqual("2026-05-08 14:12", result.dataframe.iloc[-1]["Last Export"])

    def test_flattened_chatgpt_copy_table_is_reconstructed(self) -> None:
        result = self.parser.parse(
            "\n"
            "Name\n"
            "Role\n"
            "Platform\n"
            "Status\n"
            "Last Export\n"
            "Rows Processed\n"
            "Andi Pratama\n"
            "Data Analyst\n"
            "Windows\n"
            "Success\n"
            "2026-05-09 14:21\n"
            "1,245\n"
            "Siti Rahma\n"
            "QA Engineer\n"
            "Linux\n"
            "Success\n"
            "2026-05-09 13:40\n"
            "842\n"
        )

        self.assertEqual(
            ["Name", "Role", "Platform", "Status", "Last Export", "Rows Processed"],
            list(result.dataframe.columns),
        )
        self.assertEqual((2, 6), result.dataframe.shape)
        self.assertEqual("1,245", result.dataframe.iloc[0]["Rows Processed"])

    def test_flattened_table_supports_many_columns(self) -> None:
        headers = [f"Column {index}" for index in range(1, 21)]
        first_row = [f"Row 1 Value {index}" for index in range(1, 21)]
        second_row = [f"Row 2 Value {index}" for index in range(1, 21)]
        result = self.parser.parse("\n".join([*headers, *first_row, *second_row]))

        self.assertEqual(headers, list(result.dataframe.columns))
        self.assertEqual((2, 20), result.dataframe.shape)
        self.assertEqual("Row 2 Value 20", result.dataframe.iloc[1]["Column 20"])

    def test_flattened_table_does_not_promote_data_values_to_columns(self) -> None:
        headers = [
            "Focus",
            "Type",
            "ID",
            "Pre-Condition",
            "Scenario",
            "Test Steps",
            "Expected Result",
            "Result",
            "Notes / Issue",
            "Module",
        ]
        records = [
            [
                "Verify newly created client",
                "Functional",
                "TC-001",
                "User has access to application and permission to create new",
                "Client Creation & Web Service Recording",
                "1. Login to application",
                "New client is created",
                "Pending",
                "Verify web service call",
                "Client Management",
            ],
            [
                "Verify recorded web service",
                "Functional",
                "TC-002",
                "New client is available",
                "Client Creation",
                "1. Open API log",
                "Web service call exists",
                "Pass",
                "Compare client information from Client Management",
                "Web Service",
            ],
            [
                "Report contains new client",
                "Regression",
                "TC-003",
                "Existing report is available",
                "Report entry validation",
                "1. Create and refresh report",
                "Report contains created client",
                "Pending",
                "System rejects invalid client data",
                "Reporting",
            ],
            [
                "Invalid client creation",
                "Negative",
                "TC-004",
                "User opens create client form",
                "Validation",
                "1. Submit incomplete client",
                "System rejects invalid input",
                "Pending",
                "Existing clients remain unchanged",
                "Client Management",
            ],
            [
                "Verify report issue",
                "Functional",
                "TC-005",
                "Report has connected data",
                "Report connected to service",
                "1. Validate report issue",
                "Report issue is visible",
                "Pending",
                "No issue found",
                "Reporting",
            ],
        ]

        result = self.parser.parse("\n".join([*headers, *(cell for row in records for cell in row)]))

        self.assertEqual(headers, list(result.dataframe.columns))
        self.assertEqual((5, 10), result.dataframe.shape)
        self.assertEqual("TC-001", result.dataframe.iloc[0]["ID"])
        self.assertEqual("Verify report issue", result.dataframe.iloc[4]["Focus"])

    def test_flattened_table_keeps_header_width_when_trailing_cells_are_missing(self) -> None:
        headers = [
            "Focus",
            "Type",
            "ID",
            "Pre-Condition",
            "Scenario",
            "Test Steps",
            "Expected Result",
            "Result",
            "Notes / Issue",
        ]
        records_without_notes = [
            [
                "Client Creation & Web Service Recording",
                "Functional",
                "TC-001",
                "User has access to application",
                "Verify newly created client",
                "1. Login to application",
                "New client is successfully created",
                "Pending",
            ],
            [
                "Client Creation & Web Service Recording",
                "Functional",
                "TC-002",
                "New client already exists",
                "Verify web service can return client data",
                "1. Open API/Web Service log",
                "Web service call returns success",
                "Pending",
            ],
            [
                "Reporting",
                "Regression",
                "TC-003",
                "Existing report data is available",
                "Report contains correct client data",
                "1. Compare client information",
                "Report entry appears correctly",
                "Pass",
            ],
        ]

        result = self.parser.parse(
            "\n".join([*headers, *(cell for row in records_without_notes for cell in row)])
        )

        self.assertEqual(headers, list(result.dataframe.columns))
        self.assertEqual((3, 9), result.dataframe.shape)
        self.assertEqual("Verify newly created client", result.dataframe.iloc[0]["Scenario"])
        self.assertEqual("Pending", result.dataframe.iloc[0]["Result"])
        self.assertEqual("", result.dataframe.iloc[0]["Notes / Issue"])


if __name__ == "__main__":
    unittest.main()
