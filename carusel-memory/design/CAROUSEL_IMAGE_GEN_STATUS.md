# Carousel Image Generation Status

**Pipeline:** Runware strip 6×4:5 (6480×1350) — **not started**

| Asset | Status | Notes |
|-------|--------|-------|
| Design contract | ✅ ready | All prompt_hints in SERIES_CONCEPT.json |
| CAROUSEL_IMAGE_PROMPT.json | ⏳ | Awaits carusel-image-prompter |
| Expert portrait Референсы/ | ⏳ pending | Optional for i2i; placeholder OK |
| master/strip PNG | ⏳ | Awaits slice |
| slide-01..06 PNG | ⏳ | Post-slice |
| slide-01.mp4 | ⏳ | Post motion-director |

## Generation config (for prompter/slice)

```json
{
  "generation_mode": "runware_strip_6x45",
  "strip_px": "6480×1350",
  "panel_count": 6,
  "panel_aspect": "4:5"
}
```

## Blockers

None at design stage.
