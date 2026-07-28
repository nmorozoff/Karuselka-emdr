#!/usr/bin/env bash
# Загрузить локальный worker-state.json в Dropbox (для cloud worker).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export WORKER_STATE_BACKEND=dropbox
export WORKER_STATE_DROPBOX_PATH=/Content_Plan/.karuselka/worker-state.json

cd "$ROOT/scripts"
python3 - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "lib")
from dropbox_client import get_access_token
from publish_config import MEMORY, load_runtime_env
from worker_state import load_state, save_state

local = MEMORY / "publish" / "worker-state.json"
if local.exists():
    data = json.loads(local.read_text(encoding="utf-8"))
else:
    data = {"published": [], "failed": {}}

env = load_runtime_env()
token = get_access_token(env)
save_state(data, token)
print("Uploaded to Dropbox:", "/Content_Plan/.karuselka/worker-state.json")
print("published:", len(data.get("published", [])))
PY
