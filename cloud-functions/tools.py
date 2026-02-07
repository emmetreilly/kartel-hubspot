"""
Tool definitions and executor for Claude API.

These tools are what Claude uses to gather data intelligently.
"""

from hubspot_client import (
    get_active_deals,
    get_deal_contacts,
    get_hubspot_tasks,
    update_deal_field,
    create_hubspot_note,
)
from gmail_client import search_gmail
from calendar_client import get_calendar_events
from email_client import send_email


# Tool definitions for Claude API
TOOLS = [
    {
        "name": "get_active_deals",
        "description": "Get all active deals from HubSpot that are not closed won or closed lost. Returns deal name, amount, stage, owner, and next_steps for each deal.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_deal_contacts",
        "description": "Get all contacts associated with a specific HubSpot deal. Returns contact name, email, company, and job title.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {
                    "type": "string",
                    "description": "The HubSpot deal ID",
                }
            },
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_hubspot_tasks",
        "description": "Get tasks from HubSpot including tasks due today, overdue tasks, and upcoming tasks (next 7 days). Returns task subject, due date, owner, and associated deal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_completed": {
                    "type": "boolean",
                    "description": "Whether to include completed tasks (default false)",
                    "default": False,
                }
            },
            "required": [],
        },
    },
    {
        "name": "search_gmail",
        "description": "Search Gmail for emails from/to specific email addresses. Only searches for emails involving the specified contacts. Returns sender, recipient, subject, date, and snippet for each email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_addresses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of email addresses to search for (from or to)",
                },
                "since_hours": {
                    "type": "integer",
                    "description": "Only get emails from the last N hours (default 24)",
                    "default": 24,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of emails to return (default 50)",
                    "default": 50,
                },
            },
            "required": ["email_addresses"],
        },
    },
    {
        "name": "get_calendar_events",
        "description": "Get Google Calendar events that include specific attendees. Only returns events with the specified contacts. Returns event title, start time, end time, and attendees.",
        "input_schema": {
            "type": "object",
            "properties": {
                "attendee_emails": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses to filter by",
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "Number of days ahead to look (default 7)",
                    "default": 7,
                },
                "include_today": {
                    "type": "boolean",
                    "description": "Whether to include today's events (default true)",
                    "default": True,
                },
            },
            "required": ["attendee_emails"],
        },
    },
    {
        "name": "update_deal_field",
        "description": "Update a field on a HubSpot deal. Use this to set next_steps or other deal properties based on email intelligence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {
                    "type": "string",
                    "description": "The HubSpot deal ID",
                },
                "field_name": {
                    "type": "string",
                    "description": "The property name to update (e.g., 'next_steps')",
                },
                "value": {
                    "type": "string",
                    "description": "The new value for the field",
                },
            },
            "required": ["deal_id", "field_name", "value"],
        },
    },
    {
        "name": "create_hubspot_note",
        "description": "Create a note on a HubSpot deal to log activity or email summaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {
                    "type": "string",
                    "description": "The HubSpot deal ID to attach the note to",
                },
                "note_body": {
                    "type": "string",
                    "description": "The content of the note",
                },
            },
            "required": ["deal_id", "note_body"],
        },
    },
    {
        "name": "send_email",
        "description": "Send an email via SendGrid. Use this to send the daily sales report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of recipient email addresses",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                },
                "body": {
                    "type": "string",
                    "description": "Email body (plain text or HTML)",
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict):
    """
    Execute a tool by name with the given input.
    Routes to the appropriate client function.
    """
    if tool_name == "get_active_deals":
        return get_active_deals()

    elif tool_name == "get_deal_contacts":
        return get_deal_contacts(tool_input["deal_id"])

    elif tool_name == "get_hubspot_tasks":
        include_completed = tool_input.get("include_completed", False)
        return get_hubspot_tasks(include_completed=include_completed)

    elif tool_name == "search_gmail":
        return search_gmail(
            email_addresses=tool_input["email_addresses"],
            since_hours=tool_input.get("since_hours", 24),
            max_results=tool_input.get("max_results", 50),
        )

    elif tool_name == "get_calendar_events":
        return get_calendar_events(
            attendee_emails=tool_input["attendee_emails"],
            days_ahead=tool_input.get("days_ahead", 7),
            include_today=tool_input.get("include_today", True),
        )

    elif tool_name == "update_deal_field":
        return update_deal_field(
            deal_id=tool_input["deal_id"],
            field_name=tool_input["field_name"],
            value=tool_input["value"],
        )

    elif tool_name == "create_hubspot_note":
        return create_hubspot_note(
            deal_id=tool_input["deal_id"],
            note_body=tool_input["note_body"],
        )

    elif tool_name == "send_email":
        return send_email(
            to=tool_input["to"],
            subject=tool_input["subject"],
            body=tool_input["body"],
        )

    else:
        raise ValueError(f"Unknown tool: {tool_name}")
