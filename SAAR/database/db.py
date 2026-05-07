# database/db.py

import sqlite3
import threading
from pathlib import Path
from .models import TABLES

# =========================
# 🔒 FIXED ABSOLUTE DB PATH
# =========================
import os
import sys

def get_base_dir():
    # We want the folder where the .exe or the script is located
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
DB_PATH = BASE_DIR / "saar.db"

# Create a dummy if missing to avoid crashes
if not DB_PATH.exists():
    with open(DB_PATH, "w") as f:
        pass


_db_lock = threading.Lock()


class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Create a database connection with safe settings"""
        if self.connection is None:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row
            self._apply_pragmas()
            self._create_tables()

    def _apply_pragmas(self):
        cursor = self.connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()

    def _create_tables(self):
        cursor = self.connection.cursor()
        for table_sql in TABLES:
            cursor.execute(table_sql)
        self.connection.commit()
        cursor.close()

    def execute(self, query: str, params: tuple = ()):
        with _db_lock:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            last_id = cursor.lastrowid
            cursor.close()
            return last_id

    def fetchone(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        cursor.close()
        return row

    def fetchall(self, query: str, params: tuple = ()):
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None


# Global DB instance
db = Database()
db.connect()
