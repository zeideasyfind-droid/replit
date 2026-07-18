#!/bin/bash
# ── EasyFind Admin — Google Cloud Run Deployment Script ──────────────────────
# Usage: bash deploy_cloudrun.sh
#
# Prerequisites:
#   1. gcloud CLI authenticated (gcloud auth login)
#   2. Service account JSON saved as GCP_SA_KEY secret in Replit
#   3. Fill in the three variables below

PROJECT_ID="YOUR_GCP_PROJECT_ID"       # e.g. my-project-123
REGION="asia-south1"                    # e.g. asia-south1, us-central1
SERVICE_NAME="easyfind-admin"           # Cloud Run service name
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

set -e

echo "▶ Building and pushing Docker image..."
gcloud builds submit --tag "$IMAGE" --project "$PROJECT_ID"

echo "▶ Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi \
  --project "$PROJECT_ID" \
  --set-env-vars "\
CLOUDINARY_CLOUD_NAME=$CLOUDINARY_CLOUD_NAME,\
META_APP_ID=$META_APP_ID,\
META_CATALOG_ID=$META_CATALOG_ID,\
WHATSAPP_PHONE_NUMBER_ID=$WHATSAPP_PHONE_NUMBER_ID,\
WHATSAPP_RECIPIENT_NUMBER=$WHATSAPP_RECIPIENT_NUMBER" \
  --update-secrets "\
ADMIN_AUTH_TOKEN=ADMIN_AUTH_TOKEN:latest,\
META_ACCESS_TOKEN=META_ACCESS_TOKEN:latest,\
WHATSAPP_ACCESS_TOKEN=WHATSAPP_ACCESS_TOKEN:latest,\
CLOUDINARY_API_KEY=CLOUDINARY_API_KEY:latest,\
CLOUDINARY_API_SECRET=CLOUDINARY_API_SECRET:latest,\
GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,\
GOOGLE_SERVICE_ACCOUNT_JSON=GOOGLE_SERVICE_ACCOUNT_JSON:latest,\
SESSION_SECRET=SESSION_SECRET:latest"

echo ""
echo "✅ Deployed! Your public URL:"
gcloud run services describe "$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --project "$PROJECT_ID" \
  --format "value(status.url)"
