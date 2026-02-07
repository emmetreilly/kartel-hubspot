# Kartel CRM Automation - Setup Guide

This guide walks through setting up fully automated daily reports and Gmail sync.

## Prerequisites

- Google Cloud SDK installed (`brew install google-cloud-sdk`)
- A Google Cloud project with billing enabled
- Google Workspace admin access (for domain-wide delegation)
- SendGrid account (free tier works)
- Anthropic API key

## Step 1: Create GCP Project

```bash
# Create project (or use existing)
gcloud projects create kartel-crm-automation --name="Kartel CRM Automation"

# Set as active project
gcloud config set project kartel-crm-automation

# Enable billing (required for Cloud Functions)
# Go to: https://console.cloud.google.com/billing

# Enable required APIs
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudscheduler.googleapis.com \
  secretmanager.googleapis.com \
  gmail.googleapis.com \
  calendar-json.googleapis.com
```

## Step 2: Create Service Account for Gmail/Calendar Access

```bash
# Create service account
gcloud iam service-accounts create kartel-crm-service \
  --display-name="Kartel CRM Service Account"

# Get the service account email
SA_EMAIL="kartel-crm-service@kartel-crm-automation.iam.gserviceaccount.com"

# Create and download key
gcloud iam service-accounts keys create service-account-key.json \
  --iam-account=$SA_EMAIL

echo "Service account key saved to: service-account-key.json"
```

## Step 3: Enable Domain-Wide Delegation (Google Workspace Admin)

This allows the service account to access @kartel.ai Gmail and Calendar.

1. Go to: https://admin.google.com
2. Navigate to: Security → API controls → Domain-wide delegation
3. Click "Add new"
4. Enter the service account's **Client ID** (find in GCP Console → IAM → Service Accounts)
5. Add these OAuth scopes:
   ```
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/calendar.readonly
   ```
6. Click "Authorize"

## Step 4: Get API Keys

### HubSpot API Key
- Already have: `YOUR_HUBSPOT_TOKEN`

### Anthropic API Key
- Go to: https://console.anthropic.com
- Create an API key

### SendGrid API Key
1. Sign up at: https://sendgrid.com (free tier)
2. Go to: Settings → API Keys → Create API Key
3. Give it "Mail Send" permission
4. **Important:** Verify a sender identity (Settings → Sender Authentication)
   - Use `reports@kartel.ai` as the sender

## Step 5: Store Secrets in Secret Manager

```bash
# Store HubSpot token
echo -n "YOUR_HUBSPOT_TOKEN" | \
  gcloud secrets create HUBSPOT_ACCESS_TOKEN --data-file=-

# Store Anthropic API key
echo -n "YOUR_ANTHROPIC_KEY" | \
  gcloud secrets create ANTHROPIC_API_KEY --data-file=-

# Store SendGrid API key
echo -n "YOUR_SENDGRID_KEY" | \
  gcloud secrets create SENDGRID_API_KEY --data-file=-

# Store Google credentials (the service account JSON)
gcloud secrets create GOOGLE_CREDENTIALS \
  --data-file=service-account-key.json

# Grant Cloud Functions access to secrets
PROJECT_NUMBER=$(gcloud projects describe kartel-crm-automation --format='value(projectNumber)')
SA_COMPUTE="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in HUBSPOT_ACCESS_TOKEN ANTHROPIC_API_KEY SENDGRID_API_KEY GOOGLE_CREDENTIALS; do
  gcloud secrets add-iam-policy-binding $SECRET \
    --member="serviceAccount:$SA_COMPUTE" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Step 6: Deploy

```bash
cd /Users/emmetreilly/Desktop/sales-brain/cloud-functions
chmod +x deploy.sh
./deploy.sh
```

## Step 7: Test

### Test Daily Report
```bash
# Trigger manually
DAILY_URL=$(gcloud functions describe daily-report --region us-west1 --format='value(serviceConfig.uri)')
curl -X POST $DAILY_URL

# Check logs
gcloud functions logs read daily-report --region us-west1 --limit 50
```

### Test Gmail Sync
```bash
SYNC_URL=$(gcloud functions describe gmail-sync --region us-west1 --format='value(serviceConfig.uri)')
curl -X POST $SYNC_URL

gcloud functions logs read gmail-sync --region us-west1 --limit 50
```

## Monitoring

### View Logs
```bash
# Daily report logs
gcloud functions logs read daily-report --region us-west1

# Gmail sync logs
gcloud functions logs read gmail-sync --region us-west1
```

### Check Scheduler Status
```bash
gcloud scheduler jobs list --location us-west1
```

### Manually Trigger a Job
```bash
gcloud scheduler jobs run daily-report-job --location us-west1
```

## Cost Estimate

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Cloud Functions | ~2000 invocations | Free tier |
| Cloud Scheduler | 2 jobs | Free tier |
| Secret Manager | 4 secrets | ~$0.25 |
| Claude API (Sonnet) | ~100 calls/mo | ~$10-15 |
| SendGrid | 30 emails | Free tier |
| **Total** | | **~$15/month** |

## Troubleshooting

### "Permission denied" on Gmail/Calendar
- Verify domain-wide delegation is set up correctly
- Ensure the OAuth scopes match exactly
- Check that the service account Client ID is correct

### Function timeout
- Increase timeout in deploy.sh (currently 540s = 9 min)
- Check if Claude is making too many tool calls

### Email not sending
- Verify SendGrid sender identity
- Check SendGrid activity feed for errors
- Ensure the from email matches verified sender
