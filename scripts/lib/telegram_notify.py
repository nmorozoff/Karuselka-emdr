"""Telegram notifications."""

from __future__ import annotations

import json
import os
import ssl
import urllib.parse
import urllib.request

from publish_config import load_runtime_env


def send_message(text: str, chat_id: str | None = None) -> dict:
    env = load_runtime_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    cid = chat_id or env.get("TELEGRAM_NOTIFY_CHAT_ID", "")
    if not token or not cid:
        raise RuntimeError("Telegram: TELEGRAM_BOT_TOKEN and TELEGRAM_NOTIFY_CHAT_ID required")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode(
        {"chat_id": cid, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
    return data


def notify_add_music(platform: str, pair_label: str, post_url: str = "") -> None:
    lines = [f"Карусель опубликована ({pair_label}) — {platform}.", ""]
    if platform.lower() == "tiktok":
        lines.append("Zernio: auto_add_music — смени трек в TikTok вручную.")
    else:
        lines.append("Instagram: добавь музыку в приложении.")
    if post_url:
        lines.extend(["", post_url])
    send_message("\n".join(lines))
