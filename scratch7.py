import sys
from PySide6.QtWidgets import QApplication, QTextEdit
from PySide6.QtCore import QMimeData

app = QApplication(sys.argv)
editor = QTextEdit()
editor.setAcceptRichText(False)

mime = QMimeData()
mime.setHtml("<table><tr><td>A</td><td>B</td></tr><tr><td>C</td><td></td></tr></table>")
mime.setText("A\tB\nC\t\n")

# Simulate paste
editor.insertFromMimeData(mime)
print(repr(editor.toPlainText()))
