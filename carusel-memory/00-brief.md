# Brief — аккаунт и ниша (базовая настройка)

> Это **не** brief конкретной карусели. Перед первым запуском пайплайна Директор дополнит поля «Тема карусели», «Референс» и т.д.

## Целевая production-архитектура (ТЗ)

**Фаза 1 (сейчас):** отладка на локальной машине + Cursor (Директор, Task-субагенты, ручные gates, Make/Airtable/Dropbox).

**Фаза 2 (после допила):** тот же пайплайн должен работать **в автоматизации в изолированной Cloud-среде** — без привязки к открытому Cursor на ноутбуке.

| Требование | Смысл |
|------------|--------|
| **Изоляция** | Отдельный cloud runtime (контейнер/VM/serverless): секреты только в env/secrets manager, не в репозитории |
| **Автоматизация end-to-end** | Telegram intake → генерация (2 варианта) → metadata clean → export → очередь → Make/Zernio → cleanup — по расписанию и по событию, без ручного «запусти Task» |
| **Тот же контракт артефактов** | `carusel-memory/` (или cloud volume): brief, runs, slides, export-log, accounts-pairs |
| **Публикация** | Make + Zernio остаются внешними orchestrator; cloud-воркер пишет в Airtable/Dropbox |
| **Наблюдаемость** | Логи, алерты в Telegram при ошибке / «добавь музыку» |

Ориентир по стеку (как у `ai-carousel-natasha`): Cloud Run / аналог для рендера и тяжёлых шагов; bridge для Telegram — отдельный сервис или scheduled worker.

Детали деплоя: **`deploy/cloud-worker/README.md`** (Cloud Run + Scheduler 11/17/21 MSK).

## Аккаунт

| Поле | Значение |
|------|----------|
| Эксперт | Наталья Морозова |
| Роль | Психолог, EMDR-терапевт |
| Сайт | https://www.morozovanatalia.ru |
| Instagram | [@nataliamorozova.psy](https://www.instagram.com/nataliamorozova.psy/) |
| Telegram | https://t.me/natalyamorozovabot |
| Дзен | https://dzen.ru/morozova_emdr |
| Телефон | +7 (929) 594-05-14 |

## Ниша и аудитория

- **Кто:** взрослые 25–55, Москва + онлайн (весь мир)
- **Боль:** тревога, панические атаки, травма, выгорание, кризисы в отношениях и бизнесе
- **Метод:** EMDR/ДПДГ + интегративный подход
- **Тон:** тёплый, экспертный, без «волшебных таблеток» и без менторского давления
- **Доверие:** 3+ года практики, 800+ часов консультаций; EMDR в рекомендациях ВОЗ при ПТСР с 2013 г.
- **Оффер:** бесплатная пробная сессия 30 мин (онлайн)

Подробнее: `profile/niche-profile.md`

## CTA по умолчанию (зафиксировано)

**Все карусели → бесплатная пробная сессия 30 мин (онлайн).**

1. **Primary:** «Запишись на бесплатную пробную сессию 30 мин» → **ссылка в шапке профиля** (morozovanatalia.ru)
2. **Secondary:** сохранить карусель + подписка
3. Telegram-бот — только если явно указано в brief поста (не по умолчанию в caption)

## Промпты текста (канон)

| Артефакт | Файл |
|----------|------|
| Текст слайдов | `profile/natasha-slide-copy-prompt.md` |
| Описание поста | `profile/natasha-caption-prompt.md` |
| Бюджет картинок | `profile/image-gen-budget-policy.md` — **1 master, не 6 вызовов** |

## Публикация

- Instagram: Make / MCP (как в Karuselka)
- **TikTok:** Zernio API (`scripts/publish-zernio-carousel.py`)
- Pinterest: auto после IG (позже)

## Бренд (визуал)

| Элемент | Значение |
|---------|----------|
| Primary | `#3d5c2e` (hsl 93 37% 26%) — тёмно-зелёный |
| Background | `#f7f5ef` (кремово-бежевый) |
| Accent gradient | зелёный → оливковый |
| Заголовки | Playfair Display |
| Текст | Inter |
| Акцентный display | Bebas Neue Cyrillic (опционально) |
| Стиль | светлый, спокойный, премиальный; не клинический белый, не «инстаграм-психология» с неоном |
| Запреты | стоковые «счастливые люди», красные тревожные плашки, эмодзи-спам, обещания «вылечу за 1 сессию» |

## Темы (источник)

Кластеры и очередь — из `sessya-morozova` + `Посты EMDR/posts-emdr-memory/topics/`.  
См. `profile/topics-queue.md`.

## Тема карусели

**Депрессивная оптика vs «розовые очки»** — адаптация карусели @life.practic для Натальи Морозовой (EMDR).  
Источник смысла: `research/competitor-decompose/DapsWejjiDu/competitor-text-for-copywriter.md`

## Референс дизайна (визуал карусели)

https://www.instagram.com/p/DbFiu0pCp2k/ — @yura.muradyan (layout, типографика, стиль слайдов)

Разбор: `research/competitor-decompose/DbFiu0pCp2k/`

## Фото эксперта (identity)

Папка проекта: **`Референсы/`** — портреты Натальи для Runware i2i (добавляет пользователь).

См. `Референсы/README.md`

## Текст на слайдах

«Придумай сам» по выбранной теме из очереди, с опорой на `niche-profile.md`.

## Подпись поста

- Тон: экспертный, человечный, с одним чётким CTA
- Хештеги: `#emdr #психолог #тревога #паническиеатаки #психотерапия` + нишевые
- UTM: `utm_source=instagram` на ссылки сайта

## Формат

- **6 слайдов** (не 9) — отдельные PNG 4:5, Runware medium
- slide-01 → опционально MP4 5s (немой hook)
- Промпт: `profile/custom-copy-prompt.md` (мастер-промпт КАРУСЕЛЬКИ, 6 слайдов)
- Разбор конкурентов: Apify + Kimi K2.5 + Groq Whisper (см. `profile/analyze-stack.md`)
