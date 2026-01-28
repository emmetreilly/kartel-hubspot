#!/usr/bin/env python3
"""
Daily CRM Sync Script
Runs daily to keep HubSpot alive and automated.

Usage: python3 daily-crm-sync.py [--dry-run]

Features:
1. Enrich new contacts (Apollo)
2. Detect stalled deals (7+ days same stage) → create tasks
3. Create renewal reminder tasks (90/15/7 days before contract end)
4. Update days_in_procurement for deals in procurement stage
5. Create delivery deals when sales deals close won
6. Create re-engagement deals when deals close lost or churn
7. Spec handoff notification when spec_required = yes
8. Send email alerts for critical items
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# API Keys
HUBSPOT_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")

# HubSpot API
BASE_URL = "https://api.hubapi.com"
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

# Pipeline IDs
ENTERPRISE_PIPELINE = "1880222397"
SMB_PIPELINE = "1880222398"
CLIENT_DELIVERY_PIPELINE = "1880222399"
REENGAGEMENT_PIPELINE = "1880222400"

# Stage IDs (need to map these)
STAGES = {
    "enterprise_closedwon": None,
    "enterprise_closedlost": None,
    "smb_closedwon": None,
    "smb_closedlost": None,
    "delivery_churned": None,
    "delivery_phase1": None,
    "reengagement_identified": None,
    "enterprise_procurement": None,
}

# Owner IDs
OWNER_BEN = "159215803"
OWNER_EMMET = "160266467"
OWNER_WAYAN = None  # Need to get this

# Thresholds
STALLED_DAYS = 7
RENEWAL_ALERTS = [90, 15, 7]  # Days before contract_end_date

DRY_RUN = "--dry-run" in sys.argv


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def get_stage_ids():
    """Fetch stage IDs for all pipelines."""
    global STAGES

    response = requests.get(f"{BASE_URL}/crm/v3/pipelines/deals", headers=HEADERS)
    if response.status_code != 200:
        log(f"Error fetching pipelines: {response.text}")
        return

    for pipeline in response.json().get("results", []):
        pid = pipeline["id"]
        for stage in pipeline.get("stages", []):
            label = stage["label"].lower()
            sid = stage["id"]

            if pid == ENTERPRISE_PIPELINE:
                if "closed won" in label:
                    STAGES["enterprise_closedwon"] = sid
                elif "closed lost" in label:
                    STAGES["enterprise_closedlost"] = sid
                elif "procurement" in label:
                    STAGES["enterprise_procurement"] = sid
            elif pid == SMB_PIPELINE:
                if "closed won" in label:
                    STAGES["smb_closedwon"] = sid
                elif "closed lost" in label:
                    STAGES["smb_closedlost"] = sid
            elif pid == CLIENT_DELIVERY_PIPELINE:
                if "churned" in label:
                    STAGES["delivery_churned"] = sid
                elif "phase i" in label or "scoping" in label:
                    STAGES["delivery_phase1"] = sid
            elif pid == REENGAGEMENT_PIPELINE:
                if "identified" in label:
                    STAGES["reengagement_identified"] = sid

    log(f"Loaded stage IDs: {sum(1 for v in STAGES.values() if v)} mapped")


def search_deals(filters, properties):
    """Search deals with given filters."""
    payload = {
        "filterGroups": [{"filters": filters}],
        "properties": properties,
        "limit": 100
    }
    response = requests.post(f"{BASE_URL}/crm/v3/objects/deals/search", headers=HEADERS, json=payload)
    if response.status_code != 200:
        log(f"Error searching deals: {response.text}")
        return []
    return response.json().get("results", [])


def create_task(title, description, owner_id, deal_id=None, due_days=1):
    """Create a task in HubSpot."""
    due_date = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

    payload = {
        "properties": {
            "hs_task_subject": title,
            "hs_task_body": description,
            "hubspot_owner_id": owner_id,
            "hs_task_status": "NOT_STARTED",
            "hs_task_priority": "HIGH",
            "hs_timestamp": datetime.now().isoformat()
        }
    }

    if DRY_RUN:
        log(f"  [DRY RUN] Would create task: {title}")
        return True

    response = requests.post(f"{BASE_URL}/crm/v3/objects/tasks", headers=HEADERS, json=payload)
    if response.status_code != 201:
        log(f"  Error creating task: {response.text[:200]}")
        return False

    task_id = response.json().get("id")

    # Associate with deal if provided
    if deal_id and task_id:
        assoc_url = f"{BASE_URL}/crm/v4/objects/tasks/{task_id}/associations/deals/{deal_id}"
        requests.put(f"{assoc_url}/task_to_deal", headers=HEADERS)

    return True


def create_deal(name, amount, pipeline_id, stage_id, owner_id, source_deal_id=None):
    """Create a new deal."""
    payload = {
        "properties": {
            "dealname": name,
            "amount": str(amount) if amount else "0",
            "pipeline": pipeline_id,
            "dealstage": stage_id,
            "hubspot_owner_id": owner_id
        }
    }

    if DRY_RUN:
        log(f"  [DRY RUN] Would create deal: {name} in pipeline {pipeline_id}")
        return None

    response = requests.post(f"{BASE_URL}/crm/v3/objects/deals", headers=HEADERS, json=payload)
    if response.status_code != 201:
        log(f"  Error creating deal: {response.text[:200]}")
        return None

    return response.json().get("id")


def update_deal(deal_id, properties):
    """Update deal properties."""
    if DRY_RUN:
        log(f"  [DRY RUN] Would update deal {deal_id}: {properties}")
        return True

    response = requests.patch(
        f"{BASE_URL}/crm/v3/objects/deals/{deal_id}",
        headers=HEADERS,
        json={"properties": properties}
    )
    return response.status_code == 200


def send_email_alert(to_email, subject, body):
    """Send email alert (placeholder - implement with your email service)."""
    log(f"  [EMAIL] To: {to_email} | Subject: {subject}")
    # TODO: Implement with SendGrid, SES, or SMTP
    pass


# ============================================
# AUTOMATION FUNCTIONS
# ============================================

def detect_stalled_deals():
    """Find deals that haven't moved stages in 7+ days and create follow-up tasks."""
    log("\n=== DETECTING STALLED DEALS ===")

    # Get all open deals
    filters = [
        {"propertyName": "dealstage", "operator": "NOT_IN", "values": [
            STAGES.get("enterprise_closedwon", ""),
            STAGES.get("enterprise_closedlost", ""),
            STAGES.get("smb_closedwon", ""),
            STAGES.get("smb_closedlost", "")
        ]}
    ]

    deals = search_deals(
        [{"propertyName": "pipeline", "operator": "IN", "values": [ENTERPRISE_PIPELINE, SMB_PIPELINE]}],
        ["dealname", "dealstage", "hubspot_owner_id", "hs_date_entered_*", "amount"]
    )

    stalled_count = 0
    today = datetime.now()

    for deal in deals:
        props = deal.get("properties", {})
        deal_id = deal.get("id")
        deal_name = props.get("dealname", "Unknown")
        owner_id = props.get("hubspot_owner_id")
        stage = props.get("dealstage")

        # Check all date_entered properties to find current stage entry date
        # HubSpot stores these as hs_date_entered_<stage_id>
        stage_entry_key = f"hs_date_entered_{stage}"
        stage_entry = props.get(stage_entry_key)

        if not stage_entry:
            continue

        try:
            entry_date = datetime.fromisoformat(stage_entry.replace("Z", "+00:00")).replace(tzinfo=None)
            days_in_stage = (today - entry_date).days

            if days_in_stage >= STALLED_DAYS:
                log(f"  STALLED: {deal_name} - {days_in_stage} days in current stage")
                create_task(
                    f"Follow up on stalled deal: {deal_name}",
                    f"This deal has been in the same stage for {days_in_stage} days. Time to push it forward or update the status.",
                    owner_id or OWNER_EMMET,
                    deal_id
                )
                stalled_count += 1
        except Exception as e:
            pass

    log(f"  Found {stalled_count} stalled deals")


def check_renewal_reminders():
    """Create tasks for deals approaching contract end date."""
    log("\n=== CHECKING RENEWAL REMINDERS ===")

    # Get deals with contract_end_date set
    deals = search_deals(
        [{"propertyName": "contract_end_date", "operator": "HAS_PROPERTY"}],
        ["dealname", "contract_end_date", "hubspot_owner_id", "amount"]
    )

    today = datetime.now().date()
    reminder_count = 0

    for deal in deals:
        props = deal.get("properties", {})
        deal_id = deal.get("id")
        deal_name = props.get("dealname", "Unknown")
        owner_id = props.get("hubspot_owner_id")
        end_date_str = props.get("contract_end_date")

        if not end_date_str:
            continue

        try:
            end_date = datetime.fromisoformat(end_date_str.replace("Z", "+00:00")).date()
            days_until = (end_date - today).days

            for alert_days in RENEWAL_ALERTS:
                if days_until == alert_days:
                    if alert_days == 90:
                        task_title = f"Identify expansion path: {deal_name}"
                        task_body = f"Contract ends in 90 days ({end_date}). Start planning renewal/expansion strategy."
                    elif alert_days == 15:
                        task_title = f"Finalize renewal strategy: {deal_name}"
                        task_body = f"Contract ends in 15 days ({end_date}). Renewal proposal should be ready."
                    else:  # 7 days
                        task_title = f"URGENT - Final renewal push: {deal_name}"
                        task_body = f"Contract ends in 7 days ({end_date}). Close this renewal NOW."

                    log(f"  RENEWAL ALERT ({alert_days} days): {deal_name}")
                    create_task(task_title, task_body, owner_id or OWNER_EMMET, deal_id)
                    reminder_count += 1
        except Exception as e:
            pass

    log(f"  Created {reminder_count} renewal reminders")


def stamp_stage_entry_dates():
    """Set date properties when deals enter certain stages."""
    log("\n=== STAMPING STAGE ENTRY DATES ===")

    today = datetime.now().strftime("%Y-%m-%d")
    stamped = 0

    # Deals in Procurement without procurement_start_date
    if STAGES.get("enterprise_procurement"):
        deals = search_deals(
            [
                {"propertyName": "dealstage", "operator": "EQ", "value": STAGES["enterprise_procurement"]},
                {"propertyName": "procurement_start_date", "operator": "NOT_HAS_PROPERTY"}
            ],
            ["dealname"]
        )
        for deal in deals:
            deal_id = deal.get("id")
            deal_name = deal.get("properties", {}).get("dealname", "Unknown")
            log(f"  Setting procurement_start_date for: {deal_name}")
            if update_deal(deal_id, {"procurement_start_date": today}):
                stamped += 1

    # Deals in Closed Won without sow_signed_date
    for stage_key in ["enterprise_closedwon", "smb_closedwon"]:
        if STAGES.get(stage_key):
            deals = search_deals(
                [
                    {"propertyName": "dealstage", "operator": "EQ", "value": STAGES[stage_key]},
                    {"propertyName": "sow_signed_date", "operator": "NOT_HAS_PROPERTY"}
                ],
                ["dealname"]
            )
            for deal in deals:
                deal_id = deal.get("id")
                deal_name = deal.get("properties", {}).get("dealname", "Unknown")
                log(f"  Setting sow_signed_date for: {deal_name}")
                if update_deal(deal_id, {"sow_signed_date": today}):
                    stamped += 1

    log(f"  Stamped dates for {stamped} deals")


def update_procurement_days():
    """Update days_in_procurement for deals in procurement stage."""
    log("\n=== UPDATING PROCUREMENT DAYS ===")

    if not STAGES.get("enterprise_procurement"):
        log("  Procurement stage ID not found, skipping")
        return

    deals = search_deals(
        [{"propertyName": "dealstage", "operator": "EQ", "value": STAGES["enterprise_procurement"]}],
        ["dealname", "procurement_start_date", "days_in_procurement"]
    )

    today = datetime.now().date()
    updated = 0

    for deal in deals:
        props = deal.get("properties", {})
        deal_id = deal.get("id")
        start_date_str = props.get("procurement_start_date")

        if not start_date_str:
            continue

        try:
            start_date = datetime.fromisoformat(start_date_str.replace("Z", "+00:00")).date()
            days = (today - start_date).days

            if update_deal(deal_id, {"days_in_procurement": str(days)}):
                updated += 1
        except Exception as e:
            pass

    log(f"  Updated {updated} deals")


def handle_closed_won_deals():
    """Create delivery deals for newly closed won deals."""
    log("\n=== HANDLING CLOSED WON DEALS ===")

    # Find deals that closed won recently (today) and don't have a delivery deal yet
    # This is simplified - in production you'd track which deals already have delivery deals

    today = datetime.now().strftime("%Y-%m-%d")

    for pipeline_id, stage_id in [
        (ENTERPRISE_PIPELINE, STAGES.get("enterprise_closedwon")),
        (SMB_PIPELINE, STAGES.get("smb_closedwon"))
    ]:
        if not stage_id:
            continue

        deals = search_deals(
            [
                {"propertyName": "dealstage", "operator": "EQ", "value": stage_id},
                {"propertyName": "closedate", "operator": "EQ", "value": today}
            ],
            ["dealname", "amount", "hubspot_owner_id"]
        )

        for deal in deals:
            props = deal.get("properties", {})
            deal_name = props.get("dealname", "Unknown")
            amount = props.get("amount", "0")
            owner_id = props.get("hubspot_owner_id", OWNER_EMMET)

            log(f"  NEW CLOSED WON: {deal_name}")

            if STAGES.get("delivery_phase1"):
                create_deal(
                    f"{deal_name} - Delivery",
                    amount,
                    CLIENT_DELIVERY_PIPELINE,
                    STAGES["delivery_phase1"],
                    owner_id
                )


def handle_closed_lost_deals():
    """Flag closed lost deals for re-engagement (create task, don't auto-create deal)."""
    log("\n=== HANDLING CLOSED LOST DEALS ===")

    today = datetime.now().strftime("%Y-%m-%d")

    for pipeline_id, stage_id in [
        (ENTERPRISE_PIPELINE, STAGES.get("enterprise_closedlost")),
        (SMB_PIPELINE, STAGES.get("smb_closedlost"))
    ]:
        if not stage_id:
            continue

        deals = search_deals(
            [
                {"propertyName": "dealstage", "operator": "EQ", "value": stage_id},
                {"propertyName": "closedate", "operator": "EQ", "value": today}
            ],
            ["dealname", "amount", "hubspot_owner_id"]
        )

        for deal in deals:
            props = deal.get("properties", {})
            deal_id = deal.get("id")
            deal_name = props.get("dealname", "Unknown")
            owner_id = props.get("hubspot_owner_id", OWNER_EMMET)

            log(f"  CLOSED LOST: {deal_name}")

            # Create a task to follow up in 90 days
            create_task(
                f"Re-engagement opportunity: {deal_name}",
                f"This deal was marked lost today. Set a reminder to revisit in 90 days.",
                owner_id,
                deal_id,
                due_days=90
            )


def check_spec_requests():
    """Notify production when spec_required = yes."""
    log("\n=== CHECKING SPEC REQUESTS ===")

    deals = search_deals(
        [{"propertyName": "spec_required", "operator": "EQ", "value": "yes"}],
        ["dealname", "hubspot_owner_id", "amount", "champion"]
    )

    for deal in deals:
        props = deal.get("properties", {})
        deal_id = deal.get("id")
        deal_name = props.get("dealname", "Unknown")

        log(f"  SPEC NEEDED: {deal_name}")

        # Create task for production
        create_task(
            f"Spec request: {deal_name}",
            f"A spec has been requested for {deal_name}. Please coordinate with sales on requirements.",
            OWNER_WAYAN or OWNER_EMMET,  # Assign to Wayan if we have their ID
            deal_id
        )

        # Mark as in_progress so we don't keep creating tasks
        if not DRY_RUN:
            update_deal(deal_id, {"spec_required": "in_progress"})


def handle_churned_clients():
    """Create re-engagement deals for churned clients."""
    log("\n=== HANDLING CHURNED CLIENTS ===")

    if not STAGES.get("delivery_churned") or not STAGES.get("reengagement_identified"):
        log("  Required stage IDs not found, skipping")
        return

    today = datetime.now().strftime("%Y-%m-%d")

    deals = search_deals(
        [
            {"propertyName": "dealstage", "operator": "EQ", "value": STAGES["delivery_churned"]},
            {"propertyName": "hs_lastmodifieddate", "operator": "GTE", "value": today}
        ],
        ["dealname", "amount", "hubspot_owner_id"]
    )

    for deal in deals:
        props = deal.get("properties", {})
        deal_name = props.get("dealname", "Unknown")
        amount = props.get("amount", "0")
        owner_id = props.get("hubspot_owner_id", OWNER_EMMET)

        log(f"  CHURNED: {deal_name}")

        create_deal(
            f"{deal_name} - Re-engagement",
            amount,
            REENGAGEMENT_PIPELINE,
            STAGES["reengagement_identified"],
            owner_id
        )


def enrich_new_contacts():
    """Enrich contacts created today with Apollo data."""
    log("\n=== ENRICHING NEW CONTACTS ===")

    if not APOLLO_KEY:
        log("  Apollo API key not set, skipping")
        return

    # Import the enrichment logic from enrich-contacts.py
    # For now, just log that we would do this
    log("  Running contact enrichment...")

    # Execute the enrichment script
    import subprocess
    result = subprocess.run(
        ["python3", "enrich-contacts.py"] + (["--dry-run"] if DRY_RUN else []),
        capture_output=True,
        text=True,
        cwd="/Users/emmetreilly/Desktop/sales-brain"
    )

    # Print last few lines of output
    for line in result.stdout.split("\n")[-10:]:
        if line.strip():
            log(f"  {line}")


def generate_daily_digest():
    """Generate a summary of today's CRM activity."""
    log("\n=== DAILY DIGEST ===")

    # Get counts
    open_enterprise = len(search_deals(
        [{"propertyName": "pipeline", "operator": "EQ", "value": ENTERPRISE_PIPELINE},
         {"propertyName": "dealstage", "operator": "NOT_IN", "values": [
             STAGES.get("enterprise_closedwon", ""),
             STAGES.get("enterprise_closedlost", "")
         ]}],
        ["dealname"]
    ))

    log(f"  Open Enterprise deals: {open_enterprise}")

    # TODO: Add more summary stats and email them


def main():
    log("=" * 60)
    log("DAILY CRM SYNC")
    log("=" * 60)

    if DRY_RUN:
        log("DRY RUN MODE - No changes will be made\n")

    if not HUBSPOT_TOKEN:
        log("ERROR: HUBSPOT_ACCESS_TOKEN not set")
        sys.exit(1)

    # Initialize stage IDs
    get_stage_ids()

    # Run all automation
    stamp_stage_entry_dates()
    detect_stalled_deals()
    check_renewal_reminders()
    update_procurement_days()
    handle_closed_won_deals()
    handle_closed_lost_deals()
    check_spec_requests()
    handle_churned_clients()
    enrich_new_contacts()
    generate_daily_digest()

    log("\n" + "=" * 60)
    log("SYNC COMPLETE")
    log("=" * 60)


if __name__ == "__main__":
    main()
