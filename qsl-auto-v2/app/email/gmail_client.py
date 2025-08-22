from __future__ import annotations
from dataclasses import dataclass
from time import monotonic, sleep
from collections import deque
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64
import pickle
from pathlib import Path
from ..config import settings

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except Exception:
    GMAIL_AVAILABLE = False

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

@dataclass
class EmailResult:
    success: bool
    message_id: str | None
    thread_id: str | None
    error: str | None = None

class TokenBucket:
    def __init__(self, rate_per_min: int):
        self.capacity = max(1, rate_per_min)
        self.tokens = self.capacity
        self.refill_interval = 60.0 / self.capacity
        self.last = monotonic()

    def take(self):
        now = monotonic()
        elapsed = now - self.last
        refill = int(elapsed / self.refill_interval)
        if refill > 0:
            self.tokens = min(self.capacity, self.tokens + refill)
            self.last = now
        if self.tokens == 0:
            sleep(self.refill_interval)
            return self.take()
        self.tokens -= 1

class GmailClient:
    def __init__(self):
        self.bucket = TokenBucket(settings.email_rate_limit_per_min)
        self.creds: Credentials | None = None
        self.service = None

    def _ensure_auth(self):
        if settings.dry_run:
            return
        if not GMAIL_AVAILABLE:
            raise RuntimeError("Gmail libraries not installed")
        token_path = Path(settings.google_token_path)
        cred_path = Path(settings.google_client_secret_path)
        creds = None
        if token_path.exists():
            with open(token_path, 'rb') as f:
                creds = pickle.load(f)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
                creds = flow.run_local_server(port=0)
            token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(token_path, 'wb') as f:
                pickle.dump(creds, f)
        self.creds = creds
        self.service = build('gmail', 'v1', credentials=creds)

    def send_email(self, to_email: str, subject: str, body: str, attachment_path: Path | None) -> EmailResult:
        if settings.dry_run:
            return EmailResult(success=True, message_id=None, thread_id=None, error=None)
        self._ensure_auth()
        self.bucket.take()
        message = MIMEMultipart()
        message['to'] = to_email
        message['subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        if attachment_path and Path(attachment_path).exists():
            part = MIMEBase('application', 'octet-stream')
            with open(attachment_path, 'rb') as f:
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{Path(attachment_path).name}"')
            message.attach(part)
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        try:
            res = self.service.users().messages().send(userId='me', body={'raw': raw}).execute()
            return EmailResult(True, res.get('id'), res.get('threadId'))
        except HttpError as e:
            return EmailResult(False, None, None, error=str(e))
