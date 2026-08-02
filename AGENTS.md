# AGENTS.md

## Cursor Cloud specific instructions

Каруселька is a Python 3.12 Instagram/TikTok carousel **publishing pipeline** (a Cursor local-plugin companion repo). It is a chain of CLI stages plus one long-running service; it is not a single web app.

### Dependencies / environment
- The codebase is almost entirely Python **standard library** (`urllib`, `json`, `http.server`, `argparse`, …). The only third-party packages are `fastapi` + `uvicorn[standard]` (for the Cloud Run worker) and optional `Pillow` (image resize in `scripts/runware-carousel-gen.py`, imported behind `try/except ImportError`).
- The startup update script installs these into a `.venv` at the repo root (git-ignored). Use `.venv/bin/python` / `.venv/bin/uvicorn` to run everything. There is no `pip` conflict with the system Python if you use the venv.
- The pinned service deps live in `deploy/cloud-worker/requirements.txt`. `Pillow` is intentionally not in that file (the Cloud Run worker doesn't need it) — it is installed separately for local script development.

### Running the one real service (Cloud Run publish worker)
`deploy/cloud-worker/main.py` is a FastAPI app. `main.py` imports `publish_engine` from `scripts/lib`, so `PYTHONPATH` must include both dirs:
```bash
WORKER_API_KEY=<any> PYTHONPATH="deploy/cloud-worker:scripts/lib" .venv/bin/uvicorn main:app --host 127.0.0.1 --port 8080
```
- `GET /health` works with no secrets. `POST /run` requires the `X-Worker-Key` header to equal `WORKER_API_KEY` (else 401), then calls the full publish pipeline.
- `POST /run` will 500 without real external credentials — it fails at the first external boundary (`dropbox_client.get_access_token`). This is expected in the cloud VM; it proves the code path runs, not a bug.

### CLI stages (one-off scripts in `scripts/`)
Run with `.venv/bin/python scripts/<name>.py --help`. Minimal end-to-end product path: `competitor_decompose.py` → `runware-carousel-gen.py` → `export_publish_bundle.py` → `publish_worker.py`. All of these hit external APIs and need secrets to do real work.

### Secrets (why full end-to-end can't run in the cloud VM by default)
Every real pipeline action depends on external API secrets. Locally these are loaded from `carusel-memory/*.env.local` dotenv files (see `carusel-memory/SECRETS.md`); with `KARUSELKA_RUNTIME=cloud` they must come from real environment variables. Required services: Runware, Kimi/Moonshot, Apify, Dropbox (OAuth trio), Airtable, Zernio, Telegram, an external Cloud Run renderer, and the `mcp-kv` AI metadata cleaner. Add these as Cursor Secrets to exercise the full publish flow. Without them you can still verify the service (`/health`, auth) and the pure-logic libs (e.g. `scripts/lib/tiktok_caption_split.py`).

### Lint / test
There is **no configured linter and no test framework** in this repo (`scripts/test_publish_from_queue.py` is a manual live-API harness, not an automated test). Use `.venv/bin/python -m py_compile scripts/*.py scripts/lib/*.py deploy/cloud-worker/main.py` as the syntax/lint gate.
