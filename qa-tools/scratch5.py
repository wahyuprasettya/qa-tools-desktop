import re
import pandas as pd
from app.core.exceptions import ParseError
from app.services.table_parser import ParseResult, TableParser

class MyParser(TableParser):
    def _parse_markdown(self, text: str) -> ParseResult:
        lines = [line for line in text.splitlines() if "|" in line]
        if not lines:
            raise ParseError("No markdown table found.")

        sep_idx = -1
        for i, line in enumerate(lines):
            cells = self._markdown_cells(line)
            if cells and self._is_markdown_separator(cells):
                sep_idx = i
                break

        has_leading_pipe = False
        has_trailing_pipe = False
        if sep_idx != -1:
            clean_line = re.sub(r"^\s*(?:[-*+]\s+|\d+[\.)]\s+)(?=\|)", "", lines[sep_idx].strip())
            has_leading_pipe = clean_line.startswith("|")
            has_trailing_pipe = clean_line.endswith("|")

        markdown_rows = []
        for i, line in enumerate(lines):
            clean_line = re.sub(r"^\s*(?:[-*+]\s+|\d+[\.)]\s+)(?=\|)", "", line.strip())
            parts = [part.strip() for part in clean_line.split("|")]
            
            pipe_count = clean_line.count("|")
            
            if has_leading_pipe and len(parts) > 1:
                parts = parts[1:]
            elif parts and parts[0] == "":
                parts = parts[1:]
                
            if has_trailing_pipe and pipe_count > 1 and len(parts) > 0:
                parts = parts[:-1]
            elif parts and parts[-1] == "":
                parts = parts[:-1]

            if parts:
                markdown_rows.append((i, parts))

        if sep_idx != -1:
            for list_idx, (orig_i, cells) in enumerate(markdown_rows):
                if orig_i == sep_idx:
                    if list_idx == 0:
                        raise ParseError("No markdown table found.")
                    rows = [markdown_rows[list_idx - 1][1]]
                    rows.extend(row_cells for o_i, row_cells in markdown_rows[list_idx + 1 :] if not self._is_markdown_separator(row_cells))
                    if len(rows) < 2:
                        raise ParseError("Markdown table needs at least one data row.")
                    return self._rows_to_result(rows, "markdown")

        rows = [cells for i, cells in markdown_rows if len(cells) >= 2]
        if len(rows) < 2:
            raise ParseError("No markdown table found.")
        return self._rows_to_result(rows, "markdown")

    def _clean_cell(self, value: object) -> str:
        if pd.isna(value):
            return ""
        cell = str(value)
        cell = re.sub(r"<br\s*/?>", "\n", cell, flags=re.IGNORECASE)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cell.split("\n")]
        cell = "\n".join(line for line in lines if line)
        return cell.strip("`")

# Test 1
text1 = """| Focus | Type | ID | Pre-Condition | Scenario | Test Steps | Expected Result | Result | Notes / Issue |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ini harus jadi nama kolom soalnya ada kejadian issue dan notes tidak jadi nama kolom tapi jadi data"""
print(MyParser().parse(text1).dataframe.shape)

# Test 2
text2 = """1. | No | Name | Status |
2. | --- | --- | --- |
3. | 1 | Login | Pass |"""
print(MyParser().parse(text2).dataframe.shape)

# Test 3
text3 = """Garbage | Col1 | Col2 |
| --- | --- |
| Val1 | Val2 | trailing garbage"""
print(MyParser().parse(text3).dataframe)

