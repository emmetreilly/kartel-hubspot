#!/bin/bash
TOKEN="${HUBSPOT_ACCESS_TOKEN}"
curl -s "https://api.hubapi.com/crm/v3/properties/deals" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
