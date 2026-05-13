from __future__ import annotations

import subprocess
import os
import signal
from pathlib import Path
from typing import Optional
from PySide6.QtCore import QObject, Signal, QProcess

class PlaywrightSignals(QObject):
    log = Signal(str)
    finished = Signal(bool, str)
    script_generated = Signal(str)
    install_progress = Signal(str)
    install_finished = Signal(bool, str)

class PlaywrightService(QObject):
    def __init__(self):
        super().__init__()
        self.signals = PlaywrightSignals()
        self.recorder_process: Optional[subprocess.Popen] = None
        self.test_process: Optional[QProcess] = None
        self.playwright_path = "npx playwright" # Default

    def set_playwright_path(self, path: str):
        self.playwright_path = path

    def check_is_installed(self) -> bool:
        """Check if node_modules/@playwright/test exists."""
        return Path("node_modules/@playwright/test").exists()

    def install_dependencies(self):
        """Runs npm init, npm install, and playwright install sequentially using QProcess."""
        if self.test_process and self.test_process.state() != QProcess.NotRunning:
            self.signals.install_finished.emit(False, "A process is already running.")
            return

        self.signals.install_progress.emit("Initializing Node project (npm init -y)...")
        
        # We will chain processes. First npm init
        self.test_process = QProcess()
        self.test_process.finished.connect(self._on_npm_init_finished)
        self.test_process.start("npm", ["init", "-y"])

    def _on_npm_init_finished(self, exit_code, exit_status):
        if exit_code != 0:
            self.signals.install_finished.emit(False, "Failed to initialize Node project.")
            return
        
        self.signals.install_progress.emit("Installing @playwright/test (this may take a minute)...")
        self.test_process = QProcess()
        self.test_process.finished.connect(self._on_npm_install_finished)
        self.test_process.start("npm", ["install", "-D", "@playwright/test"])

    def _on_npm_install_finished(self, exit_code, exit_status):
        if exit_code != 0:
            self.signals.install_finished.emit(False, "Failed to install @playwright/test.")
            return
        
        self.signals.install_progress.emit("Downloading Playwright browsers (this may take several minutes)...")
        self.test_process = QProcess()
        self.test_process.finished.connect(self._on_playwright_install_finished)
        
        parts = self.playwright_path.split()
        cmd = parts[0]
        args = parts[1:] + ["install"]
        self.test_process.start(cmd, args)

    def _on_playwright_install_finished(self, exit_code, exit_status):
        if exit_code == 0:
            self.signals.install_finished.emit(True, "Installation complete.")
        else:
            self.signals.install_finished.emit(False, "Failed to download Playwright browsers.")

    def start_recording(self, url: str = "https://google.com"):
        """Starts Playwright codegen."""
        try:
            # We use subprocess.Popen for codegen because it opens its own window
            # and we might want to capture the output when it's closed.
            # Using -o to a temp file to capture the script.
            temp_script = Path("temp_recording.spec.ts")
            cmd = f"{self.playwright_path} codegen {url} -o {temp_script}"
            
            self.signals.log.emit(f"Starting recorder: {cmd}")
            
            # Use shell=True for cross-platform npx handling if needed, 
            # but better to split if possible.
            self.recorder_process = subprocess.Popen(
                cmd, 
                shell=True, 
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
        except Exception as e:
            self.signals.log.emit(f"Error starting recorder: {str(e)}")
            self.signals.finished.emit(False, str(e))

    def stop_recording(self):
        """Stops the recording process."""
        if self.recorder_process:
            if os.name == 'nt':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.recorder_process.pid)])
            else:
                os.killpg(os.getpgid(self.recorder_process.pid), signal.SIGTERM)
            
            self.recorder_process = None
            self.signals.log.emit("Recording stopped.")
            
            # Read the generated script if it exists
            temp_script = Path("temp_recording.spec.ts")
            if temp_script.exists():
                script_content = temp_script.read_text(encoding="utf-8")
                self.signals.script_generated.emit(script_content)
                # We don't delete it yet, maybe keep it as a backup? 
                # Actually, better to clean up.
                # temp_script.unlink()

    def run_test(self, script_path: str):
        """Runs playwright test using QProcess for real-time output."""
        if self.test_process and self.test_process.state() != QProcess.NotRunning:
            self.signals.log.emit("A test is already running.")
            return

        self.test_process = QProcess()
        self.test_process.readyReadStandardOutput.connect(self._handle_stdout)
        self.test_process.readyReadStandardError.connect(self._handle_stderr)
        self.test_process.finished.connect(self._handle_finished)

        # Split playwright_path into command and initial args
        parts = self.playwright_path.split()
        cmd = parts[0]
        args = parts[1:] + ["test", script_path]
        
        self.signals.log.emit(f"Running test: {cmd} {' '.join(args)}")
        self.test_process.start(cmd, args)

    def _handle_stdout(self):
        data = self.test_process.readAllStandardOutput().data().decode()
        self.signals.log.emit(data.strip())

    def _handle_stderr(self):
        data = self.test_process.readAllStandardError().data().decode()
        self.signals.log.emit(f"[ERROR] {data.strip()}")

    def _handle_finished(self, exit_code, exit_status):
        success = exit_code == 0
        msg = "Test completed successfully." if success else f"Test failed with exit code {exit_code}."
        self.signals.finished.emit(success, msg)
        self.test_process = None
