#!/usr/bin/env bash
# Cloud Scheduler: 11:00, 17:00, 21:00 Europe/Moscow → POST /run

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

# shellcheck source=/dev/null
source "$DIR/.env.deploy" 2>/dev/null || true

PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-europe-west1}"
SERVICE_NAME="${SERVICE_NAME:-karuselka-publish-worker}"
WORKER_URL="${WORKER_URL:-}"
WORKER_API_KEY="${WORKER_API_KEY:-}"
SCHEDULER_LOCATION="${SCHEDULER_LOCATION:-europe-west1}"

if [[ -z "$PROJECT_ID" || -z "$WORKER_API_KEY" ]]; then
  echo "Нужны PROJECT_ID и WORKER_API_KEY (deploy/cloud-worker/.env.deploy)" >&2
  exit 1
fi

if [[ -z "$WORKER_URL" ]]; then
  WORKER_URL="$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format='value(status.url)' 2>/dev/null || true)"
fi
if [[ -z "$WORKER_URL" ]]; then
  echo "Задайте WORKER_URL или задеплойте сервис: ./deploy.sh" >&2
  exit 1
fi

gcloud config set project "$PROJECT_ID" >/dev/null
gcloud services enable cloudscheduler.googleapis.com run.googleapis.com >/dev/null 2>&1 || true

create_job() {
  local id="$1"
  local schedule="$2"
  local desc="$3"
  if gcloud scheduler jobs describe "$id" --location="$SCHEDULER_LOCATION" >/dev/null 2>&1; then
    gcloud scheduler jobs update http "$id" \
      --location="$SCHEDULER_LOCATION" \
      --schedule="$schedule" \
      --time-zone="Europe/Moscow" \
      --uri="${WORKER_URL}/run?pair=pair1&limit=1" \
      --http-method=POST \
      --headers="X-Worker-Key=${WORKER_API_KEY}" \
      --description="$desc"
  else
    gcloud scheduler jobs create http "$id" \
      --location="$SCHEDULER_LOCATION" \
      --schedule="$schedule" \
      --time-zone="Europe/Moscow" \
      --uri="${WORKER_URL}/run?pair=pair1&limit=1" \
      --http-method=POST \
      --headers="X-Worker-Key=${WORKER_API_KEY}" \
      --description="$desc"
  fi
}

create_job "karuselka-publish-1100" "0 11 * * *" "Karuselka publish 11:00 MSK"
create_job "karuselka-publish-1700" "0 17 * * *" "Karuselka publish 17:00 MSK"
create_job "karuselka-publish-2100" "0 21 * * *" "Karuselka publish 21:00 MSK"

echo ""
echo "Scheduler OK (Europe/Moscow): 11:00, 17:00, 21:00"
echo "Target: ${WORKER_URL}/run"
gcloud scheduler jobs list --location="$SCHEDULER_LOCATION" --filter="name:karuselka-publish" --format="table(name,schedule,timeZone,state)"
