#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== ENTERPRISE PIPELINE STAGES ==="
curl -s "$BASE/crm/v3/pipelines/deals/1880222397" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d.get('stages', []):
    print(f'{s[\"label\"]}: {s[\"id\"]}')
"

echo ""
echo "=== SMB PIPELINE STAGES ==="
curl -s "$BASE/crm/v3/pipelines/deals/1880222398" \
  -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d.get('stages', []):
    print(f'{s[\"label\"]}: {s[\"id\"]}')
"
