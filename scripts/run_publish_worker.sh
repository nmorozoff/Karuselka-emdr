#!/usr/bin/env bash
# Запуск воркера публикации (3×/день ≈ каждые 8ч или по cron).
# Альтернатива Make, пока сценарий invalid / Cloud Run > 40s для MCP.

set -euo pipefail
export PYTHONUNBUFFERED=1
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/scripts"
exec python3 publish_worker.py --pair pair1 --limit 1 "$@"
