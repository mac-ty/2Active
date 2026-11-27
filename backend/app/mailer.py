"""
Email services.

Provides utilities for sending transactional emails through
the Brevo API, including email verification messages and
other application-generated communications.
"""


import html

import httpx

from app.config import settings

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


class EmailSendError(Exception):
    pass


def send_email(to_email: str, to_name: str, subject: str, html_content: str) -> None:
    payload = {
        "sender": {
            "name": settings.brevo_sender_name,
            "email": settings.brevo_sender_email,
        },
        "to": [{"email": to_email, "name": to_name}],
        "subject": subject,
        "htmlContent": html_content,
    }
    headers = {
        "api-key": settings.brevo_api_key,
        "accept": "application/json",
        "content-type": "application/json",
    }
    try:
        response = httpx.post(BREVO_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise EmailSendError("Could not send email") from exc


def send_verification_code(to_email: str, name: str, code: str) -> None:
    safe_name = html.escape(name)
    body = (
        f"<p>Hi {safe_name},</p>"
        f"<p>Your 2Active verification code is:</p>"
        f"<h2 style='letter-spacing:4px'>{code}</h2>"
        f"<p>It expires in 5 minutes. If you didn't sign up, ignore this email.</p>"
    )
    send_email(to_email, name, "Your 2Active verification code", body)