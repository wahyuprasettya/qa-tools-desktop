import sys
from PySide6.QtWidgets import QApplication, QTextEdit

app = QApplication(sys.argv)
editor = QTextEdit()
html = """
<table>
  <tr><th>Focus</th><th>Type</th><th>Notes</th></tr>
  <tr><td>Client Creation</td><td>Functional</td><td>Pending</td></tr>
  <tr><td>Data</td><td>Regression</td><td></td></tr>
</table>
"""
editor.insertHtml(html)
print(repr(editor.toPlainText()))
