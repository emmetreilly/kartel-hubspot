"""
HubSpot API client for deal, contact, and task operations.
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests


HUBSPOT_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
BASE_URL = "https://api.hubapi.com"

# Owner ID mapping
OWNERS = {
    "159215803": "Ben Kusin",
    "160266467": "Emmet Reilly",
    "156092023": "Kevin Reilly",
    "160266468": "Luke Peterson",
}


def _headers():
    return {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }


def get_active_deals() -> List[Dict[str, Any]]:
    """
    Get all active deals (not closed won/lost).
    Returns simplified deal objects with key fields.
    """
    url = f"{BASE_URL}/crm/v3/objects/deals/search"

    # Search for deals not in closed stages
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "hs_is_closed",
                        "operator": "EQ",
                        "value": "false",
                    }
                ]
            }
        ],
        "properties": [
            "dealname",
            "amount",
            "dealstage",
            "hubspot_owner_id",
            "next_steps",
            "deal_tier",
            "pipeline",
            "closedate",
        ],
        "limit": 100,
    }

    response = requests.post(url, headers=_headers(), json=payload)

    if response.status_code != 200:
        raise Exception(f"HubSpot API error: {response.text}")

    deals = []
    for deal in response.json().get("results", []):
        props = deal.get("properties", {})
        owner_id = props.get("hubspot_owner_id", "")

        deals.append(
            {
                "id": deal.get("id"),
                "name": props.get("dealname", "Unknown"),
                "amount": props.get("amount"),
                "stage": props.get("dealstage"),
                "pipeline": props.get("pipeline"),
                "owner_id": owner_id,
                "owner_name": OWNERS.get(owner_id, "Unassigned"),
                "next_step": props.get("next_steps"),
                "deal_tier": props.get("deal_tier"),
                "close_date": props.get("closedate"),
            }
        )

    return deals


def get_deal_contacts(deal_id: str) -> List[Dict[str, Any]]:
    """
    Get all contacts associated with a deal.
    """
    url = f"{BASE_URL}/crm/v4/objects/deals/{deal_id}/associations/contacts"

    response = requests.get(url, headers=_headers())

    if response.status_code != 200:
        return []

    contact_ids = [
        assoc.get("toObjectId") for assoc in response.json().get("results", [])
    ]

    if not contact_ids:
        return []

    # Batch get contact details
    contacts = []
    for contact_id in contact_ids[:10]:  # Limit to 10 contacts per deal
        contact_url = f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}"
        params = {"properties": "email,firstname,lastname,company,jobtitle"}

        contact_response = requests.get(contact_url, headers=_headers(), params=params)

        if contact_response.status_code == 200:
            props = contact_response.json().get("properties", {})
            if props.get("email"):  # Only include contacts with email
                contacts.append(
                    {
                        "id": contact_id,
                        "email": props.get("email"),
                        "name": f"{props.get('firstname', '')} {props.get('lastname', '')}".strip(),
                        "company": props.get("company"),
                        "title": props.get("jobtitle"),
                    }
                )

    return contacts


def get_hubspot_tasks(include_completed: bool = False) -> Dict[str, List[Dict]]:
    """
    Get tasks organized by status: due_today, overdue, upcoming.
    """
    url = f"{BASE_URL}/crm/v3/objects/tasks/search"

    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    week_end = today_end + timedelta(days=7)

    # Build filter based on completion status
    filters = []
    if not include_completed:
        filters.append(
            {
                "propertyName": "hs_task_status",
                "operator": "NEQ",
                "value": "COMPLETED",
            }
        )

    payload = {
        "filterGroups": [{"filters": filters}] if filters else [],
        "properties": [
            "hs_task_subject",
            "hs_task_status",
            "hs_timestamp",
            "hubspot_owner_id",
            "hs_task_body",
        ],
        "limit": 100,
    }

    response = requests.post(url, headers=_headers(), json=payload)

    if response.status_code != 200:
        raise Exception(f"HubSpot API error: {response.text}")

    result = {"due_today": [], "overdue": [], "upcoming": []}

    for task in response.json().get("results", []):
        props = task.get("properties", {})
        due_timestamp = props.get("hs_timestamp")

        if not due_timestamp:
            continue

        # Parse due date
        try:
            due_date = datetime.fromisoformat(due_timestamp.replace("Z", "+00:00"))
            due_date_only = due_date.date()
        except ValueError:
            continue

        owner_id = props.get("hubspot_owner_id", "")

        task_obj = {
            "id": task.get("id"),
            "subject": props.get("hs_task_subject", "No subject"),
            "status": props.get("hs_task_status"),
            "due_date": due_date_only.isoformat(),
            "owner_id": owner_id,
            "owner_name": OWNERS.get(owner_id, "Unassigned"),
            "body": props.get("hs_task_body", ""),
        }

        # Categorize
        if due_date_only < today:
            result["overdue"].append(task_obj)
        elif due_date_only == today:
            result["due_today"].append(task_obj)
        elif due_date_only <= (today + timedelta(days=7)):
            result["upcoming"].append(task_obj)

    return result


def update_deal_field(deal_id: str, field_name: str, value: str) -> Dict[str, Any]:
    """
    Update a single field on a deal.
    """
    url = f"{BASE_URL}/crm/v3/objects/deals/{deal_id}"

    payload = {"properties": {field_name: value}}

    response = requests.patch(url, headers=_headers(), json=payload)

    if response.status_code != 200:
        raise Exception(f"Failed to update deal: {response.text}")

    return {"success": True, "deal_id": deal_id, "field": field_name, "value": value}


def create_hubspot_note(deal_id: str, note_body: str) -> Dict[str, Any]:
    """
    Create a note and associate it with a deal.
    """
    # Create the note
    url = f"{BASE_URL}/crm/v3/objects/notes"

    payload = {
        "properties": {
            "hs_note_body": note_body,
            "hs_timestamp": datetime.now().isoformat(),
        }
    }

    response = requests.post(url, headers=_headers(), json=payload)

    if response.status_code != 201:
        raise Exception(f"Failed to create note: {response.text}")

    note_id = response.json().get("id")

    # Associate note with deal
    assoc_url = f"{BASE_URL}/crm/v4/objects/notes/{note_id}/associations/deals/{deal_id}"

    assoc_payload = [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 214}]

    assoc_response = requests.put(assoc_url, headers=_headers(), json=assoc_payload)

    return {"success": True, "note_id": note_id, "deal_id": deal_id}


class HubSpotClient:
    """HubSpot API client class for re-engagement operations."""

    def __init__(self):
        self.token = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
        self.base_url = BASE_URL

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_deal(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """Get a deal by ID."""
        url = f"{self.base_url}/crm/v3/objects/deals/{deal_id}"
        params = {
            "properties": "dealname,amount,dealstage,hubspot_owner_id,pipeline,loss_reason"
        }

        response = requests.get(url, headers=self._headers(), params=params)
        if response.status_code != 200:
            return None
        return response.json()

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get a company by ID."""
        url = f"{self.base_url}/crm/v3/objects/companies/{company_id}"
        params = {"properties": "name,domain,industry"}

        response = requests.get(url, headers=self._headers(), params=params)
        if response.status_code != 200:
            return None
        return response.json()

    def get_deal_associations(self, deal_id: str, to_object_type: str) -> List[Dict]:
        """Get associations for a deal."""
        url = f"{self.base_url}/crm/v4/objects/deals/{deal_id}/associations/{to_object_type}"

        response = requests.get(url, headers=self._headers())
        if response.status_code != 200:
            return []

        return [
            {"id": assoc.get("toObjectId")}
            for assoc in response.json().get("results", [])
        ]

    def create_deal(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new deal."""
        url = f"{self.base_url}/crm/v3/objects/deals"

        payload = {"properties": properties}

        response = requests.post(url, headers=self._headers(), json=payload)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create deal: {response.text}")

        return response.json()

    def create_association(
        self,
        from_id: str,
        from_type: str,
        to_id: str,
        to_type: str
    ) -> bool:
        """Create an association between objects."""
        url = f"{self.base_url}/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}"

        # Association type for deal to company
        payload = [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 342}]

        response = requests.put(url, headers=self._headers(), json=payload)
        return response.status_code in [200, 201]

    def create_task(
        self,
        properties: Dict[str, Any],
        associated_deal_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a task and optionally associate with a deal."""
        url = f"{self.base_url}/crm/v3/objects/tasks"

        # Add timestamp if not provided
        if "hs_timestamp" not in properties:
            properties["hs_timestamp"] = datetime.now().isoformat()

        payload = {"properties": properties}

        response = requests.post(url, headers=self._headers(), json=payload)
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to create task: {response.text}")

        task = response.json()
        task_id = task.get("id")

        # Associate with deal if provided
        if associated_deal_id and task_id:
            assoc_url = f"{self.base_url}/crm/v4/objects/tasks/{task_id}/associations/deals/{associated_deal_id}"
            assoc_payload = [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}]
            requests.put(assoc_url, headers=self._headers(), json=assoc_payload)

        return task
