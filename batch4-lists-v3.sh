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
      "filterBranchType": "OR",
      "filterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "contact_designation",
          "operation": {
            "operationType": "ENUMERATION",
            "operator": "IS_ANY_OF",
            "values": ["investor"]
          }
        }]
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", \"Unknown error\")}')
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
      "filterBranchType": "OR",
      "filterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "contact_designation",
          "operation": {
            "operationType": "ENUMERATION",
            "operator": "IS_ANY_OF",
            "values": ["advisor"]
          }
        }]
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", \"Unknown error\")}')
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
      "filterBranchType": "OR",
      "filterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "contact_designation",
          "operation": {
            "operationType": "ENUMERATION",
            "operator": "IS_ANY_OF",
            "values": ["partner"]
          }
        }]
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", \"Unknown error\")}')
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
      "filterBranchType": "OR",
      "filterBranches": [{
        "filterBranchType": "AND",
        "filters": [{
          "filterType": "PROPERTY",
          "property": "contact_designation",
          "operation": {
            "operationType": "ENUMERATION",
            "operator": "IS_ANY_OF",
            "values": ["past_client"]
          }
        }]
      }]
    }
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'listId' in d:
    print(f'  ✓ Created (ID: {d[\"listId\"]})')
else:
    print(f'  ✗ Error: {d.get(\"message\", \"Unknown error\")}')
"

echo ""
echo "=== BATCH 4 COMPLETE ==="
