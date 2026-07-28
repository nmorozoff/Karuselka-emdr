# Product Roadmap — Каруселька v2

Дата: 2026-07-23  
Статус: согласование архитектуры

## Цель

Полный цикл: **ссылка конкурента в Telegram** → разбор контента → текст по промпту → слайды (Runware) → публикация **Instagram + Pinterest** → **музыка в IG** (гибрид).

**Production (после допила):** весь цикл — в **изолированной Cloud-среде** (автоматизация без Cursor на ноутбуке). Локальная разработка = фаза отладки; cloud = целевой runtime. См. `00-brief.md` → «Целевая production-архитектура».

---

## 1. Telegram → Cursor (intake ссылок)

### Что уже есть

MCP `user-mcp-kv`: `telegram_get_updates`, `telegram_send_message`, `telegram_send_photo` и др.

### Как сделать правильно

Cursor **не может** принимать webhook в фоне. Нужен локальный **bridge** (как у Гипериона `ui_server.py`):

```text
Ты кидаешь ссылку в Telegram-бот
    ↓
Bridge (python, localhost) читает updates / webhook
    ↓
Пишет carusel-memory/intake/inbox.json + статус READY_FOR_AGENT
    ↓
Директор в Cursor подхватывает и запускает Task-цепочку
```

### Формат сообщения в боте

```text
https://www.instagram.com/p/XXXXX/
```

или с пометкой:

```text
ref: https://www.instagram.com/p/XXXXX/
caption: (опционально, если IG не отдаст описание)
```

### Рекомендация

Отдельный бот/чат **«Каруселька — референсы»**, чтобы не смешивать с каналом публикаций Posts EMDR.

---

## 2. Разбор ссылки конкурента (новый модуль)

Новый агент/скрипт: **`carusel-competitor-intake`**

| Тип поста | Что извлекаем | Как |
|-----------|---------------|-----|
| Говорящее видео / Reels в карусели | Транскрипт спикера | faster-whisper (уже в Гиперионе) |
| Слайды-картинки | Текст с каждого слайда | Vision OCR (GPT-4o / Claude vision / Tesseract) |
| 5s немой рилс + заголовок на видео | Заголовок + оверлей-текст | OCR по ключевым кадрам (frame 0, 1s, 2s…) |
| Описание поста | Полный caption | ⚠️ см. ниже |

### ⚠️ Главный риск — Instagram не отдаёт чужие посты по API

Варианты (по надёжности):

1. **Ты дублируешь caption в Telegram** вместе со ссылкой (100% надёжно)
2. **Playwright / Undetectable** с залогиненным IG-аккаунтом — скачать медиа + caption
3. Сторонние парсеры (нестабильно, ToS)

**Выходной артефакт:** `carusel-memory/research/competitor-decompose/{id}.json`

```json
{
  "source_url": "...",
  "post_type": "carousel_mixed | carousel_images | carousel_video | reel",
  "caption_raw": "...",
  "slides": [
    { "index": 1, "type": "video", "transcript": "...", "on_screen_text": "..." },
    { "index": 2, "type": "image", "ocr_text": "..." }
  ],
  "hook_detected": "...",
  "structure_notes": "9 slides, hook-value-cta"
}
```

---

## 3. Промпты — что уже в плагине

### Встроенные (сейчас)

| Файл | Роль |
|------|------|
| `shared/carousel-professional-playbook.md` | структура 9 панелей, hook frameworks, QA |
| `shared/carousel-prompt-library.md` | research, hook lab, copywriter, design, image, motion |
| `skills/carusel-copywriter/SKILL.md` | лимиты символов, JSON-схема слайдов |
| `skills/carusel-researcher/SKILL.md` | dossier, hook lab, 9-panel arc |

### Логика copywriter (кратко)

- 5 вариантов hook → выбор одного с `hook_rationale`
- Дуга: hook → problem → mistake → mechanism → proof → flow → save×2 → CTA
- Caption ≤ 2200 символов, ≤ 30 хештегов

### Твой «мясной» промпт

Когда дашь — положим в:

`carusel-memory/profile/custom-copy-prompt.md`

и copywriter будет читать его **вместо** или **поверх** library (приоритет: custom > playbook).

---

## 4. Генерация слайдов — Runware (не Kie)

### Сейчас в плагине

- Master 3×3 → **Kie.ai** (`kie_carousel_gen.py`)
- Slide-01 video → **Grok via Kie**

### Твоя задача

Перейти на **Runware** (`openai:gpt-image@2`) как в Posts EMDR.

### Настройки из Posts EMDR

Файл: `Посты EMDR/posts-emdr-memory/runware.env.example`

```env
RUNWARE_API_KEY=          # ← отдельный ключ для КАРУСЕЛЬКИ
RUNWARE_COVER_WIDTH=1280
RUNWARE_COVER_HEIGHT=1024
RUNWARE_COVER_QUALITY=low
```

Скрипт-референс: `Посты EMDR/scripts/runware-cover.py`  
API: `https://api.runware.ai/v1`, модель `openai:gpt-image@2`

### Для карусели (отличие от обложек постов)

| Параметр | Обложка EMDR | Карусель master 3×3 |
|----------|--------------|---------------------|
| Размер | 1280×1024 (5:4) | ~3072×4096 или кратно 3×4 панелям |
| Задача | 1 картинка | 1 master → slice 9 PNG |

**Действие:** создать `carusel-memory/runware.env.local` с **отдельным** `RUNWARE_API_KEY` (не шарить с Posts EMDR).

---

## 5. Pinterest — форматы и лимиты

### Pinterest API (прямая публикация)

| Формат | Лимит | Форматы файлов |
|--------|-------|----------------|
| **Carousel pin** | **2–5 изображений** (не 9!) | JPG/PNG, одинаковый aspect 1:1 или **2:3** |
| **Video pin** | 1 видео | MP4/MOV/M4V, 4 с — 15 мин, нужен cover |
| **Смешанный carousel** (видео + картинки) | ❌ через API carousel | только images |

### Наш кейс (slide-01 = video, slides 2–9 = PNG)

**Прямой API Pinterest carousel не подходит** для 1 video + 8 images в одном пине.

### Варианты для Pinterest

| Стратегия | Плюсы | Минусы |
|-----------|-------|--------|
| **A. Auto-publish IG→Pinterest** (claim account) | Карусели с 7+ слайдами уже конвертируются (апдейт Nov 2025) | Задержка до 24ч; музыка IG не переносится; video slide — уточнить на тесте |
| **B. Отдельный Pinterest-пакет: 5 лучших слайдов** | Контроль, 2:3, SEO title | Ручная/отдельная автоматизация |
| **C. Video pin = slide-01 + link на IG** | Один пин с видео | Остальные слайды отдельно |
| **D. Склейка 9 слайдов в один tall-pin 1:2.1** | Весь контент в 1 пине | Не свайп-карусель |

### Auto cross-post Instagram → Pinterest ✅

**Да, настройка есть** — не через Make, а в Pinterest:

1. Pinterest → Settings → **Claim Instagram account**
2. Включить **Auto-publish**
3. Выбрать доску + keyword filter (исключить `#ad`)
4. С Nov 2025: **IG carousel → Pinterest carousel** (не разбивается на отдельные пины)
5. Тесты показывают **7+ слайдов** проходят

**Музыка:** Pinterest не использует музыку Instagram. Для Pinterest это не проблема.

**Рекомендация:** основной путь Pinterest = **auto-publish после IG**, плюс fallback API для отдельных 5-slide пинов на SEO-страницы сайта.

---

## 6. Музыка в Instagram — критично ⚠️

### Факт

**Instagram Graph API / Make НЕ добавляют музыку в карусели.**

- `audio_name` — **только Reels**, не carousel
- Make/MCP публикует **без звука** (или только звук, вшитый в MP4 файл)

### Claude iOS Simulator — НЕ решение

Документация Claude Desktop iOS Simulator:

- Это симулятор для **твоих приложений из Xcode**
- **Нельзя** запустить App Store Instagram и выбрать трек из библиотеки IG
- Claude **не управляет физическим iPhone**

### Реальные варианты для музыки IG

| Вариант | Реалистичность | Комментарий |
|---------|------------------|-------------|
| **Гибрид: авто-пост → ты добавляешь музыку вручную 30 сек** | ✅ Высокая | Бот шлёт «пост live, добавь трек X» |
| **Вшить royalty-free в MP4 slide-01** | ✅ Средняя | Не IG-библиотека, зато автомат |
| **Публикация через реальный iPhone (Shortcuts/автоматизация)** | ⚠️ Низкая | Хрупко, ToS, ломается при обновлениях |
| **Undetectable + реальный IG в браузере** | ⚠️ Средняя | Теоретически можно, но нестабильно для carousel+music |
| **Make + музыка** | ❌ Невозможно | API не поддерживает |

### Рекомендуемый workflow (музыка)

```text
1. Пайплайн генерирует карусель (slide-01 silent MP4 + 8 PNG)
2. Make/MCP публикует в IG (или сохраняет черновик, если API позволит)
3. Telegram-бот: «Опубликовано. Открой IG → Редактировать → Музыка → [рекомендованный жанр/темп]»
4. (опционально) Через 24ч Pinterest подхватит auto-publish
```

Если музыка **обязательна до публикации** — единственный надёжный путь сейчас: **ручной финальный шаг в приложении IG** или лицензированный аудиотрек, вшитый в видео до загрузки.

---

## 7. CTA (зафиксировано)

Все карусели → **бесплатная пробная сессия 30 мин** (онлайн).

Шаблон slide-09 + caption:

> Запишитесь на бесплатную пробную сессию 30 мин — ссылка в bio / Telegram @natalyamorozovabot

---

## 8. Фазы внедрения

| Фаза | Что делаем | Результат |
|------|------------|-----------|
| **P0** | Telegram bridge + competitor decompose (Playwright) | Ссылка → JSON с текстами |
| **P1** | Runware adapter для master 3×3 + отдельный API key | Генерация без Kie |
| **P2** | Custom prompt slot + первый прогон по твоему референсу | Готовая карусель |
| **P3** | IG publish (Make/MCP) + Telegram «добавь музыку» | Публикация с напоминанием |
| **P4** | Pinterest claim + auto-publish тест | IG → Pinterest |
| **P5** | (опционально) Pinterest API 5-slide SEO pins | Доп. трафик на сайт |

---

## 9. Что нужно от тебя сейчас

1. **Отдельный `RUNWARE_API_KEY`** для КАРУСЕЛЬКИ (создать в runware.ai dashboard)
2. **Telegram:** отдельный бот или использовать текущий MCP-бот?
3. **Референс дизайна** + **@Instagram аккаунт**
4. **IG-аккаунт для парсинга** (логин в Undetectable/Playwright) — для скачивания чужих каруселей
5. Подтверди стратегию **музыки**: гибрид (авто + 30 сек руками) или только вшитый royalty-free?

---

## 10. Следующий шаг

После твоего «ок» на архитектуру:

1. Пишу `scripts/telegram_intake_bridge.py`
2. Пишу `scripts/competitor_decompose.py` (скачивание + whisper + OCR)
3. Адаптирую `runware-carousel-gen.py` из Posts EMDR
4. Первый тест на одной ссылке конкурента
