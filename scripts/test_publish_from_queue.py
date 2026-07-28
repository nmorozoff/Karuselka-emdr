#!/usr/bin/env python3
"""Test publish one carousel from Airtable queue (same logic as Make Pair1).

Flow: Airtable row → Dropbox slides → Cloud Run render → Zernio IG+TikTok.

Usage:
  python scripts/test_publish_from_queue.py --list
  python scripts/test_publish_from_queue.py --name crsl_20260702_1234_o00dkh --dry-run
  python scripts/test_publish_from_queue.py --name crsl_20260702_1234_o00dkh
"""

from __future__ import annotations

import argparse
import json
import random
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from lib.dropbox_client import ensure_shared_link, get_access_token
from lib.publish_config import MEMORY, merge_env, pair_config

CLOUD_RUN_URL = (
    "https://ai-carousel-renderer-861393245289.europe-west1.run.app/generate-carousel"
)
TRACKS_TABLE = "tblfLD5ET7vvp1raT"
ZERNIO_URL = "https://zernio.com/api/v1/posts"


def http_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    body: dict | list | str | None = None,
    timeout: int = 600,
) -> dict:
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        if isinstance(body, str):
            data = body.encode("utf-8")
        else:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            hdrs.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code} {url}: {detail[:2000]}") from e


def load_env() -> dict[str, str]:
    return merge_env(
        MEMORY / "airtable.env.local",
        MEMORY / "dropbox.env.local",
        MEMORY / "zernio.env.local",
        MEMORY / "make.env.local",
    )


def list_queue_records(env: dict[str, str], pair: dict) -> list[dict]:
    base = pair["airtable"]["base_id"]
    table = pair["airtable"]["table_id"]
    token = env["AIRTABLE_ACCESS_TOKEN"]
    url = f"https://api.airtable.com/v0/{base}/{table}?maxRecords=50"
    data = http_json("GET", url, headers={"Authorization": f"Bearer {token}"})
    return data.get("records", [])


def pick_track(env: dict[str, str], pair: dict) -> dict:
    base = pair["airtable"]["base_id"]
    token = env["AIRTABLE_ACCESS_TOKEN"]
    formula = urllib.parse.quote("{Active}=1")
    url = f"https://api.airtable.com/v0/{base}/{TRACKS_TABLE}?filterByFormula={formula}"
    data = http_json("GET", url, headers={"Authorization": f"Bearer {token}"})
    records = data.get("records", [])
    if not records:
        raise SystemExit("No active tracks in Airtable")
    rec = random.choice(records)
    return rec.get("fields", {})


def list_slide_paths(token: str, folder_name: str) -> list[str]:
    dropbox_folder = f"/Content_Plan/{folder_name}"
    req = urllib.request.Request(
        "https://api.dropboxapi.com/2/files/list_folder",
        data=json.dumps({"path": dropbox_folder, "recursive": False}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        entries = json.loads(resp.read().decode()).get("entries", [])
    slides = sorted(
        e["path_lower"]
        for e in entries
        if e.get(".tag") == "file" and e.get("name", "").startswith("slide-")
    )
    if len(slides) != 7:
        raise SystemExit(f"Expected 7 slides in {dropbox_folder}, got {len(slides)}: {slides}")
    return slides


def render_carousel(env: dict[str, str], payload: dict) -> dict:
    api_key = env.get("CLOUD_RUN_API_KEY", "")
    if not api_key:
        raise SystemExit("Set CLOUD_RUN_API_KEY in cloud-worker.env.local or env")
    return http_json(
        "POST",
        CLOUD_RUN_URL,
        headers={"X-API-Key": api_key, "Accept": "application/json"},
        body=payload,
        timeout=600,
    )


def build_tiktok_payload(fields: dict, image_urls: list[str], account_id: str) -> dict:
    return {
        "content": (fields.get("TikTok заголовок") or "Карусель")[:90],
        "mediaItems": [{"type": "image", "url": u} for u in image_urls],
        "platforms": [{"platform": "tiktok", "accountId": account_id}],
        "tiktokSettings": {
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "allow_comment": True,
            "media_type": "photo",
            "photo_cover_index": 0,
            "description": (fields.get("TikTok описание") or fields.get("Описание карусели") or "")[:4000],
            "auto_add_music": True,
            "content_preview_confirmed": True,
            "express_consent_given": True,
        },
        "publishNow": True,
    }


def post_zernio(env: dict[str, str], body: dict | str, label: str, dry_run: bool) -> dict:
    body_json = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    if dry_run:
        parsed = json.loads(body_json)
        return {"dry_run": True, "label": label, "platforms": parsed.get("platforms")}
    api_key = env["ZERNIO_API_KEY"]
    return http_json(
        "POST",
        ZERNIO_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body=body_json,
        timeout=120,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--name", help="Airtable Name / Dropbox folder (crsl_...)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-zernio", action="store_true", help="Only Cloud Run render")
    parser.add_argument("--tiktok-only", action="store_true", help="Skip Cloud Run; photo carousel via Zernio")
    args = parser.parse_args()

    env = load_env()
    pair = pair_config("pair1")
    records = list_queue_records(env, pair)

    if args.list:
        for rec in records:
            f = rec.get("fields", {})
            print(f"{f.get('Name')}\t{f.get('TikTok заголовок', '')[:60]}")
        return

    if not records:
        raise SystemExit("Airtable queue is empty")

    if args.name:
        rec = next((r for r in records if r.get("fields", {}).get("Name") == args.name), None)
        if not rec:
            raise SystemExit(f"Record not found: {args.name}")
    else:
        rec = records[0]

    fields = rec.get("fields", {})
    name = fields.get("Name")
    if not name:
        raise SystemExit("Record has no Name field")

    dropbox_token = get_access_token(env)
    slide_paths = list_slide_paths(dropbox_token, name)
    track = pick_track(env, pair)

    payload = {
        "carousel_name": name,
        "folder_name": name,
        "job_id": name,
        "instagram_caption": fields.get("Описание карусели", ""),
        "tiktok_title": fields.get("TikTok заголовок", ""),
        "tiktok_description": fields.get("TikTok описание", ""),
        "dropbox_image_paths": slide_paths,
        "dropbox_audio_path": track.get("Audio Path", ""),
        "audio_start": track.get("Audio Start", 0),
        "audio_end": track.get("Audio End", 30),
        "reuse_audio_segment": bool(track.get("Reuse Audio Segment")),
        "output_folder": "/Ready_Carousel",
    }

    print("Carousel:", name)
    print("Slides:", len(slide_paths))
    print("Track:", track.get("Track Name"), track.get("Audio Path"))

    if args.tiktok_only:
        print("Building Dropbox dl=1 URLs for TikTok photo carousel...")
        image_urls = [ensure_shared_link(p, dropbox_token) for p in slide_paths]
        tt_payload = build_tiktok_payload(fields, image_urls, env["ZERNIO_TIKTOK_ACCOUNT_ID"])
        if args.dry_run:
            print(json.dumps(tt_payload, ensure_ascii=False, indent=2)[:4000])
            return
        print("Publishing TikTok via Zernio...")
        tt_res = post_zernio(env, tt_payload, "tiktok", dry_run=False)
        print("TikTok:", json.dumps(tt_res, ensure_ascii=False)[:800])
        result_path = MEMORY / "output" / f"test-publish-{name}-tiktok.json"
        result_path.write_text(json.dumps({"name": name, "tiktok": tt_res}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Done:", result_path)
        return

    if args.dry_run:
        print("\n--- Cloud Run payload ---")
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:4000])
        return

    print("Rendering via Cloud Run...")
    render = render_carousel(env, payload)
    if render.get("status") != "success":
        raise SystemExit(f"Cloud Run failed: {json.dumps(render, ensure_ascii=False)[:2000]}")

    log_path = MEMORY / "output" / "test-publish-log.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps({"name": name, "render": render}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Cloud Run OK. Log:", log_path)

    if args.skip_zernio:
        return

    ig_json = render.get("instagram_zernio_post_json")
    tt_json = render.get("tiktok_zernio_post_json")
    if not ig_json or not tt_json:
        raise SystemExit("Cloud Run response missing zernio JSON fields")

    print("Publishing Instagram via Zernio...")
    ig_res = post_zernio(env, ig_json, "instagram", dry_run=False)
    print("Instagram:", json.dumps(ig_res, ensure_ascii=False)[:500])

    print("Publishing TikTok via Zernio...")
    tt_res = post_zernio(env, tt_json, "tiktok", dry_run=False)
    print("TikTok:", json.dumps(tt_res, ensure_ascii=False)[:500])

    result_path = MEMORY / "output" / f"test-publish-{name}.json"
    result_path.write_text(
        json.dumps(
            {"name": name, "airtable_id": rec["id"], "instagram": ig_res, "tiktok": tt_res},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Done:", result_path)


if __name__ == "__main__":
    main()
