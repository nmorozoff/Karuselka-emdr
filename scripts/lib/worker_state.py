"""Worker state: local file or Dropbox (для cloud + синхронизация с Mac)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from publish_config import MEMORY

DEFAULT_LOCAL = MEMORY / "publish" / "worker-state.json"
DEFAULT_DROPBOX = "/Content_Plan/.karuselka/worker-state.json"


def backend() -> str:
    return os.environ.get("WORKER_STATE_BACKEND", "local").strip().lower()


def state_path() -> Path:
    raw = os.environ.get("WORKER_STATE_PATH", "")
    if raw:
        return Path(raw)
    return DEFAULT_LOCAL


def dropbox_state_path() -> str:
    return os.environ.get("WORKER_STATE_DROPBOX_PATH", DEFAULT_DROPBOX)


def _dropbox_download(token: str, path: str) -> dict | None:
    req = urllib.request.Request(
        "https://content.dropboxapi.com/2/files/download",
        headers={
            "Authorization": f"Bearer {token}",
            "Dropbox-API-Arg": json.dumps({"path": path}),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        return None


def _dropbox_upload(token: str, path: str, data: dict) -> None:
    from dropbox_client import create_folder, upload_file

    folder = path.rsplit("/", 1)[0]
    create_folder(folder, token)
    upload_file(path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"), token)


def load_state(token: str | None = None) -> dict:
    if backend() == "dropbox":
        if not token:
            raise RuntimeError("Dropbox token required for WORKER_STATE_BACKEND=dropbox")
        data = _dropbox_download(token, dropbox_state_path())
        return data if data else {"published": [], "failed": {}}

    path = state_path()
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"published": [], "failed": {}}


def save_state(state: dict, token: str | None = None) -> None:
    if backend() == "dropbox":
        if not token:
            raise RuntimeError("Dropbox token required for WORKER_STATE_BACKEND=dropbox")
        _dropbox_upload(token, dropbox_state_path(), state)
        return

    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
