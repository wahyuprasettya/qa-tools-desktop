import re
from app.core.exceptions import ParseError
from app.services.table_parser import ParseResult, TableParser

class MyParser(TableParser):
    def _parse_markdown(self, text: str) -> ParseResult:
        lines = [line for line in text.splitlines() if "|" in line]
        if not lines:
            raise ParseError("No markdown table found.")

        sep_idx = -1
        for i, line in enumerate(lines):
            cells = [c.strip() for c in line.split("|")]
            if cells and cells[0] == "": cells = cells[1:]
            if cells and cells[-1] == "": cells = cells[:-1]
            if self._is_markdown_separator(cells):
                sep_idx = i
                break

        has_leading_pipe = False
        has_trailing_pipe = False
        if sep_idx != -1:
            sep_line = lines[sep_idx]
            has_leading_pipe = sep_line.lstrip().startswith("|")
            has_trailing_pipe = sep_line.rstrip().endswith("|")

        markdown_rows = []
        for i, line in enumerate(lines):
            if has_leading_pipe:
                pipe_idx = line.find("|")
                if pipe_idx != -1:
                    line = line[pipe_idx:]
            if has_trailing_pipe:
                pipe_idx = line.rfind("|")
                if pipe_idx != -1:
                    line = line[: pipe_idx + 1]

            cells = self._markdown_cells(line)
            if cells:
                markdown_rows.append((i, cells))

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

text = """benerin ketika data dari chat gpt seperti ini | Focus | Type | ID |
| --- | --- | --- |
| Client | Functional | TC-001 | 
| Pending | Functional | TC-002 | tabel jadi berantakan"""

p = MyParser()
res = p.parse(text)
import pandas as pd
print(res.dataframe)

