from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, QTimer, Qt
from PySide6.QtWidgets import QLabel, QWidget


class Toast(QLabel):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.hide()
        self._animation = QPropertyAnimation(self, b"windowOpacity", self)
        self._animation.setDuration(180)

    def show_message(self, message: str, kind: str = "info", timeout: int = 2800) -> None:
        self.setProperty("kind", kind)
        self.setText(message)
        self.adjustSize()
        width = min(max(self.sizeHint().width() + 36, 280), max(280, self.parentWidget().width() - 48))
        self.setFixedWidth(width)
        self.move((self.parentWidget().width() - width) // 2, 24)
        self.setWindowOpacity(0.0)
        self.show()
        self._animation.stop()
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()
        QTimer.singleShot(timeout, self._hide)

    def _hide(self) -> None:
        self._animation.stop()
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.finished.connect(self.hide)
        self._animation.start()

