# Editorial guide

## Source hierarchy

Use sources in this order where they exist:

1. a scholarly historical dictionary, grammar, or primary language authority;
2. an official dictionary or book for Esperanto and Toki Pona;
3. a well-referenced Wiktionary entry that exposes its bibliography and revision history;
4. a specialist secondary source with named authorship.

Do not turn a search-result snippet, generated answer, or visual resemblance into an etymology. Links should land on the page that supports the specific form or route.

## PIE entries

- Mark every reconstructed form with `*`.
- State whether the item is a root, stem, inflected form, or noun.
- Treat laryngeals, accent, ablaut, and morphological analyses as scholarly reconstructions.
- Verify every route at each important intermediate stage. A modern word may be a learned Latin loan even when English also inherited a cousin through Germanic.
- Keep diagrams selective and say so.
- Give the mini-sentence a morpheme gloss, a natural translation, and a note that it is a pedagogical reconstruction. Avoid claiming a uniquely recoverable PIE sentence.

## Esperanto and Toki Pona entries

- Name the immediate donor when known; a donor’s deeper source can appear as a second comparison.
- When Esperanto deliberately combines international models, say “compares with” or name the source family instead of inventing a single donor.
- Do not make Toki Pona compounds look like fixed dictionary words. Explain the literal phrase and contextual reading.
- Keep sentences within beginner grammar and check particles, agreement, and object marking.
- Treat semantic range as current usage, not as a prison imposed by the donor word.

## Solresol entries

- Use Sudre's dictionary or Gajewski's grammar for the assigned sequence and historical gloss; name later community reinterpretations as such.
- Store every word as an ordered `notes` array using only `do`, `re`, `mi`, `fa`, `sol`, `la`, and `si`.
- Do not describe assigned a priori vocabulary as borrowed or etymologically derived from a language that happens to have a similar syllable.
- Mark newly assembled phrases as teaching examples. If an example is expanded from the grammar's abbreviated note spelling, say so.
- Treat colour and digit forms as alternate encodings of the same note sequence, not separate descendants.
- Render every sequence on a modern treble clef and make the same ordered notes playable. Label the convenient C-major pitches as a presentation choice, not an absolute-pitch rule of the language.
- Random notation cards may use Gajewski's documented digits, shortened initials, or rainbow colours. Preserve his `so` abbreviation for `sol` and do not improvise historical shorthand signs.

## Queue discipline

New content is appended to each file’s `entries` array. Never reorder already-published slugs. `content/state.json` is the only publication clock.

Before committing an addition:

```sh
python3 -m json.tool content/pie.json >/dev/null
python3 -m json.tool content/esperanto.json >/dev/null
python3 -m json.tool content/toki.json >/dev/null
python3 -m json.tool content/solresol.json >/dev/null
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/verify.py dist
```

Keep at least six unpublished weeks in each garden. The publisher is intentionally deterministic; editorial judgment replenishes the queue.

## Tone

Short, curious, and specific. A small joke is welcome when it clarifies the history. Avoid fake certainty, generic wonder, or pretending that an old root consciously “wanted” to become a modern word.
