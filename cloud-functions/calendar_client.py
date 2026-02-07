"""
Google Calendar API client for event retrieval.

Uses domain-wide delegation to access @kartel.ai calendars.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

from google.oauth2 import service_account
from googleapiclient.discovery import build


# Service account credentials (stored as JSON string in env var)
GOOGLE_CREDENTIALS = os.environ.get("GOOGLE_CREDENTIALS", "{}")

# Kartel team calendars to search
KARTEL_CALENDARS = [
    "ben@kartel.ai",
    "kevin@kartel.ai",
    "emmet@kartel.ai",
    "luke@kartel.ai",
]

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def _get_calendar_service(user_email: str):
    """
    Get Calendar API service for a specific user via domain-wide delegation.
    """
    creds_info = json.loads(GOOGLE_CREDENTIALS)

    credentials = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )

    # Delegate to the specific user
    delegated_credentials = credentials.with_subject(user_email)

    service = build("calendar", "v3", credentials=delegated_credentials)
    return service


def get_calendar_events(
    attendee_emails: List[str],
    days_ahead: int = 7,
    include_today: bool = True,
) -> List[Dict[str, Any]]:
    """
    Get calendar events that include specific attendees.

    Args:
        attendee_emails: List of attendee emails to filter by
        days_ahead: Number of days ahead to look
        include_today: Whether to include today's events

    Returns:
        List of event objects with title, start, end, attendees
    """
    if not attendee_emails:
        return []

    # Set time range
    now = datetime.now()
    if include_today:
        time_min = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        time_min = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    time_max = (now + timedelta(days=days_ahead)).replace(
        hour=23, minute=59, second=59, microsecond=0
    )

    # Convert attendee_emails to lowercase for comparison
    target_emails = {email.lower() for email in attendee_emails}

    all_events = []
    seen_event_ids = set()

    # Search each Kartel calendar
    for calendar_user in KARTEL_CALENDARS:
        try:
            service = _get_calendar_service(calendar_user)

            # Get events from this calendar
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min.isoformat() + "Z",
                    timeMax=time_max.isoformat() + "Z",
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=100,
                )
                .execute()
            )

            events = events_result.get("items", [])

            for event in events:
                event_id = event.get("id")

                # Skip duplicates
                if event_id in seen_event_ids:
                    continue

                # Check if any target attendee is in this event
                attendees = event.get("attendees", [])
                attendee_list = [a.get("email", "").lower() for a in attendees]

                # Also check organizer
                organizer = event.get("organizer", {}).get("email", "").lower()
                if organizer:
                    attendee_list.append(organizer)

                # Check for overlap with target emails
                if not target_emails.intersection(attendee_list):
                    continue

                seen_event_ids.add(event_id)

                # Parse start/end times
                start = event.get("start", {})
                end = event.get("end", {})

                start_time = start.get("dateTime") or start.get("date")
                end_time = end.get("dateTime") or end.get("date")

                all_events.append(
                    {
                        "id": event_id,
                        "title": event.get("summary", "(no title)"),
                        "start": start_time,
                        "end": end_time,
                        "attendees": [
                            {
                                "email": a.get("email"),
                                "name": a.get("displayName"),
                                "response": a.get("responseStatus"),
                            }
                            for a in attendees
                        ],
                        "location": event.get("location"),
                        "description": event.get("description", "")[:500],  # Truncate
                        "calendar_owner": calendar_user,
                    }
                )

        except Exception as e:
            print(f"Error accessing calendar for {calendar_user}: {e}")
            continue

    # Sort by start time
    all_events.sort(key=lambda x: x.get("start") or "")

    return all_events
