# Секреты КАРУСЕЛЬКА

Скопируйте каждый example → `.local` и заполните. **Не коммитить `.local` файлы.**

```bash
cd carusel-memory
cp runware.env.example runware.env.local
cp telegram.env.example telegram.env.local
cp analyze.env.example analyze.env.local
cp dropbox.env.example dropbox.env.local
cp airtable.env.example airtable.env.local
cp zernio.env.example zernio.env.local
cp cleaner.env.example cleaner.env.local
```

## Обязательные ключи (чеклист)

| # | Файл | Переменная | Зачем |
|---|------|------------|-------|
| 1 | `runware.env.local` | `RUNWARE_API_KEY` | генерация слайдов |
| 2 | `telegram.env.local` | `TELEGRAM_BOT_TOKEN` | бот intake + уведомления |
| 3 | `telegram.env.local` | `TELEGRAM_INTAKE_CHAT_ID` | куда ты шлёшь ссылки |
| 4 | `telegram.env.local` | `TELEGRAM_NOTIFY_CHAT_ID` | уведомление «добавь музыку» |
| 5 | `analyze.env.local` | **`KIMI_API_KEY`** | OCR слайдов + разбор структуры (Kimi K2.5) |
| 6 | `analyze.env.local` | `APIFY_TOKEN` | скачать IG carousel + caption |
| 7 | `analyze.env.local` | `GROQ_API_KEY` | транскрипт речи из видео (Whisper) |
| 8 | `dropbox.env.local` | `DROPBOX_ACCESS_TOKEN` | папки для Make |
| 9 | `airtable.env.local` | `AIRTABLE_*` | очередь публикации (2 таблицы) |
| 10 | `cleaner.env.local` | `AI_CLEANER_API_KEY` | **обязательная** очистка EXIF/AI-метаданных слайдов |
| 11 | `publish/accounts-pairs.json` | FILL_ME | пары IG/TikTok, пути Dropbox, table IDs |

Make API token — в Make Profile → API (не MCP). См. `deploy/make/README-KARUSELKA.md`.

Без **Kimi + Apify + Groq** разбор ссылок конкурентов не заработает (только ручной текст).

### Kimi API — где взять

1. https://platform.moonshot.ai/ → регистрация / вход  
2. Console → **API Keys** → Create  
3. Вставить в `analyze.env.local` → `KIMI_API_KEY=sk-...`  
4. Модель уже стоит: `KIMI_MODEL=kimi-k2.5`

### Telegram chat_id — как узнать

**Способ 1 (самый простой):**

1. Найди в Telegram бота **@userinfobot** или **@getidsbot**  
2. Нажми **Start**  
3. Он пришлёт твой id, например `123456789` — это и есть `chat_id`

**Способ 2 (через своего бота Каруселька):**

1. Открой своего бота (которого создала в @BotFather) → **Start**  
2. Напиши любое сообщение, например `привет`  
3. В браузере открой (подставь свой токен вместо `ТОКЕН`):

   `https://api.telegram.org/botТОКЕН/getUpdates`

4. В JSON найди `"chat":{"id": 123456789` — это число в оба поля:
   - `TELEGRAM_INTAKE_CHAT_ID=123456789`
   - `TELEGRAM_NOTIFY_CHAT_ID=123456789` (обычно то же самое)

**Если бот в группе:** добавь бота в группу, напиши в группе `/start`, снова `getUpdates` — `chat_id` группы будет **отрицательным** (например `-1001234567890`).

## Файлы

| Файл | Что внутри |
|------|------------|
| `runware.env.local` | `RUNWARE_API_KEY`, quality **medium**, 1080×1350 |
| `telegram.env.local` | токен **отдельного** бота, chat_id intake + notify |
| `analyze.env.local` | **Apify, Kimi K2.5, Groq Whisper** |
| `dropbox.env.local` | экспорт слайдов в Dropbox |
| `airtable.env.local` | очередь для Make (pair1 + pair2) |

## Музыка после публикации

### Instagram

После публикации бот шлёт в `TELEGRAM_NOTIFY_CHAT_ID`:

> Карусель опубликована. Открой Instagram → Редактировать → Музыка → добавь трек.

### TikTok (Zernio)

В API **обязательно** `tiktokSettings.auto_add_music: true` (см. `scripts/publish-zernio-carousel.py` и [Zernio TikTok docs](https://docs.zernio.com/platforms/tiktok)).

После успешной публикации бот шлёт:

> Карусель опубликована в TikTok. Zernio поставил рекомендованный трек (auto_add_music). Открой TikTok → Редактировать → **смени музыку** на нужную.

## Размеры слайдов

См. `profile/platform-dimensions.md` — IG 1080×1350 (4:5) ✅; TikTok нативно 9:16, Zernio ресайзит до 1080×1920.

## Pinterest

Auto-publish IG→Pinterest настроишь позже в Pinterest Settings.

## Безопасность

- Не вставляй токены в чат с агентом и не коммить `.local` в git.  
- Если токен бота засветился — в @BotFather: `/revoke` → новый токен.
