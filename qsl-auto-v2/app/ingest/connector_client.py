from __future__ import annotations
import httpx
import asyncio
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
            # Basic retry to allow connector to come up
            backoffs = [0.5, 1.0, 2.0]
            last_exc: Exception | None = None
            for delay in [0.0] + backoffs:
                if delay:
                    await asyncio.sleep(delay)
                async with httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=10) as client:
                    try:
                        r = await client.get("/qsos", params=params)
                        r.raise_for_status()
                        data = r.json()
                        for item in data.get("items", []):
                            yield QSOModel(**item)
                        return
                    except Exception as e:
                        last_exc = e
                        continue
            # After retries, yield nothing to avoid crashing the pipeline in dev/dry-run
            return

    async def update_status(self, qso_id: int, payload: dict) -> None:
        backoffs = [0.5, 1.0, 2.0]
        async with httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=30) as client:
            for delay in backoffs:
                try:
                    r = await client.post(f"/qsos/{qso_id}/status", json=payload)
                    r.raise_for_status()
                    return
                except (httpx.ConnectError, httpx.ReadTimeout):
                    await asyncio.sleep(delay)
            r = await client.post(f"/qsos/{qso_id}/status", json=payload)
            r.raise_for_status()
