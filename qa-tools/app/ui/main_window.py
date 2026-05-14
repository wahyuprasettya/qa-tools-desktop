from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
from PySide6.QtCore import QThreadPool, QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QStackedWidget, QVBoxLayout, QWidget

from app.core.constants import APP_NAME, DEFAULT_EXPORT_BASENAME
from app.services.config_manager import ConfigManager
from app.services.export_service import ExportService
from app.services.file_manager import FileManager
from app.services.history_service import HistoryService
from app.services.loadrunner_history import LoadRunnerHistoryService
from app.services.session_service import SessionService
from app.services.table_parser import ParseResult, TableParser
from app.services.theme_manager import ThemeManager
from app.ui.screens import (
    DashboardScreen,
    ExportScreen,
    HistoryScreen,
    InputScreen,
    PreviewScreen,
    SettingsScreen,
)
from app.ui.loadrunner_screen import LoadRunnerScreen
from app.ui.pagespeed_screen import PageSpeedScreen
from app.ui.playwright_screen import PlaywrightScreen
from app.ui.widgets_preview_screen import WidgetsPreviewScreen
from app.services.playwright_service import PlaywrightService
from app.utils.worker import Worker
from app.widgets.sidebar import Sidebar
from app.widgets.loading_overlay import LoadingOverlay
from app.widgets.title_bar import TitleBar
from app.widgets.toast import Toast


class MainWindow(QWidget):
    def __init__(
        self,
        config: ConfigManager,
        theme: ThemeManager,
        history: HistoryService,
        session: SessionService,
    ) -> None:
        super().__init__()
        self.config = config
        self.theme = theme
        self.history = history
        self.lr_history = LoadRunnerHistoryService()
        self.session = session
        self.parser = TableParser()
        self.exporter = ExportService()
        self.thread_pool = QThreadPool.globalInstance()
        self.playwright_service = PlaywrightService()
        self.current_dataframe: pd.DataFrame | None = None
        self.export_in_progress = False
        self.active_workers: list[Worker] = []

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(1180, 760)
        self.setMinimumSize(940, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(0)
        self.shell = QWidget()
        self.shell.setObjectName("AppShell")
        root.addWidget(self.shell)
        shell_layout = QVBoxLayout(self.shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self.title_bar = TitleBar(APP_NAME)
        shell_layout.addWidget(self.title_bar)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        shell_layout.addLayout(body, stretch=1)

        self.sidebar = Sidebar()
        body.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        body.addWidget(self.stack, stretch=1)

        self.dashboard_screen = DashboardScreen()
        self.input_screen = InputScreen()
        self.preview_screen = PreviewScreen(self.config.settings.max_preview_rows)
        self.export_screen = ExportScreen(self.config.settings)
        self.loadrunner_screen = LoadRunnerScreen(self.lr_history)
        self.pagespeed_screen = PageSpeedScreen(self.config.settings)
        self.playwright_screen = PlaywrightScreen(self.playwright_service)
        self.widgets_screen = WidgetsPreviewScreen()
        self.history_screen = HistoryScreen()
        self.settings_screen = SettingsScreen(self.config.settings)
        self.screens = {
            "dashboard": self.dashboard_screen,
            "input": self.input_screen,
            "preview": self.preview_screen,
            "export": self.export_screen,
            "loadrunner": self.loadrunner_screen,
            "pagespeed": self.pagespeed_screen,
            "playwright": self.playwright_screen,
            "widgets": self.widgets_screen,
            "history": self.history_screen,
            "settings": self.settings_screen,
        }
        for screen in self.screens.values():
            self.stack.addWidget(screen)

        self.playwright_service.set_playwright_path(self.config.settings.playwright_path)
        self.toast = Toast(self.shell)
        self.loading = LoadingOverlay(self.shell)
        self._connect_signals()
        self._install_shortcuts()
        self.input_screen.set_text(self.session.load_text())
        self.refresh_history()

    def _connect_signals(self) -> None:
        self.title_bar.closeRequested.connect(self.close)
        self.title_bar.minimizeRequested.connect(self.showMinimized)
        self.title_bar.maximizeRequested.connect(self._toggle_maximized)
        self.sidebar.navigationRequested.connect(self.navigate)
        self.dashboard_screen.goInputRequested.connect(lambda: self.navigate("input"))
        self.input_screen.parseRequested.connect(self.parse_text)
        self.preview_screen.exportRequested.connect(lambda: self.navigate("export"))
        self.export_screen.exportRequested.connect(self.export_current)
        self.loadrunner_screen.reportRequested.connect(lambda msg: self.toast.show_message(msg, "info"))
        self.settings_screen.settingsChanged.connect(self.save_settings)
        self.history_screen.clearRequested.connect(self.clear_history)
        
        self.playwright_service.signals.install_progress.connect(self.loading.show_message)
        self.playwright_service.signals.install_finished.connect(self._handle_playwright_install_finished)

    def _handle_playwright_install_finished(self, success: bool, message: str) -> None:
        self.loading.hide()
        if success:
            self.toast.show_message("Playwright setup complete!", "success")
        else:
            self.toast.show_message(message, "error")

    def _install_shortcuts(self) -> None:
        shortcuts = [
            ("Ctrl+N", lambda: self.navigate("input")),
            ("Ctrl+R", lambda: self.parse_text(self.input_screen.text())),
            ("Ctrl+E", lambda: self.navigate("export")),
            ("Ctrl+,", lambda: self.navigate("settings")),
        ]
        for sequence, callback in shortcuts:
            action = QAction(self)
            action.setShortcut(QKeySequence(sequence))
            action.triggered.connect(callback)
            self.addAction(action)

    def navigate(self, route: str) -> None:
        widget = self.screens[route]
        self.stack.setCurrentWidget(widget)
        self.sidebar.set_active(route)
        if route == "history":
            self.refresh_history()
        elif route == "export":
            self.export_screen.set_summary(self.current_dataframe)
        elif route == "playwright":
            if not self.playwright_service.check_is_installed():
                self.loading.show_message("Setting up Playwright for the first time...")
                self.playwright_service.install_dependencies()

    def parse_text(self, text: str) -> None:
        if self.config.settings.autosave_session:
            self.session.save_text(text)
        self.toast.show_message("Detecting table...", "info")
        self.loading.show_message("Detecting and cleaning table...")
        worker = Worker(self.parser.parse, text)
        worker.signals.finished.connect(self._handle_parse_result)
        worker.signals.failed.connect(self._handle_worker_error)
        self.thread_pool.start(worker)

    def _handle_parse_result(self, result: ParseResult) -> None:
        self.loading.hide()
        self.current_dataframe = result.dataframe
        self.preview_screen.set_dataframe(result.dataframe, result.source_format, result.warnings)
        self.export_screen.set_summary(result.dataframe)
        self.navigate("preview")
        self.toast.show_message("Table detected and cleaned.", "success")

    def export_current(self, filename: str, file_type: str) -> None:
        if self.current_dataframe is None or self.current_dataframe.empty:
            self.toast.show_message("Detect a table before exporting.", "error")
            return
        clean_name = "".join(char for char in filename.strip() if char not in '<>:"/\\|?*')
        clean_name = clean_name or DEFAULT_EXPORT_BASENAME
        if not clean_name.endswith(f".{file_type}"):
            clean_name = f"{clean_name}.{file_type}"
        output_dir = FileManager.default_output_dir(self.config.settings.output_directory)
        output_path = output_dir / clean_name
        if output_path.exists():
            stem = output_path.stem
            suffix = output_path.suffix
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_path.with_name(f"{stem}_{timestamp}{suffix}")
        self.toast.show_message("Exporting file...", "info")
        self.export_in_progress = True
        self.export_screen.reset_export_status()
        self.export_screen.set_export_running(True)
        self.loading.show_message("Creating export file... 0%")
        worker = Worker(self.exporter.export, self.current_dataframe, output_path, file_type)
        worker.kwargs["progress_callback"] = worker.signals.progress.emit
        worker.signals.progress.connect(self._handle_export_progress)
        worker.signals.debug.connect(self.export_screen.append_debug)
        worker.signals.finished.connect(lambda path: self._handle_exported(Path(path), file_type, worker))
        worker.signals.failed.connect(lambda message: self._handle_worker_error(message, worker))
        self.active_workers.append(worker)
        self.thread_pool.start(worker)

    def _handle_export_progress(self, percent: int, message: str) -> None:
        self.export_screen.set_export_progress(percent, message)
        if percent >= 100:
            self.export_in_progress = False
            self.export_screen.set_export_running(False)
            self.loading.hide()
            QTimer.singleShot(0, self.loading.hide)
            return
        if self.export_in_progress:
            self.loading.show_message(f"{message} {percent}%")

    def _handle_exported(self, path: Path, file_type: str, worker: Worker | None = None) -> None:
        self.export_in_progress = False
        self.loading.hide()
        self.export_screen.set_export_running(False)
        dataframe = self.current_dataframe
        assert dataframe is not None
        self.history.add_record(path.name, path, file_type, len(dataframe), len(dataframe.columns))
        self.refresh_history()
        self.export_screen.append_debug(f"Exported file: {path}")
        self.toast.show_message(f"Exported {path.name}", "success")
        if self.config.settings.open_after_export:
            try:
                FileManager.open_in_file_manager(path)
            except Exception as exc:  # noqa: BLE001 - file manager integration should not block export success.
                self.export_screen.append_debug(f"Could not open file manager: {exc}")
        self._release_worker(worker)

    def save_settings(self, values: dict) -> None:
        self.config.update(**values)
        self.playwright_service.set_playwright_path(self.config.settings.playwright_path)
        self.theme.apply(self.config.settings.theme)
        self.toast.show_message("Settings saved.", "success")

    def refresh_history(self) -> None:
        self.history_screen.set_records(self.history.list_records())

    def clear_history(self) -> None:
        self.history.clear()
        self.refresh_history()
        self.toast.show_message("History cleared.", "success")

    def _handle_worker_error(self, message: str, worker: Worker | None = None) -> None:
        self.export_in_progress = False
        self.loading.hide()
        self.export_screen.set_export_running(False)
        self.toast.show_message(message, "error")
        self._release_worker(worker)

    def _release_worker(self, worker: Worker | None) -> None:
        if worker in self.active_workers:
            self.active_workers.remove(worker)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.config.settings.autosave_session:
            self.session.save_text(self.input_screen.text())
        self.widgets_screen.stop_server()
        super().closeEvent(event)

    def _toggle_maximized(self) -> None:
        self.showNormal() if self.isMaximized() else self.showMaximized()
