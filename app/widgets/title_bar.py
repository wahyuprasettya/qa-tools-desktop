from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class TitleBar(QWidget):
    closeRequested = Signal()
    minimizeRequested = Signal()
    maximizeRequested = Signal()

    def __init__(self, title: str) -> None:
        super().__init__()
        self.setObjectName("TitleBar")
        self._drag_position: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.back_button = QPushButton("<")
        self.back_button.setObjectName("BackButton")
        self.back_button.setFixedSize(30, 24)
        layout.addWidget(self.back_button)
        layout.addStretch()

        self.title = QLabel(title)
        self.title.setObjectName("WindowTitle")
        layout.addWidget(self.title)
        layout.addStretch()

        self.min_button = QPushButton("_")
        self.max_button = QPushButton("□")
        self.close_button = QPushButton("X")
        for button in (self.min_button, self.max_button, self.close_button):
            button.setObjectName("WindowButton")
            button.setFixedSize(30, 24)
        self.close_button.setObjectName("CloseButton")
        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.close_button)

        self.min_button.clicked.connect(self.minimizeRequested.emit)
        self.max_button.clicked.connect(self.maximizeRequested.emit)
        self.close_button.clicked.connect(self.closeRequested.emit)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._drag_position is not None and event.buttons() & Qt.LeftButton:
            window = self.window()
            delta = event.globalPosition().toPoint() - self._drag_position
            window.move(window.pos() + delta)
            self._drag_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_position = None
