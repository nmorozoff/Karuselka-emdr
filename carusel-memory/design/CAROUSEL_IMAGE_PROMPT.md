# CAROUSEL_IMAGE_PROMPT — Runware strip 6×4:5

**Серия:** morozova-depressive-optics-2026  
**Эксперт:** Наталья Морозова  
**Тема:** Депрессивная оптика vs розовые очки — EMDR  
**Режим:** `strip_6` → master **6480×1350** → slice → 6 PNG 1080×1350

---

## Модель и параметры

| Параметр | Значение |
|----------|----------|
| Модель | `openai:gpt-image@2` |
| Quality | medium |
| Master | 6480 × 1350 px |
| Панель | 1080 × 1350 (4:5) |
| Панелей | 6 в ряд, gutters 0 |
| Animate | slide-01 (motion-safe hook) |

Перед генерацией в `runware.env.local`:

```env
RUNWARE_GPT_IMAGE_WIDTH=6480
RUNWARE_GPT_IMAGE_HEIGHT=1350
RUNWARE_IMAGE_QUALITY=medium
```

После slice вернуть 1080×1350 для одиночных слайдов.

---

## Reference Contract

**Роль референса:** style + layout (@yura.muradyan, `DbFiu0pCp2k`)

### Preserve

- Кремовый matte фон `#f7f5ef`, full-bleed
- Иерархия slide-02: headline → accent rule → hero phrase → insight pill
- Пагинация `N/6` top-right, muted gray
- Крупная типографика hook, icon-led lists, rounded pills
- Портрет эксперта на hook (справа) и CTA (слева)
- Спокойный premium B2B-education тон, поля ~8%

### Change

- Оранжевый → `#3d5c2e`
- Sans-only → Playfair Display + Inter
- 9 слайдов → 6-panel horizontal strip
- ЗОЖ/коучинг → депрессивная оптика / EMDR
- Лицо конкурента → Наталья Морозова (`Референсы/0C2A3279.jpg`)
- CTA → бесплатная пробная сессия 30 мин, Telegram @natalyamorozovabot

### Do not borrow

- Лицо @yura.muradyan, PRADA, ZOH/ВЦИОМ тексты
- Оранжевый primary, вебинар конкурента
- Stock happy people, неон, красные тревожные плашки

---

## Style Lock

| Элемент | Значение |
|---------|----------|
| Background | `#f7f5ef` |
| Accent | `#3d5c2e` |
| Text | `#1a1a1a` / muted `#5c5c5c` |
| Surface pill | `#ede8e0` |
| Headline | Playfair Display 700–800 |
| Body | Inter 400–600 |
| Иконки | line-art в кругах `#e8e2d8` |
| Mood | тёплый экспертный editorial, не клиника, не мотивационный неон |

**Composition orient:** `slide-02.jpg` — эталон панели 2 (stat_insight).

---

## Input References (local → HTTPS перед Runware)

| Роль | Путь |
|------|------|
| Style/layout anchor | `carusel-memory/research/competitor-decompose/DbFiu0pCp2k/media/slide-02.jpg` |
| Hook layout | `.../media/slide-01.jpg` |
| CTA layout | `.../media/slide-09.jpg` |
| Identity primary | `Референсы/0C2A3279.jpg` |
| Identity fallback | `Референсы/0C2A3302.jpg` |

`input_urls` пуст до upload. Slice-агент загружает локальные файлы перед i2i.

---

## Panel Flow (01 → 06)

### 01 — Hook (motion-safe)

- **Текст:** «Депрессивная оптика» / «видит правду» (акцент на «правду»)
- **Layout:** ref-01 hook_portrait — текст слева, портрет Натальи справа 42%
- **Motion:** статичный текст, лёгкий фон/портрет

### 02 — Pain (composition orient)

- **Текст:** «ПРАВДА ДЕПРЕССИВНОГО ВЗГЛЯДА» + hero «Будущее непредсказуемо — это факт»
- **Layout:** точная копия ref slide-02, зелёный вместо оранжевого
- **Pill:** «Обжигающе честно — и совершенно не помогает»

### 03 — Insight

- **Текст:** «01» + «ЗДОРОВОМУ МОЗГУ» + «нужна иллюзия, чтобы жить»
- **Icons:** открытки, домик в воздухе, дофамин, механизм выживания

### 04 — Proof

- **Текст:** «НЕ ПЕРЕКРАШИВАТЬ / А СОСУЩЕСТВОВАТЬ»
- **Visual:** мини-гравюра Гойи line-art + X-list EMDR-путь

### 05 — Save

- **Текст:** «ШКАЛА ОПТИКИ» — 4 уровня: Гойя → Открытки → Влюблённость → Середина
- **Micro:** «Тепло · Чай · Рядом» + «Где вы сегодня?»

### 06 — CTA

- **Текст:** «ПРОБНАЯ СЕССИЯ» / «30 мин — бесплатно, онлайн»
- **CTA pill:** «Telegram @natalyamorozovabot» / «или ссылка в bio →»
- **Portrait:** Наталья слева 35%, ref slide-09

---

## Typography Rules

- Verbatim Russian only — из `CAROUSEL_SLIDE_COPY.json` + blueprints
- No substitutions, no extra labels, no duplicate text
- Safe margin 10–12% от cut-lines и краёв панели
- Max ~120 видимых символов на панель
- Без emoji, без английских служебных меток

---

## Negative Constraints

9 panels, 3×3, 2×3, vertical stack, visible gutters, white borders, watermark, blurry Cyrillic, orange accent, competitor text, stock happy people, horror Goya, neon, emoji.

---

## Prompt Compaction

- `prompt_char_count`: 3596 (≤ 4500)
- Детали в `reference_contract`, `style_lock`, `panel_visual_brief`
- Machine prompt: `CAROUSEL_IMAGE_PROMPT.json` → поле `prompt`

---

## Следующий шаг

→ `carusel-slice` (Runware generate 6480×1350 + `slice_carousel.py` → slide-01..06.png)
