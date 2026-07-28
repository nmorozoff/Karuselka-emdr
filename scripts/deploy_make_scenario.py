#!/usr/bin/env python3
"""Deploy Karuselka Make blueprints via REST API (Token auth)."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
MAKE_DIR = SCRIPTS.parent / "deploy" / "make"
MEMORY = SCRIPTS.parent / "carusel-memory"


def load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    path = MEMORY / "make.env.local"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def api(token: str, zone: str, method: str, url: str, body: dict | None = None, timeout: int = 120) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"https://{zone}/api/v2{url}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Make API {method} {url}: {e.code} {e.read().decode()[:500]}") from e


def list_scenarios(token: str, zone: str, team_id: str) -> list[dict]:
    out: list[dict] = []
    offset = 0
    while True:
        q = urllib.parse.urlencode({"teamId": team_id, "pg[limit]": 10, "pg[offset]": offset})
        try:
            data = api(token, zone, "GET", f"/scenarios?{q}")
        except SystemExit:
            if offset == 0:
                raise
            break
        batch = data.get("scenarios", [])
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 10:
            break
        offset += 10
        time.sleep(0.4)
    return out


def deploy_pair(token: str, zone: str, team_id: str, blueprint_file: Path, fallback_names: list[str]) -> str:
    blueprint = json.loads(blueprint_file.read_text(encoding="utf-8"))
    name = blueprint.get("name") or blueprint_file.stem
    scheduling = {"type": "indefinitely", "interval": 28800}
    payload = {
        "blueprint": json.dumps(blueprint, ensure_ascii=False),
        "scheduling": json.dumps(scheduling),
    }
    scenarios = list_scenarios(token, zone, team_id)
    sid = None
    for s in scenarios:
        if s.get("name") in fallback_names or s.get("name") == name:
            sid = s["id"]
            break
    if sid:
        result = api(token, zone, "PATCH", f"/scenarios/{sid}?confirmed=true", payload)
    else:
        result = api(
            token,
            zone,
            "POST",
            "/scenarios",
            {"teamId": int(team_id), "name": name, **payload},
        )
    scenario = result.get("scenario", {})
    return str(scenario.get("id", ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", choices=["pair1", "pair2", "both"], default="pair1")
    args = parser.parse_args()

    env = load_env()
    token = env.get("MAKE_API_TOKEN", "")
    zone = env.get("MAKE_ZONE", "eu2.make.com")
    team_id = env.get("MAKE_TEAM_ID", "1121616")
    if not token:
        raise SystemExit("MAKE_API_TOKEN missing in carusel-memory/make.env.local")

    pairs = []
    if args.pair in ("pair1", "both"):
        pairs.append(
            (
                MAKE_DIR / "karuselka-publish-pair1.blueprint.json",
                ["Karuselka Publish Pair1", "Выкладка каруселей Инста1 + Railway музыка (черновик)"],
            )
        )
    if args.pair in ("pair2", "both"):
        pairs.append((MAKE_DIR / "karuselka-publish-pair2.blueprint.json", ["Karuselka Publish Pair2"]))

    for bp, names in pairs:
        sid = deploy_pair(token, zone, team_id, bp, names)
        print(json.dumps({"blueprint": bp.name, "scenario_id": sid}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
