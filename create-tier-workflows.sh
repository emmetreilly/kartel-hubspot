#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== CREATING DEAL TIER AUTO-ASSIGNMENT WORKFLOWS ==="
echo ""

# SMB Tier (amount < $50,000)
echo "1. Creating Deal Tier: SMB (< \$50K)..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-Set Deal Tier: SMB (< $50K)",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": true,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-5",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "property_name": "deal_tier",
        "value": {
          "staticValue": "smb",
          "type": "STATIC_VALUE"
        }
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": true,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
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
              "value": 50000,
              "includeObjectsWithNoValueSet": false
            }
          },{
            "filterType": "PROPERTY",
            "property": "amount",
            "operation": {
              "operationType": "NUMBER",
              "operator": "IS_GREATER_THAN",
              "value": 0,
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      },
      "reEnrollmentTriggersFilterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "hs_name",
          "operation": {
            "operationType": "STRING",
            "operator": "IS_EQUAL_TO",
            "value": "amount",
            "includeObjectsWithNoValueSet": false
          }
        }]
      }]
    },
    "timeWindows": [],
    "blockedDates": [],
    "customProperties": {},
    "dataSources": []
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'id' in d:
        print(f'  ✓ Created (ID: {d[\"id\"]})')
    else:
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:300])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# Mid-Market Tier ($50K - $150K)
echo "2. Creating Deal Tier: Mid-Market (\$50K - \$150K)..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-Set Deal Tier: Mid-Market ($50K-$150K)",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": true,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-5",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "property_name": "deal_tier",
        "value": {
          "staticValue": "mid_market",
          "type": "STATIC_VALUE"
        }
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": true,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
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
              "value": 50000,
              "includeObjectsWithNoValueSet": false
            }
          },{
            "filterType": "PROPERTY",
            "property": "amount",
            "operation": {
              "operationType": "NUMBER",
              "operator": "IS_LESS_THAN",
              "value": 150000,
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      },
      "reEnrollmentTriggersFilterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "hs_name",
          "operation": {
            "operationType": "STRING",
            "operator": "IS_EQUAL_TO",
            "value": "amount",
            "includeObjectsWithNoValueSet": false
          }
        }]
      }]
    },
    "timeWindows": [],
    "blockedDates": [],
    "customProperties": {},
    "dataSources": []
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'id' in d:
        print(f'  ✓ Created (ID: {d[\"id\"]})')
    else:
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:300])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# Enterprise Tier ($250K+)
echo "3. Creating Deal Tier: Enterprise (\$250K+)..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Auto-Set Deal Tier: Enterprise ($250K+)",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": true,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-5",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "property_name": "deal_tier",
        "value": {
          "staticValue": "enterprise",
          "type": "STATIC_VALUE"
        }
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": true,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
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
              "value": 250000,
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      },
      "reEnrollmentTriggersFilterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "hs_name",
          "operation": {
            "operationType": "STRING",
            "operator": "IS_EQUAL_TO",
            "value": "amount",
            "includeObjectsWithNoValueSet": false
          }
        }]
      }]
    },
    "timeWindows": [],
    "blockedDates": [],
    "customProperties": {},
    "dataSources": []
  }' | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if 'id' in d:
        print(f'  ✓ Created (ID: {d[\"id\"]})')
    else:
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:300])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

echo ""
echo "=== DEAL TIER WORKFLOWS COMPLETE ==="
