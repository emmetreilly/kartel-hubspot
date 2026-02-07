#!/usr/bin/env python3
"""
Create Lead Properties in HubSpot

Creates duplicate properties on the Lead object that mirror Contact/Company properties
so key info from forms can be displayed in the Leads pipeline view.

Properties to create:
- Company Type
- Company Name
- Company Size
- Job Title
- Industry
- What's your timeline
- Use Case
"""

import requests
import time
import os
from datetime import datetime

# Configuration
HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

# Lead object type ID in HubSpot
LEAD_OBJECT_TYPE = "0-4"

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

# Define Lead properties to create
# These mirror existing Contact/Company properties
LEAD_PROPERTIES = [
    {
        "name": "lead_company_name",
        "label": "Company Name",
        "type": "string",
        "fieldType": "text",
        "groupName": "lead_form_info",
        "description": "Company name from form submission"
    },
    {
        "name": "lead_company_type",
        "label": "Company Type",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "lead_form_info",
        "description": "Type of company (Brand, Agency, Production, etc.)",
        "options": [
            {"label": "Brand", "value": "brand"},
            {"label": "Agency", "value": "agency"},
            {"label": "Production Company", "value": "production"},
            {"label": "Platform", "value": "platform"},
            {"label": "Studio", "value": "studio"},
            {"label": "Network", "value": "network"},
            {"label": "Label", "value": "label"},
            {"label": "Startup", "value": "startup"},
            {"label": "Enterprise", "value": "enterprise"},
            {"label": "Other", "value": "other"}
        ]
    },
    {
        "name": "lead_company_size",
        "label": "Company Size",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "lead_form_info",
        "description": "Company size bucket",
        "options": [
            {"label": "1-10", "value": "1-10"},
            {"label": "11-50", "value": "11-50"},
            {"label": "51-200", "value": "51-200"},
            {"label": "201-500", "value": "201-500"},
            {"label": "501-1000", "value": "501-1000"},
            {"label": "1001-5000", "value": "1001-5000"},
            {"label": "5000+", "value": "5000+"}
        ]
    },
    {
        "name": "lead_job_title",
        "label": "Job Title",
        "type": "string",
        "fieldType": "text",
        "groupName": "lead_form_info",
        "description": "Job title from form submission"
    },
    {
        "name": "lead_industry",
        "label": "Industry",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "lead_form_info",
        "description": "Industry segment",
        "options": [
            {"label": "Entertainment", "value": "entertainment"},
            {"label": "Agency", "value": "agency"},
            {"label": "Tech", "value": "tech"},
            {"label": "Music", "value": "music"},
            {"label": "CPG", "value": "cpg"},
            {"label": "Beauty/Fashion", "value": "beauty"},
            {"label": "Hospitality", "value": "hospitality"},
            {"label": "Automotive", "value": "automotive"},
            {"label": "Healthcare", "value": "healthcare"},
            {"label": "Finance", "value": "finance"},
            {"label": "Retail", "value": "retail"},
            {"label": "Other", "value": "other"}
        ]
    },
    {
        "name": "lead_timeline",
        "label": "What's Your Timeline",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "lead_form_info",
        "description": "Project timeline from form",
        "options": [
            {"label": "ASAP", "value": "asap"},
            {"label": "This Month", "value": "this_month"},
            {"label": "This Quarter", "value": "this_quarter"},
            {"label": "Next Quarter", "value": "next_quarter"},
            {"label": "6+ Months", "value": "6_months_plus"},
            {"label": "Just Exploring", "value": "exploring"}
        ]
    },
    {
        "name": "lead_use_case",
        "label": "Use Case",
        "type": "string",
        "fieldType": "textarea",
        "groupName": "lead_form_info",
        "description": "Use case or project description from form"
    }
]


def create_property_group():
    """Create the Lead Information property group if it doesn't exist"""
    url = f"https://api.hubapi.com/crm/v3/properties/{LEAD_OBJECT_TYPE}/groups"

    # First check if group exists
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        groups = response.json().get('results', [])
        existing_names = [g['name'] for g in groups]

        if 'lead_form_info' in existing_names:
            print("  → Property group 'Lead Form Info' already exists")
            return True
    except Exception as e:
        print(f"Error checking property groups: {e}")

    # Create the group
    group_def = {
        "name": "lead_form_info",
        "label": "Lead Form Info",
        "displayOrder": 1
    }

    try:
        response = requests.post(url, headers=HEADERS, json=group_def)
        response.raise_for_status()
        print("  ✓ Created property group 'Lead Form Info'")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409 or "already exists" in str(e.response.text).lower():
            print("  → Property group 'Lead Form Info' already exists")
            return True
        print(f"  ✗ Failed to create property group: {e.response.text[:200]}")
        return False
    except Exception as e:
        print(f"  ✗ Failed to create property group: {str(e)[:200]}")
        return False


def get_existing_lead_properties():
    """Get all existing Lead properties"""
    url = f"https://api.hubapi.com/crm/v3/properties/{LEAD_OBJECT_TYPE}"

    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        properties = response.json().get('results', [])
        return {p['name']: p for p in properties}
    except Exception as e:
        print(f"Error fetching Lead properties: {e}")
        return {}


def create_lead_property(prop_def):
    """Create a single Lead property"""
    url = f"https://api.hubapi.com/crm/v3/properties/{LEAD_OBJECT_TYPE}"

    try:
        response = requests.post(url, headers=HEADERS, json=prop_def)
        response.raise_for_status()
        return True, "Created"
    except requests.exceptions.HTTPError as e:
        error_body = e.response.text if hasattr(e, 'response') else str(e)
        if "already exists" in error_body.lower() or e.response.status_code == 409:
            return True, "Already exists"
        return False, f"Error: {error_body[:200]}"
    except Exception as e:
        return False, f"Error: {str(e)[:200]}"


def update_lead_property(prop_name, prop_def):
    """Update an existing Lead property"""
    url = f"https://api.hubapi.com/crm/v3/properties/{LEAD_OBJECT_TYPE}/{prop_name}"

    # Remove fields that can't be updated
    update_def = {k: v for k, v in prop_def.items() if k not in ['name', 'type']}

    try:
        response = requests.patch(url, headers=HEADERS, json=update_def)
        response.raise_for_status()
        return True, "Updated"
    except Exception as e:
        return False, f"Update error: {str(e)[:200]}"


def main():
    print("\n" + "="*70)
    print("CREATE LEAD PROPERTIES IN HUBSPOT")
    print("="*70)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Creating {len(LEAD_PROPERTIES)} properties on Lead object...")

    # Create property group first
    print("\nCreating property group...")
    if not create_property_group():
        print("WARNING: Could not create property group, properties may fail")

    # Get existing properties
    print("\nFetching existing Lead properties...")
    existing = get_existing_lead_properties()
    print(f"Found {len(existing)} existing properties")

    # Create/update each property
    print("\n" + "-"*70)
    print("CREATING LEAD PROPERTIES")
    print("-"*70)

    results = {
        'created': 0,
        'existing': 0,
        'updated': 0,
        'failed': 0
    }

    for prop in LEAD_PROPERTIES:
        prop_name = prop['name']
        prop_label = prop['label']

        if prop_name in existing:
            print(f"  → {prop_label}: Already exists")
            results['existing'] += 1
        else:
            success, message = create_lead_property(prop)
            if success:
                if "exists" in message.lower():
                    print(f"  → {prop_label}: {message}")
                    results['existing'] += 1
                else:
                    print(f"  ✓ {prop_label}: {message}")
                    results['created'] += 1
            else:
                print(f"  ✗ {prop_label}: {message}")
                results['failed'] += 1

        time.sleep(0.3)  # Rate limiting

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"  Created: {results['created']}")
    print(f"  Already existed: {results['existing']}")
    print(f"  Failed: {results['failed']}")

    print("\n" + "-"*70)
    print("LEAD PROPERTIES CREATED:")
    print("-"*70)
    for prop in LEAD_PROPERTIES:
        print(f"  • {prop['label']} ({prop['name']})")

    print("\n" + "-"*70)
    print("NEXT STEPS:")
    print("-"*70)
    print("""
1. Go to HubSpot Settings > Objects > Leads > Properties
   Verify the new properties appear under 'Lead Information'

2. Add properties to Lead pipeline cards:
   - Go to Leads > Pipeline view
   - Click 'Actions' > 'Edit cards'
   - Add the new properties to your card view

3. Map form fields to Lead properties:
   - Go to your form in HubSpot
   - Map each form field to the corresponding lead_* property

4. Set up automation to copy data from Contact to Lead:
   - Create a workflow triggered when a Lead is created
   - Copy values from associated Contact to Lead properties

Alternative: Use HubSpot's property sync feature if available in your plan.
""")

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
