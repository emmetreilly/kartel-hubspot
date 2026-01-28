#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== BATCH 2: PIPELINES ==="
echo ""

# 1. Create Enterprise Pipeline (8 stages)
echo "1. Creating Enterprise Pipeline (8 stages)..."
curl -s -X POST "$BASE/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Enterprise Pipeline",
    "displayOrder": 1,
    "stages": [
      {"label": "Discovery", "displayOrder": 1, "metadata": {"probability": "0.10"}},
      {"label": "Product Scope", "displayOrder": 2, "metadata": {"probability": "0.20"}},
      {"label": "Budget Scope", "displayOrder": 3, "metadata": {"probability": "0.40"}},
      {"label": "Proposal", "displayOrder": 4, "metadata": {"probability": "0.60"}},
      {"label": "Negotiation", "displayOrder": 5, "metadata": {"probability": "0.75"}},
      {"label": "Procurement", "displayOrder": 6, "metadata": {"probability": "0.90"}},
      {"label": "Closed Won", "displayOrder": 7, "metadata": {"probability": "1.0", "isClosed": "true"}},
      {"label": "Closed Lost", "displayOrder": 8, "metadata": {"probability": "0.0", "isClosed": "true"}}
    ]
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'id' in d:
    print(f'  ✓ Enterprise Pipeline created (ID: {d[\"id\"]})')
    print(f'    Stages: {len(d.get(\"stages\", []))}')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

# 2. Create SMB Pipeline (5 stages)
echo ""
echo "2. Creating SMB Pipeline (5 stages)..."
curl -s -X POST "$BASE/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "SMB Pipeline",
    "displayOrder": 2,
    "stages": [
      {"label": "Scoping", "displayOrder": 1, "metadata": {"probability": "0.20"}},
      {"label": "Proposal Sent", "displayOrder": 2, "metadata": {"probability": "0.50"}},
      {"label": "Negotiation", "displayOrder": 3, "metadata": {"probability": "0.80"}},
      {"label": "Closed Won", "displayOrder": 4, "metadata": {"probability": "1.0", "isClosed": "true"}},
      {"label": "Closed Lost", "displayOrder": 5, "metadata": {"probability": "0.0", "isClosed": "true"}}
    ]
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'id' in d:
    print(f'  ✓ SMB Pipeline created (ID: {d[\"id\"]})')
    print(f'    Stages: {len(d.get(\"stages\", []))}')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

# 3. Create Client Delivery Pipeline (6 stages)
echo ""
echo "3. Creating Client Delivery Pipeline (6 stages)..."
curl -s -X POST "$BASE/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Client Delivery",
    "displayOrder": 3,
    "stages": [
      {"label": "Phase I - Scoping", "displayOrder": 1, "metadata": {"probability": "0.25"}},
      {"label": "Phase II - Build/Test", "displayOrder": 2, "metadata": {"probability": "0.50"}},
      {"label": "Phase III - Pending Start", "displayOrder": 3, "metadata": {"probability": "0.75"}},
      {"label": "Phase III - Active Retainer", "displayOrder": 4, "metadata": {"probability": "1.0"}},
      {"label": "Churned", "displayOrder": 5, "metadata": {"probability": "0.0", "isClosed": "true"}},
      {"label": "Renewed", "displayOrder": 6, "metadata": {"probability": "1.0", "isClosed": "true"}}
    ]
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'id' in d:
    print(f'  ✓ Client Delivery Pipeline created (ID: {d[\"id\"]})')
    print(f'    Stages: {len(d.get(\"stages\", []))}')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

# 4. Create Re-engagement Pipeline (6 stages)
echo ""
echo "4. Creating Re-engagement Pipeline (6 stages)..."
curl -s -X POST "$BASE/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Re-engagement",
    "displayOrder": 4,
    "stages": [
      {"label": "Opportunity Identified", "displayOrder": 1, "metadata": {"probability": "0.10"}},
      {"label": "Outreach", "displayOrder": 2, "metadata": {"probability": "0.25"}},
      {"label": "Qualified", "displayOrder": 3, "metadata": {"probability": "0.50"}},
      {"label": "Scoping New Work", "displayOrder": 4, "metadata": {"probability": "0.75"}},
      {"label": "Converted to Deal", "displayOrder": 5, "metadata": {"probability": "1.0", "isClosed": "true"}},
      {"label": "Not Now", "displayOrder": 6, "metadata": {"probability": "0.0", "isClosed": "true"}}
    ]
  }' | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'id' in d:
    print(f'  ✓ Re-engagement Pipeline created (ID: {d[\"id\"]})')
    print(f'    Stages: {len(d.get(\"stages\", []))}')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"

echo ""
echo "=== BATCH 2 COMPLETE ==="
echo ""

# Verify pipelines
echo "=== VERIFICATION: All Pipelines ==="
curl -s "$BASE/crm/v3/pipelines/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for p in d.get('results', []):
    stages = len(p.get('stages', []))
    print(f'{p[\"label\"]} (ID: {p[\"id\"]}) - {stages} stages')
"
