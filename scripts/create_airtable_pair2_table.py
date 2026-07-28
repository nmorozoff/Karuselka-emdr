#!/usr/bin/env python3
"""Create Airtable table «Каруселька Pair2 (Минимализм)» in existing base.

Requires airtable.env.local with AIRTABLE_ACCESS_TOKEN (scope: schema.bases:write).

Usage:
  python scripts/create_airtable_pair2_table.py
  python scripts/create_airtable_pair2_table.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
MEMORY = SCRIPTS.parent / "carusel-memory"
PAIRS_JSON = MEMORY / "publish" / "accounts-pairs.json"

TABLE_NAME = "Каруселька Pair2 (Минимализм)"
TABLE_DESCRIPTION = "Очередь публикации Make — пара IG2+TikTok2, стиль Минимализм"


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def api_request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Airtable API {e.code}: {e.read().decode()}") from e


def table_schema() -> dict:
    return {
        "name": TABLE_NAME,
        "description": TABLE_DESCRIPTION,
        "fields": [
            {"name": "Name", "type": "singleLineText"},
            {"name": "Описание карусели", "type": "multilineText"},
            {"name": "TikTok заголовок", "type": "singleLineText"},
            {"name": "TikTok описание", "type": "multilineText"},
            {"name": "Dropbox Path", "type": "singleLineText"},
            {
                "name": "Created At",
                "type": "dateTime",
                "options": {
                    "dateFormat": {"name": "iso", "format": "YYYY-MM-DD"},
                    "timeFormat": {"name": "24hour", "format": "HH:mm"},
                    "timeZone": "Europe/Moscow",
                },
            },
        ],
    }


def find_existing_table(token: str, base_id: str) -> str | None:
    data = api_request("GET", f"https://api.airtable.com/v0/meta/bases/{base_id}/tables", token)
    for table in data.get("tables", []):
        if table.get("name") == TABLE_NAME:
            return table.get("id")
    return None


def update_blueprint_table_id(table_id: str) -> None:
    bp_path = SCRIPTS.parent / "deploy" / "make" / "karuselka-publish-pair2.blueprint.json"
    if not bp_path.exists():
        return
    text = bp_path.read_text(encoding="utf-8")
    text = text.replace("FILL_ME_PAIR2_TABLE", table_id)
    bp_path.write_text(text, encoding="utf-8")


def update_pairs_json(pair2_table_id: str, base_id: str) -> None:
    pairs = json.loads(PAIRS_JSON.read_text(encoding="utf-8"))
    pairs["pair1"]["airtable"]["base_id"] = base_id
    pairs["pair1"]["airtable"]["table_id"] = pairs["natasha_reference"]["airtable_example_table_pair1"]
    pairs["pair2"]["airtable"]["base_id"] = base_id
    pairs["pair2"]["airtable"]["table_id"] = pair2_table_id
    PAIRS_JSON.write_text(json.dumps(pairs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_blueprint_table_id(pair2_table_id)


def write_env_local(token: str, base_id: str, pair2_table_id: str) -> None:
    env_path = MEMORY / "airtable.env.local"
    env_path.write_text(
        "\n".join(
            [
                "# Airtable — Каруселька (из base natasha)",
                f"AIRTABLE_ACCESS_TOKEN={token}",
                f"AIRTABLE_BASE_ID={base_id}",
                "AIRTABLE_PAIR1_TABLE_ID=tblFWCmLCXLrOdKut",
                f"AIRTABLE_PAIR2_TABLE_ID={pair2_table_id}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = load_env(MEMORY / "airtable.env.local")
    token = env.get("AIRTABLE_ACCESS_TOKEN", "")
    base_id = env.get("AIRTABLE_BASE_ID") or "appQTNsDMuodYyp34"

    if not token:
        raise SystemExit(
            "AIRTABLE_ACCESS_TOKEN missing in carusel-memory/airtable.env.local\n"
            "Возьмите PAT в Airtable → Builder hub → Personal access tokens "
            "(scopes: data.records:read/write + schema.bases:read/write)"
        )

    existing = find_existing_table(token, base_id)
    if existing:
        print(f"Table already exists: {existing}")
        if not args.dry_run:
            update_pairs_json(existing, base_id)
            write_env_local(token, base_id, existing)
        print(json.dumps({"base_id": base_id, "pair2_table_id": existing}, indent=2))
        return

    schema = table_schema()
    if args.dry_run:
        print(json.dumps({"action": "create", "base_id": base_id, "schema": schema}, ensure_ascii=False, indent=2))
        return

    result = api_request(
        "POST",
        f"https://api.airtable.com/v0/meta/bases/{base_id}/tables",
        token,
        schema,
    )
    table_id = result.get("id")
    if not table_id:
        raise SystemExit(f"No table id in response: {result}")

    write_env_local(token, base_id, table_id)
    update_pairs_json(table_id, base_id)
    print(json.dumps({"created": True, "base_id": base_id, "table_id": table_id, "name": TABLE_NAME}, indent=2))


if __name__ == "__main__":
    main()
