#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== CREATING WORKFLOWS ==="
echo ""

# 4.1 Deal Tier Auto-Assignment (SMB < $50K)
echo "1. Creating Deal Tier: SMB workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-Set Deal Tier: SMB",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": true,
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeId": "0-5",
      "actionTypeVersion": 0,
      "type": "SINGLE_CONNECTION",
      "fields": {
        "property": "deal_tier",
        "value": "smb"
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": true,
      "type": "LIST_BASED",
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "amount",
            "operation": {
              "operationType": "NUMBER",
              "operator": "IS_LESS_THAN",
              "value": 50000
            }
          }]
        }]
      }
    }
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'id' in d:
        print(f'  ✓ Created (ID: {d[\"id\"]})')
    else:
        print(f'  ✗ Error: {d.get(\"message\", d)}')
except:
    print('  ✗ Failed to parse response')
"

# 4.1b Deal Tier Auto-Assignment (Mid-Market $50K-$150K)
echo "2. Creating Deal Tier: Mid-Market workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-Set Deal Tier: Mid-Market",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": true,
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeId": "0-5",
      "actionTypeVersion": 0,
      "type": "SINGLE_CONNECTION",
      "fields": {
        "property": "deal_tier",
        "value": "mid_market"
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": true,
      "type": "LIST_BASED",
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "amount",
            "operation": {
              "operationType": "NUMBER",
              "operator": "IS_GREATER_THAN_OR_EQUAL_TO",
              "value": 50000
            }
          },{
            "filterType": "PROPERTY",
            "property": "amount",
            "operation": {
              "operationType": "NUMBER",
              "operator": "IS_LESS_THAN",
              "value": 150000
            }
          }]
        }]
      }
    }
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'id' in d:
        print(f'  ✓ Created (ID: {d[\"id\"]})')
    else:
        print(f'  ✗ Error: {d.get(\"message\", d)}')
except:
    print('  ✗ Failed to parse response')
"

# 4.1c Deal Tier Auto-Assignment (Enterprise $250K+)
echo "3. Creating Deal Tier: Enterprise workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-Set Deal Tier: Enterprise",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": true,
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeId": "0-5",
      "actionTypeVersion": 0,
      "type": "SINGLE_CONNECTION",
      "fields": {
        "property": "deal_tier",
        "value": "enterprise"
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": true,
      "type": "LIST_BASED",
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "amount",
            "operation": {
              "operationType": "NUMBER",
              "operator": "IS_GREATER_THAN_OR_EQUAL_TO",
              "value": 250000
            }
          }]
        }]
      }
    }
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'id' in d:
        print(f'  ✓ Created (ID: {d[\"id\"]})')
    else:
        print(f'  ✗ Error: {d.get(\"message\", d)}')
except:
    print('  ✗ Failed to parse response')
"

echo ""
echo "=== WORKFLOWS CREATED ==="
