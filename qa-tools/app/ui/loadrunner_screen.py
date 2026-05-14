from __future__ import annotations

import datetime
from PySide6.QtCore import Qt, Signal, QThreadPool, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog,
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

from app.models.loadrunner_model import LoadRunnerTableModel
from app.services.loadrunner_service import LoadRunnerService, LoadRunnerSignals, TransactionStatus
from app.services.loadrunner_history import LoadRunnerHistoryService, LRHistoryRecord
from app.utils.worker import Worker


class RunScenarioDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configure Scenario")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        self.scenario_path = QLineEdit()
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.scenario_path)
        path_layout.addWidget(browse_btn)
        
        form.addRow("Scenario File:", path_layout)
        
        self.vusers = QLineEdit("10")
        form.addRow("Virtual Users:", self.vusers)
        
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        run_btn = QPushButton("Run")
        run_btn.setObjectName("PrimaryButton")
        run_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons.addStretch()
        buttons.addWidget(cancel_btn)
        buttons.addWidget(run_btn)
        layout.addLayout(buttons)

    def _browse(self) -> None:
        file, _ = QFileDialog.getOpenFileName(self, "Select Scenario File", "", "LoadRunner Scenarios (*.lrs *.usr);;All Files (*)")
        if file:
            self.scenario_path.setText(file)

    def get_config(self) -> dict:
        return {
            "path": self.scenario_path.text(),
            "vusers": int(self.vusers.text() or 0)
        }


class LoadRunnerScreen(QWidget):
    # Signal emitted when a report is generated
    reportRequested = Signal(str)

    def __init__(self, history_service: LoadRunnerHistoryService) -> None:
        super().__init__()
        self.history = history_service
        self.lr_service = LoadRunnerService()
        self.thread_pool = QThreadPool.globalInstance()
        self.is_running = False
        self._stop_event = [False]
        self._start_time = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_elapsed_time)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("LoadRunner Execution")
        title.setObjectName("PageTitle")
        subtitle = QLabel("Run scenarios and monitor performance in real-time.")
        subtitle.setObjectName("Muted")
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        header.addLayout(title_layout)
        
        header.addStretch()
        
        self.status_badge = QLabel("READY")
        self.status_badge.setObjectName("StatusBadge")
        self.status_badge.setStyleSheet("background-color: #3b82f6; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        header.addWidget(self.status_badge)
        
        self.run_btn = QPushButton("Run Scenario")
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.clicked.connect(self._show_run_dialog)
        header.addWidget(self.run_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_execution)
        header.addWidget(self.stop_btn)
        
        layout.addLayout(header)

        # Dashboard Cards
        cards = QHBoxLayout()
        self.card_vusers = self._create_card("Active Vusers", "0")
        self.card_elapsed = self._create_card("Elapsed Time", "00:00:00")
        self.card_passed = self._create_card("Passed Transactions", "0")
        self.card_failed = self._create_card("Failed Transactions", "0")
        
        cards.addWidget(self.card_vusers["frame"])
        cards.addWidget(self.card_elapsed["frame"])
        cards.addWidget(self.card_passed["frame"])
        cards.addWidget(self.card_failed["frame"])
        layout.addLayout(cards)

        # Content Splitter (Table & Terminal)
        content_layout = QHBoxLayout()
        
        # Left side: Table
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Execution Realtime Transactions:"))
        self.model = LoadRunnerTableModel()
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        left_layout.addWidget(self.table)
        content_layout.addLayout(left_layout, stretch=2)
        
        # Right side: Terminal
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("Execution Logs:"))
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        font = QFont("monospace")
        font.setStyleHint(QFont.Monospace)
        self.terminal.setFont(font)
        self.terminal.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; padding: 8px;")
        right_layout.addWidget(self.terminal)
        content_layout.addLayout(right_layout, stretch=1)
        
        layout.addLayout(content_layout, stretch=1)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        # Generate Report Button
        report_btn = QPushButton("Generate Simple Report")
        report_btn.clicked.connect(self._generate_report)
        layout.addWidget(report_btn, alignment=Qt.AlignRight)

    def _create_card(self, title: str, value: str) -> dict:
        frame = QFrame()
        frame.setObjectName("MetricCard")
        l = QVBoxLayout(frame)
        l.addWidget(QLabel(title))
        val_label = QLabel(value)
        val_label.setObjectName("MetricValue")
        l.addWidget(val_label)
        return {"frame": frame, "value_label": val_label}

    def _show_run_dialog(self) -> None:
        dialog = RunScenarioDialog(self)
        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()
            if not config["path"]:
                self.terminal.append("[WARNING] No scenario path provided. Using dummy path.")
                config["path"] = "/dummy/scenario.lrs"
            self._start_execution(config)

    def _start_execution(self, config: dict) -> None:
        self.model.clear()
        self.terminal.clear()
        self.progress.setValue(0)
        self.is_running = True
        self._stop_event[0] = False
        
        self.status_badge.setText("RUNNING")
        self.status_badge.setStyleSheet("background-color: #f59e0b; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        self.card_vusers["value_label"].setText(str(config["vusers"]))
        self.card_passed["value_label"].setText("0")
        self.card_failed["value_label"].setText("0")
        
        self._start_time = datetime.datetime.now()
        self._timer.start(1000)
        self.current_scenario_path = config["path"]

        signals = LoadRunnerSignals()
        signals.progress.connect(self.progress.setValue)
        signals.log.connect(self.terminal.append)
        signals.transaction.connect(self._handle_transaction)
        signals.finished.connect(self._handle_finished)

        # Start service in background thread
        self.worker = Worker(self.lr_service.run_scenario, config["path"], signals, self._stop_event)
        self.thread_pool.start(self.worker)

    def _stop_execution(self) -> None:
        if self.is_running:
            self._stop_event[0] = True
            self.stop_btn.setEnabled(False)
            self.terminal.append("Stopping execution...")

    def _handle_transaction(self, tx: TransactionStatus) -> None:
        self.model.add_transaction(tx)
        self.table.scrollToBottom()
        
        stats = self.model.get_stats()
        self.card_passed["value_label"].setText(str(stats["passed"]))
        self.card_failed["value_label"].setText(str(stats["failed"]))

    def _handle_finished(self, success: bool, message: str) -> None:
        self.is_running = False
        self._timer.stop()
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.status_badge.setText("COMPLETED")
            self.status_badge.setStyleSheet("background-color: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
        else:
            self.status_badge.setText("STOPPED")
            self.status_badge.setStyleSheet("background-color: #ef4444; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;")
            
        # Save to history
        duration = 0
        if self._start_time:
            duration = (datetime.datetime.now() - self._start_time).total_seconds()
            
        stats = self.model.get_stats()
        record = LRHistoryRecord(
            timestamp=datetime.datetime.now().isoformat(),
            scenario_path=self.current_scenario_path,
            status="Completed" if success else "Stopped",
            duration_sec=duration,
            total_transactions=stats["total"],
            passed_transactions=stats["passed"],
            failed_transactions=stats["failed"]
        )
        self.history.add_record(record)
        self.terminal.append(f"Execution finished. Status: {message}")

    def _update_elapsed_time(self) -> None:
        if self._start_time:
            delta = datetime.datetime.now() - self._start_time
            # Format delta to HH:MM:SS
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.card_elapsed["value_label"].setText(time_str)

    def _generate_report(self) -> None:
        # Create a simple report from the model
        stats = self.model.get_stats()
        if stats["total"] == 0:
            self.reportRequested.emit("No data to report.")
            return
            
        report = (
            f"--- LoadRunner Execution Report ---\n"
            f"Scenario: {self.current_scenario_path}\n"
            f"Total Transactions: {stats['total']}\n"
            f"Passed: {stats['passed']}\n"
            f"Failed: {stats['failed']}\n"
            f"-----------------------------------\n"
        )
        self.terminal.append(report)
        self.reportRequested.emit("Simple report generated in terminal.")
