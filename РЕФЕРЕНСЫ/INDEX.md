# Референсы — фото эксперта (identity для Runware)

**Статус:** ✅ загружено пользователем (2026-07-24)

## Primary portrait (для i2i)

| Приоритет | Файл | Заметка |
|-----------|------|---------|
| **P0** | `0C2A3279.jpg` | профессиональный портрет, вертикаль |
| **P0** | `0C2A3302.jpg` | запасной портрет |
| P1 | `DSC09841.JPG` | полный рост / кабинет |
| P1 | `референс1.jpeg`, `референс2.jpeg` | пользовательские референсы |

## Не использовать как identity

- `Generated Image *`, `Gemini_Generated_Image_*` — AI-генерация, не лицо
- `Снимок экрана *.png` — скриншот
- `photo_5408933254414853605_y.jpg` — мелкий thumbnail

## Путь для пайплайна

```text
Референсы/0C2A3279.jpg  → primary reference photo
```

Designer + image-prompter: `CAROUSEL_ASSET_REGISTRY.json` → `expert_portrait_primary`
