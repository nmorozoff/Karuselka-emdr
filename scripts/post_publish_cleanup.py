#!/usr/bin/env python3
"""После публикации Make: Telegram «добавь музыку» + удалить Airtable + Dropbox.

Make HTTP module в конце сценария:
  POST https://YOUR_TUNNEL/post-publish-cleanup
  Body: {"pair":"pair1","airtable_record_id":"rec...","dropbox_path":"/Content_Plan/...","platform":"tiktok","post_url":"..."}

Или локально:
  python scripts/post_publish_cleanup.py --pair pair1 --record recXXX --dropbox /path --platform tiktok

"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS / "lib"))

from airtable_client import delete_record  # noqa: E402
from dropbox_client import get_access_token  # noqa: E402
from publish_config import MEMORY, merge_env, pair_config  # noqa: E402
from telegram_notify import notify_add_music  # noqa: E402


def cleanup(payload: dict) -> dict:
    pair_id = payload.get("pair", "pair1")
    pair = pair_config(pair_id)
    env = merge_env(MEMORY / "dropbox.env.local", MEMORY / "airtable.env.local")

    platform = payload.get("platform", "tiktok")
    post_url = payload.get("post_url", "")
    notify_add_music(platform, pair.get("label", pair_id), post_url)

    record_id = payload.get("airtable_record_id", "")
    base_id = env.get("AIRTABLE_BASE_ID") or pair["airtable"]["base_id"]
    table_id = (
        env.get("AIRTABLE_PAIR1_TABLE_ID" if pair_id == "pair1" else "AIRTABLE_PAIR2_TABLE_ID")
        or pair["airtable"]["table_id"]
    )
    if record_id and env.get("AIRTABLE_ACCESS_TOKEN"):
        delete_record(env["AIRTABLE_ACCESS_TOKEN"], base_id, table_id, record_id)

    dropbox_path = payload.get("dropbox_path", "")
    if dropbox_path and env.get("DROPBOX_ACCESS_TOKEN"):
        token = get_access_token(env)
        import urllib.request

        req = urllib.request.Request(
            "https://api.dropboxapi.com/2/files/delete_v2",
            data=json.dumps({"path": dropbox_path}).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=60)
        except Exception as e:
            return {"ok": True, "notify": "sent", "dropbox_delete_error": str(e)}

    return {"ok": True, "notify": "sent", "airtable_deleted": bool(record_id), "dropbox_deleted": bool(dropbox_path)}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
            result = cleanup(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, fmt, *args):
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="pair1")
    parser.add_argument("--record", default="")
    parser.add_argument("--dropbox", default="")
    parser.add_argument("--platform", default="tiktok")
    parser.add_argument("--post-url", default="")
    parser.add_argument("--serve", type=int, default=0, help="HTTP server port for Make webhook")
    args = parser.parse_args()

    if args.serve:
        server = HTTPServer(("127.0.0.1", args.serve), Handler)
        print(f"post_publish_cleanup listening http://127.0.0.1:{args.serve}/")
        server.serve_forever()
    else:
        print(json.dumps(cleanup({
            "pair": args.pair,
            "airtable_record_id": args.record,
            "dropbox_path": args.dropbox,
            "platform": args.platform,
            "post_url": args.post_url,
        }), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
