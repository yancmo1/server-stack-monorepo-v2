from __future__ import annotations
import httpx
from typing import AsyncGenerator
from .models import QSOModel
from ..config import settings

class ConnectorClient:
    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = base_url or settings.connector_base_url
        self.token = token or settings.connector_token
        self._headers = {"Authorization": f"Bearer {self.token}"}

    async def fetch_qsos(self, since: str | None = None, limit: int = 100) -> AsyncGenerator[QSOModel, None]:
        params: dict[str, str | int] = {"limit": limit}
        if since:
            params["since"] = since
        async with httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=30) as client:
            r = await client.get("/qsos", params=params)
            r.raise_for_status()
            data = r.json()
            for item in data.get("items", []):
                yield QSOModel(**item)

    async def update_status(self, qso_id: int, payload: dict) -> None:
        async with httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=30) as client:
            r = await client.post(f"/qsos/{qso_id}/status", json=payload)
            r.raise_for_status()
