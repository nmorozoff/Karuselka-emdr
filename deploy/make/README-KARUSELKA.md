# Пайплайн публикации Каруселька v3

Два варианта дизайна на одну ссылку → две пары IG+TikTok → Make по расписанию.

## Поток

```text
Telegram (ссылка IG)
  → telegram_intake_bridge.py → intake/inbox.json READY_FOR_AGENT
  → pipeline_run_from_inbox.py (decompose + run-request)
  → Director Task: copywriter → designer x2 → image-prompter x2 → Runware master 3×2 x2
  → export_publish_bundle.py (pair1 + pair2)
       → Dropbox /Content_Plan/Pair1|Pair2/crsl_...
       → Airtable (очередь Make)
  → Make (3×/день на пару): IG + TikTok (Zernio auto_add_music)
  → post_publish_cleanup.py: Telegram «добавь музыку» + delete Airtable + Dropbox
```

## Пары аккаунтов

| | Pair 1 | Pair 2 |
|---|--------|--------|
| Стиль | Ротация: светлая инфографика / тёмная / сторителлинг | Минимализм (промпт от вас) |
| Dropbox | `accounts-pairs.json` → pair1.dropbox_root | pair2.dropbox_root |
| Airtable | pair1 table | pair2 table |
| Make | сценарий Pair1 | сценарий Pair2 |

Настройка: `carusel-memory/publish/accounts-pairs.json`

## Стили pair 1 (из ai-carousel-natasha)

- `carusel-memory/styles/expert-infographic-light.md`
- `carusel-memory/styles/expert-infographic-dark.md`
- `carusel-memory/styles/storytelling.md`

Ротация: `scripts/lib/style_rotation.py` + `publish/style-rotation-state.json`

## Make

Blueprints (на базе natasha `vykladka-karusely-inst1-fixed`):

| Файл | Пара | Dropbox root | Airtable table |
|------|------|--------------|----------------|
| `karuselka-publish-pair1.blueprint.json` | Pair1 | `/Content_Plan/Pair1/{Name}` | `tblFWCmLCXLrOdKut` |
| `karuselka-publish-pair2.blueprint.json` | Pair2 | `/Content_Plan/Pair2/{Name}` | `tbl2zotNwOmWLSTyC` |

Референс: `/Users/natala/Documents/Playground/ai-carousel-natasha/deploy/make/`

### Импорт в Make

1. **Import Blueprint** → `deploy/make/karuselka-publish-pair1.json` (и отдельно pair2)
2. Подключить Instagram, Airtable, Dropbox (те же connections что в natasha)
3. Zernio API key + `accountId` TikTok для каждой пары
4. Расписание: **3×/день** (каждые 8 ч) или три сценария

### PATCH через API

```bash
export MAKE_API_TOKEN="токен Make → Profile → API"
cd deploy/make
MAKE_SCENARIO_NAME="Karuselka Publish Pair1" BLUEPRINT_FILE=karuselka-publish-pair1.blueprint.json ./patch-make-scenario.sh
MAKE_SCENARIO_NAME="Karuselka Publish Pair2" BLUEPRINT_FILE=karuselka-publish-pair2.blueprint.json ./patch-make-scenario.sh
```

MCP `user-make` в Cursor сейчас недоступен — нужен REST API token.

## Airtable — таблица Pair2

```bash
# Таблица Pair2 уже создана: tbl2zotNwOmWLSTyC
# При необходимости пересоздать:
python scripts/create_airtable_pair2_table.py
```

Поля таблицы Pair2 (как Pair1): `Name`, `Описание карусели`, `TikTok заголовок`, `TikTok описание`, `Dropbox Path`, `Created At`.

### 3 карусели в день

Варианты в Make:

1. **Schedule** каждые 8 часов (08:00, 16:00, 00:00)
2. Три отдельных сценария с разным временем
3. Airtable: брать **3 старые** строки за раз (Limit 3) — только если очередь всегда полна

## TikTok (Zernio)

Обязательно в API (см. `scripts/publish-zernio-carousel.py`):

```json
"tiktokSettings": {
  "media_type": "photo",
  "auto_add_music": true,
  "description": "...",
  "content_preview_confirmed": true,
  "express_consent_given": true
}
```

После публикации — **ручная смена музыки** в TikTok; бот напомнит.

## Секреты

| Файл | Назначение |
|------|------------|
| `telegram.env.local` | intake + notify |
| `dropbox.env.local` | экспорт слайдов |
| `airtable.env.local` | очередь Make |
| `zernio.env.local` | TikTok (если не только Make) |
| `analyze.env.local` | Apify + Kimi |
| `runware.env.local` | генерация |

## Команды

```bash
# Тестовая публикация из очереди Airtable (без Make)
python scripts/test_publish_from_queue.py --list
python scripts/test_publish_from_queue.py --name crsl_20260702_1234_o00dkh --tiktok-only
python scripts/test_publish_from_queue.py --name crsl_...            # Cloud Run + Zernio IG+TT
```

**Важно:** карусели лежат в Dropbox `/Content_Plan/{Name}` (поле `Name` в Airtable). Blueprint Make использует тот же путь (не `/Content_Plan/Pair1/`).

## Автоворкер (без Make / пока Cloud Run > 40s)

```bash
python scripts/publish_worker.py --pair pair1 --limit 1
./scripts/run_publish_worker.sh
```

**Облако (Mac выключен):** `deploy/cloud-worker/README.md` — Cloud Scheduler **11:00 / 17:00 / 21:00** MSK.

```bash
./scripts/prepare_cloud_env.sh
./deploy/cloud-worker/deploy.sh
./deploy/cloud-worker/setup-scheduler.sh
```

Локальный cron (`install_publish_cron.sh`) — только резерв при включённом Mac.

```bash
# 1. Bridge (фон)
python scripts/telegram_intake_bridge.py --poll

# 2. После ссылки в боте
python scripts/pipeline_run_from_inbox.py

# 3. После генерации слайдов
python scripts/export_publish_bundle.py --pair pair1 --variant-dir carusel-memory/runs/RUN_ID/variant-a
python scripts/export_publish_bundle.py --pair pair2 --variant-dir carusel-memory/runs/RUN_ID/variant-b

# 4. Webhook для Make (локально + ngrok)
python scripts/post_publish_cleanup.py --serve 8766
```

## Cloud (целевое состояние)

После завершения отладки локально пайплайн v3 переносится в **изолированную Cloud-среду**:

```text
[Cloud worker / Cloud Run]
  Telegram webhook или poll-bridge
  → decompose + copy/design/generate (API)
  → metadata clean (AI Cleaner)
  → export → Dropbox + Airtable
  → (внешне) Make 3×/день → IG + TikTok Zernio
  → cleanup webhook → Telegram notify
```

Принципы:

- Секреты: Secret Manager / env injection (не `*.local` в git)
- Один воркер на run_id, идемпотентный export
- Healthcheck + логи; при сбое — Telegram alert
- Cursor + Task-субагенты остаются инструментом **разработки**, не production runtime

Референс деплоя: `ai-carousel-natasha/deploy/cloud-run/`.

## Что нужно от вас

1. **Airtable PAT** → `airtable.env.local`, затем `python scripts/create_airtable_pair2_table.py`
2. **Make API token** → импорт/patch двух blueprints (см. выше)
3. **Zernio:** TikTok account ID для каждой пары → `accounts-pairs.json`
4. **Instagram handles** для pair1/pair2 → `accounts-pairs.json`
