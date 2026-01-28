#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== CREATING DATE-BASED WORKFLOWS ==="
echo ""

# Phase III 30-Day Alert using simpler date filter
echo "1. Creating Phase III 30-Day Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Phase III Start - 30 Day Alert",
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
              "operator": "IS_BETWEEN",
              "lowerBoundTimePoint": {"timeType": "RELATIVE", "zoneId": "America/Los_Angeles", "offset": {"amount": 25, "timeUnit": "DAY", "timeDirection": "FORWARD"}},
              "upperBoundTimePoint": {"timeType": "RELATIVE", "zoneId": "America/Los_Angeles", "offset": {"amount": 35, "timeUnit": "DAY", "timeDirection": "FORWARD"}},
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:300])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# Renewal 30-Day Alert
echo "2. Creating Renewal 30-Day Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Renewal Decision - 30 Day Alert",
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
              "operator": "IS_BETWEEN",
              "lowerBoundTimePoint": {"timeType": "RELATIVE", "zoneId": "America/Los_Angeles", "offset": {"amount": 25, "timeUnit": "DAY", "timeDirection": "FORWARD"}},
              "upperBoundTimePoint": {"timeType": "RELATIVE", "zoneId": "America/Los_Angeles", "offset": {"amount": 35, "timeUnit": "DAY", "timeDirection": "FORWARD"}},
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:300])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

# Payment Due Alert - simpler version
echo "3. Creating Payment Due Alert workflow..."
curl -s -X POST "$BASE/automation/v4/flows" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Payment Expected - Follow Up",
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
        "subject": "Payment expected - follow up on invoice",
        "body": "Payment was expected based on Net 30 terms. Check if payment has been received, and if not, follow up with the client.",
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
              "operationType": "TIME_RANGED",
              "operator": "IS_BETWEEN",
              "lowerBoundTimePoint": {"timeType": "RELATIVE", "zoneId": "America/Los_Angeles", "offset": {"amount": 0, "timeUnit": "DAY", "timeDirection": "BACKWARD"}},
              "upperBoundTimePoint": {"timeType": "RELATIVE", "zoneId": "America/Los_Angeles", "offset": {"amount": 3, "timeUnit": "DAY", "timeDirection": "FORWARD"}},
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
        print(f'  ✗ Error: {d.get(\"message\", str(d)[:300])}')
except Exception as e:
    print(f'  ✗ Parse error: {e}')
"

echo ""
echo "=== DATE-BASED WORKFLOWS COMPLETE ==="
