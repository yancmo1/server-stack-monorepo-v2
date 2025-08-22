import asyncio
from pathlib import Path
from datetime import datetime, timezone
import types

def test_pipeline_dry_run(tmp_path, monkeypatch):
    # Import late to allow monkeypatch of settings
    from app import config as cfg
    cfg.settings.output_dir = tmp_path

    from app.ingest.models import QSOModel
    from app.cli import send
    from app.ingest import connector_client as cc

    async def fake_fetch_qsos(self, since=None, limit=1):
        yield QSOModel(
            id=123,
            callsign='K1ABC',
            qso_datetime=datetime(2024,1,1,12,0, tzinfo=timezone.utc),
            band='20m', mode='SSB', rst_sent='59', rst_recv='59', email_to='test@example.com'
        )

    monkeypatch.setattr(cc.ConnectorClient, 'fetch_qsos', fake_fetch_qsos, raising=True)

    # Run pipeline (dry-run default)
    send(limit=1, size='4x6')

    # Check that a PDF placeholder exists
    pdfs = list(tmp_path.rglob('*.pdf'))
    assert len(pdfs) >= 1
