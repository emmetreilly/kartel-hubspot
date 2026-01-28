#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

echo "=== BATCH 1: DEAL PROPERTIES ==="
echo ""

# 1. Update msa_status - add in_review and signed options
echo "1. Updating msa_status options..."
curl -s -X PATCH "$BASE/crm/v3/properties/deals/msa_status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "options": [
      {"label": "Not Sent", "value": "not_sent", "displayOrder": 1, "hidden": false},
      {"label": "Sent (Day 0)", "value": "sent", "displayOrder": 2, "hidden": false},
      {"label": "In Legal Review", "value": "in_review", "displayOrder": 3, "hidden": false},
      {"label": "Signed", "value": "signed", "displayOrder": 4, "hidden": false}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ msa_status updated' if 'name' in d else f'  ✗ Error: {d}')"

# 2. Update dealtype - add expansion and renewal options
echo "2. Updating dealtype options..."
curl -s -X PATCH "$BASE/crm/v3/properties/deals/dealtype" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "options": [
      {"label": "New Business", "value": "newbusiness", "displayOrder": 1, "hidden": false},
      {"label": "Existing Business", "value": "existingbusiness", "displayOrder": 2, "hidden": false},
      {"label": "Expansion", "value": "expansion", "displayOrder": 3, "hidden": false},
      {"label": "Renewal", "value": "renewal", "displayOrder": 4, "hidden": false},
      {"label": "Re-engagement", "value": "re_engagement", "displayOrder": 5, "hidden": false}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ dealtype updated' if 'name' in d else f'  ✗ Error: {d}')"

# 3. Update business_vertical (Client Type)
echo "3. Updating business_vertical (Client Type)..."
curl -s -X PATCH "$BASE/crm/v3/properties/deals/business_vertical" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "Client Type",
    "options": [
      {"label": "Agency", "value": "agency", "displayOrder": 1, "hidden": false},
      {"label": "Brand", "value": "brand", "displayOrder": 2, "hidden": false},
      {"label": "Production Company", "value": "production_company", "displayOrder": 3, "hidden": false},
      {"label": "Real Estate", "value": "real_estate", "displayOrder": 4, "hidden": false}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ business_vertical updated' if 'name' in d else f'  ✗ Error: {d}')"

# 4. Update deal_category (Creative Deliverable)
echo "4. Updating deal_category (Creative Deliverable)..."
curl -s -X PATCH "$BASE/crm/v3/properties/deals/deal_category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "options": [
      {"label": "Production Assets", "value": "production_assets", "displayOrder": 1, "hidden": false},
      {"label": "Social Content", "value": "social_content", "displayOrder": 2, "hidden": false},
      {"label": "Campaign Assets", "value": "campaign_assets", "displayOrder": 3, "hidden": false},
      {"label": "Spec / Development", "value": "spec_development", "displayOrder": 4, "hidden": false}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ deal_category updated' if 'name' in d else f'  ✗ Error: {d}')"

# 5. Update deal_tier
echo "5. Updating deal_tier options..."
curl -s -X PATCH "$BASE/crm/v3/properties/deals/deal_tier" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "options": [
      {"label": "SMB ($0-50K)", "value": "smb", "displayOrder": 1, "hidden": false},
      {"label": "Mid-Market ($50K-150K)", "value": "mid_market", "displayOrder": 2, "hidden": false},
      {"label": "Enterprise ($250K+)", "value": "enterprise", "displayOrder": 3, "hidden": false}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ deal_tier updated' if 'name' in d else f'  ✗ Error: {d}')"

echo ""
echo "=== CREATING NEW PROPERTIES ==="
echo ""

# 6. Create champion (text)
echo "6. Creating champion property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "champion",
    "label": "Champion",
    "type": "string",
    "fieldType": "text",
    "groupName": "dealinformation",
    "description": "Name + title (e.g., Jimmy Jia - VP Brand)"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ champion created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 7. Create spec_required (enum)
echo "7. Creating spec_required property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "spec_required",
    "label": "Spec Required",
    "type": "enumeration",
    "fieldType": "select",
    "groupName": "dealinformation",
    "options": [
      {"label": "Yes", "value": "yes", "displayOrder": 1},
      {"label": "No", "value": "no", "displayOrder": 2},
      {"label": "In Progress", "value": "in_progress", "displayOrder": 3},
      {"label": "Delivered", "value": "delivered", "displayOrder": 4}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ spec_required created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 8. Create sow_signed_date (date)
echo "8. Creating sow_signed_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "sow_signed_date",
    "label": "SOW Signed Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ sow_signed_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 9. Create procurement_start_date (date)
echo "9. Creating procurement_start_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "procurement_start_date",
    "label": "Procurement Start Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ procurement_start_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 10. Create procurement_complete_date (date)
echo "10. Creating procurement_complete_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "procurement_complete_date",
    "label": "Procurement Complete Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation",
    "description": "Expected: SOW signed + 30 days"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ procurement_complete_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 11. Create work_start_date (date)
echo "11. Creating work_start_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "work_start_date",
    "label": "Work Start Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ work_start_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 12. Create payment_expected_date (date)
echo "12. Creating payment_expected_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "payment_expected_date",
    "label": "Payment Expected Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation",
    "description": "Invoice date + 30 days (Net 30)"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ payment_expected_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 13. Create days_in_procurement (number)
echo "13. Creating days_in_procurement property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "days_in_procurement",
    "label": "Days in Procurement",
    "type": "number",
    "fieldType": "number",
    "groupName": "dealinformation",
    "description": "Calculated: today - procurement_start_date"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ days_in_procurement created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 14. Create phase_3_start_date (date)
echo "14. Creating phase_3_start_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "phase_3_start_date",
    "label": "Phase III Start Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation",
    "description": "Date Phase III retainer begins (12-month commitment)"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ phase_3_start_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 15. Create contract_end_date (date)
echo "15. Creating contract_end_date property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "contract_end_date",
    "label": "Contract End Date",
    "type": "date",
    "fieldType": "date",
    "groupName": "dealinformation",
    "description": "Phase III start + 12 months"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ contract_end_date created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 16. Create termination_eligible (enum)
echo "16. Creating termination_eligible property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "termination_eligible",
    "label": "Termination Eligible",
    "type": "enumeration",
    "fieldType": "select",
    "groupName": "dealinformation",
    "options": [
      {"label": "Yes (Pre-Phase III)", "value": "yes", "displayOrder": 1},
      {"label": "No (Phase III Active)", "value": "no", "displayOrder": 2}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ termination_eligible created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 17. Create msa_link (text)
echo "17. Creating msa_link property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "msa_link",
    "label": "MSA Link",
    "type": "string",
    "fieldType": "text",
    "groupName": "dealinformation"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ msa_link created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

# 18. Create deck_link (text)
echo "18. Creating deck_link property..."
curl -s -X POST "$BASE/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "deck_link",
    "label": "Pitch Deck Link",
    "type": "string",
    "fieldType": "text",
    "groupName": "dealinformation"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ deck_link created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

echo ""
echo "=== CONTACT PROPERTY ==="
echo ""

# 19. Create contact_designation (contact property)
echo "19. Creating contact_designation property..."
curl -s -X POST "$BASE/crm/v3/properties/contacts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "contact_designation",
    "label": "Contact Designation",
    "type": "enumeration",
    "fieldType": "select",
    "groupName": "contactinformation",
    "options": [
      {"label": "Standard Contact", "value": "standard", "displayOrder": 1},
      {"label": "Investor", "value": "investor", "displayOrder": 2},
      {"label": "Advisor", "value": "advisor", "displayOrder": 3},
      {"label": "Partner", "value": "partner", "displayOrder": 4},
      {"label": "Past Client", "value": "past_client", "displayOrder": 5}
    ]
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print('  ✓ contact_designation created' if 'name' in d else f'  ✗ Error: {d.get(\"message\", d)}')"

echo ""
echo "=== BATCH 1 COMPLETE ==="
