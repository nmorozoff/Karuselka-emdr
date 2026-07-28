# Pipeline fix queue

## INC-001 — per-slide Runware без согласования

- **status:** open
- **date:** 2026-07-24
- **incident_report:** Запущена генерация 6 отдельных PNG (~$0.41) вместо одного master 3×2 (~$0.07). Нарушение бюджета на масштабе 100+ каруселей.
- **fix:** `profile/image-gen-budget-policy.md`; переделать `scripts/runware-carousel-gen.py` на master 3×2 + slice; флаг `--approved-multi` для исключений.
- **copy:** Тексты слайдов и caption переписать по `natasha-*-prompt.md` (Task copywriter).
