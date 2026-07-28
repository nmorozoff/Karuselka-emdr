# КАРУСЕЛЬКА — Instagram-карусели для Натальи Морозовой

Рабочий проект для плагина **Каруселька** (Cursor local plugin).

## Что установлено

| Компонент | Путь |
|-----------|------|
| Плагин Каруселька | `~/.cursor/plugins/local/carusel` |
| Репозиторий (справка) | `./Karuselka/` |
| Плагин Гиперион (Reels/Shorts) | `~/.cursor/plugins/local/hyperion` |
| Профиль ниши | `carusel-memory/profile/niche-profile.md` |
| Очередь тем | `carusel-memory/profile/topics-queue.md` |

> **Важно:** ссылка `hyperion-reels` — это **нарезка видео Reels**, не Instagram-карусели. Для каруселей используется **Karuselka**.

## Секреты и настройка

См. **`carusel-memory/SECRETS.md`** — куда положить Runware API, Telegram-бота и Apify/Kimi/Groq.

```bash
cd carusel-memory
cp runware.env.example runware.env.local
cp telegram.env.example telegram.env.local
cp analyze.env.example analyze.env.local
# заполни ключи в *.local
```

## Формат

- **6 слайдов** 4:5 (не 9-panel grid) — см. `carusel-memory/profile/format-6-slides.md`
- Промпт копирайта: `carusel-memory/profile/custom-copy-prompt.md` (мастер-промпт КАРУСЕЛЬКИ)
- Разбор конкурентов: Apify + Kimi K2.5 + Groq — `profile/analyze-stack.md`

## Команда

`/carusel-new` — новая карусель

## Пайплайн v3 (Telegram → 2 варианта → Airtable/Dropbox → публикация)

Полная схема: **`deploy/make/README-KARUSELKA.md`**

**Автопубликация (воркер, без Make):**

```bash
python scripts/publish_worker.py --pair pair1 --limit 1
./scripts/run_publish_worker.sh   # обёртка для cron
```

Очередь: Airtable `Name` = папка в Dropbox `/Content_Plan/{Name}`. Уже опубликованные — `carusel-memory/publish/worker-state.json`.

**Облако (11:00 / 17:00 / 21:00 MSK, Mac выключен):** `deploy/cloud-worker/README.md`

```bash
cp carusel-memory/cloud-worker.env.example carusel-memory/cloud-worker.env.local
./scripts/prepare_cloud_env.sh
./scripts/sync_worker_state_to_dropbox.sh   # опционально
./deploy/cloud-worker/deploy.sh
./deploy/cloud-worker/setup-scheduler.sh
```


## Пайплайн (ручной /carusel-new)

```text
researcher → copywriter → designer → image-prompter → slice
→ motion-director → animate → design-guardian → upload → publish
```
