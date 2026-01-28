#!/usr/bin/env python3
"""
Dashboard Data Extractor
Pulls all key metrics that would appear on HubSpot dashboards via API.
Run: python3 dashboard-data.py
"""

import requests
import json
from datetime import datetime, timedelta

import os
TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
BASE = "https://api.hubapi.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Pipeline IDs
PIPELINES = {
    "enterprise": "1880222397",
    "smb": "1880222398",
    "client_delivery": "1880222399",
    "reengagement": "1880222400"
}

def search_deals(filters, properties=None):
    """Search deals with given filters"""
    if properties is None:
        properties = ["dealname", "amount", "dealstage", "pipeline", "closedate",
                     "hubspot_owner_id", "deal_tier", "payment_expected_date",
                     "payment_received_date", "phase_3_start_date", "renewal_date"]

    payload = {
        "filterGroups": filters,
        "properties": properties,
        "limit": 100
    }

    r = requests.post(f"{BASE}/crm/v3/objects/deals/search",
                     headers=HEADERS, json=payload)
    if r.status_code == 200:
        return r.json().get("results", [])
    return []

def get_all_deals():
    """Get all deals"""
    return search_deals([])

def format_currency(amount):
    """Format as currency"""
    if amount is None:
        return "$0"
    return f"${amount:,.0f}"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def print_table(headers, rows):
    """Simple table printer"""
    if not rows:
        print("  No data")
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    # Print header
    header_line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    print(f"  {header_line}")
    print(f"  {'-' * len(header_line)}")

    # Print rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        print(f"  {row_line}")

# ============================================================
# EXECUTIVE DASHBOARD
# ============================================================
print_section("EXECUTIVE DASHBOARD")

deals = get_all_deals()

# Total Pipeline Value (open deals)
open_deals = [d for d in deals if d["properties"].get("dealstage") not in ["closedwon", "closedlost", None]]
total_pipeline = sum(float(d["properties"].get("amount") or 0) for d in open_deals)
print(f"\n  Total Pipeline Value: {format_currency(total_pipeline)}")
print(f"  Open Deals: {len(open_deals)}")

# Pipeline by Tier
tier_totals = {}
for d in open_deals:
    tier = d["properties"].get("deal_tier") or "unassigned"
    amount = float(d["properties"].get("amount") or 0)
    tier_totals[tier] = tier_totals.get(tier, 0) + amount

print(f"\n  Pipeline by Deal Tier:")
for tier, total in sorted(tier_totals.items(), key=lambda x: -x[1]):
    print(f"    {tier}: {format_currency(total)}")

# Won deals
won_deals = [d for d in deals if d["properties"].get("dealstage") == "closedwon"]
total_won = sum(float(d["properties"].get("amount") or 0) for d in won_deals)
print(f"\n  Total Won Revenue: {format_currency(total_won)}")
print(f"  Won Deals: {len(won_deals)}")

# ============================================================
# SALES DASHBOARD
# ============================================================
print_section("SALES DASHBOARD")

# Active deals sorted by amount
print("\n  Top Active Deals:")
sorted_deals = sorted(open_deals, key=lambda d: float(d["properties"].get("amount") or 0), reverse=True)[:10]
rows = []
for d in sorted_deals:
    rows.append([
        d["properties"].get("dealname", "")[:30],
        format_currency(float(d["properties"].get("amount") or 0)),
        d["properties"].get("dealstage", "")[:15],
        d["properties"].get("deal_tier", "")
    ])
print_table(["Deal Name", "Amount", "Stage", "Tier"], rows)

# Deals by pipeline
print("\n  Deals by Pipeline:")
pipeline_counts = {}
pipeline_amounts = {}
for d in open_deals:
    p = d["properties"].get("pipeline", "unknown")
    pipeline_counts[p] = pipeline_counts.get(p, 0) + 1
    pipeline_amounts[p] = pipeline_amounts.get(p, 0) + float(d["properties"].get("amount") or 0)

for name, pid in PIPELINES.items():
    count = pipeline_counts.get(pid, 0)
    amount = pipeline_amounts.get(pid, 0)
    print(f"    {name}: {count} deals, {format_currency(amount)}")

# ============================================================
# CASH FLOW DASHBOARD
# ============================================================
print_section("CASH FLOW DASHBOARD")

today = datetime.now()
today_str = today.strftime("%Y-%m-%d")

# Expected payments (have invoice, no payment received)
print("\n  Payments Expected (no payment received yet):")
expected_payments = []
for d in deals:
    expected = d["properties"].get("payment_expected_date")
    received = d["properties"].get("payment_received_date")
    if expected and not received:
        expected_payments.append(d)

expected_payments.sort(key=lambda d: d["properties"].get("payment_expected_date", "9999"))
rows = []
total_expected = 0
for d in expected_payments[:10]:
    amount = float(d["properties"].get("amount") or 0)
    total_expected += amount
    rows.append([
        d["properties"].get("dealname", "")[:30],
        format_currency(amount),
        d["properties"].get("payment_expected_date", "")[:10]
    ])
print_table(["Deal", "Amount", "Expected Date"], rows)
print(f"\n  Total Expected: {format_currency(total_expected)}")

# Overdue payments
print("\n  Overdue Payments:")
overdue = []
for d in expected_payments:
    expected = d["properties"].get("payment_expected_date", "")[:10]
    if expected and expected < today_str:
        overdue.append(d)

rows = []
total_overdue = 0
for d in overdue:
    amount = float(d["properties"].get("amount") or 0)
    total_overdue += amount
    rows.append([
        d["properties"].get("dealname", "")[:30],
        format_currency(amount),
        d["properties"].get("payment_expected_date", "")[:10]
    ])
print_table(["Deal", "Amount", "Was Due"], rows)
print(f"\n  Total Overdue: {format_currency(total_overdue)}")

# ============================================================
# OPERATIONS DASHBOARD
# ============================================================
print_section("OPERATIONS DASHBOARD")

# Client Delivery pipeline
delivery_deals = [d for d in deals if d["properties"].get("pipeline") == PIPELINES["client_delivery"]]
print(f"\n  Client Delivery Pipeline: {len(delivery_deals)} deals")

# Phase III upcoming (next 60 days)
print("\n  Phase III Starts (next 60 days):")
future_60 = (today + timedelta(days=60)).strftime("%Y-%m-%d")
phase3_upcoming = []
for d in deals:
    p3_date = d["properties"].get("phase_3_start_date") or ""
    p3_date = p3_date[:10] if p3_date else ""
    if p3_date and today_str <= p3_date <= future_60:
        phase3_upcoming.append(d)

rows = []
for d in phase3_upcoming:
    p3 = d["properties"].get("phase_3_start_date") or ""
    rows.append([
        (d["properties"].get("dealname") or "")[:30],
        p3[:10] if p3 else "",
        format_currency(float(d["properties"].get("amount") or 0))
    ])
print_table(["Deal", "Phase III Date", "Value"], rows)

# Renewals upcoming (next 90 days)
print("\n  Renewals Due (next 90 days):")
future_90 = (today + timedelta(days=90)).strftime("%Y-%m-%d")
renewals_upcoming = []
for d in deals:
    renewal = d["properties"].get("renewal_date") or ""
    renewal = renewal[:10] if renewal else ""
    if renewal and today_str <= renewal <= future_90:
        renewals_upcoming.append(d)

rows = []
for d in renewals_upcoming:
    ren = d["properties"].get("renewal_date") or ""
    rows.append([
        (d["properties"].get("dealname") or "")[:30],
        ren[:10] if ren else "",
        format_currency(float(d["properties"].get("amount") or 0))
    ])
print_table(["Deal", "Renewal Date", "Value"], rows)

# Re-engagement pipeline
reengagement_deals = [d for d in deals if d["properties"].get("pipeline") == PIPELINES["reengagement"]]
print(f"\n  Re-engagement Pipeline: {len(reengagement_deals)} deals")

print("\n" + "="*60)
print(f"  Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*60 + "\n")
