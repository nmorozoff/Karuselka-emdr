# Промпт генерации master-карусели — 6 слайдов (Runware strip)

Шаблон image-prompter для **6 панелей в горизонтальной полосе** (не Kie 3×3).

## Размеры (обязательно)

| Параметр | Значение |
|----------|----------|
| Слайд IG | **1080 × 1350** (4:5) |
| Master Runware | **6480 × 1350** (6 × 1080) |
| Соотношение master | **4.8 : 1** |
| Нарезка | `Karuselka/scripts/slice_carousel.py` → 6 PNG |
| Модель | `openai:gpt-image@2`, quality **medium** |

**Почему горизонтальная полоса, не 2×3:** `slice_carousel.py` заточен под **6 слайдов в ряд**; после slice каждая ячейка = готовый 4:5 для Instagram.

В `runware.env.local` для master-генерации временно:

```env
RUNWARE_GPT_IMAGE_WIDTH=6480
RUNWARE_GPT_IMAGE_HEIGHT=1350
```

После генерации вернуть `1080` / `1350` для одиночных слайдов (если перейдёте на per-slide).

---

## Шаблон промпта (русский, для Runware)

Подставляются: `{reference_contract}`, `{topic}`, `{headlines_01_06}`, `{style_lock}`.

```text
[STYLE LOCK]
Одно изображение — превью Instagram-карусели: ровно 6 равных вертикальных панелей в одной горизонтальной полосе слева направо.
Каждая панель — отдельный слайд 4:5 (1080×1350 после нарезки).
Стиль как на референсе: {style_lock — палитра, типографика, иллюстрации, контраст, отступы}.
Полноразмерный фон edge-to-edge. Без Instagram/TikTok UI, без рамки телефона.

[REFERENCE CONTRACT]
Роль референса: style + layout reference.
Сохранить: {palette}, {grid/reading order}, {иерархия типографики}, {отступы}, {архетипы панелей}, {контраст}.
Изменить: тема → {topic}; новые объекты/метафоры под EMDR/психологию; новый CTA.
Не копировать: чужой логотип, бренд, лица с референса, случайный текст с референса.

[OUTPUT FORMAT]
Master 6480×1350 px, 6 equal vertical panels in one row.
Reading order left to right: 01 → 02 → 03 → 04 → 05 → 06.
Невидимые линии разреза на 1/6, 2/6, … — без белых gutters, без рамок между панелями.
Каждая панель — самостоятельный слайд, единый визуальный язык серии.

[TYPOGRAPHY]
Рендерить ТОЛЬКО точный текст в кавычках из блока PANELS.
Verbatim text; no substitutions; no extra labels; no duplicate text.
Иерархия: headline > short body > pill/CTA.
Высокий контраст, щедрые поля. Текст и плашки — не ближе **10–12%** к линии разреза и краям панели.
Только русский. Без emoji. Без английских служебных меток (HEADLINE, BODY, CTA).

[PANELS — row 01..06]
Панель 1 (hook, motion-safe): точный заголовок «{headline_01}»; {body_01}; визуальные зоны ...
Панель 2: точный заголовок «{headline_02}»; {body_02}; ...
Панель 3: точный заголовок «{headline_03}»; {body_03}; ...
Панель 4: точный заголовок «{headline_04}»; {body_04}; ...
Панель 5 (save): точный заголовок «{headline_05}»; {body_05}; ...
Панель 6 (cta): точный заголовок «{headline_06}»; точный CTA «{cta_06}»; ...

[NEGATIVE]
wrong panel count, 9 panels, 3x3 grid, 2x3 grid, vertical stack, horizontal strip with wrong aspect,
visible gutters, white borders, outer frame, watermark, blurry text, style drift,
unreadable Cyrillic, duplicate labels, cropped text, English UI labels.

[TOPIC]
Адаптировать сцену под тему: {topic}
Акцентный цвет бренда: #3d5c2e
```

---

## JSON для скрипта (будущий `runware-carousel-gen.py`)

```json
{
  "version": "1",
  "generation_mode": "strip_6",
  "model": "openai:gpt-image@2",
  "width": 6480,
  "height": 1350,
  "slide_width": 1080,
  "slide_height": 1350,
  "slide_count": 6,
  "quality": "medium",
  "prompt": "...",
  "negative_prompt": "...",
  "input_urls": ["https://REFERENCE_HTTPS"],
  "grid": { "cols": 6, "rows": 1, "order": "row-major" },
  "animate_slide": 1
}
```

---

## Цепочка

```text
competitor_decompose.py → competitor-text-for-copywriter.md
    → copywriter (6 слайдов, custom-copy-prompt.md)
    → CAROUSEL_SLIDE_COPY.json
    → image-prompter заполняет PANELS в prompt выше
    → Runware 6480×1350
    → slice_carousel.py → slide-01..06.png
```
