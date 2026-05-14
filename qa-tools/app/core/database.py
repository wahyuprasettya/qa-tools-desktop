import sqlite3
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional
from app.core.paths import DB_PATH

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.db_path = DB_PATH
        self._init_db()
        self._initialized = True

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize tables if they don't exist."""
        queries = [
            """
            CREATE TABLE IF NOT EXISTS export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                rows INTEGER,
                columns INTEGER,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS lr_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scenario_path TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_sec REAL,
                total_transactions INTEGER,
                passed_transactions INTEGER,
                failed_transactions INTEGER
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sessions (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        ]
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
            logger.info("Database initialized successfully.")
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")

    def execute(self, query: str, params: tuple = ()) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute(query, params)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database execute error: {e}")

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Database fetch_all error: {e}")
            return []

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Database fetch_one error: {e}")
            return None
