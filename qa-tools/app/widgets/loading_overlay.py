from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class LoadingOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("LoadingOverlay")
        self.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        self.label = QLabel("Working...")
        self.label.setObjectName("LoadingLabel")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.hide()

    def show_message(self, message: str) -> None:
        self.label.setText(message)
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)

