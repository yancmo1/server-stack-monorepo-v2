import smtplib
from email.mime.text import MIMEText
import os

def send_crash_email(subject, body):
    # These should be set in your environment or .env file
    GMAIL_USER = os.getenv('GMAIL_USER')
    GMAIL_PASS = os.getenv('GMAIL_PASS')
    TO_EMAIL = os.getenv('ADMIN_EMAIL')
    if not (GMAIL_USER and GMAIL_PASS and TO_EMAIL):
        return False
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = GMAIL_USER
    msg['To'] = TO_EMAIL
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, [TO_EMAIL], msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send crash notification: {e}")
        return False
