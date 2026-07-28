# Carousel Style Match Scorecard

**Series:** Депрессивная оптика · **Reference:** @yura.muradyan DbFiu0pCp2k  
**Date:** 2026-07-24 · **Designer gate:** PASS

## Overall score: **84 / 100** ✅ (threshold ≥ 70)

| Criterion | Weight | Score | Notes |
|-----------|--------|-------|-------|
| Source decomposition present | P0 | 10/10 | CAROUSEL_SOURCE_DECOMPOSITION.json complete |
| carousel_family in registry | P0 | 10/10 | `slide_numbered_series` + `stat_blocks` |
| preserve/change/do_not_borrow | P0 | 10/10 | Documented in CAROUSELDESIGN + JSON |
| panel_archetype_map (6 slides) | P0 | 10/10 | Mapped 01–06 to ref archetypes |
| Composition orient slide-02 | P0 | 9/10 | Blueprint zone-level spec for pain slide |
| Palette fidelity (structure) | 8 | 8/10 | Orange→green intentional brand swap |
| Typography hierarchy | 8 | 7/10 | Playfair adds premium; differs from ref sans |
| Layout rhythm | 10 | 9/10 | 6-slide arc preserves ref list/stat patterns |
| Identity policy | 5 | 5/10 | Path set; portrait pending (not blocker) |
| Thumbnail / save test | 5 | 6/10 | Hook + save slide defined |

## P0 blockers: **none**

## Warnings (non-blocking)

1. **Portrait pending** — `Референсы/` пуста; image-prompter должен использовать silhouette/placeholder до загрузки.
2. **Typography drift** — Playfair vs ref all-sans; acceptable per brand brief.
3. **9→6 compression** — stat-heavy ref slides merged into insight/proof/save; monitor text density at generation.

## Fidelity anchors for guardian

- [ ] Slide-02 matches stat_insight layout (headline → rule → hero phrase → pill)
- [ ] Cream `#f7f5ef` + green `#3d5c2e` on all panels
- [ ] Pagination 1/6…6/6 top-right
- [ ] No competitor text / orange primary / wrong panel count
- [ ] Slide-06 CTA single action present

## Verdict

**✅ DESIGN OK** — ready for `carusel-image-prompter`
