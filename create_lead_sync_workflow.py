#!/usr/bin/env python3
"""
Create HubSpot Workflow: Sync Contact Properties to Lead

Creates an automated workflow that triggers when a Lead exists
and copies properties from the associated Contact to the Lead.
"""

import requests
import json
import os
from datetime import datetime

# Configuration
HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}


def get_existing_workflows():
    """Get existing workflows"""
    url = "https://api.hubapi.com/automation/v4/flows"
    params = {"limit": 100}

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        return response.json().get("results", [])
    except Exception as e:
        print(f"  Error fetching workflows: {str(e)[:100]}")
        return []


def create_lead_sync_workflow():
    """Create workflow to sync Contact properties to Lead"""

    url = "https://api.hubapi.com/automation/v4/flows"

    # Property mappings: (contact_property, lead_property)
    property_mappings = [
        ("company", "lead_company_name"),
        ("contact_type", "lead_company_type"),
        ("company_size", "lead_company_size"),
        ("jobtitle", "lead_job_title"),
        ("industry", "lead_industry"),
        ("timeline", "lead_timeline"),
        ("use_case", "lead_use_case"),
    ]

    # Build actions - SET_PROPERTY_VALUE actions
    actions = []
    action_id = 1

    for contact_prop, lead_prop in property_mappings:
        actions.append({
            "actionId": str(action_id),
            "actionTypeVersion": 0,
            "actionTypeId": "0-4",  # Lead object
            "type": "SINGLE_CONNECTION",
            "fields": {
                "propertyName": lead_prop,
                "propertyValue": {
                    "type": "ASSOCIATION_PROPERTY_VALUE",
                    "associationPropertyValue": {
                        "objectTypeId": "0-1",  # Contact
                        "propertyName": contact_prop,
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 578  # Lead to Contact
                    }
                }
            }
        })
        action_id += 1

    workflow_def = {
        "name": "Sync Contact Info to Lead",
        "description": "Copies Contact properties (company, job title, industry, etc.) to Lead properties for pipeline visibility",
        "type": "PLATFORM_FLOW",
        "flowType": "WORKFLOW",
        "objectTypeId": "0-4",  # Lead object
        "isEnabled": False,  # Create disabled first
        "startActionId": "1",
        "nextAvailableActionId": str(action_id),
        "actions": actions,
        "enrollmentCriteria": {
            "type": "LIST_BASED",
            "shouldReEnroll": False,
            "unEnrollObjectsNotMeetingCriteria": False,
            "reEnrollmentTriggersFilterBranches": [],
            "listFilterBranch": {
                "filterBranchType": "AND",
                "filterBranchOperator": "AND",
                "filters": [
                    {
                        "filterType": "PROPERTY",
                        "property": "hs_lead_name",
                        "operation": {
                            "operationType": "ALL_PROPERTY",
                            "operator": "IS_KNOWN",
                            "includeObjectsWithNoValueSet": False
                        }
                    }
                ],
                "filterBranches": []
            }
        },
        "timeWindows": [],
        "blockedDates": [],
        "customProperties": {},
        "dataSources": []
    }

    try:
        response = requests.post(url, headers=HEADERS, json=workflow_def)
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)


def activate_workflow(flow_id):
    """Activate the workflow"""
    url = f"https://api.hubapi.com/automation/v4/flows/{flow_id}"

    try:
        response = requests.patch(url, headers=HEADERS, json={"isEnabled": True})
        return response.status_code in [200, 204]
    except:
        return False


def main():
    print("\n" + "=" * 70)
    print("CREATE HUBSPOT WORKFLOW: SYNC CONTACT TO LEAD")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check for existing workflow
    print("\nChecking existing workflows...")
    existing = get_existing_workflows()

    for wf in existing:
        if wf.get("name") == "Sync Contact Info to Lead":
            print(f"  ✓ Workflow already exists!")
            print(f"    ID: {wf.get('id')}")
            print(f"    Status: {'Active' if wf.get('isEnabled') else 'Inactive'}")
            return

    # Create the workflow
    print("\nCreating workflow...")
    success, result = create_lead_sync_workflow()

    if success:
        flow_id = result.get("id")
        print(f"  ✓ Workflow created!")
        print(f"    ID: {flow_id}")
        print(f"    Name: {result.get('name')}")

        print("\nActivating workflow...")
        if activate_workflow(flow_id):
            print("  ✓ Workflow activated!")
        else:
            print("  → Created but needs manual activation")
            print(f"    Go to: HubSpot > Automation > Workflows")

        print("\n" + "-" * 70)
        print("PROPERTY MAPPINGS:")
        print("-" * 70)
        print("  Contact Property    →  Lead Property")
        print("  ─────────────────────────────────────")
        print("  company             →  lead_company_name")
        print("  contact_type        →  lead_company_type")
        print("  company_size        →  lead_company_size")
        print("  jobtitle            →  lead_job_title")
        print("  industry            →  lead_industry")
        print("  timeline            →  lead_timeline")
        print("  use_case            →  lead_use_case")

    else:
        print(f"  ✗ Failed to create workflow")
        print(f"    Error: {str(result)[:500]}")


if __name__ == "__main__":
    main()
