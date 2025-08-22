from app.render.renderer import PDFRenderer, QSO
from datetime import datetime, timezone
from pathlib import Path

def test_render_tmp(tmp_path: Path):
    r = PDFRenderer()
    qso = QSO(
        id=1,
        callsign='K1ABC',
        qso_datetime=datetime(2024,1,1,12,0, tzinfo=timezone.utc),
        band='20m', mode='SSB', rst_sent='59', rst_recv='59', qth='Austin, TX', grid='EM10')
    out = r.render(qso, size='4x6', out_path=tmp_path / 'card.pdf')
    assert out.exists()
    assert out.suffix == '.pdf'
