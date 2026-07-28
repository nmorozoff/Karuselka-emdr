#!/usr/bin/env python3
"""Подготовка dual-variant run из inbox (ссылка из Telegram).

Шаги:
  1. Читает carusel-memory/intake/inbox.json (READY_FOR_AGENT)
  2. competitor_decompose.py --url
  3. Создаёт carusel-memory/runs/{run_id}/ с variant-a (pair1 style) и variant-b (minimalism)
  4. Пишет run-request.json для Директора (Task: copywriter x2, designer, image-prompter, runware master 3x2)

Usage:
  python scripts/pipeline_run_from_inbox.py
  python scripts/pipeline_run_from_inbox.py --decompose-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
WORKSPACE = SCRIPTS.parent
MEMORY = WORKSPACE / "carusel-memory"
INTAKE = MEMORY / "intake" / "inbox.json"

sys.path.insert(0, str(SCRIPTS / "lib"))
from style_rotation import next_pair1_style, pair2_style  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decompose-only", action="store_true")
    args = parser.parse_args()

    if not INTAKE.exists():
        raise SystemExit(f"No inbox: {INTAKE}")

    inbox = json.loads(INTAKE.read_text(encoding="utf-8"))
    if inbox.get("status") != "READY_FOR_AGENT":
        raise SystemExit(f"Inbox status: {inbox.get('status')}")

    url = inbox["source_url"]
    run_id = inbox.get("run_id") or f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    run_dir = MEMORY / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    style_a = next_pair1_style()
    style_b = pair2_style()

    subprocess.run(
        [sys.executable, str(SCRIPTS / "competitor_decompose.py"), "--url", url, "--use-cache"],
        cwd=WORKSPACE,
        check=True,
    )

    for variant, style, pair in (
        ("variant-a", style_a, "pair1"),
        ("variant-b", style_b, "pair2"),
    ):
        vdir = run_dir / variant
        vdir.mkdir(exist_ok=True)
        (vdir / "slides").mkdir(exist_ok=True)
        (vdir / "style.json").write_text(
            json.dumps({"pair": pair, **style}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        guide_path = MEMORY / "styles" / style["guide_file"]
        if guide_path.exists():
            (vdir / "STYLE_GUIDE.md").write_text(guide_path.read_text(encoding="utf-8"), encoding="utf-8")

    request = {
        "run_id": run_id,
        "source_url": url,
        "status": "AWAITING_TASKS",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variants": {
            "variant-a": {"pair": "pair1", "style": style_a, "dir": str(run_dir / "variant-a")},
            "variant-b": {"pair": "pair2", "style": style_b, "dir": str(run_dir / "variant-b")},
        },
        "director_tasks": [
            "carusel-copywriter (shared copy → both variants)",
            "carusel-designer variant-a + variant-b",
            "carusel-image-prompter per style guide",
            "runware master 3x2 ONE call per variant (image-gen-budget-policy)",
            "export_publish_bundle.py --pair pair1 --variant-dir .../variant-a",
            "export_publish_bundle.py --pair pair2 --variant-dir .../variant-b",
        ],
        "make": "3 carousels/day per pair — see deploy/make/README-KARUSELKA.md",
    }
    (run_dir / "run-request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")

    inbox["status"] = "PROCESSING"
    inbox["run_dir"] = str(run_dir)
    INTAKE.write_text(json.dumps(inbox, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(request, ensure_ascii=False, indent=2))
    if args.decompose_only:
        return
    print("\n→ Директор: запусти Task-цепочку по run-request.json")


if __name__ == "__main__":
    main()
