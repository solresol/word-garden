# Repository instructions

- Read `docs/editorial.md` before changing content.
- Preserve already-published entry order and treat `content/state.json` as publication state.
- Never add an etymology from spelling resemblance alone.
- Mark reconstructed PIE forms with `*` and describe mini-sentences as pedagogical reconstructions.
- Keep the sites static-only unless a requested feature cannot work in the browser or build pipeline.
- Do not commit `dist/`, screenshots, or generated browser artifacts.
- Run unit tests, build, and `scripts/verify.py` before pushing.
- Deployment targets `merah`; do not introduce a local container dependency.
