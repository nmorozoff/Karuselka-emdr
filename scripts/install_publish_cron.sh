#!/usr/bin/env bash
# Установить cron: публикация каруселей в 11:00, 17:00, 21:00 (локальное время).
#
#   ./scripts/install_publish_cron.sh
#   ./scripts/install_publish_cron.sh --uninstall

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORKER="$ROOT/scripts/run_publish_worker.sh"
LOG="$ROOT/carusel-memory/output/worker-cron.log"
MARKER_BEGIN="# KARUSELKA_PUBLISH_CRON_BEGIN"
MARKER_END="# KARUSELKA_PUBLISH_CRON_END"

if [[ ! -x "$WORKER" ]]; then
  chmod +x "$WORKER"
fi

mkdir -p "$(dirname "$LOG")"

CRON_BLOCK=$(cat <<EOF
$MARKER_BEGIN
0 11 * * * /bin/bash -lc '$WORKER >> $LOG 2>&1'
0 17 * * * /bin/bash -lc '$WORKER >> $LOG 2>&1'
0 21 * * * /bin/bash -lc '$WORKER >> $LOG 2>&1'
$MARKER_END
EOF
)

if [[ "${1:-}" == "--uninstall" ]]; then
  if crontab -l >/dev/null 2>&1; then
    crontab -l | awk -v b="$MARKER_BEGIN" -v e="$MARKER_END" '
      $0 == b { skip=1; next }
      $0 == e { skip=0; next }
      !skip { print }
    ' | crontab -
    echo "Удалено: расписание Каруселька из crontab."
  else
    echo "Crontab пуст — нечего удалять."
  fi
  exit 0
fi

EXISTING=""
if crontab -l >/dev/null 2>&1; then
  EXISTING="$(crontab -l | awk -v b="$MARKER_BEGIN" -v e="$MARKER_END" '
    $0 == b { skip=1; next }
    $0 == e { skip=0; next }
    !skip { print }
  ')"
fi

{
  if [[ -n "$EXISTING" ]]; then
    printf '%s\n' "$EXISTING"
  fi
  printf '%s\n' "$CRON_BLOCK"
} | crontab -

echo "Cron установлен (локальный резерв — Mac должен быть включён)."
echo "Production без Mac: deploy/cloud-worker/README.md (Cloud Scheduler 11/17/21)."
echo "Лог: $LOG"
crontab -l | sed -n "/$MARKER_BEGIN/,/$MARKER_END/p"
