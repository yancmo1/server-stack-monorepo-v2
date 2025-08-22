from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
from datetime import datetime
import os

DB_PATH = os.environ.get('SOURCE_DB_PATH', 'Log4OM db.SQLite')
API_TOKEN = os.environ.get('CONNECTOR_TOKEN', 'please-change-me')

app = FastAPI(title='QSL Connector')

class QSO(BaseModel):
    id: int
    callsign: str
    qso_datetime: datetime
    band: str
    mode: str
    rst_sent: str
    rst_recv: str
    operator_name: Optional[str] = None
    qth: Optional[str] = None
    grid: Optional[str] = None
    notes: Optional[str] = None
    email_to: Optional[str] = None

class QSOItems(BaseModel):
    items: List[QSO]

class UpdateStatus(BaseModel):
    qsl_sent_flag: bool
    qsl_sent_at: str
    email_message_id: Optional[str] = None
    postcard_ref: Optional[str] = None

async def auth(authorization: str = Header(default='')):
    if not authorization.startswith('Bearer '):
        raise HTTPException(401, 'Unauthorized')
    token = authorization[7:]
    if token != API_TOKEN:
        raise HTTPException(401, 'Unauthorized')

@app.get('/qsos', response_model=QSOItems)
async def get_qsos(limit: int = 50, since: Optional[str] = None, _=Depends(auth)):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    query = "SELECT Id as id, callsign, qsodate as qso_datetime, band, mode, rstsent as rst_sent, rstrcvd as rst_recv, name as operator_name, qth, grid, notes, email as email_to FROM Log ORDER BY qsodate DESC LIMIT ?"
    params = [limit]
    rows = cur.execute(query, params).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        items.append(QSO(**d))
    return {"items": items}

@app.post('/qsos/{qso_id}/status')
async def post_status(qso_id: int, body: UpdateStatus, _=Depends(auth)):
    # For safety: write to a sidecar table instead of touching core Log table
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS qsl_status (qso_id INTEGER PRIMARY KEY, qsl_sent_flag INTEGER, qsl_sent_at TEXT, email_message_id TEXT, postcard_ref TEXT)")
    cur.execute("INSERT INTO qsl_status(qso_id, qsl_sent_flag, qsl_sent_at, email_message_id, postcard_ref) VALUES(?,?,?,?,?) ON CONFLICT(qso_id) DO UPDATE SET qsl_sent_flag=excluded.qsl_sent_flag, qsl_sent_at=excluded.qsl_sent_at, email_message_id=excluded.email_message_id, postcard_ref=excluded.postcard_ref", (qso_id, 1 if body.qsl_sent_flag else 0, body.qsl_sent_at, body.email_message_id, body.postcard_ref))
    conn.commit()
    return {"ok": True}
