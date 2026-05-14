from __future__ import annotations


class QAToolsError(Exception):
    """Base application exception."""


class ParseError(QAToolsError):
    """Raised when text cannot be parsed into a usable table."""


class ExportError(QAToolsError):
    """Raised when export fails."""
