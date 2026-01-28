#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
BASE="https://api.hubapi.com"

# Pipeline IDs
ENTERPRISE_PIPELINE="1880222397"
SMB_PIPELINE="1880222398"

# Enterprise Stage IDs
DISCOVERY="2978915058"
PRODUCT_SCOPE="2978915059"
BUDGET_SCOPE="2978915060"
PROPOSAL="2978915061"
NEGOTIATION="2978915062"
PROCUREMENT="2978915063"

# SMB Stage IDs
SCOPING="2978916026"

echo "=== BATCH 3: DEAL MIGRATION ==="
echo ""
echo "Moving deals to Enterprise Pipeline (ID: $ENTERPRISE_PIPELINE)"
echo ""

# Function to migrate a deal
migrate_deal() {
    local DEAL_ID=$1
    local DEAL_NAME=$2
    local PIPELINE=$3
    local STAGE=$4
    local STAGE_NAME=$5

    echo "Migrating: $DEAL_NAME → $STAGE_NAME"
    curl -s -X PATCH "$BASE/crm/v3/objects/deals/$DEAL_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"properties\": {
          \"pipeline\": \"$PIPELINE\",
          \"dealstage\": \"$STAGE\"
        }
      }" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'id' in d:
    print('  ✓ Success')
else:
    print(f'  ✗ Error: {d.get(\"message\", d)}')
"
}

# Enterprise Pipeline Migrations
echo "--- Enterprise Pipeline ---"
migrate_deal "238644740816" "Newell" "$ENTERPRISE_PIPELINE" "$PROCUREMENT" "Procurement"
migrate_deal "156586259177" "Saatchi (Toyota)" "$ENTERPRISE_PIPELINE" "$PRODUCT_SCOPE" "Product Scope"
migrate_deal "269512003303" "Treefort Media" "$ENTERPRISE_PIPELINE" "$BUDGET_SCOPE" "Budget Scope"
migrate_deal "267448910574" "EarnIn - New Deal" "$ENTERPRISE_PIPELINE" "$PRODUCT_SCOPE" "Product Scope"
migrate_deal "258119715525" "Horizon Media" "$ENTERPRISE_PIPELINE" "$PRODUCT_SCOPE" "Product Scope"
migrate_deal "264081845953" "Marc Jacobs - New Deal" "$ENTERPRISE_PIPELINE" "$PROPOSAL" "Proposal"
migrate_deal "275504255704" "Blur Studio" "$ENTERPRISE_PIPELINE" "$DISCOVERY" "Discovery"
migrate_deal "275296605929" "Team One - New Deal" "$ENTERPRISE_PIPELINE" "$BUDGET_SCOPE" "Budget Scope"
migrate_deal "222208972517" "Wheelhouse Entertainment" "$ENTERPRISE_PIPELINE" "$PROPOSAL" "Proposal"
migrate_deal "232556695258" "Kargo (Agency)" "$ENTERPRISE_PIPELINE" "$PRODUCT_SCOPE" "Product Scope"
migrate_deal "241531026162" "Crispin (Agency)" "$ENTERPRISE_PIPELINE" "$BUDGET_SCOPE" "Budget Scope"
migrate_deal "240440333003" "Havas" "$ENTERPRISE_PIPELINE" "$PROPOSAL" "Proposal"
migrate_deal "268019930834" "Smuggler" "$ENTERPRISE_PIPELINE" "$DISCOVERY" "Discovery"
migrate_deal "240974350026" "Amazon (Internal)" "$ENTERPRISE_PIPELINE" "$DISCOVERY" "Discovery"
migrate_deal "260427287257" "AvantStay - New Deal" "$ENTERPRISE_PIPELINE" "$DISCOVERY" "Discovery"

echo ""
echo "--- SMB Pipeline ---"
migrate_deal "262436627162" "PriceSmart - New Deal" "$SMB_PIPELINE" "$SCOPING" "Scoping"
migrate_deal "256773059272" "Russo Development" "$SMB_PIPELINE" "$SCOPING" "Scoping"
migrate_deal "203472612062" "Princeton Nurseries" "$SMB_PIPELINE" "$SCOPING" "Scoping"

echo ""
echo "=== MIGRATION COMPLETE ==="
