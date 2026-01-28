#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

# Search for specific deals to migrate
DEALS=("Newell" "Saatchi" "Treefort" "EarnIn" "Horizon" "Marc Jacobs" "Blur Studio" "Team One" "Wheelhouse" "Kargo" "Crispin" "Havas" "Smuggler" "Amazon" "AvantStay" "PriceSmart" "Russo" "Princeton")

echo "=== SEARCHING FOR MIGRATION DEALS ==="
echo ""

for DEAL in "${DEALS[@]}"; do
    echo "Searching: $DEAL"
    curl -s -X POST "$BASE/crm/v3/objects/deals/search" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"filterGroups\": [{
          \"filters\": [{
            \"propertyName\": \"dealname\",
            \"operator\": \"CONTAINS_TOKEN\",
            \"value\": \"$DEAL\"
          }]
        }],
        \"properties\": [\"dealname\", \"dealstage\", \"pipeline\", \"amount\"],
        \"limit\": 5
      }" | python3 -c "
import sys, json
d = json.load(sys.stdin)
deals = d.get('results', [])
if not deals:
    print('  No results found')
else:
    for deal in deals:
        props = deal.get('properties', {})
        name = props.get('dealname', 'Unknown')
        print(f'  ID: {deal[\"id\"]} | {name}')
"
    echo ""
done
