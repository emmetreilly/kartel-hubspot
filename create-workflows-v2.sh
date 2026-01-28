#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== CREATING WORKFLOWS ==="
echo ""

# Create a task-based workflow for procurement overdue alert
echo "1. Creating Procurement Overdue Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Procurement Overdue (30+ Days)",
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
        "subject": "ALERT: Deal in Procurement 30+ days - Follow up needed",
        "body": "This deal has been in Procurement stage for more than 30 days. Please follow up on signature status.",
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
            "property": "dealstage",
            "operation": {
              "operationType": "ENUMERATION",
              "operator": "IS_ANY_OF",
              "values": ["2978915063"],
              "includeObjectsWithNoValueSet": false
            }
          },{
            "filterType": "PROPERTY",
            "property": "pipeline",
            "operation": {
              "operationType": "ENUMERATION",
              "operator": "IS_ANY_OF",
              "values": ["1880222397"],
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
        print(f'  Response: {json.dumps(d, indent=2)[:500]}')
except Exception as e:
    print(f'  ✗ Error: {e}')
"

echo ""
echo "=== DONE ==="
