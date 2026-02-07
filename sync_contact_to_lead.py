#!/usr/bin/env python3
"""
Sync Contact Properties to Lead Properties

This script copies relevant properties from associated Contacts to Leads,
so key info is visible in the Leads pipeline view.

Property Mapping:
  Contact/Company → Lead
  ─────────────────────────────────────
  company         → lead_company_name
  contact_type    → lead_company_type
  company_size    → lead_company_size
  jobtitle        → lead_job_title
  industry        → lead_industry
  timeline        → lead_timeline
  use_case        → lead_use_case

Run this script:
- Once to backfill existing Leads
- Periodically (cron) to keep Leads in sync
- Or trigger via webhook when new Leads are created
"""

import requests
import time
import os
from datetime import datetime

# Configuration
HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_TOKEN}",
    "Content-Type": "application/json"
}

# Property mapping: Contact property → Lead property
CONTACT_TO_LEAD_MAPPING = {
    "company": "lead_company_name",
    "contact_type": "lead_company_type",
    "company_size": "lead_company_size",
    "jobtitle": "lead_job_title",
    "industry": "lead_industry",
    "timeline": "lead_timeline",
    "use_case": "lead_use_case",
}

# Also try to get from associated Company if Contact doesn't have it
COMPANY_FALLBACK_MAPPING = {
    "name": "lead_company_name",
    "industry": "lead_industry",
    "numberofemployees": "lead_company_size",
}


class ContactToLeadSync:
    def __init__(self):
        self.stats = {
            "leads_processed": 0,
            "leads_updated": 0,
            "leads_skipped": 0,
            "errors": 0
        }

    def get_all_leads(self):
        """Fetch all Leads from HubSpot"""
        leads = []
        url = "https://api.hubapi.com/crm/v3/objects/leads"
        params = {
            "limit": 100,
            "properties": ",".join([
                "hs_lead_name",
                "lead_company_name",
                "lead_company_type",
                "lead_company_size",
                "lead_job_title",
                "lead_industry",
                "lead_timeline",
                "lead_use_case"
            ])
        }

        after = None
        while True:
            if after:
                params["after"] = after

            try:
                response = requests.get(url, headers=HEADERS, params=params)
                response.raise_for_status()
                data = response.json()

                leads.extend(data.get("results", []))

                # Check for pagination
                paging = data.get("paging", {})
                if paging.get("next"):
                    after = paging["next"]["after"]
                else:
                    break

            except Exception as e:
                print(f"Error fetching leads: {e}")
                break

            time.sleep(0.1)

        return leads

    def get_associated_contact(self, lead_id):
        """Get the Contact associated with a Lead"""
        url = f"https://api.hubapi.com/crm/v3/objects/leads/{lead_id}/associations/contacts"

        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            results = response.json().get("results", [])

            if results:
                contact_id = results[0]["toObjectId"]
                return self.get_contact_details(contact_id)

        except Exception as e:
            if "404" not in str(e):
                print(f"    Error getting associations for lead {lead_id}: {str(e)[:100]}")

        return None

    def get_contact_details(self, contact_id):
        """Get Contact properties"""
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        params = {
            "properties": ",".join([
                "email",
                "firstname",
                "lastname",
                "company",
                "jobtitle",
                "industry",
                "contact_type",
                "company_size",
                "timeline",
                "use_case"
            ])
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"    Error fetching contact {contact_id}: {str(e)[:100]}")
            return None

    def get_associated_company(self, contact_id):
        """Get Company associated with a Contact"""
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/companies"

        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            results = response.json().get("results", [])

            if results:
                company_id = results[0]["toObjectId"]
                return self.get_company_details(company_id)

        except Exception:
            pass

        return None

    def get_company_details(self, company_id):
        """Get Company properties"""
        url = f"https://api.hubapi.com/crm/v3/objects/companies/{company_id}"
        params = {
            "properties": "name,industry,numberofemployees,type"
        }

        try:
            response = requests.get(url, headers=HEADERS, params=params)
            response.raise_for_status()
            return response.json()

        except Exception:
            return None

    def map_company_size(self, employee_count):
        """Map employee count to company size bucket"""
        if not employee_count:
            return None

        try:
            count = int(employee_count)
            if count <= 10:
                return "1-10"
            elif count <= 50:
                return "11-50"
            elif count <= 200:
                return "51-200"
            elif count <= 500:
                return "201-500"
            elif count <= 1000:
                return "501-1000"
            elif count <= 5000:
                return "1001-5000"
            else:
                return "5000+"
        except (ValueError, TypeError):
            return None

    def update_lead(self, lead_id, properties):
        """Update Lead with new properties"""
        url = f"https://api.hubapi.com/crm/v3/objects/leads/{lead_id}"

        try:
            response = requests.patch(url, headers=HEADERS, json={"properties": properties})
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"    Error updating lead {lead_id}: {str(e)[:100]}")
            return False

    def sync_lead(self, lead):
        """Sync a single Lead with its associated Contact"""
        lead_id = lead["id"]
        lead_props = lead.get("properties", {})
        lead_name = lead_props.get("hs_lead_name", "Unknown")

        # Get associated Contact
        contact = self.get_associated_contact(lead_id)
        if not contact:
            return False, "No associated contact"

        contact_props = contact.get("properties", {})
        contact_id = contact["id"]

        # Get associated Company (for fallback data)
        company = self.get_associated_company(contact_id)
        company_props = company.get("properties", {}) if company else {}

        # Build update properties
        updates = {}

        # Map Contact properties to Lead
        for contact_prop, lead_prop in CONTACT_TO_LEAD_MAPPING.items():
            value = contact_props.get(contact_prop)
            if value and value.strip():
                # Only update if Lead doesn't already have this value
                current_value = lead_props.get(lead_prop)
                if not current_value or current_value.strip() == "":
                    updates[lead_prop] = value

        # Fallback to Company for missing data
        for company_prop, lead_prop in COMPANY_FALLBACK_MAPPING.items():
            if lead_prop not in updates:
                value = company_props.get(company_prop)
                if value:
                    current_value = lead_props.get(lead_prop)
                    if not current_value or current_value.strip() == "":
                        # Special handling for employee count → size bucket
                        if company_prop == "numberofemployees":
                            mapped_size = self.map_company_size(value)
                            if mapped_size:
                                updates[lead_prop] = mapped_size
                        else:
                            updates[lead_prop] = value

        if not updates:
            return False, "No new data to sync"

        # Update the Lead
        if self.update_lead(lead_id, updates):
            return True, f"Updated {len(updates)} properties"
        else:
            return False, "Update failed"

    def run(self, dry_run=False):
        """Run the sync for all Leads"""
        print("\n" + "=" * 70)
        print("SYNC CONTACT PROPERTIES TO LEADS")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if dry_run:
            print("MODE: DRY RUN (no changes will be made)")

        # Fetch all Leads
        print("\nFetching all Leads...")
        leads = self.get_all_leads()
        print(f"Found {len(leads)} Leads")

        if not leads:
            print("No Leads to process")
            return

        # Process each Lead
        print("\n" + "-" * 70)
        print("SYNCING LEADS")
        print("-" * 70)

        for idx, lead in enumerate(leads, 1):
            lead_id = lead["id"]
            lead_name = lead.get("properties", {}).get("hs_lead_name", "Unknown")

            self.stats["leads_processed"] += 1

            if idx % 10 == 0 or idx == len(leads):
                print(f"\nProgress: {idx}/{len(leads)}")

            success, message = self.sync_lead(lead)

            if success:
                self.stats["leads_updated"] += 1
                print(f"  ✓ {lead_name}: {message}")

                if dry_run:
                    print(f"    (DRY RUN - no actual update)")
            else:
                if "No new data" in message or "No associated" in message:
                    self.stats["leads_skipped"] += 1
                else:
                    self.stats["errors"] += 1
                    print(f"  ✗ {lead_name}: {message}")

            time.sleep(0.2)  # Rate limiting

        # Summary
        print("\n" + "=" * 70)
        print("SYNC COMPLETE")
        print("=" * 70)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nSummary:")
        print(f"  Leads processed: {self.stats['leads_processed']}")
        print(f"  Leads updated:   {self.stats['leads_updated']}")
        print(f"  Leads skipped:   {self.stats['leads_skipped']} (no new data or no contact)")
        print(f"  Errors:          {self.stats['errors']}")


def main():
    import sys

    dry_run = "--dry-run" in sys.argv

    sync = ContactToLeadSync()
    sync.run(dry_run=dry_run)


if __name__ == "__main__":
    main()
