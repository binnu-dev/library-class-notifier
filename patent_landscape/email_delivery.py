"""Email delivery of the weekly brief over SMTP (v1 channel)."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .brief import Brief, render_text
from .config import Settings


class EmailDeliveryError(RuntimeError):
    pass


def build_message(brief: Brief, settings: Settings) -> EmailMessage:
    if not settings.email_from:
        raise EmailDeliveryError("EMAIL_FROM / SMTP_USER is not set.")
    if not settings.email_to:
        raise EmailDeliveryError("PATENT_EMAIL_TO is not set.")

    msg = EmailMessage()
    msg["Subject"] = brief.subject
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(settings.email_to)
    msg.set_content(render_text(brief))
    return msg


def send_brief(brief: Brief, settings: Settings) -> None:
    """Send the brief. Raises EmailDeliveryError on misconfiguration."""
    if not settings.smtp_host:
        raise EmailDeliveryError("SMTP_HOST is not set.")

    msg = build_message(brief, settings)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        try:
            server.starttls()
            server.ehlo()
        except smtplib.SMTPException:
            pass  # server without STARTTLS (e.g. local test relay)
        if settings.smtp_user and settings.smtp_password:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(msg)
