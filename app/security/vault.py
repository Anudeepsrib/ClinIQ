import os
import sqlite3
from contextlib import contextmanager

from app.core.config import settings


class Vault:
    def __init__(self, db_path: str = None):
        db_path = db_path or settings.VAULT_DB_PATH
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS token_map (
                    token TEXT PRIMARY KEY,
                    original_value TEXT NOT NULL
                )
            """)

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def store(self, token: str, original_value: str):
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO token_map (token, original_value) VALUES (?, ?)",
                (token, original_value)
            )

    def get(self, token: str) -> str | None:
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT original_value FROM token_map WHERE token = ?",
                (token,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

vault = Vault()
