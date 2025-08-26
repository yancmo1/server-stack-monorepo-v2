from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime
import os

API_TOKEN = os.environ.get('CONNECTOR_TOKEN', 'please-change-me')

def _resolve_db_path() -> str:
    """Resolve the SQLite DB path with sensible fallbacks.

    Precedence:
    1) SOURCE_DB_PATH if it points to an existing file.
       - If it points to a directory, search common filenames inside it.
    2) Look for common filenames in common directories: /data, current dir.
    3) Fallback to the literal value of SOURCE_DB_PATH even if missing (so API reports intent).
    """
    env_val = os.environ.get('SOURCE_DB_PATH', '').strip()
    common_names = [
        'Log4OM.db',
        'Log4OM db.SQLite',
        'Log4OM.db3',
    ]

    def first_existing(candidates: list[str]) -> Optional[str]:
        for p in candidates:
            try:
                if p and os.path.isfile(p):
                    return p
            except Exception:
                pass
        return None

    # Explicit file path provided
    if env_val and os.path.isfile(env_val):
        return env_val

    # If env points to a directory, search inside it
    if env_val and os.path.isdir(env_val):
        hits = first_existing([os.path.join(env_val, n) for n in common_names])
        if hits:
            return hits

    # Common locations
    search_dirs = ['/data', os.getcwd()]
    hits = first_existing([os.path.join(d, n) for d in search_dirs for n in common_names])
    if hits:
        return hits

    # Last resort: return env_val (even if missing) or default filename
    return env_val or 'Log4OM db.SQLite'

DB_PATH = _resolve_db_path()

app = FastAPI(title='QSL Connector')


class QSO(BaseModel):
    id: int
    callsign: str
    # ISO8601 string; client parses to datetime
    qso_datetime: str
    band: Optional[str] = None
    mode: Optional[str] = None
    rst_sent: Optional[str] = None
    rst_recv: Optional[str] = None
    operator_name: Optional[str] = None
    qth: Optional[str] = None
    grid: Optional[str] = None
    notes: Optional[str] = None
    email_to: Optional[str] = None


class QSOItems(BaseModel):
    items: List[QSO]


class UpdateStatus(BaseModel):
    qsl_sent_flag: bool
    qsl_sent_at: Optional[str] = None
    email_message_id: Optional[str] = None
    postcard_ref: Optional[str] = None


async def auth(authorization: str = Header(default='')):
    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Unauthorized')
    token = authorization.split(' ', 1)[1]
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail='Forbidden')
    return True


@app.get('/')
async def root():
    """Simple health endpoint."""
    exists = os.path.exists(DB_PATH)
    return {"status": "ok", "db_path": DB_PATH, "db_exists": exists}


@app.get('/qsos', response_model=QSOItems)
async def get_qsos(limit: int = 50, since: Optional[str] = None, _=Depends(auth)):
    """Return latest QSOs; if DB or table missing, return empty set."""
    # Return empty set gracefully if DB doesn't exist
    if not os.path.exists(DB_PATH):
        return {"items": []}
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # Attempt query; if table missing, return empty
        base_query = (
            "SELECT Id as id, COALESCE(callsign, '') as callsign, COALESCE(qsodate, '') as qso_datetime, "
            "COALESCE(band, '') as band, COALESCE(mode, '') as mode, COALESCE(rstsent, '') as rst_sent, COALESCE(rstrcvd, '') as rst_recv, "
            "COALESCE(name, '') as operator_name, COALESCE(qth, '') as qth, COALESCE(grid, '') as grid, COALESCE(notes, '') as notes, COALESCE(email, '') as email_to FROM Log"
        )
        params: list = []
        if since:
            base_query += " WHERE qsodate >= ?"
            params.append(since)
        base_query += " ORDER BY qsodate DESC LIMIT ?"
        params.append(int(limit))
        rows = cur.execute(base_query, params).fetchall()
        items = [QSO(**dict(r)) for r in rows]
        return {"items": items}
    except sqlite3.Error:
        return {"items": []}
    finally:
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass


@app.post('/qsos/{qso_id}/status')
async def post_status(qso_id: int, body: UpdateStatus, _=Depends(auth)):
    # Write to a sidecar table `qsl_status` so we don't modify the source schema
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail='DB not found')
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS qsl_status (qso_id INTEGER PRIMARY KEY, qsl_sent_flag INTEGER, qsl_sent_at TEXT, email_message_id TEXT, postcard_ref TEXT)"
    )
    # Upsert pattern using ON CONFLICT in SQLite
    cur.execute(
        "INSERT INTO qsl_status(qso_id, qsl_sent_flag, qsl_sent_at, email_message_id, postcard_ref) VALUES(?,?,?,?,?) "
        "ON CONFLICT(qso_id) DO UPDATE SET qsl_sent_flag=excluded.qsl_sent_flag, qsl_sent_at=excluded.qsl_sent_at, email_message_id=excluded.email_message_id, postcard_ref=excluded.postcard_ref",
        (
            qso_id,
            1 if body.qsl_sent_flag else 0,
            body.qsl_sent_at or datetime.utcnow().isoformat(),
            body.email_message_id,
            body.postcard_ref,
        ),
    )
    conn.commit()
    conn.close()
    return {"ok": True}
