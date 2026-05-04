"""Send support-ticket confirmation emails via SMTP (optional — requires env configuration)."""

from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional

from app.config import (
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_SSL,
    SMTP_USE_TLS,
    SMTP_USER,
)


def smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_FROM)


def send_ticket_confirmation(
    *,
    to_addr: str,
    ticket_id: str,
    category_label: str,
    summary: str,
    created_at: str,
    description: str,
    where_hint: Optional[str] = None,
    location_graph_id: Optional[str] = None,
) -> None:
    """
    Send a plain-text confirmation to the address the user entered when raising a ticket.

    Raises on SMTP / TLS / auth errors so callers can surface a generic failure.
    """
    if not smtp_configured():
        raise RuntimeError("SMTP is not configured")

    subject = f"AirHelp Terminal 2 — ticket {ticket_id}"

    body_lines = [
        "Thank you for reporting an issue through AirHelp (Terminal 2).",
        "",
        f"Ticket reference: {ticket_id}",
        f"Created (UTC): {created_at}",
        f"Issue type: {category_label}",
        "",
        "What you told us:",
        description.strip(),
        "",
    ]
    if where_hint:
        body_lines.extend(["Where you were (your note):", where_hint.strip(), ""])
    if location_graph_id:
        body_lines.extend(["Map location id attached to the ticket:", location_graph_id.strip(), ""])
    body_lines.extend(
        [
            "Short summary:",
            summary.strip(),
            "",
            "Keep this email or the ticket number if you follow up with support.",
            "",
            "— AirHelp (automated message, do not reply unless your mail host supports it)",
        ]
    )
    body = "\n".join(body_lines)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_addr
    msg.set_content(body)

    if SMTP_USE_SSL or SMTP_PORT == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as smtp:
            if SMTP_USER and SMTP_PASSWORD:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
            smtp.send_message(msg)
        return

    context = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as smtp:
        smtp.ehlo()
        if SMTP_USE_TLS:
            smtp.starttls(context=context)
            smtp.ehlo()
        if SMTP_USER and SMTP_PASSWORD:
            smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def try_send_ticket_confirmation(
    *,
    to_addr: Optional[str],
    ticket_id: str,
    category_label: str,
    summary: str,
    created_at: str,
    description: str,
    where_hint: Optional[str] = None,
    location_graph_id: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """
    If ``to_addr`` is set, attempt to send confirmation email.

    Returns ``(email_sent, email_notice)`` where ``email_notice`` is a short user-facing line
    (success explanation, missing SMTP, or send failure — ticket is still stored on disk).
    """
    if not to_addr:
        return False, None

    if not smtp_configured():
        return (
            False,
            "Email delivery is not set up on this server yet — your ticket is still saved. "
            "Copy the ticket number below.",
        )

    try:
        send_ticket_confirmation(
            to_addr=to_addr,
            ticket_id=ticket_id,
            category_label=category_label,
            summary=summary,
            created_at=created_at,
            description=description,
            where_hint=where_hint,
            location_graph_id=location_graph_id,
        )
        return True, f"A confirmation with your ticket details was sent to {to_addr}."
    except Exception:
        return (
            False,
            "We could not send the confirmation email (mail server error). "
            "Your ticket is still saved — please copy the ticket number below.",
        )
