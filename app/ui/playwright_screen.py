from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTabWidget, QTextEdit, QPlainTextEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFileDialog, QSplitter,
    QLineEdit, QFormLayout, QApplication
)
from PySide6.QtGui import QFont

from app.services.playwright_service import PlaywrightService
from app.services.playwright_report_service import PlaywrightReportService, PlaywrightTestResult
from app.utils.highlighter import TypeScriptHighlighter
from app.core.paths import PLAYWRIGHT_DIR

class PlaywrightScreen(QWidget):
    def __init__(self, playwright_service: PlaywrightService) -> None:
        super().__init__()
        self.service = playwright_service
        self.report_service = PlaywrightReportService()
        self.results: list[PlaywrightTestResult] = []
        
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        title = QLabel("Playwright Automation Suite")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("PlaywrightTabs")
        layout.addWidget(self.tabs)

        # 1. Recorder Tab
        self.recorder_tab = QWidget()
        self.setup_recorder_tab()
        self.tabs.addTab(self.recorder_tab, "Recorder")

        # 2. Script Editor Tab
        self.editor_tab = QWidget()
        self.setup_editor_tab()
        self.tabs.addTab(self.editor_tab, "Script Editor")

        # 3. Execution Tab
        self.execution_tab = QWidget()
        self.setup_execution_tab()
        self.tabs.addTab(self.execution_tab, "Execution Log")

        # 4. Report Tab
        self.report_tab = QWidget()
        self.setup_report_tab()
        self.tabs.addTab(self.report_tab, "Report Preview")

    def setup_recorder_tab(self):
        layout = QVBoxLayout(self.recorder_tab)
        layout.setSpacing(20)
        
        info = QLabel("Record browser interactions to generate Playwright scripts.")
        info.setObjectName("Muted")
        layout.addWidget(info)

        form_group = QWidget()
        form_layout = QFormLayout(form_group)
        self.target_url = QLineEdit("https://example.com")
        self.target_url.setPlaceholderText("Enter target URL...")
        form_layout.addRow("Target URL:", self.target_url)
        layout.addWidget(form_group)

        btn_layout = QHBoxLayout()
        self.start_record_btn = QPushButton("Start Recording")
        self.start_record_btn.setObjectName("PrimaryButton")
        self.stop_record_btn = QPushButton("Stop Recording")
        self.stop_record_btn.setEnabled(False)
        
        btn_layout.addWidget(self.start_record_btn)
        btn_layout.addWidget(self.stop_record_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()

    def setup_editor_tab(self):
        layout = QVBoxLayout(self.editor_tab)
        
        self.script_editor = QPlainTextEdit()
        self.script_editor.setFont(QFont("Courier New", 11))
        self.script_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #000000;
                color: #00FF00;
                selection-background-color: #333333;
                border: 1px solid #333333;
            }
        """)
        self.script_editor.setPlaceholderText("Record a script or paste your Playwright code here...")
        self.highlighter = TypeScriptHighlighter(self.script_editor.document())
        layout.addWidget(self.script_editor)

        btn_layout = QHBoxLayout()
        self.save_script_btn = QPushButton("Save Script (.spec.ts)")
        self.run_test_btn = QPushButton("Run Test")
        self.run_test_btn.setObjectName("PrimaryButton")
        
        btn_layout.addWidget(self.save_script_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.run_test_btn)
        layout.addLayout(btn_layout)

    def setup_execution_tab(self):
        layout = QVBoxLayout(self.execution_tab)
        
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setFont(QFont("Courier New", 10))
        self.log_viewer.setObjectName("LogViewer")
        layout.addWidget(self.log_viewer)

        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("Muted")
        layout.addWidget(self.status_label)

    def setup_report_tab(self):
        layout = QVBoxLayout(self.report_tab)
        
        self.report_table = QTableWidget(0, 9)
        self.report_table.setHorizontalHeaderLabels([
            "Focus", "Type", "ID", "Pre-Condition", 
            "Scenario", "Test Steps", "Expected Result", 
            "Result", "Notes"
        ])
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.report_table)

        btn_layout = QHBoxLayout()
        self.export_report_btn = QPushButton("Export to Excel")
        self.export_report_btn.setObjectName("PrimaryButton")
        self.add_row_btn = QPushButton("Add Manual Result")
        self.copy_comment_btn = QPushButton("Copy Jira/ADO Comment")
        
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.copy_comment_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_report_btn)
        layout.addLayout(btn_layout)

    def connect_signals(self):
        self.start_record_btn.clicked.connect(self.start_recording)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        self.save_script_btn.clicked.connect(self.save_script)
        self.run_test_btn.clicked.connect(self.run_test)
        self.export_report_btn.clicked.connect(self.export_report)
        self.add_row_btn.clicked.connect(self.add_empty_row)
        self.copy_comment_btn.clicked.connect(self.copy_jira_comment)

        self.service.signals.log.connect(self.append_log)
        self.service.signals.finished.connect(self.on_execution_finished)
        self.service.signals.script_generated.connect(self.on_script_generated)

    def start_recording(self):
        url = self.target_url.text()
        self.service.start_recording(url)
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(True)
        self.append_log(f"Recording session started for: {url}")

    def stop_recording(self):
        self.service.stop_recording()
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        self.tabs.setCurrentWidget(self.editor_tab)

    def on_script_generated(self, script: str):
        self.script_editor.setPlainText(script)
        self.append_log("Script generated and loaded into editor.")

    def save_script(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Script", "", "Playwright Script (*.spec.ts)")
        if path:
            Path(path).write_text(self.script_editor.toPlainText())
            self.append_log(f"Script saved to: {path}")

    def run_test(self):
        # Temporarily save script to run it in PLAYWRIGHT_DIR
        temp_path = PLAYWRIGHT_DIR / "temp_test.spec.ts"
        temp_path.write_text(self.script_editor.toPlainText())
        
        self.log_viewer.clear()
        self.status_label.setText("Running tests...")
        self.tabs.setCurrentWidget(self.execution_tab)
        self.service.run_test(str(temp_path))

    def append_log(self, message: str):
        self.log_viewer.append(message)
        # Scroll to bottom
        self.log_viewer.verticalScrollBar().setValue(self.log_viewer.verticalScrollBar().maximum())

    def on_execution_finished(self, success: bool, message: str):
        self.status_label.setText(message)
        # Parse output for results (mocked for now, adding a row)
        result = "PASS" if success else "FAIL"
        self.add_test_result(
            PlaywrightTestResult(
                focus="Web App",
                test_type="Regression",
                test_id="PW-001",
                pre_condition="Browser Open",
                scenario="Automated Recording Execution",
                steps="Execute generated Playwright script",
                expected_result="Test passes without errors",
                result=result,
                notes=message if not success else ""
            )
        )
        self.tabs.setCurrentWidget(self.report_tab)

    def add_test_result(self, result: PlaywrightTestResult):
        self.results.append(result)
        row = self.report_table.rowCount()
        self.report_table.insertRow(row)
        
        items = [
            result.focus, result.test_type, result.test_id,
            result.pre_condition, result.scenario, result.steps,
            result.expected_result, result.result, result.notes
        ]
        
        for i, text in enumerate(items):
            item = QTableWidgetItem(text)
            if i == 7: # Result
                if text == "PASS": item.setBackground(Qt.green)
                elif text == "FAIL": item.setBackground(Qt.red)
            self.report_table.setItem(row, i, item)

    def add_empty_row(self):
        self.report_table.insertRow(self.report_table.rowCount())

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Report", "Regression_Report.xlsx", "Excel Files (*.xlsx)")
        if path:
            # Sync table back to results list if edited
            self.results = []
            for row in range(self.report_table.rowCount()):
                data = []
                for col in range(9):
                    item = self.report_table.item(row, col)
                    data.append(item.text() if item else "")
                
                if any(data):
                    self.results.append(PlaywrightTestResult(*data))

            self.report_service.generate_report(self.results, Path(path))
            self.append_log(f"Report exported to: {path}")

    def copy_jira_comment(self):
        row = self.report_table.currentRow()
        if row < 0:
            # Fallback to last row if none selected
            row = self.report_table.rowCount() - 1
            
        if row < 0:
            return

        # Get data from table
        scenario = self.report_table.item(row, 4).text() if self.report_table.item(row, 4) else "N/A"
        result = self.report_table.item(row, 7).text() if self.report_table.item(row, 7) else "N/A"
        notes = self.report_table.item(row, 8).text() if self.report_table.item(row, 8) else ""
        
        # Format comment
        comment = f"[{result}] {scenario}"
        if notes:
            comment += f" - {notes}"
            
        # Copy to clipboard
        QApplication.clipboard().setText(comment)
        self.append_log(f"Copied Jira/ADO comment: {comment}")
