#!/usr/bin/env python3
"""Export carousel variant → Dropbox folder + Airtable row.

Usage:
  python scripts/export_publish_bundle.py --pair pair1 --variant-dir carusel-memory/runs/xxx/variant-a
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))
from airtable_client import create_record  # noqa: E402
from dropbox_client import get_access_token, upload_directory, create_folder  # noqa: E402
from image_metadata_cleaner import clean_slides_directory, load_slides_copy  # noqa: E402
from publish_config import MEMORY, merge_env, pair_config  # noqa: E402
from tiktok_caption_split import split_caption  # noqa: E402

SLIDES_GLOB = ("slide-*.png", "slide-*.jpg")


def folder_name(now: datetime) -> str:
    return f"crsl_{now.strftime('%Y%m%d_%H%M')}_{now.microsecond // 1000:03d}"


def load_caption(variant_dir: Path) -> str:
    cap_json = variant_dir / "CAROUSEL_CAPTION.json"
    if cap_json.exists():
        obj = json.loads(cap_json.read_text(encoding="utf-8"))
        return (obj.get("full_caption") or "").strip()
    cap_md = variant_dir / "CAROUSEL_CAPTION.md"
    if cap_md.exists():
        return cap_md.read_text(encoding="utf-8").strip()
    raise SystemExit(f"No caption in {variant_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True, choices=["pair1", "pair2"])
    parser.add_argument("--variant-dir", required=True, help="Folder with slides/ and CAROUSEL_CAPTION.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-metadata-clean", action="store_true", help="Emergency only")
    args = parser.parse_args()

    variant_dir = Path(args.variant_dir)
    if not variant_dir.is_absolute():
        variant_dir = SCRIPTS.parent / variant_dir
    slides_dir = variant_dir / "slides"
    if not slides_dir.is_dir():
        raise SystemExit(f"Missing {slides_dir}")

    env = merge_env(
        MEMORY / "dropbox.env.local",
        MEMORY / "airtable.env.local",
        MEMORY / "cleaner.env.local",
    )

    if not args.dry_run and not args.skip_metadata_clean:
        api_key = env.get("AI_CLEANER_API_KEY", "")
        if not api_key:
            raise SystemExit("AI_CLEANER_API_KEY missing — export без очистки метаданных запрещён")
        clean_reports = clean_slides_directory(
            slides_dir,
            api_key=api_key,
            api_url=env.get("AI_CLEANER_API_URL", "https://mcp-kv.ru/ai-delete/api/clean"),
            slides_copy=load_slides_copy(SCRIPTS.parent),
        )
        (variant_dir / "metadata-clean-report.json").write_text(
            json.dumps({"cleaned": len(clean_reports), "items": clean_reports}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    pair = pair_config(args.pair)
    caption = load_caption(variant_dir)
    tiktok_title, tiktok_desc = split_caption(caption)
    now = datetime.now(timezone.utc)
    name = folder_name(now)
    dropbox_root = pair["dropbox_root"].rstrip("/")
    dropbox_path = f"{dropbox_root}/{name}"

    at = pair["airtable"]
    base_id = env.get("AIRTABLE_BASE_ID") or at.get("base_id")
    table_id = (
        env.get("AIRTABLE_PAIR1_TABLE_ID" if args.pair == "pair1" else "AIRTABLE_PAIR2_TABLE_ID")
        or at.get("table_id")
    )
    if not base_id or not table_id or "FILL" in str(table_id):
        raise SystemExit("Configure Airtable IDs in accounts-pairs.json and airtable.env.local")

    fields = {
        at["fields"]["name"]: name,
        at["fields"]["instagram_caption"]: caption[:100000],
        at["fields"]["tiktok_title"]: tiktok_title,
        at["fields"]["tiktok_description"]: tiktok_desc,
    }
    if at["fields"].get("folder_path"):
        fields[at["fields"]["folder_path"]] = dropbox_path

    manifest = {
        "pair": args.pair,
        "folderName": name,
        "folderPath": dropbox_path,
        "createdAt": now.isoformat(),
        "tiktok": {"title": tiktok_title, "description": tiktok_desc},
        "style": json.loads((variant_dir / "style.json").read_text()) if (variant_dir / "style.json").exists() else {},
    }

    if args.dry_run:
        print(json.dumps({"dropbox_path": dropbox_path, "airtable_fields": fields, "manifest": manifest}, ensure_ascii=False, indent=2))
        return

    token = get_access_token(env)
    create_folder(dropbox_path, token)
    # staging bundle
    bundle = variant_dir / "publish-bundle"
    bundle.mkdir(exist_ok=True)
    for slide in sorted(slides_dir.glob("slide-*.png")) + sorted(slides_dir.glob("slide-*.jpg")):
        bundle.joinpath(slide.name).write_bytes(slide.read_bytes())
    (bundle / "caption.txt").write_text(caption, encoding="utf-8")
    (bundle / "tiktok-caption.json").write_text(json.dumps(manifest["tiktok"], ensure_ascii=False, indent=2), encoding="utf-8")
    (bundle / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    upload_directory(bundle, dropbox_path, token)

    at_token = env.get("AIRTABLE_ACCESS_TOKEN", "")
    if not at_token:
        raise SystemExit("AIRTABLE_ACCESS_TOKEN missing")
    record_id = create_record(at_token, base_id, table_id, fields)

    out = {
        "success": True,
        "pair": args.pair,
        "folderName": name,
        "dropboxPath": dropbox_path,
        "airtableRecordId": record_id,
        "tiktokTitle": tiktok_title,
    }
    log_path = variant_dir / "export-log.json"
    log_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
