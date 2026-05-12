from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget


class Sidebar(QWidget):
    navigationRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        self._buttons: dict[str, QPushButton] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(8)

        brand = QLabel("QA tools")
        brand.setObjectName("Brand")
        layout.addWidget(brand)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        items = [
            ("dashboard", "Dashboard"),
            ("input", "Paste"),
            ("preview", "Preview"),
            ("export", "Export"),
            ("loadrunner", "LoadRunner"),
            ("pagespeed", "Accessibility"),
            ("history", "History"),
            ("settings", "Settings"),
        ]
        for key, label in items:
            button = QPushButton(label)
            button.setObjectName("NavButton")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, route=key: self.navigationRequested.emit(route))
            self.group.addButton(button)
            self._buttons[key] = button
            layout.addWidget(button)
        layout.addStretch()
        self.set_active("dashboard")

    def set_active(self, key: str) -> None:
        if key in self._buttons:
            self._buttons[key].setChecked(True)
