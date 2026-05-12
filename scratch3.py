import re
from app.core.exceptions import ParseError
from app.services.table_parser import ParseResult, TableParser

class MyParser(TableParser):
    def _parse_markdown(self, text: str) -> ParseResult:
        lines = [line for line in text.splitlines() if "|" in line]
        
        # Find the separator
        sep_idx = -1
        for i, line in enumerate(lines):
            cells = [c.strip() for c in line.split("|")]
            if cells and cells[0] == "": cells = cells[1:]
            if cells and cells[-1] == "": cells = cells[:-1]
            if self._is_markdown_separator(cells):
                sep_idx = i
                break
                
        if sep_idx == -1:
            # fallback to old behavior
            return super()._parse_markdown(text)
            
        sep_line = lines[sep_idx]
        has_leading_pipe = sep_line.lstrip().startswith("|")
        has_trailing_pipe = sep_line.rstrip().endswith("|")
        
        markdown_rows = []
        for i, line in enumerate(lines):
            # Clean leading/trailing garbage based on the separator's style
            if has_leading_pipe:
                pipe_idx = line.find("|")
                if pipe_idx != -1:
                    line = line[pipe_idx:]
            if has_trailing_pipe:
                pipe_idx = line.rfind("|")
                if pipe_idx != -1:
                    line = line[:pipe_idx+1]
                    
            cells = self._markdown_cells(line)
            if not cells:
                continue
            markdown_rows.append((i, cells))
            
        # Filter rows around the separator
        # Since we stored original indices, we can find the header and data
        header_idx = -1
        for idx, (orig_i, cells) in enumerate(markdown_rows):
            if orig_i == sep_idx:
                if idx == 0:
                    raise ParseError("No markdown table found.")
                rows = [markdown_rows[idx - 1][1]] # Header
                # Add data rows
                rows.extend(row_cells for o_i, row_cells in markdown_rows[idx + 1:] if not self._is_markdown_separator(row_cells))
                if len(rows) < 2:
                    raise ParseError("Markdown table needs at least one data row.")
                return self._rows_to_result(rows, "markdown")
                
        raise ParseError("No markdown table found.")

text = """benerin ketika data dari chat gpt seperti ini | Focus | Type | ID |
| --- | --- | --- |
| Client | Functional | TC-001 | 
| Pending | Functional | TC-002 | tabel jadi berantakan"""

p = MyParser()
res = p.parse(text)
import pandas as pd
print(res.dataframe)

