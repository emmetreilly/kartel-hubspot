"""
Email client using SendGrid for sending reports.
"""

import os
from typing import List, Dict, Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
FROM_EMAIL = "reports@kartel.ai"  # Must be verified in SendGrid


def send_email(
    to: List[str],
    subject: str,
    body: str,
) -> Dict[str, Any]:
    """
    Send an email via SendGrid.

    Args:
        to: List of recipient email addresses
        subject: Email subject line
        body: Email body (plain text)

    Returns:
        Dict with success status and message ID
    """
    if not SENDGRID_API_KEY:
        raise Exception("SENDGRID_API_KEY not configured")

    # Create message
    message = Mail(
        from_email=Email(FROM_EMAIL, "Kartel CRM"),
        to_emails=[To(email) for email in to],
        subject=subject,
    )

    # Add plain text content
    message.add_content(Content("text/plain", body))

    # Also add HTML version (converting plain text to basic HTML)
    html_body = body.replace("\n", "<br>")
    html_body = f"<pre style='font-family: monospace; white-space: pre-wrap;'>{html_body}</pre>"
    message.add_content(Content("text/html", html_body))

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        return {
            "success": True,
            "status_code": response.status_code,
            "recipients": to,
        }

    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")
