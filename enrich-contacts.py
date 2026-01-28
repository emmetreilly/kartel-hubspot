#!/usr/bin/env python3
"""
Contact Enrichment Script
Enriches HubSpot contacts with Apollo.io data and sets lead_tier for routing.

Usage: python3 enrich-contacts.py [--dry-run]
"""

import os
import sys
import json
import requests
from time import sleep

# API Keys
HUBSPOT_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
APOLLO_KEY = os.environ.get("APOLLO_API_KEY", "")

# Routing thresholds
ENTERPRISE_REVENUE = 50_000_000  # $50M
ENTERPRISE_EMPLOYEES = 500
MID_MARKET_REVENUE = 10_000_000  # $10M
MID_MARKET_EMPLOYEES = 100

# Senior titles for routing
SENIOR_TITLES = ["ceo", "cmo", "cfo", "coo", "cto", "vp", "president", "director", "head of", "chief", "founder", "owner"]

# Owner IDs
OWNER_BEN = "159215803"
OWNER_EMMET = "160266467"


def get_contacts_to_enrich():
    """Get contacts missing company revenue data."""
    url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Get contacts where annualrevenue is unknown
    payload = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "annualrevenue",
                "operator": "NOT_HAS_PROPERTY"
            }]
        }],
        "properties": ["email", "firstname", "lastname", "company", "jobtitle", "annualrevenue", "numemployees", "lead_tier", "hubspot_owner_id"],
        "limit": 100
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        print(f"Error fetching contacts: {response.text}")
        return []

    return response.json().get("results", [])


def enrich_from_apollo(email=None, domain=None):
    """Enrich contact/company from Apollo."""
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_KEY
    }

    # Try person enrichment first if we have email
    if email:
        url = "https://api.apollo.io/api/v1/people/match"
        payload = {"email": email}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            person = data.get("person", {})
            org = person.get("organization", {})
            if org:
                return {
                    "name": org.get("name"),
                    "revenue": org.get("organization_revenue"),
                    "revenue_printed": org.get("organization_revenue_printed"),
                    "employees": org.get("estimated_num_employees"),
                    "industry": org.get("industry")
                }

    # Fall back to domain enrichment
    if domain:
        url = f"https://api.apollo.io/api/v1/organizations/enrich?domain={domain}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            org = data.get("organization", {})
            if org:
                return {
                    "name": org.get("name"),
                    "revenue": org.get("organization_revenue"),
                    "revenue_printed": org.get("organization_revenue_printed"),
                    "employees": org.get("estimated_num_employees"),
                    "industry": org.get("industry")
                }

    return None


def determine_lead_tier(revenue, employees, job_title):
    """Determine lead tier based on company size and contact title."""
    is_senior = False
    if job_title:
        title_lower = job_title.lower()
        is_senior = any(t in title_lower for t in SENIOR_TITLES)

    # Enterprise: Big company + senior title
    if revenue and revenue >= ENTERPRISE_REVENUE:
        if is_senior:
            return "enterprise", OWNER_BEN
        else:
            return "mid_market", OWNER_EMMET

    if employees and employees >= ENTERPRISE_EMPLOYEES:
        if is_senior:
            return "enterprise", OWNER_BEN
        else:
            return "mid_market", OWNER_EMMET

    # Mid-market
    if revenue and revenue >= MID_MARKET_REVENUE:
        return "mid_market", OWNER_EMMET

    if employees and employees >= MID_MARKET_EMPLOYEES:
        return "mid_market", OWNER_EMMET

    # SMB (default)
    return "smb", OWNER_EMMET


def employee_count_to_range(count):
    """Convert employee count to HubSpot range value."""
    if not count:
        return None
    if count <= 5:
        return "1-5"
    elif count <= 25:
        return "5-25"
    elif count <= 50:
        return "25-50"
    elif count <= 100:
        return "50-100"
    elif count <= 500:
        return "100-500"
    elif count <= 1000:
        return "500-1000"
    else:
        return "1000+"


def update_hubspot_contact(contact_id, properties):
    """Update contact in HubSpot."""
    url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json={"properties": properties})
    if response.status_code != 200:
        print(f"    API Error: {response.text[:200]}")
    return response.status_code == 200


def main():
    dry_run = "--dry-run" in sys.argv

    if not HUBSPOT_TOKEN or not APOLLO_KEY:
        print("Error: Set HUBSPOT_ACCESS_TOKEN and APOLLO_API_KEY environment variables")
        sys.exit(1)

    print("=" * 60)
    print("CONTACT ENRICHMENT SCRIPT")
    print("=" * 60)
    if dry_run:
        print("DRY RUN MODE - No changes will be made\n")

    # Get contacts to enrich
    print("Fetching contacts missing company data...")
    contacts = get_contacts_to_enrich()
    print(f"Found {len(contacts)} contacts to enrich\n")

    enriched = 0
    skipped = 0
    errors = 0

    for contact in contacts:
        props = contact.get("properties", {})
        contact_id = contact.get("id")
        email = props.get("email", "")
        name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
        company = props.get("company", "")
        job_title = props.get("jobtitle", "")

        print(f"\n--- {name or email} ---")
        print(f"  Company: {company}")
        print(f"  Title: {job_title}")

        # Get domain from email
        domain = None
        if email and "@" in email:
            domain = email.split("@")[1]
            # Skip personal email domains
            if domain in ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]:
                domain = None

        # Enrich from Apollo
        enrichment = enrich_from_apollo(email=email, domain=domain)

        if not enrichment:
            print("  Apollo: No data found")
            skipped += 1
            continue

        revenue = enrichment.get("revenue") or 0
        employees = enrichment.get("employees") or 0

        print(f"  Apollo: {enrichment.get('name')}")
        print(f"    Revenue: {enrichment.get('revenue_printed') or 'Unknown'}")
        print(f"    Employees: {employees or 'Unknown'}")
        print(f"    Industry: {enrichment.get('industry') or 'Unknown'}")

        # Determine tier and owner
        tier, owner_id = determine_lead_tier(revenue, employees, job_title)
        owner_name = "Ben" if owner_id == OWNER_BEN else "Emmet"
        print(f"  Routing: {tier.upper()} → {owner_name}")

        # Prepare update
        updates = {
            "lead_tier": tier,
            "hubspot_owner_id": owner_id
        }

        if revenue:
            updates["annualrevenue"] = str(int(revenue))
        if employees:
            emp_range = employee_count_to_range(employees)
            if emp_range:
                updates["numemployees"] = emp_range
        if enrichment.get("industry"):
            updates["industry"] = enrichment.get("industry")

        if dry_run:
            print(f"  Would update: {updates}")
        else:
            if update_hubspot_contact(contact_id, updates):
                print("  Updated in HubSpot ✓")
                enriched += 1
            else:
                print("  Failed to update HubSpot ✗")
                errors += 1

        # Rate limit
        sleep(0.5)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total contacts: {len(contacts)}")
    print(f"Enriched: {enriched}")
    print(f"Skipped (no data): {skipped}")
    print(f"Errors: {errors}")


if __name__ == "__main__":
    main()
