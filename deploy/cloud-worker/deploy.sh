#!/usr/bin/env bash
# Деплой Cloud Run worker (публикация по HTTP).

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"

# shellcheck source=/dev/null
source "$DIR/.env.deploy" 2>/dev/null || true

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-karuselka-publish-worker}"
ENV_FILE="${ENV_FILE:-$DIR/.env.deploy.yaml}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Задайте PROJECT_ID в deploy/cloud-worker/.env.deploy или export PROJECT_ID=..." >&2
  exit 1
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Установите Google Cloud CLI: https://cloud.google.com/sdk/docs/install" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Сначала: $ROOT/scripts/prepare_cloud_env.sh" >&2
  exit 1
fi

"$DIR/prepare_bundle.sh"

gcloud config set project "$PROJECT_ID" >/dev/null

gcloud run deploy "$SERVICE_NAME" \
  --source "$DIR" \
  --region "$REGION" \
  --platform managed \
  --allow-unauthenticated \
  --timeout 3600 \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 1 \
  --min-instances 0 \
  --port 8080 \
  --env-vars-file "$ENV_FILE"

URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)')"
echo ""
echo "Deployed: $URL"
echo "Health:   $URL/health"
echo "Дальше:   WORKER_URL=$URL ./deploy/cloud-worker/setup-scheduler.sh"
