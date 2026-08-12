# Curatorial automation prompt

Use this prompt for a weekly repository-maintenance automation that replenishes the queue. The GitHub publisher itself is deterministic and does not invent content.

> Work in the Word Garden repository. Inspect `content/state.json` and the ordered entries in `content/pie.json`, `content/esperanto.json`, and `content/toki.json`. If any garden has fewer than four unpublished entries, add enough source-backed entries to restore six weeks of runway. Follow `docs/editorial.md`; reopen every cited source; do not infer etymology from similarity; and label every PIE example sentence as a pedagogical reconstruction. Preserve published order and unrelated work. Run the unit tests, build, and verifier. If and only if content changed and validation passed, commit the narrow content changes and push `main`; deployment is push-driven. Report the added words, sources, validation, commit, and queue runway. If no queue is low, make no commit.

This separation is deliberate: scheduling and state transitions are ordinary code; sourcing remains a reviewable editorial act.
