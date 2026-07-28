#!/usr/bin/env python3
"""Автоматический воркер публикации (локально или cloud через publish_engine)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))

from publish_config import MEMORY  # noqa: E402
from publish_engine import run_publish_batch  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="pair1", choices=["pair1", "pair2"])
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--name", help="Конкретная карусель по Name")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-cleanup", action="store_true")
    parser.add_argument("--tiktok-only", action="store_true")
    parser.add_argument("--include-published", action="store_true")
    args = parser.parse_args()

    result = run_publish_batch(
        pair_id=args.pair,
        limit=args.limit,
        name=args.name,
        dry_run=args.dry_run,
        skip_cleanup=args.skip_cleanup,
        tiktok_only=args.tiktok_only,
        include_published=args.include_published,
    )

    out = MEMORY / "output" / "worker-last-run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "error" and not result.get("results"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
