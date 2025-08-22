from app.ingest.models import QSOModel
from datetime import datetime, timezone

def test_stable_key():
    q = QSOModel(
        id=1,
        callsign='K1ABC',
        qso_datetime=datetime(2024,1,1,12,0, tzinfo=timezone.utc),
        band='20m',
        mode='SSB',
        rst_sent='59',
        rst_recv='59',
        email_to='a@example.com'
    )
    assert q.stable_key().startswith('K1ABC|2024-01-01T12:00:00+00:00|20m|SSB')
