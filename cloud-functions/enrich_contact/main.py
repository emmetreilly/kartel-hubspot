#!/usr/bin/env python3
"""
Lead Enrichment Cloud Function
Triggered when a Lead is created in HubSpot.
- Gets associated contact
- Enriches contact with Apollo data
- Routes lead to correct owner (Ben/Emmet/Tim)
- Syncs contact properties to lead
"""

import functions_framework
import requests
import os

HUBSPOT_TOKEN = os.getenv('HUBSPOT_ACCESS_TOKEN')
APOLLO_KEY = os.getenv('APOLLO_API_KEY')
HUBSPOT_BASE = "https://api.hubapi.com"

# Owner IDs for routing
OWNERS = {
    "ben": "159215803",      # Ben Kusin - CRO (high-value)
    "emmet": "160266467",    # Emmet Reilly (middle tier)
    "tim": "161182435",      # Tim Burke (junk/spam)
}


def enrich_with_apollo(email):
    """Enrich contact using Apollo API"""
    try:
        response = requests.post(
            "https://api.apollo.io/v1/people/match",
            headers={"x-api-key": APOLLO_KEY, "Content-Type": "application/json"},
            json={"email": email}
        )

        if response.status_code == 200:
            data = response.json().get('person', {})
            if data:
                org = data.get('organization', {})
                return {
                    'firstname': data.get('first_name'),
                    'lastname': data.get('last_name'),
                    'jobtitle': data.get('title'),
                    'seniority': data.get('seniority'),
                    'company': org.get('name'),
                    'company_size': org.get('estimated_num_employees'),
                    'company_revenue': org.get('estimated_annual_revenue'),
                    'industry': org.get('industry'),
                    'linkedin_url': data.get('linkedin_url')
                }
    except Exception as e:
        print(f"Apollo error: {e}")

    return None


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


def calculate_lead_tier(company_size, company_revenue):
    """Calculate lead tier based on company data"""
    if (company_size and company_size >= 500) or (company_revenue and company_revenue >= 50000000):
        return 'enterprise'

    if (company_size and company_size >= 100) or (company_revenue and company_revenue >= 10000000):
        return 'mid_market'

    return 'smb'


def calculate_priority_level(decision_maker, engagement_score):
    """Calculate priority level"""
    score = 0

    if decision_maker:
        score += 50

    if engagement_score:
        if engagement_score >= 80:
            score += 40
        elif engagement_score >= 50:
            score += 25
        elif engagement_score >= 20:
            score += 10

    if score >= 80:
        return 'CRITICAL'
    elif score >= 60:
        return 'High'
    elif score >= 30:
        return 'Medium'
    else:
        return 'Low'


def map_apollo_industry_to_hubspot(apollo_industry):
    """Map Apollo industry to HubSpot category"""
    if not apollo_industry:
        return None

    industry_lower = apollo_industry.lower()

    if any(kw in industry_lower for kw in ['tech', 'software', 'saas', 'ai', 'data']):
        return 'Technology'
    elif any(kw in industry_lower for kw in ['retail', 'ecommerce', 'commerce']):
        return 'Retail'
    elif any(kw in industry_lower for kw in ['consumer', 'cpg', 'food', 'beverage', 'cosmetic', 'beauty']):
        return 'CPG'
    elif any(kw in industry_lower for kw in ['entertainment', 'media', 'film', 'tv', 'studio']):
        return 'Entertainment'
    elif any(kw in industry_lower for kw in ['music', 'record', 'audio']):
        return 'Music'
    elif any(kw in industry_lower for kw in ['financial', 'investment', 'bank', 'capital', 'fund']):
        return 'Financial Services'
    elif any(kw in industry_lower for kw in ['market', 'advertis', 'agency', 'pr']):
        return 'Marketing'
    elif any(kw in industry_lower for kw in ['health', 'medical', 'pharma', 'hospital']):
        return 'Healthcare'
    elif any(kw in industry_lower for kw in ['fashion', 'apparel', 'clothing']):
        return 'Fashion'
    elif any(kw in industry_lower for kw in ['real estate', 'property']):
        return 'Real Estate'

    return 'Technology'  # Default


def parse_company_size(size_value):
    """
    Parse company size from form dropdown or Apollo integer.
    Returns a tier: 'large', 'medium', 'small', or None if unknown.

    Form dropdown values: "1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5000+"
    Apollo returns integer (estimated_num_employees)
    """
    if not size_value:
        return None

    # If it's already an integer (from Apollo)
    if isinstance(size_value, int):
        if size_value >= 500:
            return 'large'
        elif size_value >= 51:
            return 'medium'
        else:
            return 'small'

    # Form dropdown string values
    size_str = str(size_value).lower().strip()

    # Large: 500+
    if size_str in ['501-1000', '1001-5000', '5000+', '5000', '1000+']:
        return 'large'

    # Medium: 51-500
    if size_str in ['51-200', '201-500']:
        return 'medium'

    # Small: 1-50
    if size_str in ['1-10', '11-50', '1-50']:
        return 'small'

    return None


def determine_lead_owner(form_company_size, apollo_company_size, apollo_revenue, is_decision_maker):
    """
    Determine lead owner based on company tier.
    Uses form data first, falls back to Apollo enrichment.

    TOP TIER (Ben - CRO):
      - Large company (500+ employees)
      - OR revenue >= $50M
      - OR decision_maker = true

    SMALL TIER (Tim):
      - Small company (1-50 employees)

    MIDDLE TIER (Emmet):
      - Everything else (51-500 employees)
    """
    # Decision makers always go to Ben
    if is_decision_maker:
        print(f"Decision maker -> Ben (Top Tier)")
        return OWNERS["ben"]

    # Parse company size - form data takes priority
    size_tier = parse_company_size(form_company_size)
    if not size_tier:
        size_tier = parse_company_size(apollo_company_size)

    # Check Apollo revenue as additional signal
    if apollo_revenue and apollo_revenue >= 50000000:
        print(f"High revenue (${apollo_revenue:,}) -> Ben (Top Tier)")
        return OWNERS["ben"]

    # Route based on company size tier
    if size_tier == 'large':
        print(f"Large company ({form_company_size or apollo_company_size}) -> Ben (Top Tier)")
        return OWNERS["ben"]

    if size_tier == 'small':
        print(f"Small company ({form_company_size or apollo_company_size}) -> Tim (Small Tier)")
        return OWNERS["tim"]

    if size_tier == 'medium':
        print(f"Mid-size company ({form_company_size or apollo_company_size}) -> Emmet (Middle Tier)")
        return OWNERS["emmet"]

    # Unknown size - default to Emmet (middle)
    print(f"Unknown company size -> Emmet (Middle Tier)")
    return OWNERS["emmet"]


def get_lead_contact(lead_id):
    """Get contact associated with a lead"""
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    # Get associated contact
    url = f"{HUBSPOT_BASE}/crm/v4/objects/leads/{lead_id}/associations/contacts"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to get lead associations: {response.status_code}")
        return None

    results = response.json().get("results", [])
    if not results:
        print(f"Lead {lead_id} has no associated contact")
        return None

    contact_id = results[0].get("toObjectId")

    # Get contact details
    contact_url = f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}"
    params = {
        "properties": "email,firstname,lastname,company,jobtitle,seniority,company_size,industry,contact_type,timeline,use_case,client_use_case,hubspotscore"
    }

    contact_response = requests.get(contact_url, headers=headers, params=params)
    if contact_response.status_code != 200:
        print(f"Failed to get contact: {contact_response.status_code}")
        return None

    return contact_response.json()


def update_lead_owner(lead_id, owner_id, lead_props=None):
    """Update a lead's owner and optionally other properties"""
    headers = {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json"
    }

    properties = {"hubspot_owner_id": owner_id}

    # Add any additional lead properties
    if lead_props:
        properties.update(lead_props)

    response = requests.patch(
        f"{HUBSPOT_BASE}/crm/v3/objects/leads/{lead_id}",
        headers=headers,
        json={"properties": properties}
    )

    return response.status_code == 200


@functions_framework.http
def enrich_contact(request):
    """
    HTTP Cloud Function - Triggered when a Lead is created.
    Gets the associated contact, enriches it, and routes the lead to the correct owner.
    """
    # CORS headers
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)

    headers_cors = {'Access-Control-Allow-Origin': '*'}

    try:
        # Get lead ID from webhook
        data = request.get_json()
        lead_id = data.get('lead_id')

        if not lead_id:
            return ({"error": "Missing lead_id"}, 400, headers_cors)

        print(f"Processing lead: {lead_id}")

        # Get associated contact
        contact = get_lead_contact(lead_id)
        if not contact:
            return ({"error": "No contact associated with lead"}, 400, headers_cors)

        contact_id = contact.get('id')
        props = contact.get('properties', {})
        email = props.get('email')

        print(f"Found associated contact: {contact_id} ({email})")

        # Check if personal email (won't enrich with Apollo but still process)
        personal_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com', 'aol.com']
        is_personal_email = any(domain in email.lower() for domain in personal_domains) if email else False

        # Enrich with Apollo (skip for personal emails)
        apollo_data = None
        if not is_personal_email and email:
            apollo_data = enrich_with_apollo(email)
        elif is_personal_email:
            print(f"Personal email - skipping Apollo enrichment: {email}")

        # Build updates (merge Apollo data with existing)
        updates = {}

        # Get names from Apollo or existing
        firstname = props.get('firstname') or (apollo_data.get('firstname') if apollo_data else None)
        lastname = props.get('lastname') or (apollo_data.get('lastname') if apollo_data else None)

        if apollo_data:
            # Job title
            if not props.get('jobtitle') and apollo_data.get('jobtitle'):
                updates['jobtitle'] = apollo_data['jobtitle']

            # Seniority
            if not props.get('seniority') and apollo_data.get('seniority'):
                updates['seniority'] = apollo_data['seniority']

            # Company
            if not props.get('company') and apollo_data.get('company'):
                updates['company'] = apollo_data['company']

            # Industry
            if not props.get('industry') and apollo_data.get('industry'):
                hubspot_industry = map_apollo_industry_to_hubspot(apollo_data['industry'])
                if hubspot_industry:
                    updates['industry'] = hubspot_industry
        elif not is_personal_email:
            print(f"Apollo returned no data for {email}")

        # Calculate decision maker
        jobtitle = updates.get('jobtitle') or props.get('jobtitle')
        seniority = updates.get('seniority') or props.get('seniority')
        is_decision_maker = calculate_decision_maker(jobtitle, seniority)
        updates['decision_maker'] = str(is_decision_maker).lower()

        # Get company size from form (contact property) and Apollo
        form_company_size = props.get('company_size')  # Form dropdown value like "51-200"
        apollo_company_size = apollo_data.get('company_size') if apollo_data else None
        apollo_revenue = apollo_data.get('company_revenue') if apollo_data else None

        # Calculate lead tier (uses Apollo data)
        lead_tier = calculate_lead_tier(apollo_company_size, apollo_revenue)
        updates['lead_tier'] = lead_tier

        # Calculate priority level
        engagement_score = int(props.get('hubspotscore', 0)) if props.get('hubspotscore') else None
        updates['priority_level'] = calculate_priority_level(is_decision_maker, engagement_score)

        # Contact type - default to lead if not set
        if not props.get('contact_type'):
            updates['contact_type'] = 'Unqualified Lead'

        # Determine lead owner based on company tier
        # Uses FORM data first (company_size dropdown), falls back to Apollo
        owner_id = determine_lead_owner(
            form_company_size,
            apollo_company_size,
            apollo_revenue,
            is_decision_maker
        )

        # Update contact in HubSpot
        if updates:
            print(f"Updating {len(updates)} fields for {email}")

            update_response = requests.patch(
                f"{HUBSPOT_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers={
                    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={"properties": updates}
            )

            if update_response.status_code != 200:
                print(f"Warning: Failed to update contact: {update_response.status_code}")

        # Build lead properties to update
        lead_props = {}
        if props.get('company') or (apollo_data and apollo_data.get('company')):
            lead_props['lead_company_name'] = props.get('company') or apollo_data.get('company')
        if props.get('company_size') or apollo_company_size:
            lead_props['lead_company_size'] = props.get('company_size') or str(apollo_company_size)
        if props.get('jobtitle') or (apollo_data and apollo_data.get('jobtitle')):
            lead_props['lead_job_title'] = props.get('jobtitle') or apollo_data.get('jobtitle')
        if props.get('industry') or updates.get('industry'):
            lead_props['lead_industry'] = props.get('industry') or updates.get('industry')
        if props.get('contact_type'):
            lead_props['lead_company_type'] = props.get('contact_type')
        if props.get('timeline'):
            lead_props['lead_timeline'] = props.get('timeline')
        # Check both use_case and client_use_case (form might map to either)
        use_case_value = props.get('use_case') or props.get('client_use_case')
        if use_case_value:
            lead_props['lead_use_case'] = use_case_value

        # Update lead with owner and properties
        owner_name = "Ben" if owner_id == OWNERS["ben"] else ("Tim" if owner_id == OWNERS["tim"] else "Emmet")
        print(f"Routing lead {lead_id} to {owner_name}")

        if update_lead_owner(lead_id, owner_id, lead_props):
            print(f"Successfully updated lead {lead_id}")
        else:
            print(f"Failed to update lead {lead_id}")

        return ({
            "success": True,
            "lead_id": lead_id,
            "contact_id": contact_id,
            "owner_id": owner_id,
            "owner_name": owner_name,
            "contact_fields_updated": list(updates.keys()),
            "lead_fields_updated": list(lead_props.keys()),
            "routing": {
                "form_company_size": form_company_size,
                "apollo_company_size": apollo_company_size,
                "apollo_revenue": apollo_revenue,
                "is_decision_maker": is_decision_maker,
            }
        }, 200, headers_cors)

    except Exception as e:
        print(f"Error: {str(e)}")
        return ({"error": str(e)}, 500, headers_cors)
