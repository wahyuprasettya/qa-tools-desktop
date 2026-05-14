from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Iterable

import pandas as pd

from app.core.exceptions import ParseError


@dataclass(slots=True)
class ParseResult:
    dataframe: pd.DataFrame
    source_format: str
    warnings: list[str]


class TableParser:
    def parse(self, raw_text: str) -> ParseResult:
        text = self._normalize_text(raw_text)
        if not text:
            raise ParseError("Paste text that contains at least one table-like row.")

        parsers = (
            self._parse_markdown,
            self._parse_flat_lines,
            self._parse_delimited,
            self._parse_spacing,
            self._parse_key_value,
        )
        errors: list[str] = []
        for parser in parsers:
            try:
                result = parser(text)
                if result.dataframe.shape[0] > 0 and result.dataframe.shape[1] > 0:
                    return self._clean_result(result)
            except ParseError as exc:
                errors.append(str(exc))
        raise ParseError("Could not detect a usable table. Try copying only the table content.")

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

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

    def _parse_delimited(self, text: str) -> ParseResult:
        candidates = [("\t", "tsv"), (",", "csv"), (";", "semicolon")]
        best: tuple[list[list[str]], str, int] | None = None
        for delimiter, name in candidates:
            sample = [row for row in csv.reader(io.StringIO(text), delimiter=delimiter) if row]
            widths = [len(row) for row in sample if row]
            if widths and widths[0] > 1 and max(widths) > 1:
                dominant_width = max(set(widths), key=widths.count)
                score = widths.count(dominant_width)
                if dominant_width != widths[0] or score < 2:
                    continue
                if best is None or score > best[2]:
                    best = (sample, name, score)
        if best is None:
            raise ParseError("No delimited table found.")
        return self._rows_to_result(best[0], best[1])

    def _parse_flat_lines(self, text: str) -> ParseResult:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if len(lines) < 4:
            raise ParseError("No flattened table found.")
        if any(any(delimiter in line for delimiter in ("|", "\t", ";")) for line in lines):
            raise ParseError("Text is not a flattened table.")
        if self._has_delimited_rows(lines, ","):
            raise ParseError("Text is not a flattened table.")

        best: tuple[int, list[list[str]], float] | None = None
        max_columns = min(200, len(lines) // 2)
        for width in range(2, max_columns + 1):
            headers = lines[:width]
            if not self._looks_like_header_row(headers):
                continue
            records = self._flat_records_for_width(lines, width)
            if not records:
                continue
            score = self._score_flat_table(headers, records)
            if best is None or score > best[2]:
                best = (width, records, score)

        if best is None or best[2] < 1:
            raise ParseError("No flattened table found.")

        width, records, _score = best
        rows = [lines[:width]]
        rows.extend(records)
        return self._rows_to_result(rows, "line-wrapped table")

    def _parse_spacing(self, text: str) -> ParseResult:
        rows = []
        for line in text.splitlines():
            cells = [cell.strip() for cell in re.split(r"\s{2,}", line.strip()) if cell.strip()]
            rows.append(cells)
        if not rows or max(len(row) for row in rows) < 2:
            raise ParseError("No aligned text table found.")
        return self._rows_to_result(rows, "fixed-width")

    def _parse_key_value(self, text: str) -> ParseResult:
        rows = []
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            rows.append([key.strip(), value.strip()])
        if len(rows) < 2:
            raise ParseError("No key-value table found.")
        return self._rows_to_result([["Field", "Value"], *rows], "key-value")

    def _rows_to_result(self, rows: Iterable[Iterable[str]], source_format: str) -> ParseResult:
        normalized = [list(row) for row in rows if any(str(cell).strip() for cell in row)]
        if len(normalized) < 2:
            raise ParseError("Table needs a header and at least one data row.")
        width = max(1, len(normalized[0]))
        padded = [self._fit_row_width(row, width) for row in normalized]
        headers = self._dedupe_headers(padded[0])
        dataframe = pd.DataFrame(padded[1:], columns=headers)
        return ParseResult(dataframe=dataframe, source_format=source_format, warnings=[])

    def _markdown_cells(self, line: str) -> list[str]:
        line = re.sub(r"^\s*(?:[-*+]\s+|\d+[\.)]\s+)(?=\|)", "", line.strip())
        parts = [part.strip() for part in line.split("|")]
        if parts and parts[0] == "":
            parts = parts[1:]
        if parts and parts[-1] == "":
            parts = parts[:-1]
        return parts

    def _fit_row_width(self, row: list[str], width: int) -> list[str]:
        if len(row) == width:
            return row
        if len(row) < width:
            return row + [""] * (width - len(row))
        return [*row[: width - 1], " | ".join(row[width - 1 :])]

    def _has_delimited_rows(self, lines: list[str], delimiter: str) -> bool:
        widths = [len(next(csv.reader([line], delimiter=delimiter))) for line in lines]
        candidate_widths = [width for width in widths if width > 1]
        if len(candidate_widths) < 2:
            return False
        dominant_width = max(set(candidate_widths), key=candidate_widths.count)
        return widths[0] == dominant_width and candidate_widths.count(dominant_width) >= 2

    def _flat_records_for_width(self, lines: list[str], width: int) -> list[list[str]]:
        remaining = lines[width:]
        if len(remaining) < width:
            return []

        row_widths = [width]
        if width > 2:
            row_widths.append(width - 1)

        for row_width in row_widths:
            if len(remaining) < row_width * 2 or len(remaining) % row_width != 0:
                continue
            records = [remaining[index : index + row_width] for index in range(0, len(remaining), row_width)]
            if row_width < width:
                records = [record + [""] * (width - row_width) for record in records]
            return records

        return []

    def _score_flat_table(self, headers: list[str], records: list[list[str]]) -> float:
        header_like = sum(1 for header in headers if self._looks_like_header(header))
        data_like_headers = sum(1 for header in headers if self._looks_like_data_value(header))
        sentence_like_headers = sum(1 for header in headers if self._looks_like_sentence_value(header))
        duplicate_headers = len(headers) - len({header.casefold() for header in headers})

        score = len(headers) * 0.25
        score += header_like * 3
        score -= data_like_headers * 12
        score -= sentence_like_headers * 8
        score -= duplicate_headers * 8

        first_record = records[0] if records else []
        score -= sum(1.5 for value in first_record if self._looks_like_header(value))
        score += sum(1 for record in records for value in record if self._looks_like_data_value(value)) / max(
            len(records),
            1,
        )
        score += sum(0.75 for record in records for value in record if self._looks_like_sentence_value(value)) / max(
            len(records),
            1,
        )
        return score

    def _looks_like_header_row(self, headers: list[str]) -> bool:
        if len(set(header.casefold() for header in headers)) != len(headers):
            return False

        header_like = sum(1 for header in headers if self._looks_like_header(header))
        data_like = sum(1 for header in headers if self._looks_like_data_value(header))
        sentence_like = sum(1 for header in headers if self._looks_like_sentence_value(header))

        return header_like / len(headers) >= 0.7 and data_like == 0 and sentence_like == 0

    def _looks_like_header(self, value: str) -> bool:
        value = value.strip()
        if not value or self._looks_like_data_value(value):
            return False
        if self._looks_like_sentence_value(value):
            return False
        words = value.split()
        if len(words) > 5:
            return False
        if not any(re.search(r"[A-Za-z]", word) for word in words):
            return False
        return all(re.fullmatch(r"[A-Za-z][A-Za-z0-9/&()\-]*|[&/]|\d+", word) for word in words)

    def _looks_like_data_value(self, value: str) -> bool:
        value = value.strip()
        if re.fullmatch(r"[A-Za-z]{1,8}-\d{1,6}", value):
            return True
        if re.fullmatch(r"\d+\.\s+\S.*", value):
            return True
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?", value):
            return True
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+|\d+", value):
            return True
        return value.lower() in {
            "success",
            "failed",
            "processing",
            "pending",
            "negative",
            "positive",
            "regression",
            "pass",
            "fail",
            "windows",
            "linux",
            "macos",
            "functional",
        }

    def _looks_like_sentence_value(self, value: str) -> bool:
        value = value.strip()
        words = value.split()
        return len(words) > 5 or bool(re.search(r"[.!?]\s+\S", value))

    def _clean_result(self, result: ParseResult) -> ParseResult:
        df = result.dataframe.copy()
        df = df.map(lambda value: self._clean_cell(value))
        df.columns = self._dedupe_headers([self._clean_header(col) for col in df.columns])
        df = df.dropna(how="all")
        if result.source_format not in {"markdown", "line-wrapped table"}:
            df = df.loc[:, ~(df.astype(str).apply(lambda col: col.str.strip().eq("").all()))]
        df = df.reset_index(drop=True)
        warnings: list[str] = []
        if df.empty:
            raise ParseError("Detected table only had empty cells.")
        if result.dataframe.shape != df.shape:
            warnings.append("Removed empty rows or columns.")
        return ParseResult(dataframe=df, source_format=result.source_format, warnings=warnings)

    def _clean_cell(self, value: object) -> str:
        if pd.isna(value):
            return ""
        cell = str(value)
        cell = re.sub(r"<br\s*/?>", "\n", cell, flags=re.IGNORECASE)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cell.split("\n")]
        cell = "\n".join(line for line in lines if line)
        return cell.strip("`")

    def _clean_header(self, value: object) -> str:
        header = self._clean_cell(value)
        header = re.sub(r"^[#*\- ]+", "", header).strip()
        return header or "Column"

    def _dedupe_headers(self, headers: list[object]) -> list[str]:
        seen: dict[str, int] = {}
        cleaned = [self._clean_header(header) for header in headers]
        output = []
        for header in cleaned:
            count = seen.get(header, 0)
            seen[header] = count + 1
            output.append(header if count == 0 else f"{header} {count + 1}")
        return output

    def _is_markdown_separator(self, cells: list[str]) -> bool:
        return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells if cell.strip())
