#!/usr/bin/env python3
"""Очистка EXIF/AI-метаданных у всех slide-*.png в папке (обязательный gate перед публикацией)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))

from image_metadata_cleaner import clean_slides_directory, load_slides_copy  # noqa: E402
from publish_config import MEMORY, merge_env  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slides-dir", required=True)
    parser.add_argument("--report", help="JSON report path")
    parser.add_argument("--skip", action="store_true", help="Emergency only — не использовать в проде")
    args = parser.parse_args()

    if args.skip:
        print("SKIP metadata clean (не для публикации)")
        return 0

    slides_dir = Path(args.slides_dir)
    if not slides_dir.is_absolute():
        slides_dir = SCRIPTS.parent / slides_dir

    env = merge_env(MEMORY / "cleaner.env.local")
    api_key = env.get("AI_CLEANER_API_KEY", "")
    api_url = env.get("AI_CLEANER_API_URL", "https://mcp-kv.ru/ai-delete/api/clean")
    if not api_key:
        print("ERROR: AI_CLEANER_API_KEY missing in carusel-memory/cleaner.env.local", file=sys.stderr)
        return 1

    workspace = SCRIPTS.parent
    reports = clean_slides_directory(
        slides_dir,
        api_key=api_key,
        api_url=api_url,
        slides_copy=load_slides_copy(workspace),
    )
    out = {"slides_dir": str(slides_dir), "cleaned": len(reports), "items": reports}
    report_path = Path(args.report) if args.report else slides_dir / "metadata-clean-report.json"
    report_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
