"""Airtable queue records."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


def create_record(
    token: str,
    base_id: str,
    table_id: str,
    fields: dict[str, str],
) -> str:
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}"
    payload = {"records": [{"fields": fields}], "typecast": True}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Airtable create error: {e.read().decode()}") from e
    rec_id = data.get("records", [{}])[0].get("id")
    if not rec_id:
        raise SystemExit(f"Airtable: no record id in {data}")
    return rec_id


def delete_record(token: str, base_id: str, table_id: str, record_id: str) -> None:
    url = f"https://api.airtable.com/v0/{base_id}/{table_id}/{record_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}"},
        method="DELETE",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Airtable delete error: {e.read().decode()}") from e
