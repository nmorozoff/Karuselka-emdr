#!/usr/bin/env python3
"""Telegram bridge: ссылка в бот → inbox READY_FOR_AGENT.

Usage:
  python scripts/telegram_intake_bridge.py --once
  python scripts/telegram_intake_bridge.py --poll   # loop каждые 5 сек

Требует carusel-memory/telegram.env.local (TELEGRAM_BOT_TOKEN, TELEGRAM_INTAKE_CHAT_ID).
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
WORKSPACE = SCRIPTS.parent
MEMORY = WORKSPACE / "carusel-memory"
INTAKE_DIR = MEMORY / "intake"
OFFSET_FILE = INTAKE_DIR / "telegram-offset.json"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = MEMORY / "telegram.env.local"
    if not path.exists():
        raise SystemExit(f"Missing {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


IG_URL_RE = re.compile(r"https?://(?:www\.)?instagram\.com/(?:p|reel|reels)/[\w-]+/?", re.I)


def extract_url(text: str) -> str | None:
    m = IG_URL_RE.search(text or "")
    return m.group(0).rstrip("/") + "/" if m else None


def get_updates(token: str, offset: int | None) -> list:
    params: dict[str, str] = {"timeout": "0"}
    if offset is not None:
        params["offset"] = str(offset)
    url = f"https://api.telegram.org/bot{token}/getUpdates?" + urllib.parse.urlencode(params)
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, context=ctx, timeout=35) as resp:
        data = json.loads(resp.read().decode())
    if not data.get("ok"):
        raise SystemExit(f"getUpdates failed: {data}")
    return data.get("result", [])


def write_inbox(source_url: str, chat_id: int, message_id: int, raw_text: str) -> Path:
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    run_id = f"run_{now.strftime('%Y%m%d_%H%M%S')}"
    payload = {
        "status": "READY_FOR_AGENT",
        "run_id": run_id,
        "source_url": source_url,
        "received_at": now.isoformat(),
        "telegram": {"chat_id": chat_id, "message_id": message_id},
        "raw_message": raw_text[:2000],
        "pipeline": "dual_variant_v1",
    }
    inbox = INTAKE_DIR / "inbox.json"
    inbox.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (INTAKE_DIR / f"{run_id}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return inbox


def process_once(env: dict[str, str]) -> bool:
    token = env["TELEGRAM_BOT_TOKEN"]
    allowed = env.get("TELEGRAM_INTAKE_CHAT_ID", "")
    offset = None
    if OFFSET_FILE.exists():
        offset = json.loads(OFFSET_FILE.read_text()).get("offset")

    updates = get_updates(token, offset)
    handled = False
    max_update_id = offset or 0

    for upd in updates:
        max_update_id = max(max_update_id, upd.get("update_id", 0))
        msg = upd.get("message") or {}
        chat = msg.get("chat") or {}
        chat_id = str(chat.get("id", ""))
        if allowed and chat_id != str(allowed):
            continue
        text = msg.get("text") or msg.get("caption") or ""
        url = extract_url(text)
        if not url:
            continue
        write_inbox(url, int(chat_id), msg.get("message_id", 0), text)
        ack = f"Принято. Ссылка в очередь Каруселька:\n{url}\n\nСтатус: READY_FOR_AGENT"
        body = urllib.parse.urlencode({"chat_id": chat_id, "text": ack}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=body, method="POST")
        urllib.request.urlopen(req, timeout=30)
        handled = True

    if updates:
        OFFSET_FILE.write_text(json.dumps({"offset": max_update_id + 1}), encoding="utf-8")
    return handled


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--interval", type=float, default=5.0)
    args = parser.parse_args()
    env = load_env()
    if args.poll:
        while True:
            process_once(env)
            time.sleep(args.interval)
    else:
        process_once(env)


if __name__ == "__main__":
    main()
