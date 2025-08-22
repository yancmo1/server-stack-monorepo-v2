from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class QSOModel(BaseModel):
    id: int
    callsign: str
    qso_datetime: datetime
    band: str
    mode: str
    rst_sent: str
    rst_recv: str
    operator_name: str | None = None
    qth: str | None = None
    grid: str | None = None
    notes: str | None = None
    email_to: EmailStr | None = Field(default=None)

    def stable_key(self) -> str:
        return f"{self.callsign}|{self.qso_datetime.isoformat()}|{self.band}|{self.mode}"
