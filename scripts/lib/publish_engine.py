"""Ядро публикации: Airtable → Cloud Run → Zernio. Локально и в Cloud Run worker."""

from __future__ import annotations

import json
import os
import random
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from airtable_client import delete_record
from dropbox_client import ensure_shared_link, get_access_token
from publish_config import load_runtime_env, pair_config
from worker_state import load_state, save_state

CLOUD_RUN_URL = os.environ.get(
    "CLOUD_RUN_RENDER_URL",
    "https://ai-carousel-renderer-861393245289.europe-west1.run.app/generate-carousel",
)
TRACKS_TABLE = os.environ.get("AIRTABLE_TRACKS_TABLE_ID", "tblfLD5ET7vvp1raT")
ZERNIO_URL = "https://zernio.com/api/v1/posts"
RENDER_TIMEOUT_SEC = int(os.environ.get("RENDER_TIMEOUT_SEC", "1200"))
POLL_INTERVAL_SEC = int(os.environ.get("RENDER_POLL_INTERVAL_SEC", "30"))
CONTENT_PLAN_ROOT = os.environ.get("DROPBOX_CONTENT_PLAN_ROOT", "/Content_Plan")


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
        raise RuntimeError(f"HTTP {e.code} {url}: {detail[:2000]}") from e


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
        raise RuntimeError("No active tracks in Airtable")
    return random.choice(records).get("fields", {})


def list_slide_paths(token: str, folder_name: str) -> list[str]:
    dropbox_folder = f"{CONTENT_PLAN_ROOT.rstrip('/')}/{folder_name}"
    req = urllib.request.Request(
        "https://api.dropboxapi.com/2/files/list_folder",
        data=json.dumps({"path": dropbox_folder, "recursive": False}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
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
        raise RuntimeError(f"Expected 7 slides in {dropbox_folder}, got {len(slides)}")
    return slides


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


def post_zernio(env: dict[str, str], body: dict | str, dry_run: bool = False) -> dict:
    body_json = body if isinstance(body, str) else json.dumps(body, ensure_ascii=False)
    if dry_run:
        return {"dry_run": True, "platforms": json.loads(body_json).get("platforms")}
    return http_json(
        "POST",
        ZERNIO_URL,
        headers={
            "Authorization": f"Bearer {env['ZERNIO_API_KEY']}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body=body_json,
        timeout=120,
    )


def dropbox_download_json(token: str, path: str) -> dict | None:
    req = urllib.request.Request(
        "https://content.dropboxapi.com/2/files/download",
        headers={"Authorization": f"Bearer {token}", "Dropbox-API-Arg": json.dumps({"path": path})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError:
        return None


def count_ready_videos(token: str, name: str) -> int:
    path = f"/Ready_Carousel/{name}"
    req = urllib.request.Request(
        "https://api.dropboxapi.com/2/files/list_folder",
        data=json.dumps({"path": path, "recursive": True}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            entries = json.loads(resp.read().decode()).get("entries", [])
    except urllib.error.HTTPError:
        return 0
    return len([e for e in entries if e.get("name", "").endswith(".mp4")])


def delete_dropbox_folder(token: str, path: str) -> None:
    req = urllib.request.Request(
        "https://api.dropboxapi.com/2/files/delete_v2",
        data=json.dumps({"path": path}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        if e.code != 409:
            raise


def build_render_payload(fields: dict, slide_paths: list[str], track: dict) -> dict:
    name = fields["Name"]
    return {
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


def wait_for_render(env: dict[str, str], payload: dict, token: str, name: str) -> dict:
    result_box: dict = {}
    error_box: dict = {}

    def _run() -> None:
        try:
            api_key = env.get("CLOUD_RUN_API_KEY", "")
            if not api_key:
                raise RuntimeError("CLOUD_RUN_API_KEY is not set")
            result_box["data"] = http_json(
                "POST",
                CLOUD_RUN_URL,
                headers={"X-API-Key": api_key, "Accept": "application/json"},
                body=payload,
                timeout=RENDER_TIMEOUT_SEC,
            )
        except Exception as exc:  # noqa: BLE001
            error_box["error"] = exc

    threading.Thread(target=_run, daemon=True).start()
    deadline = time.time() + RENDER_TIMEOUT_SEC
    manifest_path = f"/Ready_Carousel/{name}/render-result.json"

    while time.time() < deadline:
        if "data" in result_box:
            data = result_box["data"]
            if data.get("status") == "success":
                return data
            raise RuntimeError(f"Cloud Run error: {json.dumps(data, ensure_ascii=False)[:1500]}")

        manifest = dropbox_download_json(token, manifest_path)
        if manifest and manifest.get("slide_count") == 7:
            break

        time.sleep(POLL_INTERVAL_SEC)

    if "data" in result_box and result_box["data"].get("status") == "success":
        return result_box["data"]

    manifest = dropbox_download_json(token, manifest_path)
    if not manifest or manifest.get("slide_count") != 7:
        err = error_box.get("error", "timeout")
        raise RuntimeError(f"Incomplete render for {name}: {count_ready_videos(token, name)}/7 mp4 — {err}")

    videos = manifest.get("videos", [])
    ig_items = [{"type": "video", "url": v["url"]} for v in videos if v.get("url")]
    image_urls = [ensure_shared_link(p, token) for p in payload["dropbox_image_paths"]]
    fields = {
        "TikTok заголовок": payload.get("tiktok_title", ""),
        "TikTok описание": payload.get("tiktok_description", ""),
        "Описание карусели": payload.get("instagram_caption", ""),
    }
    tt_payload = build_tiktok_payload(fields, image_urls, env["ZERNIO_TIKTOK_ACCOUNT_ID"])
    ig_payload = {
        "content": (payload.get("instagram_caption") or "")[:2200],
        "mediaItems": ig_items,
        "platforms": [{"platform": "instagram", "accountId": env["ZERNIO_INSTAGRAM_ACCOUNT_ID"]}],
        "publishNow": True,
    }
    return {
        "status": "success",
        "instagram_zernio_post_json": json.dumps(ig_payload, ensure_ascii=False),
        "tiktok_zernio_post_json": json.dumps(tt_payload, ensure_ascii=False),
        "recovered_from_manifest": True,
    }


def process_record(
    env: dict[str, str],
    pair: dict,
    rec: dict,
    *,
    dry_run: bool,
    skip_cleanup: bool,
    tiktok_only: bool,
) -> dict[str, Any]:
    fields = rec.get("fields", {})
    name = fields.get("Name")
    if not name:
        raise RuntimeError("Record missing Name")

    dropbox_token = get_access_token(env)
    slide_paths = list_slide_paths(dropbox_token, name)
    track = pick_track(env, pair)
    payload = build_render_payload(fields, slide_paths, track)

    if dry_run:
        return {"dry_run": True, "name": name, "payload": payload}

    if tiktok_only:
        image_urls = [ensure_shared_link(p, dropbox_token) for p in slide_paths]
        tt_payload = build_tiktok_payload(fields, image_urls, env["ZERNIO_TIKTOK_ACCOUNT_ID"])
        result: dict[str, Any] = {"name": name, "tiktok": post_zernio(env, tt_payload), "mode": "tiktok_only"}
    else:
        ready_path = f"/Ready_Carousel/{name}"
        if count_ready_videos(dropbox_token, name) > 0:
            delete_dropbox_folder(dropbox_token, ready_path)
        render = wait_for_render(env, payload, dropbox_token, name)
        ig_json = render.get("instagram_zernio_post_json")
        tt_json = render.get("tiktok_zernio_post_json")
        if not ig_json or not tt_json:
            raise RuntimeError("Missing zernio JSON after render")
        result = {
            "name": name,
            "airtable_id": rec["id"],
            "instagram": post_zernio(env, ig_json),
            "tiktok": post_zernio(env, tt_json),
            "recovered_from_manifest": render.get("recovered_from_manifest", False),
        }

    try:
        from telegram_notify import notify_add_music

        notify_add_music("TikTok", pair.get("label", "pair1"), name)
        notify_add_music("Instagram", pair.get("label", "pair1"), name)
    except Exception as exc:  # noqa: BLE001
        result["telegram_error"] = str(exc)

    if not skip_cleanup:
        delete_record(
            env["AIRTABLE_ACCESS_TOKEN"],
            pair["airtable"]["base_id"],
            pair["airtable"]["table_id"],
            rec["id"],
        )
        delete_dropbox_folder(dropbox_token, f"{CONTENT_PLAN_ROOT.rstrip('/')}/{name}")
        result["cleanup"] = True

    return result


def run_publish_batch(
    *,
    pair_id: str = "pair1",
    limit: int = 1,
    name: str | None = None,
    dry_run: bool = False,
    skip_cleanup: bool = False,
    tiktok_only: bool = False,
    include_published: bool = False,
) -> dict[str, Any]:
    env = load_runtime_env()
    pair = pair_config(pair_id)
    dropbox_token = get_access_token(env)
    state = load_state(dropbox_token)
    published = set(state.get("published", []))
    records = list_queue_records(env, pair)

    if name:
        records = [r for r in records if r.get("fields", {}).get("Name") == name]
    elif not include_published:
        records = [r for r in records if r.get("fields", {}).get("Name") not in published]

    records = sorted(records, key=lambda r: r.get("fields", {}).get("Name", ""))
    if not records:
        return {"status": "empty", "message": "Queue empty or all published", "results": []}

    results: list[dict] = []
    errors: list[dict] = []

    for rec in records[: max(1, limit)]:
        carousel_name = rec.get("fields", {}).get("Name", "")
        try:
            res = process_record(
                env, pair, rec, dry_run=dry_run, skip_cleanup=skip_cleanup, tiktok_only=tiktok_only
            )
            if not dry_run:
                published.add(carousel_name)
                state["published"] = sorted(published)
                state.setdefault("last_run", {})[carousel_name] = {
                    "at": datetime.now(timezone.utc).isoformat(),
                    "ok": True,
                }
            results.append(res)
        except Exception as exc:  # noqa: BLE001
            state.setdefault("failed", {})[carousel_name] = {
                "at": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }
            errors.append({"name": carousel_name, "error": str(exc)})

    if not dry_run:
        save_state(state, dropbox_token)

    status = "ok" if results and not errors else ("partial" if results else "error")
    return {
        "status": status,
        "pair": pair_id,
        "processed": len(results),
        "errors": errors,
        "results": results,
        "at": datetime.now(timezone.utc).isoformat(),
    }
