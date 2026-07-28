---
name: Наталья Морозова — Депрессивная оптика
expert: Наталья Морозова
topic: Депрессивная оптика vs розовые очки — EMDR
reference_url: https://www.instagram.com/p/DbFiu0pCp2k/
reference_author: "@yura.muradyan"
composition_orient: slide-02 (img_index=2)
format:
  generation_mode: runware_strip_6x45
  slide_count: 6
  grid:
    cols: 6
    rows: 1
    order: left-to-right
  strip_px: "6480×1350"
  panel_px: "1080×1350"
  panel_aspect: "4:5"
  resolution: medium
  animate_slide: 1
colors:
  primary: "#3d5c2e"
  primary_dark: "#2d4522"
  background: "#f7f5ef"
  on_background: "#1a1a1a"
  on_background_muted: "#5c5c5c"
  accent: "#3d5c2e"
  accent_secondary: "#6b8f5a"
  surface: "#ede8e0"
  surface_warm: "#e8e2d8"
  outline: "#d4cfc5"
  highlight_stat: "#3d5c2e"
typography:
  slide-headline:
    family: "Playfair Display"
    weights: [700, 800]
    style: "uppercase for hook lines; sentence case for empathetic subheads"
    letter_spacing: "-0.02em"
  slide-body:
    family: Inter
    weights: [400, 500, 600]
    line_height: 1.35
  slide-stat:
    family: Inter
    weights: [700, 800]
    size_role: "hero number or key phrase"
  slide-cta:
    family: Inter
    weights: [600, 700]
  slide-number:
    family: Inter
    weight: 400
    color: "#9a9a9a"
  display_accent:
    family: "Bebas Neue Cyrillic"
    optional: true
    use: "single-word emphasis on hook only"
grid:
  cols: 6
  rows: 1
  gutters_px: 0
  cell_is_self_contained: true
  safe_margin_pct: 8
  animate_slide: 1
carousel_system:
  carousel_family: slide_numbered_series
  secondary_family: stat_blocks
  narrative: hook-pain-insight-proof-save-cta
  slide_roles:
    - hook
    - pain
    - insight
    - proof
    - save
    - cta
identity:
  expert_portrait_path: "Референсы/"
  portrait_policy: runware_i2i
  portrait_status: pending_user_upload
  slides_with_portrait: [1, 6]
reference_role:
  style: editorial infographic, cream matte, bold hierarchy
  layout: slide-02 as composition anchor — headline + accent rule + stat block + insight pill
  typography: large caps headlines, muted pagination, icon-led lists
  mood: calm premium professional, not clinical
---

# CarouselDesign — Наталья Морозова

## Source Replication Doctrine

Референс @yura.muradyan (`DbFiu0pCp2k`) — **закон по layout и ритму**, не по теме. У референса 9 слайдов инфографики ЗОЖ; мы адаптируем **архетипы** под 6 слайдов EMDR-темы, сохраняя читаемость и editorial-премиум.

**Ориентир композиции:** `slide-02` (img_index=2) — вертикальная иерархия: пагинация → капс-заголовок → короткая акцентная линия → крупный stat/ключевая фраза слева + пояснение справа → нижняя insight-плашка с иконкой.

## Composition Lock (все 6 панелей)

- Фон: сплошной крем `#f7f5ef`, без градиентных «инста-пятен»
- Поля: ~8% от краёв панели; текст не касается cut-line strip
- Пагинация: `N/6` тонким Inter, правый верх, `#9a9a9a`
- Акцентная черта: горизонталь 40–60px, `#3d5c2e`, под главным заголовком (где есть headline-block)
- Иконки: line-art, чёрные/тёмно-зелёные, в кругах `#ede8e0`
- Нет watermark, нет чужих логотипов, нет PRADA/ЗОЖ-текста
- Каждая панель — **самодостаточная** 4:5 композиция (strip 6480×1350, 6 равных ячеек)

## Philosophy & Vibe

Тёплый экспертный editorial: как журнал о психологии, не как «мотивационный инстаграм». Контраст референса (оранжевый stat) → бренд-зелёный `#3d5c2e`. Playfair даёт премиальность заголовкам; Inter — ясность body и списков. Метафоры (очки, Гойя, открытки) — иллюстративные, спокойные, без мрачного хоррора и без «счастливых стоков».

## Grid Rules

```text
[01 hook] [02 pain] [03 insight] [04 proof] [05 save] [06 cta]
```

- Strip: 6480×1350 px, 6 колонок по 1080 px
- Порядок: слева направо = slide-01 … slide-06
- Gutters: 0 (full-bleed per panel; рез по границам ячеек)
- slide-01: motion-safe — статичный текст, лёгкая анимация фона/портрета

## Color Guidance

| Роль | Hex | Применение |
|------|-----|------------|
| Background | `#f7f5ef` | 100% площади панели |
| Primary text | `#1a1a1a` | заголовки, body |
| Muted text | `#5c5c5c` | вторичные подписи |
| Brand accent | `#3d5c2e` | линии, stat, акцентные слова |
| Surface pill | `#ede8e0` | insight-box, CTA card |
| Outline | `#d4cfc5` | разделители списков |

WCAG: body на креме ≥ 4.5:1; stat зелёный на креме — только крупный жирный (≥ 3:1 для display size).

## Typography & Readability

- **slide-01 hook:** 2 строки max на изображении (`imageTitle` + `imageBody`); Playfair 800, крупно
- **slide-02–04:** заголовок caps или sentence — не более 4 строк; body в промпте сокращать до pills/коротких блоков
- **slide-05 save:** checklist — иконка + короткая строка, max 4 пункта на панели
- **slide-06:** CTA одно действие; Telegram + bio
- Лимит видимого текста на панели: ~120 символов (без мелкого legal)

## Slide Rhythm

```text
01 HOOK     — pattern interrupt, contrarian truth (портрет опционально)
02 PAIN     — slide-02 layout: правда депрессивного взгляда
03 INSIGHT  — механизм «иллюзионист мозга», розовые открытки
04 PROOF    — Гойя / сосуществование, мягкая EMDR-рамка
05 SAVE     — шкала оптики + микро-моменты (save card)
06 CTA      — пробная сессия 30 мин + портрет
```

## Expert Identity Policy

- Папка: `Референсы/` (корень проекта)
- Ожидаемые файлы: `natalia-portrait-front.jpg`, `natalia-portrait-34.jpg` (или любой `*.jpg|*.png` в папке)
- Использование: slide-01 (правый край, как ref slide-01), slide-06 (левый край, как ref slide-09)
- Runware i2i: портрет как reference identity, не копировать лицо @yura.muradyan
- **Статус:** портрет ещё не загружен — **не BLOCKER** для design contract; image-prompter/slice используют placeholder silhouette до появления файла

## preserve / change / do_not_borrow

### preserve

- Кремовый matte editorial фон
- Иерархия slide-02: headline → accent rule → hero stat/phrase → insight pill
- Пагинация N/M в правом верхнем углу
- Крупная типографика hook, icon-led lists, rounded insight boxes
- Портрет эксперта на hook и CTA (позиция как у референса)
- Спокойный premium B2B-education тон

### change

- Палитра: оранжевый → `#3d5c2e`
- Шрифты: sans-only ref → Playfair + Inter
- Тема: ЗОЖ/коучинг → депрессивная оптика / EMDR
- 9 слайдов → 6; stats ЗОЖ → психологические метафоры и шкала
- CTA: вебинар → бесплатная пробная сессия Telegram/bio

### do_not_borrow

- Лицо и тело @yura.muradyan
- Тексты ЗОЖ, ВЦИОМ, PRADA, проценты конкурента
- Оранжевая палитра как primary
- Неон, красные тревожные плашки, stock happy people

## panel_archetype_map

| Slide | Role | Reference archetype | Adaptation |
|-------|------|---------------------|------------|
| 01 | hook | ref-01 big statement + portrait | Contrarian headline, зелёный акцент на ключевом слове, портрет Натальи справа |
| 02 | pain | **ref-02 stat + insight box** | «Правда депрессивного взгляда» + ключевая фраза вместо 53% + empathy pill |
| 03 | insight | ref-03 numbered + icon list | «01» → metaphor brain; список розовых иллюзий мозга |
| 04 | proof | ref-08 icon + X-list | Гойя-метафора + 3 пункта «не перекрашивать» |
| 05 | save | ref-07 multi-row stats | Шкала 4 уровня оптики + микро-моменты |
| 06 | cta | ref-09 portrait + CTA card | Портрет слева, сессия 30 мин, Telegram CTA |

## thumbnail_test

Slide-01 читается за 2 сек: крупный контрастный заголовок «ДЕПРЕССИВНАЯ ОПТИКА» + зелёное «видит правду» на креме; при наличии портрета — узнаваемый силуэт справа.

## save_test

Slide-05 — шкала «Гойя → открытки → влюблённость → середина» + микро-моменты; формат checklist как ref-07/08, высокий save-value.

## Do's and Don'ts

**Do:** короткий текст на панели; иконки line-art; единый ритм полей; мягкие метафоры; EMDR без обещаний «вылечу за 1 сессию».

**Don't:** плотные абзацы body на изображении; чужой бренд; клинический белый; эмодзи-спам; копировать оранжевый accent; 9-panel grid.
