#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

# Pipeline IDs
ENTERPRISE="1880222397"
SMB="1880222398"
CLIENT_DELIVERY="1880222399"
REENGAGEMENT="1880222400"

# Enterprise Stage IDs
ENT_DISCOVERY="2978915058"
ENT_PRODUCT_SCOPE="2978915059"
ENT_BUDGET_SCOPE="2978915060"
ENT_PROPOSAL="2978915061"
ENT_NEGOTIATION="2978915062"
ENT_PROCUREMENT="2978915063"
ENT_CLOSED_WON="2978915064"

# Client Delivery Stage IDs (get these first)
echo "Getting Client Delivery stage IDs..."
curl -s "$BASE/crm/v3/pipelines/deals/$CLIENT_DELIVERY" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d.get('stages', []):
    print(f'{s[\"label\"]}: {s[\"id\"]}')
"

echo ""
echo "=== CREATING TASK-BASED WORKFLOWS ==="
echo ""

# 4.4 Go/No-Go Rule (spec delivered + budget_scope > 5 days)
echo "1. Creating Go/No-Go Rule Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Go/No-Go Rule: Spec Delivered in Budget Scope",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": false,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-3",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "task_type": "TODO",
        "subject": "GO/NO-GO: Spec delivered - move to Proposal or close deal",
        "body": "Spec has been delivered and deal is still in Budget Scope. Force a decision within 5 business days: either move to Proposal with verbal yes, or close as lost.",
        "associations": [{"target": {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}, "value": {"type": "ENROLLED_OBJECT"}}],
        "use_explicit_associations": "true",
        "owner_assignment": {"value": {"propertyName": "hubspot_owner_id", "type": "OBJECT_PROPERTY"}, "type": "CUSTOM"},
        "priority": "HIGH",
        "due_time": {"delta": 5, "timeUnit": "DAYS", "timeOfDay": {"hour": 9, "minute": 0}, "daysOfWeek": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]}
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": false,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "dealstage",
            "operation": {
              "operationType": "ENUMERATION",
              "operator": "IS_ANY_OF",
              "values": ["'$ENT_BUDGET_SCOPE'"],
              "includeObjectsWithNoValueSet": false
            }
          },{
            "filterType": "PROPERTY",
            "property": "pipeline",
            "operation": {
              "operationType": "ENUMERATION",
              "operator": "IS_ANY_OF",
              "values": ["'$ENTERPRISE'"],
              "includeObjectsWithNoValueSet": false
            }
          },{
            "filterType": "PROPERTY",
            "property": "spec_required",
            "operation": {
              "operationType": "ENUMERATION",
              "operator": "IS_ANY_OF",
              "values": ["delivered"],
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      }
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:200])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# 4.5 Payment Due Alert
echo "2. Creating Payment Due Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Payment Due Today - Follow Up",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": false,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-3",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "task_type": "TODO",
        "subject": "Payment expected today - follow up on invoice",
        "body": "Payment was expected today based on Net 30 terms. Check if payment has been received, and if not, follow up with the client.",
        "associations": [{"target": {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}, "value": {"type": "ENROLLED_OBJECT"}}],
        "use_explicit_associations": "true",
        "owner_assignment": {"value": {"propertyName": "hubspot_owner_id", "type": "OBJECT_PROPERTY"}, "type": "CUSTOM"},
        "priority": "HIGH",
        "due_time": {"delta": 0, "timeUnit": "DAYS", "timeOfDay": {"hour": 10, "minute": 0}, "daysOfWeek": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]}
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": false,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "payment_expected_date",
            "operation": {
              "operationType": "TIME_POINT",
              "operator": "IS_EQUAL_TO",
              "timestamp": 0,
              "timestampType": "TODAY",
              "includeObjectsWithNoValueSet": false
            }
          },{
            "filterType": "PROPERTY",
            "property": "payment_received_date",
            "operation": {
              "operationType": "ALL_PROPERTY",
              "operator": "HAS_NEVER_BEEN_SET_ANY_VALUE",
              "includeObjectsWithNoValueSet": true
            }
          }]
        }]
      }
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:200])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# 4.6 Phase III Start 30-Day Alert
echo "3. Creating Phase III 30-Day Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Phase III Start in 30 Days",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": false,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-3",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "task_type": "TODO",
        "subject": "Phase III starts in 30 days - confirm commitment",
        "body": "Client is approaching Phase III commitment date. Confirm they are ready to proceed with the 12-month retainer.",
        "associations": [{"target": {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}, "value": {"type": "ENROLLED_OBJECT"}}],
        "use_explicit_associations": "true",
        "owner_assignment": {"value": {"propertyName": "hubspot_owner_id", "type": "OBJECT_PROPERTY"}, "type": "CUSTOM"},
        "priority": "MEDIUM",
        "due_time": {"delta": 1, "timeUnit": "DAYS", "timeOfDay": {"hour": 9, "minute": 0}, "daysOfWeek": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]}
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": false,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "phase_3_start_date",
            "operation": {
              "operationType": "TIME_RANGED",
              "operator": "IS_WITHIN",
              "lowerBoundEndpointBehavior": "INCLUSIVE",
              "upperBoundEndpointBehavior": "INCLUSIVE",
              "lowerBoundOffset": {"amount": 29, "timeUnit": "DAY", "timeDirection": "FORWARD"},
              "upperBoundOffset": {"amount": 31, "timeUnit": "DAY", "timeDirection": "FORWARD"},
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      }
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:200])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# 4.6 Renewal Date 30-Day Alert
echo "4. Creating Renewal 30-Day Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Renewal Decision in 30 Days",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": false,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-3",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "task_type": "TODO",
        "subject": "Renewal decision needed in 30 days",
        "body": "Client renewal decision is due in 30 days. Schedule renewal conversation and assess expansion opportunities.",
        "associations": [{"target": {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}, "value": {"type": "ENROLLED_OBJECT"}}],
        "use_explicit_associations": "true",
        "owner_assignment": {"value": {"propertyName": "hubspot_owner_id", "type": "OBJECT_PROPERTY"}, "type": "CUSTOM"},
        "priority": "HIGH",
        "due_time": {"delta": 1, "timeUnit": "DAYS", "timeOfDay": {"hour": 9, "minute": 0}, "daysOfWeek": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]}
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": false,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "renewal_date",
            "operation": {
              "operationType": "TIME_RANGED",
              "operator": "IS_WITHIN",
              "lowerBoundEndpointBehavior": "INCLUSIVE",
              "upperBoundEndpointBehavior": "INCLUSIVE",
              "lowerBoundOffset": {"amount": 29, "timeUnit": "DAY", "timeDirection": "FORWARD"},
              "upperBoundOffset": {"amount": 31, "timeUnit": "DAY", "timeDirection": "FORWARD"},
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      }
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:200])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# 4.7 Re-engagement Trigger - Phase III Active
echo "5. Creating Re-engagement Check (Phase III Active) workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Re-engagement Check: Phase III Active",
    "objectTypeId": "0-3",
    "flowType": "WORKFLOW",
    "isEnabled": false,
    "type": "PLATFORM_FLOW",
    "startActionId": "1",
    "nextAvailableActionId": "2",
    "actions": [{
      "actionId": "1",
      "actionTypeVersion": 0,
      "actionTypeId": "0-3",
      "type": "SINGLE_CONNECTION",
      "fields": {
        "task_type": "TODO",
        "subject": "Review client for expansion opportunity",
        "body": "Client has entered Phase III Active Retainer. Review account for upsell/expansion opportunities and schedule strategic review.",
        "associations": [{"target": {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 216}, "value": {"type": "ENROLLED_OBJECT"}}],
        "use_explicit_associations": "true",
        "owner_assignment": {"value": {"propertyName": "hubspot_owner_id", "type": "OBJECT_PROPERTY"}, "type": "CUSTOM"},
        "priority": "MEDIUM",
        "due_time": {"delta": 7, "timeUnit": "DAYS", "timeOfDay": {"hour": 9, "minute": 0}, "daysOfWeek": ["MONDAY","TUESDAY","WEDNESDAY","THURSDAY","FRIDAY"]}
      }
    }],
    "enrollmentCriteria": {
      "shouldReEnroll": false,
      "type": "LIST_BASED",
      "unEnrollObjectsNotMeetingCriteria": false,
      "listFilterBranch": {
        "filterBranchType": "OR",
        "filterBranches": [{
          "filterBranchType": "AND",
          "filters": [{
            "filterType": "PROPERTY",
            "property": "pipeline",
            "operation": {
              "operationType": "ENUMERATION",
              "operator": "IS_ANY_OF",
              "values": ["'$CLIENT_DELIVERY'"],
              "includeObjectsWithNoValueSet": false
            }
          }]
        }]
      }
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:200])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

echo ""
echo "=== WORKFLOWS COMPLETE ==="
echo ""
echo "Note: All workflows created in DISABLED state."
echo "Enable them in HubSpot UI after reviewing enrollment criteria."
