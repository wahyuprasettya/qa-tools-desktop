from __future__ import annotations

import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat

class TypeScriptHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#C678DD")) # Purple
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "await", "async", "test", "expect", "const", "let", "var",
            "import", "from", "return", "if", "else", "for", "while",
            "new", "function", "class", "try", "catch", "finally"
        ]
        for word in keywords:
            pattern = re.compile(f"\\b{word}\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#98C379")) # Green
        self.highlighting_rules.append((re.compile("'[^']*'"), string_format))
        self.highlighting_rules.append((re.compile('"[^"]*"'), string_format))
        self.highlighting_rules.append((re.compile("`[^`]*`"), string_format))

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#5C6370")) # Grey
        self.highlighting_rules.append((re.compile("//[^\n]*"), comment_format))
        self.highlighting_rules.append((re.compile("/\\*.*\\*/"), comment_format))

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#61AFEF")) # Blue
        self.highlighting_rules.append((re.compile("\\b[A-Za-z0-9_]+(?=\\()"), function_format))

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#D19A66")) # Orange
        self.highlighting_rules.append((re.compile("\\b[0-9]+\\b"), number_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)
