#!/usr/bin/env python3
import requests
import json

import os
TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")
BASE = "https://api.hubapi.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Test what reporting endpoints exist
endpoints_to_test = [
    ("GET", "/crm/v3/objects/deals", "Deals"),
    ("GET", "/analytics/v2/reports", "Analytics Reports"),
    ("GET", "/crm/v3/properties/deals", "Deal Properties"),
    ("POST", "/crm/v3/objects/deals/search", "Deal Search"),
    ("GET", "/crm-pipelines/v1/pipelines/deals", "Pipelines v1"),
    ("GET", "/reporting/v1/reports", "Reporting v1"),
    ("GET", "/reporting-api/v1/reports", "Reporting API v1"),
]

print("=== Testing HubSpot API Endpoints ===\n")

for method, endpoint, name in endpoints_to_test:
    url = BASE + endpoint
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, timeout=10)
        else:
            r = requests.post(url, headers=HEADERS, json={"limit": 1}, timeout=10)

        status = r.status_code
        if status == 200:
            print(f"✓ {name}: OK (200)")
        elif status == 404:
            print(f"✗ {name}: Not Found (404)")
        elif status == 401 or status == 403:
            print(f"⚠ {name}: Auth/Permission issue ({status})")
        else:
            print(f"? {name}: {status}")
    except Exception as e:
        print(f"✗ {name}: Error - {e}")

print("\n=== Checking for Custom Object / Report Creation ===\n")

# Try to find report creation endpoint
test_endpoints = [
    "/reports/v3/reports",
    "/reporting/v3/reports",
    "/cms/v3/reports",
    "/crm/v3/extensions/reports",
]

for endpoint in test_endpoints:
    url = BASE + endpoint
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.status_code != 404:
        print(f"Found: {endpoint} - Status: {r.status_code}")
        print(f"  Response: {r.text[:200]}")
