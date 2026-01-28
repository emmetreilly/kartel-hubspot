#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== BATCH 4: UPDATE LIST FILTERS ==="
echo ""

# Update Investors list (ID: 144)
echo "1. Updating Investors list filter..."
curl -s -X PUT "$BASE/crm/v3/lists/144" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
    print('  ✓ Updated')
else:
    print(f'  Response: {d}')
"

# Update Advisors list (ID: 145)
echo "2. Updating Advisors list filter..."
curl -s -X PUT "$BASE/crm/v3/lists/145" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
    print('  ✓ Updated')
else:
    print(f'  Response: {d}')
"

# Update Partners list (ID: 146)
echo "3. Updating Partners list filter..."
curl -s -X PUT "$BASE/crm/v3/lists/146" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
    print('  ✓ Updated')
else:
    print(f'  Response: {d}')
"

# Update Past Clients list (ID: 147)
echo "4. Updating Past Clients list filter..."
curl -s -X PUT "$BASE/crm/v3/lists/147" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
    print('  ✓ Updated')
else:
    print(f'  Response: {d}')
"

echo ""
echo "=== BATCH 4 COMPLETE ==="
