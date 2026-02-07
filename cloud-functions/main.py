"""
Kartel CRM Automation - Google Cloud Functions

Two functions:
1. daily_report - Generates and emails daily sales report at 6am PT
2. gmail_sync - Syncs relevant Gmail emails to HubSpot every 15 min

Both use Claude API with tools for intelligent data gathering.
"""

import functions_framework
import json
import os
from datetime import datetime

import anthropic

from tools import TOOLS, execute_tool


def get_secrets():
    """Get secrets from environment (set via Secret Manager)."""
    return {
        "HUBSPOT_ACCESS_TOKEN": os.environ.get("HUBSPOT_ACCESS_TOKEN"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "SENDGRID_API_KEY": os.environ.get("SENDGRID_API_KEY"),
        "GOOGLE_CREDENTIALS": os.environ.get("GOOGLE_CREDENTIALS"),
    }


def run_claude_agent(prompt: str, max_iterations: int = 20) -> str:
    """
    Run Claude with tools in an agentic loop.
    Claude will use tools to gather data, then generate output.
    """
    client = anthropic.Anthropic()

    messages = [{"role": "user", "content": prompt}]

    iteration = 0
    final_response = ""

    while iteration < max_iterations:
        iteration += 1

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8192,
            tools=TOOLS,
            messages=messages,
        )

        # Check if Claude wants to use tools
        if response.stop_reason == "tool_use":
            tool_results = []

            for block in response.content:
                if block.type == "tool_use":
                    print(f"[Agent] Using tool: {block.name}")
                    try:
                        result = execute_tool(block.name, block.input)
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                            }
                        )
                    except Exception as e:
                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": f"Error: {str(e)}",
                                "is_error": True,
                            }
                        )

            # Add assistant response and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Claude is done - extract final text response
            for block in response.content:
                if hasattr(block, "text"):
                    final_response = block.text
            break

    return final_response


@functions_framework.http
def daily_report(request):
    """
    Generate and email daily sales report.

    Triggered by Cloud Scheduler at 6am PT daily.
    """
    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""Generate today's daily sales report for Kartel AI.

Today's date: {today}

## Instructions

Follow these steps IN ORDER:

### Step 1: Get HubSpot Data
1. Call get_active_deals() to get all active deals (not closed won/lost)
2. Call get_hubspot_tasks() to get tasks (due today, overdue, upcoming 7 days)

### Step 2: Get Contact Emails for Each Deal
For each active deal, call get_deal_contacts(deal_id) to get associated contact emails.
Build a list of all unique contact email addresses.

### Step 3: Search Gmail (Smart Filtering)
Call search_gmail() with ONLY the contact emails from Step 2.
This ensures we only look at relevant emails, not the entire inbox.
Look at emails from the last 24 hours.

### Step 4: Check Calendar (Smart Filtering)
Call get_calendar_events() with ONLY the contact emails from Step 2.
Get events for today and the next 7 days.

### Step 5: Generate the Report
Create a report with these sections:

```
Subject: Daily Sales Report - {today}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIPELINE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Pipeline: $X,XXX,XXX
Enterprise: $X,XXX,XXX (X deals)
SMB: $XXX,XXX (X deals)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TODAY'S PRIORITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Tasks due today - checkbox format]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERDUE ITEMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Tasks past due with warning emoji]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEALS BY OWNER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Group deals by owner (Ben Kusin, Emmet Reilly, Kevin Reilly, Luke Peterson)
For each deal show: Name, Amount, Stage, Next Step (from emails or HubSpot)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEETINGS TODAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Calendar events for today with times and attendees]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECENT ACTIVITY (Last 24h)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Summary of important emails - who responded, key updates]
```

### Step 6: Send the Report
Call send_email() with:
- to: ["emmet@kartel.ai"]
- subject: "Daily Sales Report - {today}"
- body: The formatted report

Be concise but comprehensive. Focus on actionable items."""

    try:
        result = run_claude_agent(prompt)
        return {"status": "success", "message": "Daily report sent"}, 200
    except Exception as e:
        print(f"Error generating daily report: {e}")
        return {"status": "error", "message": str(e)}, 500


@functions_framework.http
def gmail_sync(request):
    """
    Sync Gmail emails to HubSpot deal records.

    Triggered by Cloud Scheduler every 15 minutes during business hours.
    """
    prompt = """Sync recent Gmail activity to HubSpot deals.

## Instructions

### Step 1: Get Active Deals
Call get_active_deals() to get all deals not in closed won/lost stages.

### Step 2: Get Contacts for Each Deal
For each deal, call get_deal_contacts(deal_id) to get associated contact emails.

### Step 3: Search Gmail for These Contacts
Call search_gmail() with the contact emails from Step 2.
Look for emails from the last 4 hours (since last sync).

### Step 4: Extract Updates from Emails
For each email found, determine:
- Which deal it relates to (based on sender/recipient matching contacts)
- Any next steps mentioned
- Any meeting requests or confirmations
- Any key decisions or updates

### Step 5: Update HubSpot
For each deal with relevant email activity:
- Call update_deal_field() to set next_steps if a clear next step was found
- Call create_hubspot_note() to log a summary of the email activity

Be selective - only update if there's meaningful new information.
Don't create noise with trivial updates."""

    try:
        result = run_claude_agent(prompt)
        return {"status": "success", "message": "Gmail sync complete"}, 200
    except Exception as e:
        print(f"Error syncing Gmail: {e}")
        return {"status": "error", "message": str(e)}, 500


@functions_framework.http
def create_reengagement_deal(request):
    """
    Create a re-engagement deal for a lost deal.

    Called by HubSpot workflow as a webhook when:
    - Deal moves to Closed Lost
    - loss_reason is budget_timing or competitor
    - After the appropriate delay (90 days or 6 months)

    Expects JSON body:
    {
        "dealId": "123456",
        "loss_reason": "budget_timing"  // or "competitor"
    }
    """
    from hubspot_client import HubSpotClient

    try:
        # Parse request
        request_json = request.get_json(silent=True) or {}
        deal_id = request_json.get("dealId") or request_json.get("object", {}).get("objectId")
        loss_reason = request_json.get("loss_reason") or request_json.get("properties", {}).get("loss_reason")

        if not deal_id:
            return {"status": "error", "message": "dealId is required"}, 400

        hs = HubSpotClient()

        # Get the original deal
        original_deal = hs.get_deal(deal_id)
        if not original_deal:
            return {"status": "error", "message": f"Deal {deal_id} not found"}, 404

        deal_name = original_deal.get("properties", {}).get("dealname", "Unknown")
        owner_id = original_deal.get("properties", {}).get("hubspot_owner_id")

        # Get associated company
        companies = hs.get_deal_associations(deal_id, "companies")
        if not companies:
            return {"status": "error", "message": "No company associated with deal"}, 400

        company_id = companies[0]["id"]
        company = hs.get_company(company_id)
        company_name = company.get("properties", {}).get("name", "Unknown Company")

        # Create re-engagement deal
        reason_text = {
            "budget_timing": "lost 90 days ago due to budget/timing",
            "competitor": "lost to competitor 6 months ago"
        }.get(loss_reason, "ready for re-engagement")

        new_deal = hs.create_deal({
            "dealname": f"Re-engage: {company_name}",
            "pipeline": "1880222400",  # Re-engagement Pipeline
            "dealstage": "2978916037",  # Opportunity Identified
            "hubspot_owner_id": owner_id,
            "description": f"Re-engagement from lost deal: {deal_name}\nReason: {loss_reason}"
        })

        new_deal_id = new_deal.get("id")

        # Associate with company (not contacts)
        hs.create_association(new_deal_id, "deals", company_id, "companies")

        # Create task for owner
        hs.create_task({
            "hs_task_subject": f"Re-engage {company_name} - {reason_text}",
            "hs_task_body": f"Original deal: {deal_name}\nLoss reason: {loss_reason}",
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "MEDIUM",
            "hubspot_owner_id": owner_id,
        }, new_deal_id)

        return {
            "status": "success",
            "reengagement_deal_id": new_deal_id,
            "company_name": company_name
        }, 200

    except Exception as e:
        print(f"Error creating re-engagement deal: {e}")
        return {"status": "error", "message": str(e)}, 500


@functions_framework.http
def create_followup_task(request):
    """
    Create a lightweight follow-up task for no-response deals.

    Called by HubSpot workflow as a webhook when:
    - Deal moves to Closed Lost
    - loss_reason is no_response
    - After 30 day delay

    Expects JSON body:
    {
        "dealId": "123456"
    }
    """
    from hubspot_client import HubSpotClient

    try:
        request_json = request.get_json(silent=True) or {}
        deal_id = request_json.get("dealId") or request_json.get("object", {}).get("objectId")

        if not deal_id:
            return {"status": "error", "message": "dealId is required"}, 400

        hs = HubSpotClient()

        # Get the original deal
        original_deal = hs.get_deal(deal_id)
        if not original_deal:
            return {"status": "error", "message": f"Deal {deal_id} not found"}, 404

        deal_name = original_deal.get("properties", {}).get("dealname", "Unknown")
        owner_id = original_deal.get("properties", {}).get("hubspot_owner_id")

        # Get associated company name
        companies = hs.get_deal_associations(deal_id, "companies")
        company_name = "Unknown Company"
        if companies:
            company = hs.get_company(companies[0]["id"])
            company_name = company.get("properties", {}).get("name", "Unknown Company")

        # Create follow-up task
        hs.create_task({
            "hs_task_subject": f"Final follow-up: {company_name} - no response, one more try",
            "hs_task_body": f"Original deal: {deal_name}\n\nThis contact went dark. One final attempt before moving on.",
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "LOW",
            "hubspot_owner_id": owner_id,
        }, deal_id)

        return {
            "status": "success",
            "company_name": company_name
        }, 200

    except Exception as e:
        print(f"Error creating follow-up task: {e}")
        return {"status": "error", "message": str(e)}, 500


# For local testing
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing daily_report...")
    response = daily_report(None)
    print(response)
