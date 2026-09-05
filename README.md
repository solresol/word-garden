# Word Garden

Four static word-of-the-day sites, all deliberately slower than advertised:

- `pie.symmachus.org` — Proto-Indo-European **word a ~~day~~ week**
- `esperanto.symmachus.org` — Esperanto **word a ~~day~~ week**
- `toki.symmachus.org` — Toki Pona **word a ~~day~~ week**
- `solresol.symmachus.org` — Solresol **word a ~~day~~ week**

Each site has a source-linked entry, a tiny example sentence, an archive, RSS and JSON feeds, a `today.json` endpoint, and a Wordle-like game called Rootle. PIE entries add Graphviz family trees and a Cognate Kerfuffle; Esperanto and Toki Pona show documented borrowing routes; Solresol words and sentences have treble-clef scores and audio playback.

Rootle randomly draws from entries published before the current featured word. Each browser remembers selected words and game progress in local storage. A new day in Sydney selects another unused word; finishing a game also offers the next unused word. Exhausted pools wait for new publications. Clearing browser storage clears that history. Solresol uses seven piano keys (or number keys 1–7), one note per tile, and English dictionary feedback for guesses.

`content/solresol-lexicon.json` is a dated snapshot of 2,660 English glosses from the community-edited Garrison Osteen translation of Sudre, with the source URL and CSV hash. It supplies guess feedback, independently of the publication queue. Some assignments differ from Gajewski; unlisted sequences are not assigned invented meanings. Builds use the saved snapshot and do not fetch the dictionary.

There is no runtime application or database. Content and publication state are JSON in Git. GitHub Actions builds the static trees and publishes them to `merah`.

## Local use

Requirements: Python 3.11+ and Graphviz for full lineage diagrams. The build has a text-only SVG fallback if `dot` is absent.

```sh
python3 scripts/build.py --today 2026-08-12
python3 scripts/verify.py dist
python3 -m unittest discover -s tests -v
python3 -m http.server 8000 --directory dist/pie
```

To simulate publication without changing the real state, copy `content/` to a temporary directory and run the unit tests. To publish the next real entries:

```sh
python3 scripts/publish_due.py
git add content/state.json
git commit -m "Publish words for YYYY-MM-DD"
git push
```

## Publication and deployment

`Publish due words` runs at 16:17 UTC on Sunday, which is early Monday morning in Sydney. All four gardens advance on Monday. The workflow commits only `content/state.json`, pushes it, and dispatches the deploy workflow because GitHub suppresses ordinary push-triggered workflows for commits made with `GITHUB_TOKEN`.

Any ordinary push to `main` triggers `Deploy Word Garden`. The deployment builds all four sites, checks links and feeds, rsyncs them to their explicit vhost roots on `merah`, and smoke-tests public HTTPS.

The repository needs two Actions secrets:

- `DEPLOYMENT_SSH_KEY`: private half of the dedicated `wordgarden` deploy key
- `DEPLOY_KNOWN_HOSTS`: pinned `merah.cassia.ifost.org.au` SSH host-key line

The OpenBSD vhost snippets are in `infra/httpd.conf`. See [deployment.md](docs/deployment.md) for the host and DNS checklist.

`scripts/ensure_cloudflare_dns.sh` audits or applies only the four intended proxied records using the local `~/.cloudflare` token.

## Editorial model

The opening queue contains twelve entries for each garden. See [editorial.md](docs/editorial.md) before adding more. In particular:

- a leading asterisk is mandatory for reconstructed PIE forms;
- descendant diagrams must show intermediate routes rather than visual similarity alone;
- PIE mini-sentences must say they are pedagogical reconstructions;
- constructed-language origin cards distinguish a documented donor from a mere lookalike;
- Solresol entries distinguish Sudre's assigned note vocabulary from later teaching examples;
- every entry carries at least one direct source link.

## Design references

The information rhythm borrows useful conventions—not visual assets or copy—from established word sites:

- [Merriam-Webster Word of the Day](https://www.merriam-webster.com/word-of-the-day): date, headword, pronunciation, concise meaning, example, deeper note, archive, and adjacent game
- [Dictionary.com Word of the Day](https://www.dictionary.com/word-of-the-day): very fast word → meaning → explanation → example scan
- [A.Word.A.Day archive](https://wordsmith.org/awad/archives.html): durable archives and themed runs

Word Garden gives the etymological route more space than those general dictionaries and keeps the production surface static, lightweight, and tracker-free.

## Licence

Code is MIT licensed. Original editorial content is offered under CC BY-SA 4.0; see [CONTENT-LICENSE.md](CONTENT-LICENSE.md). Linked sources retain their own licences.
