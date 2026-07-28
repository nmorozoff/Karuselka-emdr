"""Rotate pair1 visual styles: light → dark → storytelling."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from publish_config import MEMORY, load_style_registry


def next_pair1_style() -> dict:
    registry = load_style_registry()
    rotation = registry["pair1_rotation"]
    state_path = MEMORY / "publish" / "style-rotation-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    idx = int(state.get("pair1_index", 0)) % len(rotation)
    style = rotation[idx]
    state["pair1_index"] = (idx + 1) % len(rotation)
    state.setdefault("history", []).append(
        {"at": datetime.now(timezone.utc).isoformat(), "style_id": style["id"], "name": style["name"]}
    )
    state["history"] = state["history"][-50:]
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    return style


def pair2_style() -> dict:
    return load_style_registry()["pair2_fixed"]
