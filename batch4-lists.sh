#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== BATCH 4: CONTACT SEGMENT LISTS ==="
echo ""

# Create Investors list
echo "1. Creating Investors list..."
curl -s -X POST "$BASE/crm/v3/lists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objectTypeId": "0-1",
    "processingType": "DYNAMIC",
    "name": "Investors",
    "filterBranch": {
      "filterBranchType": "AND",
      "filters": [{
        "filterType": "PROPERTY",
        "property": "contact_designation",
        "operation": {
          "operationType": "STRING",
          "operator": "IS_EQUAL_TO",
          "value": "investor"
        }
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

# Create Advisors list
echo "2. Creating Advisors list..."
curl -s -X POST "$BASE/crm/v3/lists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objectTypeId": "0-1",
    "processingType": "DYNAMIC",
    "name": "Advisors",
    "filterBranch": {
      "filterBranchType": "AND",
      "filters": [{
        "filterType": "PROPERTY",
        "property": "contact_designation",
        "operation": {
          "operationType": "STRING",
          "operator": "IS_EQUAL_TO",
          "value": "advisor"
        }
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

# Create Partners list
echo "3. Creating Partners list..."
curl -s -X POST "$BASE/crm/v3/lists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objectTypeId": "0-1",
    "processingType": "DYNAMIC",
    "name": "Partners",
    "filterBranch": {
      "filterBranchType": "AND",
      "filters": [{
        "filterType": "PROPERTY",
        "property": "contact_designation",
        "operation": {
          "operationType": "STRING",
          "operator": "IS_EQUAL_TO",
          "value": "partner"
        }
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

# Create Past Clients list
echo "4. Creating Past Clients list..."
curl -s -X POST "$BASE/crm/v3/lists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "objectTypeId": "0-1",
    "processingType": "DYNAMIC",
    "name": "Past Clients",
    "filterBranch": {
      "filterBranchType": "AND",
      "filters": [{
        "filterType": "PROPERTY",
        "property": "contact_designation",
        "operation": {
          "operationType": "STRING",
          "operator": "IS_EQUAL_TO",
          "value": "past_client"
        }
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

echo ""
echo "=== BATCH 4 COMPLETE ==="
