from __future__ import annotations
import asyncio
import typer
from typing import Optional
from datetime import datetime
import time
from .config import settings
from .render.renderer import PDFRenderer, QSO
from .ingest.models import QSOModel
from .ingest.connector_client import ConnectorClient
from .email.gmail_client import GmailClient
from .sync.syncer import Syncer
from .storage.state import StateStore

app = typer.Typer(add_completion=False)


@app.command()
def scan(limit: int = typer.Option(10), since: Optional[str] = None):
    """Fetch QSOs via connector and print summary."""
    async def _run():
        client = ConnectorClient()
        count = 0
        async for qso in client.fetch_qsos(since=since, limit=limit):
            typer.echo(f"{qso.id} {qso.callsign} {qso.qso_datetime} {qso.band} {qso.mode} -> {qso.email_to}")
            count += 1
        typer.echo(f"Total: {count}")

    asyncio.run(_run())


@app.command()
def render(limit: int = 5, size: str = '4x6'):
    """Render PDFs for latest QSOs without sending."""
    async def _run():
        client = ConnectorClient()
        renderer = PDFRenderer()
        store = StateStore()
        processed = 0
        async for item in client.fetch_qsos(limit=limit):
            key = item.stable_key()
            existing = store.get_by_key(key)
            if existing and existing.get('sent_at'):
                continue
            qso = QSO(**item.model_dump())
            pdf = renderer.render(qso=qso, size=size)
            typer.echo(f"Rendered {pdf}")
            processed += 1
        typer.echo(f"Rendered: {processed}")

    asyncio.run(_run())


@app.command()
def send(limit: int = 5, size: str = '4x6', max_retries: int = 3):
    """Send emails (respects DRY_RUN)."""
    async def _run():
        client = ConnectorClient()
        renderer = PDFRenderer()
        mailer = GmailClient()
        syncer = Syncer(client)
        store = StateStore()
        metrics = {"fetched": 0, "rendered": 0, "sent": 0, "prepared": 0, "skipped": 0, "errors": 0}
        async for item in client.fetch_qsos(limit=limit):
            metrics["fetched"] += 1
            key = item.stable_key()
            existing = store.get_by_key(key)
            if existing and existing.get('sent_at'):
                metrics["skipped"] += 1
                continue
            qso = QSO(**item.model_dump())
            pdf = renderer.render(qso=qso, size=size)
            metrics["rendered"] += 1
            # In dry-run, do not send, do not mark state, do not sync
            if settings.dry_run:
                metrics["prepared"] += 1
                continue
            attempt = 0
            while attempt < max_retries:
                attempt += 1
                result = mailer.send_email(item.email_to or settings.from_email, f"QSL Confirmation - {item.callsign}", "See attached postcard.", pdf)
                if result.success:
                    sent_at = datetime.utcnow().isoformat()
                    store.mark_sent(item.id, key, str(pdf), result.message_id, sent_at)
                    await syncer.mark_sent(item.id, result.message_id, str(pdf))
                    metrics["sent"] += 1
                    break
                else:
                    store.upsert_attempt(item.id, key, error=result.error)
                    metrics["errors"] += 1
                    # Backoff
                    time.sleep(min(2 ** attempt, 30))
        typer.echo(
            f"Run report: fetched={metrics['fetched']} rendered={metrics['rendered']} "
            f"prepared={metrics['prepared']} sent={metrics['sent']} skipped={metrics['skipped']} "
            f"errors={metrics['errors']} dry_run={settings.dry_run}"
        )

    asyncio.run(_run())


@app.command()
def run(limit: int = 10, size: str = '4x6'):
    """Full pipeline: fetch → dedupe → render → email → sync → report."""
    send(limit=limit, size=size)


if __name__ == '__main__':
    app()
