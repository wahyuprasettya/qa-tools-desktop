from __future__ import annotations

import subprocess
import socket
import tempfile
import os
import signal
from pathlib import Path
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QSplitter, QFileDialog, QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QFont


# Inline Node.js server script
NODE_SERVER_SCRIPT = """
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

const FOLDER = process.argv[2];
const PORT = process.argv[3];

const MIME_TYPES = {
    '.html': 'text/html',
    '.css':  'text/css',
    '.js':   'application/javascript',
    '.json': 'application/json',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif':  'image/gif',
    '.svg':  'image/svg+xml',
    '.ico':  'image/x-icon',
    '.woff': 'font/woff',
    '.woff2':'font/woff2',
    '.ttf':  'font/ttf',
};

const server = http.createServer((req, res) => {
    const parsed = url.parse(req.url);
    let filePath = path.join(FOLDER, decodeURIComponent(parsed.pathname));

    // Default to index.html for directory requests
    if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
        filePath = path.join(filePath, 'index.html');
    }

    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(404, { 'Content-Type': 'text/plain' });
            res.end('404 Not Found: ' + req.url);
            return;
        }
        const ext = path.extname(filePath).toLowerCase();
        const mimeType = MIME_TYPES[ext] || 'application/octet-stream';
        res.writeHead(200, { 'Content-Type': mimeType });
        res.end(data);
    });
});

server.listen(PORT, '127.0.0.1', () => {
    process.stdout.write('READY:' + PORT + '\\n');
});

process.on('SIGTERM', () => server.close(() => process.exit(0)));
process.on('SIGINT',  () => server.close(() => process.exit(0)));
"""


def _find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class WidgetsPreviewScreen(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.current_folder: Path | None = None
        self._server_process: subprocess.Popen | None = None
        self._server_port: int | None = None
        self._server_script_path: str | None = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title_layout = QVBoxLayout()
        title = QLabel("Widgets Preview")
        title.setObjectName("PageTitle")
        self.status_label = QLabel("Select a folder to start the preview server.")
        self.status_label.setObjectName("Muted")
        title_layout.addWidget(title)
        title_layout.addWidget(self.status_label)
        header.addLayout(title_layout)

        header.addStretch()

        self.browse_btn = QPushButton("Import Folder")
        self.browse_btn.setObjectName("PrimaryButton")
        self.browse_btn.clicked.connect(self.browse_folder)
        header.addWidget(self.browse_btn)

        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_server)
        header.addWidget(self.stop_btn)

        layout.addLayout(header)

        # Main Splitter: file list | browser preview
        self.main_splitter = QSplitter(Qt.Horizontal)

        # Left: HTML file list
        self.file_list = QListWidget()
        self.file_list.setObjectName("FileList")
        self.file_list.setFixedWidth(220)
        self.file_list.itemClicked.connect(self.load_file)
        self.main_splitter.addWidget(self.file_list)

        # Right: Web browser preview
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("about:blank"))
        self.main_splitter.addWidget(self.browser)

        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)

        layout.addWidget(self.main_splitter, stretch=1)

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Widgets Folder")
        if not folder:
            return
        self.stop_server()
        self.current_folder = Path(folder)
        self.status_label.setText(f"Starting server for: {folder}")
        self._start_server()

    def _start_server(self):
        if not self.current_folder:
            return

        # Write server script to a temp file
        tmp = tempfile.NamedTemporaryFile(
            suffix=".js", mode="w", delete=False, encoding="utf-8"
        )
        tmp.write(NODE_SERVER_SCRIPT)
        tmp.flush()
        tmp.close()
        self._server_script_path = tmp.name

        port = _find_free_port()
        self._server_port = port

        try:
            self._server_process = subprocess.Popen(
                ["node", self._server_script_path, str(self.current_folder), str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,  # process group for clean kill
            )
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Node.js not found. Please install Node.js.")
            return

        # Poll until server is READY
        self._poll_server_ready()

    def _poll_server_ready(self, attempts: int = 0):
        if self._server_process is None:
            return

        line = self._server_process.stdout.readline()
        if line.startswith("READY:"):
            self.status_label.setText(
                f"Server running on port {self._server_port} → {self.current_folder.name}"
            )
            self.browse_btn.setText("Change Folder")
            self.stop_btn.setEnabled(True)
            self._refresh_file_list()
        elif attempts < 30:
            QTimer.singleShot(100, lambda: self._poll_server_ready(attempts + 1))
        else:
            self.status_label.setText("Server failed to start.")
            QMessageBox.critical(self, "Error", "Node.js server did not start in time.")

    def stop_server(self):
        if self._server_process:
            try:
                os.killpg(os.getpgid(self._server_process.pid), signal.SIGTERM)
            except Exception:
                self._server_process.terminate()
            self._server_process = None

        if self._server_script_path and os.path.exists(self._server_script_path):
            os.unlink(self._server_script_path)
            self._server_script_path = None

        self._server_port = None
        self.browser.setUrl(QUrl("about:blank"))
        self.file_list.clear()
        self.stop_btn.setEnabled(False)
        self.browse_btn.setText("Import Folder")
        self.status_label.setText("Server stopped.")

    # ------------------------------------------------------------------
    # File list & navigation
    # ------------------------------------------------------------------

    def _refresh_file_list(self):
        self.file_list.clear()
        if not self.current_folder:
            return
        html_files = sorted(self.current_folder.glob("*.html"))
        for f in html_files:
            self.file_list.addItem(f.name)

        # Auto-load index.html if present
        if (self.current_folder / "index.html").exists():
            items = self.file_list.findItems("index.html", Qt.MatchExactly)
            if items:
                self.file_list.setCurrentItem(items[0])
                self.load_file(items[0])

    def load_file(self, item):
        if not self._server_port:
            return
        url = f"http://127.0.0.1:{self._server_port}/{item.text()}"
        self.browser.setUrl(QUrl(url))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self.stop_server()
        super().closeEvent(event)

    def hideEvent(self, event):
        # Keep server alive when switching tabs — no stop here
        super().hideEvent(event)
