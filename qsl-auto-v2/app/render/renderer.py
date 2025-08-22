from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
try:
    from weasyprint import HTML  # type: ignore
    _WEASY = True
except Exception:
    _WEASY = False
from ..config import settings


@dataclass
class QSO:
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
    email_to: str | None = None


class PDFRenderer:
    def __init__(self):
        templates_dir = Path(__file__).resolve().parent.parent / 'templates' / 'postcard'
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(['html'])
        )

    def render(self, qso: QSO, size: str = '4x6', out_path: Path | None = None) -> Path:
        template_name = '4x6.html' if size == '4x6' else '5x7.html'
        tmpl = self.env.get_template(template_name)
        html = tmpl.render(qso=qso, settings=settings, generated_at=datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC'))
        out_path = out_path or (Path(settings.output_dir) / f"{qso.qso_datetime:%Y}/{qso.qso_datetime:%m}/{qso.callsign}/QSL_{qso.callsign}_{qso.qso_datetime:%Y%m%d_%H%M%S}_{size}.pdf")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if _WEASY:
            HTML(string=html).write_pdf(str(out_path))
        else:
            # Fallback: write HTML next to expected PDF to aid local testing without system deps
            html_path = out_path.with_suffix('.html')
            html_path.write_text(html, encoding='utf-8')
            # Touch a placeholder PDF file
            out_path.write_bytes(b"%PDF-1.4\n% placeholder generated without weasyprint\n")
        return out_path
