"""Shared config for publish pipeline."""

from __future__ import annotations

import json
import os
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
MEMORY = WORKSPACE / "carusel-memory"


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def accounts_pairs_path() -> Path:
    raw = os.environ.get("ACCOUNTS_PAIRS_PATH", "")
    if raw:
        return Path(raw)
    return MEMORY / "publish" / "accounts-pairs.json"


def load_accounts_pairs() -> dict:
    return json.loads(accounts_pairs_path().read_text(encoding="utf-8"))


def load_style_registry() -> dict:
    path = MEMORY / "styles" / "registry.json"
    return json.loads(path.read_text(encoding="utf-8"))


def merge_env(*paths: Path) -> dict[str, str]:
    merged: dict[str, str] = dict(os.environ)
    for p in paths:
        merged.update(load_dotenv(p))
    return merged


def load_runtime_env() -> dict[str, str]:
    """Cloud: только os.environ. Локально: *.env.local + os.environ."""
    if os.environ.get("KARUSELKA_RUNTIME", "").lower() == "cloud":
        required = [
            "AIRTABLE_ACCESS_TOKEN",
            "DROPBOX_APP_KEY",
            "DROPBOX_APP_SECRET",
            "DROPBOX_REFRESH_TOKEN",
            "ZERNIO_API_KEY",
            "ZERNIO_INSTAGRAM_ACCOUNT_ID",
            "ZERNIO_TIKTOK_ACCOUNT_ID",
            "CLOUD_RUN_API_KEY",
        ]
        missing = [k for k in required if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f"Missing cloud env: {', '.join(missing)}")
        return dict(os.environ)

    return merge_env(
        MEMORY / "airtable.env.local",
        MEMORY / "dropbox.env.local",
        MEMORY / "zernio.env.local",
        MEMORY / "make.env.local",
        MEMORY / "telegram.env.local",
    )


def pair_config(pair_id: str) -> dict:
    cfg = load_accounts_pairs()
    key = "pair1" if pair_id in ("pair1", "1", "a", "variant-a") else "pair2"
    return cfg[key]
