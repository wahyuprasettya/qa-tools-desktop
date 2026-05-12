from __future__ import annotations

from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.dataframe_model import DataFrameModel
from app.services.config_manager import AppSettings
from app.services.history_service import ExportRecord


class DashboardScreen(QWidget):
    goInputRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        title = QLabel("Dashboard")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Turn copied ChatGPT tables into polished spreadsheets.")
        subtitle.setObjectName("Muted")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        cards = QHBoxLayout()
        for label, value in (("Detected formats", "Markdown, TSV, CSV, spaced text"), ("Exports", "XLSX and CSV"), ("Session", "Autosaved locally")):
            card = QFrame()
            card.setObjectName("MetricCard")
            card_layout = QVBoxLayout(card)
            card_layout.addWidget(QLabel(label))
            number = QLabel(value)
            number.setObjectName("MetricValue")
            number.setWordWrap(True)
            card_layout.addWidget(number)
            cards.addWidget(card)
        layout.addLayout(cards)
        action = QPushButton("Start from pasted text")
        action.setObjectName("PrimaryButton")
        action.clicked.connect(self.goInputRequested.emit)
        layout.addWidget(action, alignment=Qt.AlignLeft)
        layout.addStretch()


class InputScreen(QWidget):
    parseRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        title = QLabel("Paste Input")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        self.editor = QTextEdit()
        self.editor.setObjectName("InputEditor")
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText("Paste a markdown table, TSV, CSV, or aligned plain text table here...")
        layout.addWidget(self.editor, stretch=1)
        actions = QHBoxLayout()
        self.parse_button = QPushButton("Detect table")
        self.parse_button.setObjectName("PrimaryButton")
        self.clear_button = QPushButton("Clear")
        actions.addWidget(self.parse_button)
        actions.addWidget(self.clear_button)
        actions.addStretch()
        layout.addLayout(actions)
        self.parse_button.clicked.connect(lambda: self.parseRequested.emit(self.editor.toPlainText()))
        self.clear_button.clicked.connect(self.editor.clear)

    def set_text(self, text: str) -> None:
        self.editor.setPlainText(text)

    def text(self) -> str:
        return self.editor.toPlainText()

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasText():
            self.editor.setPlainText(event.mimeData().text())
            return
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self.editor.setPlainText(path.read_text(encoding="utf-8", errors="replace"))
                break


class PreviewScreen(QWidget):
    exportRequested = Signal()

    def __init__(self, max_rows: int) -> None:
        super().__init__()
        self.model = DataFrameModel(max_rows=max_rows, editable=True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        self.title = QLabel("Table Preview")
        self.title.setObjectName("PageTitle")
        self.meta = QLabel("No table detected yet.")
        self.meta.setObjectName("Muted")
        layout.addWidget(self.title)
        layout.addWidget(self.meta)
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setEditTriggers(
            QTableView.DoubleClicked
            | QTableView.SelectedClicked
            | QTableView.EditKeyPressed
            | QTableView.AnyKeyPressed
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setDefaultSectionSize(150)
        self.table.horizontalHeader().setMinimumSectionSize(80)
        self.table.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self.table, stretch=1)
        button = QPushButton("Export this table")
        button.setObjectName("PrimaryButton")
        button.clicked.connect(self.exportRequested.emit)
        layout.addWidget(button, alignment=Qt.AlignRight)

    def set_dataframe(self, dataframe: pd.DataFrame, source_format: str, warnings: list[str]) -> None:
        self.model.set_dataframe(dataframe)
        warning_text = f" • {' '.join(warnings)}" if warnings else ""
        self.meta.setText(f"{len(dataframe)} rows, {len(dataframe.columns)} columns • Detected {source_format}{warning_text}")


class ExportScreen(QWidget):
    exportRequested = Signal(str, str)

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        title = QLabel("Export")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.filename = QLineEdit("chatgpt_table")
        self.format = QComboBox()
        self.format.addItems(["xlsx", "csv"])
        self.format.setCurrentText(settings.default_export_format)
        form.addRow("File name", self.filename)
        form.addRow("Format", self.format)
        layout.addLayout(form)
        self.summary = QLabel("Detect a table before exporting.")
        self.summary.setObjectName("Muted")
        layout.addWidget(self.summary)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("Export progress: %p%")
        layout.addWidget(self.progress)
        self.export_button = QPushButton("Export file")
        self.export_button.setObjectName("PrimaryButton")
        self.export_button.clicked.connect(lambda: self.exportRequested.emit(self.filename.text(), self.format.currentText()))
        layout.addWidget(self.export_button, alignment=Qt.AlignLeft)
        debug_label = QLabel("Debug")
        debug_label.setObjectName("Muted")
        layout.addWidget(debug_label)
        self.debug = QTextEdit()
        self.debug.setObjectName("ExportDebug")
        self.debug.setReadOnly(True)
        self.debug.setPlaceholderText("Export details and errors will appear here.")
        self.debug.setMinimumHeight(140)
        layout.addWidget(self.debug, stretch=1)
        layout.addStretch()

    def set_summary(self, dataframe: pd.DataFrame | None) -> None:
        if dataframe is None or dataframe.empty:
            self.summary.setText("Detect a table before exporting.")
        else:
            self.summary.setText(f"Ready to export {len(dataframe)} rows and {len(dataframe.columns)} columns.")

    def reset_export_status(self) -> None:
        self.progress.setValue(0)
        self.progress.setFormat("Export progress: %p%")
        self.debug.clear()
        self.export_button.setEnabled(True)

    def set_export_progress(self, percent: int, message: str) -> None:
        self.progress.setValue(percent)
        self.progress.setFormat(f"{message} %p%")
        self.append_debug(f"[{percent:3d}%] {message}")

    def set_export_running(self, running: bool) -> None:
        self.export_button.setEnabled(not running)

    def append_debug(self, message: str) -> None:
        if not message:
            return
        if self.debug.toPlainText():
            self.debug.append(message)
        else:
            self.debug.setPlainText(message)


class SettingsScreen(QWidget):
    settingsChanged = Signal(dict)
    browseRequested = Signal()

    def __init__(self, settings: AppSettings) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        form = QFormLayout()
        self.theme = QComboBox()
        self.theme.addItems(["dark", "light"])
        self.theme.setCurrentText(settings.theme)
        self.default_format = QComboBox()
        self.default_format.addItems(["xlsx", "csv"])
        self.default_format.setCurrentText(settings.default_export_format)
        self.output_dir = QLineEdit(settings.output_directory)
        self.pagespeed_api_key = QLineEdit(settings.pagespeed_api_key)
        self.pagespeed_api_key.setEchoMode(QLineEdit.Password)
        self.autosave = QCheckBox("Save pasted text between launches")
        self.autosave.setChecked(settings.autosave_session)
        self.open_after_export = QCheckBox("Open exported file after export")
        self.open_after_export.setChecked(settings.open_after_export)
        browse = QPushButton("Browse")
        browse.clicked.connect(self._choose_directory)
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_dir)
        output_row.addWidget(browse)
        form.addRow("Theme", self.theme)
        form.addRow("Default format", self.default_format)
        form.addRow("Output directory", output_row)
        form.addRow("PageSpeed API Key", self.pagespeed_api_key)
        form.addRow("", self.autosave)
        form.addRow("", self.open_after_export)
        layout.addLayout(form)
        save = QPushButton("Save settings")
        save.setObjectName("PrimaryButton")
        save.clicked.connect(self._emit_settings)
        layout.addWidget(save, alignment=Qt.AlignLeft)
        layout.addStretch()

    def _choose_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose output directory", self.output_dir.text())
        if directory:
            self.output_dir.setText(directory)

    def _emit_settings(self) -> None:
        self.settingsChanged.emit(
            {
                "theme": self.theme.currentText(),
                "default_export_format": self.default_format.currentText(),
                "output_directory": self.output_dir.text(),
                "pagespeed_api_key": self.pagespeed_api_key.text(),
                "autosave_session": self.autosave.isChecked(),
                "open_after_export": self.open_after_export.isChecked(),
            }
        )


class HistoryScreen(QWidget):
    clearRequested = Signal()

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        title = QLabel("Export History")
        title.setObjectName("PageTitle")
        layout.addWidget(title)
        self.table = QTableView()
        self.model = DataFrameModel()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, stretch=1)
        clear = QPushButton("Clear history")
        clear.clicked.connect(self.clearRequested.emit)
        layout.addWidget(clear, alignment=Qt.AlignRight)

    def set_records(self, records: list[ExportRecord]) -> None:
        dataframe = pd.DataFrame(
            [
                {
                    "Created": record.created_at,
                    "File": record.filename,
                    "Type": record.file_type,
                    "Rows": record.rows,
                    "Columns": record.columns,
                    "Path": record.path,
                }
                for record in records
            ]
        )
        self.model.set_dataframe(dataframe)
