#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"

echo "=== DEAL PROPERTIES ==="
curl -s "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('results', []):
    print(f\"{p['name']}: {p['type']} - {p.get('label', 'N/A')}\")
" | sort

echo ""
echo "=== PIPELINES ==="
curl -s "https://api.hubapi.com/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('results', []):
    print(f\"Pipeline: {p['label']} (ID: {p['id']})\")
    for s in p.get('stages', []):
        print(f\"  - {s['label']} ({s.get('metadata', {}).get('probability', 'N/A')})\")
"
