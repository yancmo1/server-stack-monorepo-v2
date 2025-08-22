from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Optional
from ..config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS deliveries (
  qso_id INTEGER PRIMARY KEY,
  stable_key TEXT NOT NULL,
  postcard_pdf_path TEXT,
  email_message_id TEXT,
  sent_at TEXT,
  attempts INTEGER DEFAULT 0,
  last_error TEXT
);
CREATE INDEX IF NOT EXISTS idx_deliveries_stable_key ON deliveries(stable_key);
"""

class StateStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or settings.state_db)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init(self):
        with self._connect() as c:
            c.executescript(SCHEMA)

    def get_by_key(self, stable_key: str) -> Optional[dict]:
        with self._connect() as c:
            cur = c.execute("SELECT qso_id, stable_key, postcard_pdf_path, email_message_id, sent_at, attempts, last_error FROM deliveries WHERE stable_key=?", (stable_key,))
            row = cur.fetchone()
            if not row:
                return None
            return {
                'qso_id': row[0],
                'stable_key': row[1],
                'postcard_pdf_path': row[2],
                'email_message_id': row[3],
                'sent_at': row[4],
                'attempts': row[5],
                'last_error': row[6],
            }

    def upsert_attempt(self, qso_id: int, stable_key: str, error: str | None = None):
        with self._connect() as c:
            cur = c.execute("SELECT attempts FROM deliveries WHERE stable_key=?", (stable_key,))
            row = cur.fetchone()
            if row:
                attempts = (row[0] or 0) + 1
                c.execute("UPDATE deliveries SET attempts=?, last_error=? WHERE stable_key=?", (attempts, error, stable_key))
            else:
                c.execute("INSERT INTO deliveries(qso_id, stable_key, attempts, last_error) VALUES (?, ?, ?, ?)", (qso_id, stable_key, 1, error))

    def mark_sent(self, qso_id: int, stable_key: str, postcard_pdf_path: str, email_message_id: str | None, sent_at_iso: str):
        with self._connect() as c:
            cur = c.execute("SELECT 1 FROM deliveries WHERE stable_key=?", (stable_key,))
            if cur.fetchone():
                c.execute("UPDATE deliveries SET postcard_pdf_path=?, email_message_id=?, sent_at=?, last_error=NULL WHERE stable_key=?", (postcard_pdf_path, email_message_id, sent_at_iso, stable_key))
            else:
                c.execute("INSERT INTO deliveries(qso_id, stable_key, postcard_pdf_path, email_message_id, sent_at, attempts) VALUES (?, ?, ?, ?, ?, 1)", (qso_id, stable_key, postcard_pdf_path, email_message_id, sent_at_iso))
