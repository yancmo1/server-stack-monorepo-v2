import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from dotenv import load_dotenv
import sys
from datetime import datetime, timezone


# Load environment variables from shared .env
load_dotenv(os.path.expanduser('~/config/.env'))

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')
RECIPIENT = GMAIL_USER  # send to self for test

# Read backup log
if len(sys.argv) > 1:
    log_path = Path(sys.argv[1])
else:
    log_path = Path.home() / 'backup_meganz.log'
if log_path.exists():
    with open(log_path, 'r') as f:
        log_content = f.read()
else:
    log_content = 'Log file not found.'

# Compose mobile-friendly plain text email
backup_file = None
for line in log_content.splitlines():
    if 'home-backup-' in line and '.tar.gz' in line:
        backup_file = line.split()[-1]
        break
if not backup_file:
    backup_file = 'Unknown (see log)'

now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
subject = 'Home Backup Completed'
body = f"""
Backup completed successfully.

Backup file: {backup_file}
Location: MEGA /UBUNTU-MAC

Summary:
- Date: {now}
- Source: /home
- Status: Success

For details, see the attached log below.

--- Backup Log ---
{log_content}
-------------------

This is an automated message. No reply needed.
"""

msg = MIMEText(body, 'plain')
msg['From'] = GMAIL_USER
msg['To'] = RECIPIENT
msg['Subject'] = subject

try:
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, RECIPIENT, msg.as_string())
    print('Test email sent successfully.')
except Exception as e:
    print(f'Failed to send email: {e}')
