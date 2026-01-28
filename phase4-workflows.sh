#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== PHASE 4: WORKFLOWS ==="
echo ""

# Note: HubSpot Workflows API (v4) requires specific scopes
# Let's first check what automation capabilities are available

echo "Checking automation API access..."
curl -s "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | head -c 500

echo ""
echo ""

# 4.1 Deal Tier Auto-Assignment Workflow
echo "Creating Deal Tier Auto-Assignment workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Deal Tier Auto-Assignment",
    "type": "WORKFLOW",
    "objectTypeId": "0-3",
    "enrollmentTrigger": {
      "type": "PROPERTY_CHANGE",
      "filterGroups": [{
        "filters": [{
          "property": "amount",
          "operator": "HAS_PROPERTY"
        }]
      }]
    },
    "actions": []
  }' 2>&1

echo ""
