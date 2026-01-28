#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== CURRENT DEALS ==="
curl -s -X POST "$BASE/crm/v3/objects/deals/search" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "filterGroups": [],
    "properties": ["dealname", "dealstage", "pipeline", "amount"],
    "limit": 100
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
deals = d.get('results', [])
print(f'Found {len(deals)} deals:\n')
for deal in sorted(deals, key=lambda x: x.get('properties', {}).get('dealname', '')):
    props = deal.get('properties', {})
    name = props.get('dealname', 'Unknown')
    stage = props.get('dealstage', 'Unknown')
    pipeline = props.get('pipeline', 'Unknown')
    amount = props.get('amount', 'N/A')
    print(f'ID: {deal[\"id\"]} | {name} | Stage: {stage} | Pipeline: {pipeline} | Amount: {amount}')
"
