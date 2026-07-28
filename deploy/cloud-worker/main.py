"""Karuselka publish worker — HTTP trigger for Cloud Scheduler."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query
from publish_engine import run_publish_batch

app = FastAPI(title="Karuselka Publish Worker", version="1.0.0")

WORKER_API_KEY = os.environ.get("WORKER_API_KEY", "")


def _auth(x_worker_key: str | None) -> None:
    if not WORKER_API_KEY:
        raise HTTPException(status_code=500, detail="WORKER_API_KEY not configured")
    if x_worker_key != WORKER_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid worker key")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "karuselka-publish-worker"}


@app.post("/run")
def run_publish(
    x_worker_key: str | None = Header(default=None, alias="X-Worker-Key"),
    pair: str = Query(default="pair1"),
    limit: int = Query(default=1, ge=1, le=3),
    name: str | None = Query(default=None),
    dry_run: bool = Query(default=False),
    skip_cleanup: bool = Query(default=False),
    tiktok_only: bool = Query(default=False),
) -> dict[str, Any]:
    _auth(x_worker_key)
    return run_publish_batch(
        pair_id=pair,
        limit=limit,
        name=name,
        dry_run=dry_run,
        skip_cleanup=skip_cleanup,
        tiktok_only=tiktok_only,
    )
