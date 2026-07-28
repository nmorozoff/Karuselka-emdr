# Облачная автоматизация публикации (Mac может быть выключен)

Публикация **11:00 / 17:00 / 21:00** (Europe/Moscow) через **Google Cloud Scheduler → Cloud Run worker**.

```text
Cloud Scheduler (11, 17, 21 MSK)
    → POST /run  (X-Worker-Key)
    → karuselka-publish-worker (Cloud Run)
        → Airtable queue
        → Cloud Run renderer (7 mp4)
        → Zernio IG + TikTok
        → cleanup Airtable + Dropbox /Content_Plan/{Name}
    → worker-state в Dropbox /Content_Plan/.karuselka/worker-state.json
```

## Быстрый старт

### 1. Секреты

```bash
cp carusel-memory/cloud-worker.env.example carusel-memory/cloud-worker.env.local
# Заполните PROJECT_ID, WORKER_API_KEY (случайная строка)
```

Остальные ключи уже в `airtable.env.local`, `dropbox.env.local`, `zernio.env.local`, `telegram.env.local`.

### 2. Сгенерировать env для Cloud Run

```bash
chmod +x scripts/prepare_cloud_env.sh deploy/cloud-worker/*.sh
./scripts/prepare_cloud_env.sh
```

Создаёт `deploy/cloud-worker/.env.deploy.yaml` (в `.gitignore`).

### 3. Синхронизировать state (опционально)

Чтобы cloud не переопубликовал уже выложенные карусели:

```bash
./scripts/sync_worker_state_to_dropbox.sh
```

### 4. Деплой Cloud Run

```bash
# Создайте deploy/cloud-worker/.env.deploy с PROJECT_ID=...
./deploy/cloud-worker/deploy.sh
```

### 5. Расписание 11 / 17 / 21

```bash
./deploy/cloud-worker/setup-scheduler.sh
```

### 6. Ручной тест

```bash
curl -sS -X POST \
  -H "X-Worker-Key: YOUR_WORKER_API_KEY" \
  "https://YOUR-WORKER-URL/run?pair=pair1&limit=1&dry_run=true"
```

## Локальный cron (резерв)

`./scripts/install_publish_cron.sh` — только если Mac **включён**. Для production используйте Cloud Scheduler.

## Файлы

| Путь | Назначение |
|------|------------|
| `scripts/lib/publish_engine.py` | Ядро (локально + cloud) |
| `scripts/lib/worker_state.py` | State local / Dropbox |
| `deploy/cloud-worker/` | Docker + deploy + scheduler |
| `carusel-memory/publish/worker-state.json` | Локальный state |
| Dropbox `/.karuselka/worker-state.json` | Cloud state |

## Требования GCP

- Cloud Run API
- Cloud Scheduler API
- Billing включён
- `gcloud auth login` + права на deploy

## Переменные Cloud Run

См. `env.example` и `scripts/prepare_cloud_env.sh`.

Обязательные: `WORKER_API_KEY`, `AIRTABLE_ACCESS_TOKEN`, Dropbox OAuth trio, `ZERNIO_*`, `CLOUD_RUN_API_KEY`.
