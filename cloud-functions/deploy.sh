#!/bin/bash
# Deploy Kartel CRM automation to Google Cloud Functions

set -e

PROJECT_ID="kartel-crm-automation"
REGION="us-west1"

echo "=== Deploying Kartel CRM Automation ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Ensure we're using the right project
gcloud config set project $PROJECT_ID

# Deploy daily report function
echo "Deploying daily-report function..."
gcloud functions deploy daily-report \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --trigger-http \
  --entry-point daily_report \
  --timeout 540 \
  --memory 512MB \
  --set-secrets "HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,SENDGRID_API_KEY=SENDGRID_API_KEY:latest,GOOGLE_CREDENTIALS=GOOGLE_CREDENTIALS:latest" \
  --allow-unauthenticated

# Deploy gmail sync function
echo ""
echo "Deploying gmail-sync function..."
gcloud functions deploy gmail-sync \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --trigger-http \
  --entry-point gmail_sync \
  --timeout 540 \
  --memory 512MB \
  --set-secrets "HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,GOOGLE_CREDENTIALS=GOOGLE_CREDENTIALS:latest" \
  --allow-unauthenticated

# Deploy re-engagement deal function (called by HubSpot workflows)
echo ""
echo "Deploying create-reengagement-deal function..."
gcloud functions deploy create-reengagement-deal \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --trigger-http \
  --entry-point create_reengagement_deal \
  --timeout 60 \
  --memory 256MB \
  --set-secrets "HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest" \
  --allow-unauthenticated

# Deploy follow-up task function (called by HubSpot workflows)
echo ""
echo "Deploying create-followup-task function..."
gcloud functions deploy create-followup-task \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --trigger-http \
  --entry-point create_followup_task \
  --timeout 60 \
  --memory 256MB \
  --set-secrets "HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest" \
  --allow-unauthenticated

# Deploy enrich-contact function (enriches contacts, routes, creates leads)
echo ""
echo "Deploying enrich-contact function..."
gcloud functions deploy enrich-contact \
  --gen2 \
  --runtime python311 \
  --region $REGION \
  --source enrich_contact \
  --trigger-http \
  --entry-point enrich_contact \
  --timeout 120 \
  --memory 256MB \
  --set-env-vars "SKIP_PERSONAL_EMAILS=false" \
  --set-secrets "HUBSPOT_ACCESS_TOKEN=HUBSPOT_ACCESS_TOKEN:latest,APOLLO_API_KEY=APOLLO_API_KEY:latest" \
  --allow-unauthenticated

# Get function URLs
echo ""
echo "=== Deployment Complete ==="
DAILY_URL=$(gcloud functions describe daily-report --region $REGION --format='value(serviceConfig.uri)')
SYNC_URL=$(gcloud functions describe gmail-sync --region $REGION --format='value(serviceConfig.uri)')
REENGAGEMENT_URL=$(gcloud functions describe create-reengagement-deal --region $REGION --format='value(serviceConfig.uri)')
FOLLOWUP_URL=$(gcloud functions describe create-followup-task --region $REGION --format='value(serviceConfig.uri)')
ENRICH_URL=$(gcloud functions describe enrich-contact --region $REGION --format='value(serviceConfig.uri)')

echo "Daily Report URL: $DAILY_URL"
echo "Gmail Sync URL: $SYNC_URL"
echo "Re-engagement Deal URL: $REENGAGEMENT_URL"
echo "Follow-up Task URL: $FOLLOWUP_URL"
echo "Enrich Contact URL: $ENRICH_URL"
echo ""
echo "Use these URLs in HubSpot workflows as webhook actions:"
echo "  Budget/Timing (90 days): POST to $REENGAGEMENT_URL"
echo "  Competitor (6 months): POST to $REENGAGEMENT_URL"
echo "  No Response (30 days): POST to $FOLLOWUP_URL"
echo "  New Contact Enrichment: POST to $ENRICH_URL with {\"contact_id\": \"{{contact.hs_object_id}}\", \"email\": \"{{contact.email}}\"}"
echo ""

# Create Cloud Scheduler jobs
echo "Creating Cloud Scheduler jobs..."

# Check if jobs exist and delete them first
gcloud scheduler jobs delete daily-report-job --location $REGION --quiet 2>/dev/null || true
gcloud scheduler jobs delete gmail-sync-job --location $REGION --quiet 2>/dev/null || true

# Daily report at 6am PT
gcloud scheduler jobs create http daily-report-job \
  --location $REGION \
  --schedule "0 6 * * *" \
  --time-zone "America/Los_Angeles" \
  --uri "$DAILY_URL" \
  --http-method POST \
  --description "Daily sales report at 6am PT"

# Gmail sync every 15 min during business hours (9am-6pm PT, weekdays)
gcloud scheduler jobs create http gmail-sync-job \
  --location $REGION \
  --schedule "*/15 9-18 * * 1-5" \
  --time-zone "America/Los_Angeles" \
  --uri "$SYNC_URL" \
  --http-method POST \
  --description "Sync Gmail to HubSpot every 15 min during business hours"

echo ""
echo "=== Scheduler Jobs Created ==="
echo "Daily Report: 6:00 AM PT, every day"
echo "Gmail Sync: Every 15 min, 9am-6pm PT, Mon-Fri"
echo ""
echo "Done! Your automation is now live."
