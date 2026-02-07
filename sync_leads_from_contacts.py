#!/usr/bin/env python3
"""
Sync all existing leads with their associated contact data.
- Maps contact properties to lead properties
- Reassigns owner based on routing rules
"""

import requests
import time
import os

HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
HUBSPOT_BASE = "https://api.hubapi.com"

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

# Owner IDs for routing
OWNERS = {
    "ben": "159215803",      # Ben Kusin - CRO (high-value)
    "emmet": "160266467",    # Emmet Reilly (middle tier)
    "tim": "161182435",      # Tim Burke (small tier)
}

OWNER_NAMES = {
    "159215803": "Ben",
    "160266467": "Emmet",
    "161182435": "Tim",
}


def calculate_decision_maker(jobtitle, seniority):
    """Calculate decision maker status"""
    if not jobtitle:
        return seniority in ['C_LEVEL', 'VP', 'DIRECTOR', 'MANAGER'] if seniority else False

    title_lower = jobtitle.lower()

    # C-level
    if any(x in title_lower for x in ['ceo', 'cfo', 'cmo', 'cto', 'coo', 'cpo', 'chief', 'founder', 'owner']):
        return True

    # VP/President
    if 'vp' in title_lower or 'vice president' in title_lower:
        return True
    if 'president' in title_lower and 'vice' not in title_lower:
        return True

    # Director/Head
    if 'director' in title_lower or 'head of' in title_lower:
        return True

    # Manager (excluding support roles)
    if 'manager' in title_lower:
        exclude = ['account manager', 'customer success', 'support', 'operations manager', 'community']
        if not any(x in title_lower for x in exclude):
            return True

    # Seniority-based
    if seniority in ['C_LEVEL', 'VP', 'DIRECTOR', 'MANAGER']:
        return True

    return False


def parse_company_size(size_value):
    """Parse company size to tier"""
    if not size_value:
        return None

    if isinstance(size_value, int):
        if size_value >= 500:
            return 'large'
        elif size_value >= 51:
            return 'medium'
        else:
            return 'small'

    size_str = str(size_value).lower().strip()

    if size_str in ['501-1000', '1001-5000', '5000+', '5000', '1000+']:
        return 'large'
    if size_str in ['51-200', '201-500']:
        return 'medium'
    if size_str in ['1-10', '11-50', '1-50']:
        return 'small'

    return None


def determine_owner(company_size, is_decision_maker):
    """Determine owner based on routing rules"""
    if is_decision_maker:
        return OWNERS["ben"], "decision_maker"

    size_tier = parse_company_size(company_size)

    if size_tier == 'large':
        return OWNERS["ben"], "large_company"
    if size_tier == 'small':
        return OWNERS["tim"], "small_company"
    if size_tier == 'medium':
        return OWNERS["emmet"], "mid_company"

    return OWNERS["emmet"], "unknown_size"


def get_all_leads():
    """Get all leads from HubSpot"""
    leads = []
    after = None

    while True:
        url = f"{HUBSPOT_BASE}/crm/v3/objects/leads"
        params = {
            "limit": 100,
            "properties": "hs_lead_name,hubspot_owner_id,lead_company_name,lead_company_size,lead_job_title"
        }
        if after:
            params["after"] = after

        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"Error fetching leads: {response.status_code}")
            break

        data = response.json()
        leads.extend(data.get("results", []))

        paging = data.get("paging", {})
        if paging.get("next"):
            after = paging["next"]["after"]
        else:
            break

    return leads


def get_lead_contact(lead_id):
    """Get contact associated with a lead"""
    url = f"{HUBSPOT_BASE}/crm/v4/objects/leads/{lead_id}/associations/contacts"

    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return None

    results = response.json().get("results", [])
    if not results:
        return None

    contact_id = results[0].get("toObjectId")

    # Get contact details
    contact_url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}"
    params = {
        "properties": "email,firstname,lastname,company,jobtitle,seniority,company_size,industry,contact_type,timeline,use_case"
    }

    contact_response = requests.get(contact_url, headers=HEADERS, params=params)
    if contact_response.status_code != 200:
        return None

    return contact_response.json()


def update_lead(lead_id, properties):
    """Update a lead's properties"""
    url = f"{HUBSPOT_BASE}/crm/v3/objects/leads/{lead_id}"

    response = requests.patch(url, headers=HEADERS, json={"properties": properties})
    return response.status_code == 200


def main():
    print("="*70)
    print("SYNC LEADS FROM CONTACTS")
    print("="*70)

    # Get all leads
    print("\nFetching all leads...")
    leads = get_all_leads()
    print(f"Found {len(leads)} leads")

    updated = 0
    skipped = 0
    errors = 0

    routing_summary = {"ben": [], "emmet": [], "tim": []}

    for i, lead in enumerate(leads):
        lead_id = lead["id"]
        lead_props = lead.get("properties", {})
        lead_name = lead_props.get("hs_lead_name", "Unknown")
        current_owner = lead_props.get("hubspot_owner_id")

        print(f"\n[{i+1}/{len(leads)}] {lead_name}")

        # Get associated contact
        contact = get_lead_contact(lead_id)
        if not contact:
            print(f"  → No contact found, skipping")
            skipped += 1
            continue

        contact_props = contact.get("properties", {})
        email = contact_props.get("email", "")
        jobtitle = contact_props.get("jobtitle", "")
        company_size = contact_props.get("company_size", "")
        seniority = contact_props.get("seniority", "")

        # Calculate routing
        is_decision_maker = calculate_decision_maker(jobtitle, seniority)
        new_owner, reason = determine_owner(company_size, is_decision_maker)

        # Build update payload
        updates = {}

        # Map contact fields to lead
        if contact_props.get("company"):
            updates["lead_company_name"] = contact_props["company"]
        if contact_props.get("company_size"):
            updates["lead_company_size"] = contact_props["company_size"]
        if contact_props.get("jobtitle"):
            updates["lead_job_title"] = contact_props["jobtitle"]
        if contact_props.get("industry"):
            updates["lead_industry"] = contact_props["industry"]
        if contact_props.get("contact_type"):
            updates["lead_company_type"] = contact_props["contact_type"]
        if contact_props.get("timeline"):
            updates["lead_timeline"] = contact_props["timeline"]
        if contact_props.get("use_case"):
            updates["lead_use_case"] = contact_props["use_case"]

        # Update owner
        updates["hubspot_owner_id"] = new_owner

        owner_name = OWNER_NAMES.get(new_owner, "Unknown")
        current_owner_name = OWNER_NAMES.get(current_owner, "Other")

        # Track for summary
        if new_owner == OWNERS["ben"]:
            routing_summary["ben"].append(lead_name)
        elif new_owner == OWNERS["emmet"]:
            routing_summary["emmet"].append(lead_name)
        else:
            routing_summary["tim"].append(lead_name)

        if current_owner != new_owner:
            print(f"  → {current_owner_name} → {owner_name} ({reason})")
        else:
            print(f"  → Keeping {owner_name} ({reason})")

        # Update lead
        if updates:
            if update_lead(lead_id, updates):
                updated += 1
            else:
                print(f"  ✗ Failed to update")
                errors += 1

        # Rate limit
        time.sleep(0.1)

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total leads: {len(leads)}")
    print(f"Updated: {updated}")
    print(f"Skipped (no contact): {skipped}")
    print(f"Errors: {errors}")

    print(f"\n--- ROUTING BREAKDOWN ---")
    print(f"Ben (Top Tier): {len(routing_summary['ben'])} leads")
    for name in routing_summary['ben'][:10]:
        print(f"  - {name}")
    if len(routing_summary['ben']) > 10:
        print(f"  ... and {len(routing_summary['ben']) - 10} more")

    print(f"\nEmmet (Mid Tier): {len(routing_summary['emmet'])} leads")
    for name in routing_summary['emmet'][:10]:
        print(f"  - {name}")
    if len(routing_summary['emmet']) > 10:
        print(f"  ... and {len(routing_summary['emmet']) - 10} more")

    print(f"\nTim (Small Tier): {len(routing_summary['tim'])} leads")
    for name in routing_summary['tim'][:10]:
        print(f"  - {name}")
    if len(routing_summary['tim']) > 10:
        print(f"  ... and {len(routing_summary['tim']) - 10} more")


if __name__ == "__main__":
    main()
