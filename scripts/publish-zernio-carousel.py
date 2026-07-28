#!/usr/bin/env python3
"""Publish carousel to TikTok (photo carousel) via Zernio API.

Zernio TikTok photo carousel:
  https://docs.zernio.com/platforms/tiktok
  - mediaItems: type "image"
  - tiktokSettings (root): media_type photo, auto_add_music true, description = full caption
  - content (root): photo title, max 90 chars

After TikTok publish → Telegram notify: «опубликовано, смени музыку».

Usage:
  python scripts/publish-zernio-carousel.py --dry-run
  python scripts/publish-zernio-carousel.py --platform tiktok
  python scripts/publish-zernio-carousel.py --platform instagram,tiktok --skip-telegram
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
ZERNIO_ENV = WORKSPACE / "carusel-memory" / "zernio.env.local"
TELEGRAM_ENV = WORKSPACE / "carusel-memory" / "telegram.env.local"
CAPTION_JSON = WORKSPACE / "carusel-memory" / "design" / "CAROUSEL_CAPTION.json"
PUBLISH_URLS = WORKSPACE / "carusel-memory" / "output" / "publish-urls.json"
API_URL = "https://zernio.com/api/v1/posts"


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def load_caption_pack() -> dict:
    if not CAPTION_JSON.exists():
        raise SystemExit(f"Missing {CAPTION_JSON}")
    return json.loads(CAPTION_JSON.read_text(encoding="utf-8"))


def tiktok_photo_title(caption_obj: dict) -> str:
    """Top-level content = photo title, max 90 chars (Zernio strips hashtags/URLs)."""
    hook = (caption_obj.get("hook") or "").strip()
    if not hook:
        full = (caption_obj.get("full_caption") or "").strip()
        hook = full.split("\n", 1)[0] if full else "Карусель"
    title = re.sub(r"#\S+", "", hook).strip()
    title = re.sub(r"https?://\S+", "", title).strip()
    return title[:90] if title else "Карусель"


def tiktok_description(caption_obj: dict) -> str:
    return (caption_obj.get("full_caption") or "").strip()[:4000]


def instagram_caption(caption_obj: dict) -> str:
    return (caption_obj.get("full_caption") or "").strip()[:2200]


def load_slide_urls() -> list[str]:
    if PUBLISH_URLS.exists():
        data = json.loads(PUBLISH_URLS.read_text(encoding="utf-8"))
        urls = data.get("slides") or data.get("urls") or []
        if len(urls) >= 6:
            return list(urls[:6])
    raise SystemExit(
        "Need 6 HTTPS slide URLs in carusel-memory/output/publish-urls.json "
        "(run carusel-upload first) or pass --slide-urls"
    )


def build_tiktok_settings(description: str) -> dict:
    """Per https://docs.zernio.com/platforms/tiktok — Photo Carousel."""
    return {
        "privacy_level": "PUBLIC_TO_EVERYONE",
        "allow_comment": True,
        "allow_duet": False,
        "allow_stitch": False,
        "media_type": "photo",
        "photo_cover_index": 0,
        "description": description,
        "auto_add_music": True,
        "content_preview_confirmed": True,
        "express_consent_given": True,
        "video_made_with_ai": True,
    }


def publish(
    zernio_env: dict[str, str],
    caption_obj: dict,
    media_urls: list[str],
    platforms: list[str],
    dry_run: bool,
) -> dict:
    media_items = [{"type": "image", "url": u} for u in media_urls]
    platform_blocks: list[dict] = []
    payload: dict = {
        "mediaItems": media_items,
        "publishNow": not dry_run,
    }

    if "tiktok" in platforms:
        acc = zernio_env.get("ZERNIO_TIKTOK_ACCOUNT_ID", "")
        if not acc and not dry_run:
            raise SystemExit("Set ZERNIO_TIKTOK_ACCOUNT_ID in zernio.env.local")
        platform_blocks.append({"platform": "tiktok", "accountId": acc or "DRY_RUN_ACCOUNT"})
        payload["content"] = tiktok_photo_title(caption_obj)
        payload["tiktokSettings"] = build_tiktok_settings(tiktok_description(caption_obj))

    if "instagram" in platforms:
        acc = zernio_env.get("ZERNIO_INSTAGRAM_ACCOUNT_ID", "")
        if not acc:
            raise SystemExit("Set ZERNIO_INSTAGRAM_ACCOUNT_ID in zernio.env.local")
        platform_blocks.append({"platform": "instagram", "accountId": acc})
        if "content" not in payload:
            payload["content"] = instagram_caption(caption_obj)
        elif "tiktok" not in platforms:
            payload["content"] = instagram_caption(caption_obj)

    if not platform_blocks:
        raise SystemExit("No platforms selected")

    payload["platforms"] = platform_blocks

    if dry_run:
        return {"dry_run": True, "payload": payload}

    api_key = zernio_env.get("ZERNIO_API_KEY", "")
    if not api_key:
        raise SystemExit("Missing ZERNIO_API_KEY in zernio.env.local")

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Zernio API HTTP {e.code}: {err}") from e


def send_telegram(text: str, tg_env: dict[str, str]) -> dict:
    token = tg_env.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = tg_env.get("TELEGRAM_NOTIFY_CHAT_ID", "")
    if not token or not chat_id:
        raise SystemExit("Telegram notify: set TELEGRAM_BOT_TOKEN and TELEGRAM_NOTIFY_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode(
        {"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}
    ).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def notify_tiktok_published(result: dict, tg_env: dict[str, str]) -> None:
    post_id = result.get("_id") or result.get("id") or result.get("post", {}).get("_id", "")
    post_url = ""
    for key in ("platform_post_url", "url", "permalink"):
        if result.get(key):
            post_url = str(result[key])
            break
    gates = result.get("platformResults") or result.get("platform_results") or []
    for g in gates if isinstance(gates, list) else []:
        if str(g.get("platform", "")).lower() == "tiktok":
            post_url = post_url or str(g.get("platform_post_url") or g.get("url") or "")

    lines = [
        "Карусель опубликована в TikTok.",
        "",
        "Zernio отправил пост с auto_add_music: TikTok поставил рекомендованный трек.",
        "Открой TikTok → найди пост → Редактировать → смени музыку на нужную.",
    ]
    if post_url:
        lines.extend(["", f"Ссылка: {post_url}"])
    if post_id:
        lines.append(f"Zernio post id: {post_id}")

    send_telegram("\n".join(lines), tg_env)


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish carousel via Zernio (TikTok / IG)")
    parser.add_argument("--dry-run", action="store_true", help="Print payload only")
    parser.add_argument("--platform", default="tiktok", help="tiktok, instagram, or comma-separated")
    parser.add_argument("--slide-urls", nargs="*", help="Override HTTPS URLs for slides 1-6")
    parser.add_argument("--skip-telegram", action="store_true", help="Do not send Telegram notify")
    args = parser.parse_args()

    zernio_env = load_dotenv(ZERNIO_ENV)
    if not zernio_env and not args.dry_run:
        raise SystemExit(f"Missing {ZERNIO_ENV} — copy from carusel-memory/zernio.env.example")

    caption_obj = load_caption_pack()
    urls = args.slide_urls if args.slide_urls else load_slide_urls()
    if len(urls) < 6:
        raise SystemExit(f"Need 6 slide URLs, got {len(urls)}")

    platforms = [p.strip().lower() for p in args.platform.split(",") if p.strip()]
    result = publish(zernio_env, caption_obj, urls[:6], platforms, args.dry_run)

    log_path = WORKSPACE / "carusel-memory" / "output" / "zernio-publish-log.json"
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"Log: {log_path}")

    if (
        not args.dry_run
        and not args.skip_telegram
        and "tiktok" in platforms
        and not result.get("dry_run")
    ):
        tg_env = load_dotenv(TELEGRAM_ENV)
        if tg_env.get("TELEGRAM_BOT_TOKEN") and tg_env.get("TELEGRAM_NOTIFY_CHAT_ID"):
            notify_tiktok_published(result, tg_env)
            print("Telegram: уведомление отправлено (смени музыку в TikTok).")
        else:
            print("Telegram: пропущено — заполни carusel-memory/telegram.env.local")


if __name__ == "__main__":
    main()
