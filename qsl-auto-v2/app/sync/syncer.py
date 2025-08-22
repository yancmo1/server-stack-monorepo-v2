from __future__ import annotations
from ..config import settings
from ..ingest.connector_client import ConnectorClient
from datetime import datetime

class Syncer:
    def __init__(self, client: ConnectorClient | None = None):
        self.client = client or ConnectorClient()

    async def mark_sent(self, qso_id: int, email_message_id: str | None, postcard_path: str) -> None:
        payload = {
            "qsl_sent_flag": True,
            "qsl_sent_at": datetime.utcnow().isoformat(),
            "email_message_id": email_message_id,
            "postcard_ref": postcard_path,
        }
        await self.client.update_status(qso_id, payload)
