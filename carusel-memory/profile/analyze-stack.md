# Стек разбора конкурентов (из ai-carousel-natasha)

Проект-референс: `/Users/natala/Documents/Playground/ai-carousel-natasha`

## Поток: ссылка Instagram → JSON

```text
Telegram bot (ссылка)
    ↓
Apify instagram-api-scraper
    → caption, childPosts, videoUrl, images
    ↓
Скачивание медиа (до 10 файлов)
    ↓
┌─ Видео с речью → Groq Whisper (дешево, точно)
├─ Картинки слайдов → Kimi K2.5 vision (OCR + структура)
└─ Немой рилс → ffmpeg кадры 0s,1s,2s… → Kimi OCR заголовка
    ↓
Kimi K2.5 (текст) → summary, keyIdeas, hookIdeas, suggestedGenerationText
    ↓
carusel-memory/research/competitor-decompose/{id}.json
```

## Почему не Undetectable

В natasha используют **Apify**, не браузерный логин:

- `APIFY_TOKEN` + actor `apify/instagram-api-scraper`
- `directUrls: [instagram_url]` → caption + все слайды carousel
- Код: `supabase/functions/analyze-source/index.ts` → `fetchInstagramContextViaApify`
- Cloud Run: `deploy/cloud-run/main.py` → `/analyze-instagram-source`

Undetectable — запасной путь, если Apify упадёт.

## Почему Kimi для vision, не «дорогой коллаж»

| Задача | Модель | Почему |
|--------|--------|--------|
| OCR слайдов, структура | **Kimi K2.5** | multimodal, дешевле пачки GPT-4o |
| Транскрипт речи | **Groq Whisper** | не LLM, копейки за минуту |
| Финальный copy 6 слайдов | master prompt + Kimi/Gemini | отдельный шаг |

Default provider для IG URL в natasha: `provider: "kimi"`.

## Правила анализа (из natasha)

- Транскрипт Whisper → **дословно** в `transcript`
- Убрать чужое авторство: @username, ссылки конкурента, их CTA
- `recommendedInputMode: "ideas"` — не готовые слайды, brief для генератора
- Не делить на слайды на этапе analyze — это делает copywriter

## Секреты

`carusel-memory/analyze.env.local` — Apify, Kimi, Groq
