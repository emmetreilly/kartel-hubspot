"""
Gmail API client for email search.

Uses domain-wide delegation to access @kartel.ai inboxes.
Requires a service account with Gmail API access and domain-wide delegation enabled.
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build


# Service account credentials (stored as JSON string in env var)
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS", "{}")

# Kartel team inboxes to search
KARTEL_INBOXES = [
    "sales@kartel.ai",
    "ben@kartel.ai",
    "kevin@kartel.ai",
    "emmet@kartel.ai",
    "luke@kartel.ai",
]

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _get_gmail_service(user_email: str):
    """
    Get Gmail API service for a specific user via domain-wide delegation.
    """
    creds_info = json.loads(GOOGLE_CREDENTIALS)

    credentials = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )

    # Delegate to the specific user
    delegated_credentials = credentials.with_subject(user_email)

    service = build("gmail", "v1", credentials=delegated_credentials)
    return service


def search_gmail(
    email_addresses: List[str],
    since_hours: int = 24,
    max_results: int = 50,
) -> List[Dict[str, Any]]:
    """
    Search Gmail for emails from/to specific email addresses.

    Args:
        email_addresses: List of contact emails to search for
        since_hours: Only get emails from the last N hours
        max_results: Maximum number of emails to return

    Returns:
        List of email objects with sender, recipient, subject, date, snippet
    """
    if not email_addresses:
        return []

    # Build Gmail search query
    # Format: (from:email1 OR from:email2 OR to:email1 OR to:email2)
    from_queries = [f"from:{email}" for email in email_addresses]
    to_queries = [f"to:{email}" for email in email_addresses]
    email_query = f"({' OR '.join(from_queries + to_queries)})"

    # Add date filter
    since_date = datetime.now() - timedelta(hours=since_hours)
    date_query = f"after:{since_date.strftime('%Y/%m/%d')}"

    full_query = f"{email_query} {date_query}"

    all_emails = []
    seen_message_ids = set()

    # Search each Kartel inbox
    for inbox in KARTEL_INBOXES:
        try:
            service = _get_gmail_service(inbox)

            # Search for messages
            results = (
                service.users()
                .messages()
                .list(userId="me", q=full_query, maxResults=max_results)
                .execute()
            )

            messages = results.get("messages", [])

            for msg in messages:
                msg_id = msg["id"]

                # Skip duplicates (same email might appear in multiple inboxes)
                if msg_id in seen_message_ids:
                    continue
                seen_message_ids.add(msg_id)

                # Get full message details
                message = (
                    service.users()
                    .messages()
                    .get(userId="me", id=msg_id, format="metadata")
                    .execute()
                )

                headers = {
                    h["name"].lower(): h["value"]
                    for h in message.get("payload", {}).get("headers", [])
                }

                # Parse date
                internal_date = message.get("internalDate")
                if internal_date:
                    email_date = datetime.fromtimestamp(int(internal_date) / 1000)
                else:
                    email_date = None

                all_emails.append(
                    {
                        "id": msg_id,
                        "from": headers.get("from", "Unknown"),
                        "to": headers.get("to", "Unknown"),
                        "subject": headers.get("subject", "(no subject)"),
                        "date": email_date.isoformat() if email_date else None,
                        "snippet": message.get("snippet", ""),
                        "searched_inbox": inbox,
                    }
                )

        except Exception as e:
            print(f"Error searching inbox {inbox}: {e}")
            continue

    # Sort by date (newest first) and limit results
    all_emails.sort(key=lambda x: x.get("date") or "", reverse=True)
    return all_emails[:max_results]
