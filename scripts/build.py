#!/usr/bin/env python3
"""Build the four static Word Garden sites without third-party Python packages."""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
from datetime import date, datetime, time, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
ASSET_DIR = ROOT / "site" / "assets"
SITE_KEYS = ("pie", "esperanto", "toki", "solresol")
SYDNEY = ZoneInfo("Australia/Sydney")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def today_sydney() -> date:
    return datetime.now(SYDNEY).date()


def published_entries(site: dict, state: dict, today: date) -> list[tuple[date, dict]]:
    entries = {entry["slug"]: entry for entry in site["entries"]}
    result: list[tuple[date, dict]] = []
    for record in state:
        published = date.fromisoformat(record["published"])
        if published <= today:
            if record["slug"] not in entries:
                raise ValueError(f"State refers to missing entry {record['slug']!r}")
            result.append((published, entries[record["slug"]]))
    result.sort(key=lambda item: item[0], reverse=True)
    return result


def nav(site_key: str) -> str:
    links = (
        ("pie", "PIE", "https://pie.symmachus.org/"),
        ("esperanto", "Esperanto", "https://esperanto.symmachus.org/"),
        ("toki", "Toki Pona", "https://toki.symmachus.org/"),
        ("solresol", "Solresol", "https://solresol.symmachus.org/"),
    )
    rendered = []
    for key, label, url in links:
        current = ' aria-current="page"' if key == site_key else ""
        rendered.append(f'<a href="{url}"{current}>{label}</a>')
    return "".join(rendered)


def page(
    site_key: str,
    site: dict,
    title: str,
    description: str,
    canonical: str,
    body: str,
    *,
    feed: bool = True,
    script: str | None = None,
) -> str:
    feed_link = (
        f'<link rel="alternate" type="application/rss+xml" title="{esc(site["title_plain"])} RSS" href="/feed.xml">'
        if feed
        else ""
    )
    page_script = script or ("/assets/solresol.js" if site_key == "solresol" else None)
    script_tag = f'<script src="{esc(page_script)}" defer></script>' if page_script else ""
    return f"""<!doctype html>
<html lang="en" data-site="{esc(site_key)}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="{esc(site['theme_color'])}">
  <link rel="canonical" href="{esc(canonical)}">
  {feed_link}
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="/assets/site.css">
  {script_tag}
</head>
<body>
  <a class="skip-link" href="#main">Skip to the word</a>
  <header class="site-header">
    <a class="garden-mark" href="/" aria-label="Word Garden home">✣ <span>Word Garden</span></a>
    <nav aria-label="Languages">{nav(site_key)}</nav>
    <nav class="utility-nav" aria-label="Site sections">
      <a href="/archive/">Archive</a>
      <a href="/rootle/">Rootle</a>
      <a href="/feed.xml">RSS</a>
      <a href="/about/">About</a>
    </nav>
  </header>
  <main id="main">{body}</main>
  <footer>
    <p>Four small words, several unruly families. Built as static files; no accounts, adverts, or tracking.</p>
    <p><a href="/feed.xml">RSS</a> · <a href="/feed.json">JSON Feed</a> · <a href="/api/today.json">today.json</a></p>
  </footer>
</body>
</html>
"""


def cadence_title(site: dict) -> str:
    if site["cadence"] == "weekly":
        return 'A word a <span class="cadence-swap"><s>day</s> <ins>week</ins></span>'
    return "A word a day"


def graph_dot(entry: dict) -> str:
    nodes: dict[tuple[str, ...], str] = {(): "n0"}
    labels: dict[str, tuple[str, bool]] = {"n0": (entry["headword"], False)}
    edges: list[tuple[str, str]] = []
    counter = 1
    for lineage in entry.get("lineages", []):
        prefix: tuple[str, ...] = ()
        parent = "n0"
        for index, label in enumerate(lineage["route"]):
            prefix = prefix + (label,)
            if prefix not in nodes:
                node_id = f"n{counter}"
                counter += 1
                nodes[prefix] = node_id
                labels[node_id] = (label, index == len(lineage["route"]) - 1)
                edges.append((parent, node_id))
            parent = nodes[prefix]
    lines = [
        "digraph lineage {",
        'graph [rankdir=LR, bgcolor="transparent", pad="0.2", nodesep="0.34", ranksep="0.55"];',
        'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=12, color="#7d6b4d", fillcolor="#fffaf0", margin="0.12,0.08"];',
        'edge [color="#9b7d43", penwidth=1.6, arrowsize=0.65];',
    ]
    for node_id, (label, modern) in labels.items():
        attrs = [f"label={json.dumps(label, ensure_ascii=False)}"]
        if node_id == "n0":
            attrs.extend(['fillcolor="#26372f"', 'fontcolor="#ffffff"', 'penwidth="2"'])
        elif modern:
            attrs.extend(['fillcolor="#f1c75b"', 'color="#80601a"'])
        lines.append(f"{node_id} [{', '.join(attrs)}];")
    lines.extend(f"{left} -> {right};" for left, right in edges)
    lines.append("}")
    return "\n".join(lines) + "\n"


def render_graph(entry: dict, site_out: Path) -> None:
    graph_dir = site_out / "graphs"
    graph_dir.mkdir(parents=True, exist_ok=True)
    dot_path = graph_dir / f"{entry['slug']}.dot"
    svg_path = graph_dir / f"{entry['slug']}.svg"
    dot_path.write_text(graph_dot(entry), encoding="utf-8")
    dot = shutil.which("dot")
    if dot:
        subprocess.run(
            [dot, "-Tsvg", str(dot_path), "-o", str(svg_path)],
            check=True,
            capture_output=True,
            text=True,
        )
    else:
        svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="80" role="img">'
            '<rect width="100%" height="100%" fill="#fffaf0"/>'
            '<text x="20" y="45" font-family="sans-serif">Lineage diagram unavailable; use the accessible list below.</text>'
            "</svg>\n",
            encoding="utf-8",
        )


def lineage_markup(entry: dict) -> str:
    cards = []
    accessible = []
    for lineage in entry.get("lineages", []):
        route = lineage["route"]
        cards.append(
            '<li><span class="branch-label">{}</span><strong>{}</strong><small>{}</small></li>'.format(
                esc(lineage["branch"]), esc(route[-1]), esc(lineage.get("gloss", ""))
            )
        )
        accessible.append(" → ".join([entry["headword"], *route]))
    alt = "; ".join(accessible)
    kerfuffle = entry.get("kerfuffle", {})
    kerfuffle_html = ""
    if kerfuffle:
        kerfuffle_html = f"""
      <aside class="kerfuffle" aria-labelledby="kerfuffle-heading">
        <p class="eyebrow">Semantic drift, politely disputed</p>
        <h3 id="kerfuffle-heading">Cognate Kerfuffle</h3>
        <p class="kerfuffle-pair"><strong>{esc(kerfuffle['left'])}</strong><span aria-hidden="true">↔</span><strong>{esc(kerfuffle['right'])}</strong></p>
        <p>{esc(kerfuffle['note'])}</p>
      </aside>
        """
    return f"""
    <section class="section-block lineage" aria-labelledby="family-heading">
      <div class="section-heading"><p class="eyebrow">Then → now</p><h2 id="family-heading">The family reunion</h2></div>
      <figure>
        <img src="/graphs/{esc(entry['slug'])}.svg" alt="{esc(alt)}" loading="lazy">
        <figcaption>Selected routes, not an exhaustive family tree. Intermediate forms are simplified for a readable first look.</figcaption>
      </figure>
      <ul class="descendant-cards">{''.join(cards)}</ul>
      {kerfuffle_html}
    </section>
    """


def origin_markup(site: dict, entry: dict) -> str:
    origin = entry["origin"]
    comparisons = "".join(f"<li>{esc(item)}</li>" for item in origin.get("comparisons", []))
    return f"""
    <section class="section-block origin" aria-labelledby="origin-heading">
      <div class="section-heading"><p class="eyebrow">Borrowed luggage</p><h2 id="origin-heading">Where it came from</h2></div>
      <div class="origin-route" aria-label="{esc(origin['source_language'])} {esc(origin['source_word'])} became {esc(entry['headword'])}">
        <span><small>{esc(origin['source_language'])}</small><strong>{esc(origin['source_word'])}</strong></span>
        <span class="route-arrow" aria-hidden="true">→</span>
        <span><small>{esc(site['language_label'])}</small><strong>{esc(entry['headword'])}</strong></span>
      </div>
      <p>{esc(origin['note'])}</p>
      {f'<ul class="comparison-list">{comparisons}</ul>' if comparisons else ''}
    </section>
    """


def solresol_markup(entry: dict) -> str:
    note_data = {
        "do": (1, "red"),
        "re": (2, "orange"),
        "mi": (3, "yellow"),
        "fa": (4, "green"),
        "sol": (5, "blue"),
        "la": (6, "indigo"),
        "si": (7, "violet"),
    }
    notes = entry["notes"]
    chips = "".join(
        f'<li class="note note-{esc(note)}"><span>{esc(note)}</span><small>{note_data[note][0]} · {note_data[note][1]}</small></li>'
        for note in notes
    )
    spoken = " · ".join(notes)
    return f"""
    <section class="section-block solresol-spelling" aria-labelledby="spelling-heading">
      <div class="section-heading"><p class="eyebrow">Seven-note spelling</p><h2 id="spelling-heading">Say it, play it, flash it</h2></div>
      <ol class="note-sequence" aria-label="{esc(spoken)}">{chips}</ol>
      <button class="play-word" type="button" data-notes="{esc(','.join(notes))}">▶ Play the word</button>
      <p>{esc(entry['origin']['note'])}</p>
      <p class="caveat">Sudre also mapped the notes to the digits 1–7 and the rainbow colours shown above. The pitches played here use a convenient C-major scale; Solresol is about the ordered notes, not absolute pitch.</p>
    </section>
    """


def article_markup(site_key: str, site: dict, entry: dict, published: date) -> str:
    meanings = "".join(f"<li>{esc(item)}</li>" for item in entry["meanings"])
    sources = "".join(
        f'<li><a href="{esc(source["url"])}" rel="external">{esc(source["title"])}</a></li>'
        for source in entry["sources"]
    )
    if site_key == "pie":
        relation = lineage_markup(entry)
    elif site_key == "solresol":
        relation = solresol_markup(entry)
    else:
        relation = origin_markup(site, entry)
    weather = entry.get("weather", site.get("weather", "Clear enough to bring a comparative dictionary."))
    return f"""
    <article>
      <header class="word-hero">
        <p class="eyebrow">{esc(site['language_label'])} · {esc(published.strftime('%-d %B %Y'))}</p>
        <p class="cadence-title">{cadence_title(site)}</p>
        <h1>{esc(entry['headword'])}</h1>
        <p class="pronunciation">{esc(entry['pronunciation'])}</p>
        <ul class="meaning-chips">{meanings}</ul>
        <p class="lede">{esc(entry['lede'])}</p>
      </header>
      {relation}
      <section class="section-block sentence" aria-labelledby="sentence-heading">
        <div class="section-heading"><p class="eyebrow">Tiny sentence</p><h2 id="sentence-heading">Use it before it gets complicated</h2></div>
        <blockquote lang="{esc(site['lang_code'])}">{esc(entry['sentence']['original'])}</blockquote>
        {f'<p class="word-gloss">{esc(entry["sentence"]["gloss"])}</p>' if entry['sentence'].get('gloss') else ''}
        <p class="translation">“{esc(entry['sentence']['translation'])}”</p>
        <p class="caveat">{esc(entry['sentence']['note'])}</p>
      </section>
      <aside class="weather" aria-label="Etymological weather">
        <span aria-hidden="true">◌</span><div><p class="eyebrow">Etymological weather</p><p>{esc(weather)}</p></div>
      </aside>
      <section class="section-block sources" aria-labelledby="sources-heading">
        <div class="section-heading"><p class="eyebrow">Receipts</p><h2 id="sources-heading">Sources and cautions</h2></div>
        <p>{esc(entry['source_note'])}</p><ul>{sources}</ul>
      </section>
      <nav class="end-nav" aria-label="After the word"><a class="button" href="/rootle/">Play this week’s Rootle</a><a href="/archive/">Browse the archive →</a></nav>
    </article>
    """


def archive_markup(site: dict, entries: list[tuple[date, dict]]) -> str:
    items = "".join(
        f'<li><a href="/archive/{quote(entry["slug"])}/"><span>{esc(entry["headword"])}</span>'
        f'<small>{esc(published.isoformat())} · {esc(entry["meanings"][0])}</small></a></li>'
        for published, entry in entries
    )
    return f"""
    <header class="simple-hero"><p class="eyebrow">All the previous small revelations</p><h1>{esc(site['language_label'])} archive</h1>
    <p>Every published word, newest first.</p></header><ol class="archive-list">{items}</ol>
    """


def about_markup(site_key: str, site: dict) -> str:
    if site_key == "pie":
        special = "Proto-Indo-European is reconstructed, not recorded. An asterisk marks a scholarly reconstruction; forms and mini-sentences can vary by model. The diagrams show selected, defensible routes rather than claiming every lookalike is a cousin."
    elif site_key == "solresol":
        special = "Solresol is built a priori from sequences of seven notes, so there is no donor language to pretend it borrowed from. The spelling card instead shows each note as a syllable, digit, colour, and playable pitch. Glosses follow the historical grammar and the community English dictionary, with teaching snippets labelled as such."
    else:
        special = "A planned language can still have a past. The origin cards identify documented models or source words, while the example sentence shows present-day use. Similarity alone is never treated as proof of borrowing."
    return f"""
    <header class="simple-hero"><p class="eyebrow">Method before mythology</p><h1>About this garden</h1>
    <p>{esc(site['description'])}</p></header>
    <div class="prose">
      <h2>Editorial promise</h2><p>{esc(special)}</p>
      <p>Each entry names its sources. Modern descendants are traced through intermediate languages where space permits. Short teaching sentences are explicitly labelled as teaching examples, not newly discovered inscriptions.</p>
      <h2>Why it looks like this</h2><p>Classic word-of-the-day sites put the word, pronunciation, short meaning, example, and archive first. This version keeps that useful rhythm, then gives etymology the largest visual surface.</p>
      <h2>How publication works</h2><p>Words and publication state are plain JSON in Git. A scheduled job publishes the next queued entry, commits the state change, and the deployment workflow rebuilds all four static sites. There is no production database.</p>
      <h2>Licensing</h2><p>Original editorial content is CC BY-SA 4.0; code is MIT licensed. Linked sources retain their own licences and authority.</p>
    </div>
    """


def rootle_markup(site_key: str, site: dict, entries: list[dict]) -> str:
    answers = [{"answer": entry["game"].lower(), "display": entry["headword"], "hint": entry["meanings"][0]} for entry in entries]
    config = json.dumps(
        {
            "site": site_key,
            "language": site["language_label"],
            "answers": answers,
            "anchor": "2026-08-10",
            "cadence": site["cadence"],
            "period_label": "This week’s" if site["cadence"] == "weekly" else "Today’s",
            "time_zone": "Australia/Sydney",
        },
        ensure_ascii=False,
    ).replace("</", "<\\/")
    return f"""
    <header class="simple-hero rootle-intro"><p class="eyebrow">A family resemblance game</p><h1>Rootle</h1>
    <p>Guess this week’s {esc(site['language_label'])} word in six tries. Accents, asterisks, and laryngeal subscripts stay outside the tiles; the hint does not.</p></header>
    <section class="game" aria-labelledby="game-heading">
      <div class="game-meta"><span id="puzzle-number"></span><button id="hint-button" type="button">Reveal a hint</button></div>
      <p id="hint" class="hint" hidden></p>
      <h2 id="game-heading" class="visually-hidden">Rootle board</h2>
      <div id="board" class="board" aria-live="polite"></div>
      <p id="game-status" class="game-status" aria-live="assertive"></p>
      <div id="keyboard" class="keyboard" aria-label="On-screen keyboard"></div>
      <div class="game-actions"><button id="share-button" type="button" hidden>Copy result</button><button id="new-game-button" type="button" hidden>Replay</button></div>
      <details><summary>How to play</summary><p>Green is the right letter in the right place; ochre belongs elsewhere; grey is absent. Any alphabetic guess of the right length is accepted—historical spelling should not become a bouncer.</p></details>
    </section>
    <script>window.ROOTLE_CONFIG={config};</script>
    """


def rss_xml(site: dict, entries: list[tuple[date, dict]]) -> str:
    items = []
    for published, entry in entries[:20]:
        link = f"{site['base_url']}/archive/{quote(entry['slug'])}/"
        pub_dt = datetime.combine(published, time(12), timezone.utc)
        items.append(
            "<item>"
            f"<title>{esc(entry['headword'])} — {esc(entry['meanings'][0])}</title>"
            f"<link>{esc(link)}</link><guid>{esc(link)}</guid>"
            f"<pubDate>{format_datetime(pub_dt)}</pubDate>"
            f"<description>{esc(entry['lede'])}</description>"
            "</item>"
        )
    return """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{title}</title><link>{link}/</link><description>{description}</description>
<language>en-au</language><ttl>1440</ttl>{items}
</channel></rss>
""".format(
        title=esc(site["title_plain"]),
        link=esc(site["base_url"]),
        description=esc(site["description"]),
        items="".join(items),
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def revision() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def build_site(site_key: str, site: dict, state: dict, out_root: Path, today: date) -> None:
    site_out = out_root / site_key
    site_out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ASSET_DIR, site_out / "assets", dirs_exist_ok=True)
    published = published_entries(site, state[site_key], today)
    if not published:
        raise ValueError(f"No {site_key} entry is published on or before {today}")

    current_date, current = published[0]
    for _, entry in published:
        if site_key == "pie":
            render_graph(entry, site_out)

    home_body = article_markup(site_key, site, current, current_date)
    home = page(
        site_key,
        site,
        f"{current['headword']} — {site['title_plain']}",
        current["lede"],
        f"{site['base_url']}/",
        home_body,
    )
    (site_out / "index.html").write_text(home, encoding="utf-8")

    archive_dir = site_out / "archive"
    archive_dir.mkdir(exist_ok=True)
    archive = page(
        site_key,
        site,
        f"Archive — {site['title_plain']}",
        f"Published {site['language_label']} words.",
        f"{site['base_url']}/archive/",
        archive_markup(site, published),
    )
    (archive_dir / "index.html").write_text(archive, encoding="utf-8")
    for published_date, entry in published:
        entry_dir = archive_dir / entry["slug"]
        entry_dir.mkdir(exist_ok=True)
        entry_page = page(
            site_key,
            site,
            f"{entry['headword']} — {site['title_plain']}",
            entry["lede"],
            f"{site['base_url']}/archive/{quote(entry['slug'])}/",
            article_markup(site_key, site, entry, published_date),
        )
        (entry_dir / "index.html").write_text(entry_page, encoding="utf-8")

    about_dir = site_out / "about"
    about_dir.mkdir(exist_ok=True)
    (about_dir / "index.html").write_text(
        page(
            site_key,
            site,
            f"About — {site['title_plain']}",
            "Editorial method, sources, and static publishing design.",
            f"{site['base_url']}/about/",
            about_markup(site_key, site),
        ),
        encoding="utf-8",
    )

    rootle_dir = site_out / "rootle"
    rootle_dir.mkdir(exist_ok=True)
    (rootle_dir / "index.html").write_text(
        page(
            site_key,
            site,
            f"Rootle — {site['title_plain']}",
            f"A weekly {site['language_label']} word-guessing game.",
            f"{site['base_url']}/rootle/",
            rootle_markup(site_key, site, site["entries"]),
            script="/assets/rootle.js",
        ),
        encoding="utf-8",
    )

    (site_out / "feed.xml").write_text(rss_xml(site, published), encoding="utf-8")
    json_items = [
        {
            "id": f"{site['base_url']}/archive/{entry['slug']}/",
            "url": f"{site['base_url']}/archive/{entry['slug']}/",
            "title": entry["headword"],
            "content_text": entry["lede"],
            "date_published": f"{published_date.isoformat()}T12:00:00Z",
        }
        for published_date, entry in published[:20]
    ]
    write_json(
        site_out / "feed.json",
        {
            "version": "https://jsonfeed.org/version/1.1",
            "title": site["title_plain"],
            "home_page_url": f"{site['base_url']}/",
            "feed_url": f"{site['base_url']}/feed.json",
            "items": json_items,
        },
    )
    write_json(
        site_out / "api" / "today.json",
        {
            "site": site_key,
            "published": current_date.isoformat(),
            "headword": current["headword"],
            "pronunciation": current["pronunciation"],
            "meanings": current["meanings"],
            "sentence": current["sentence"],
            "url": f"{site['base_url']}/archive/{current['slug']}/",
        },
    )
    write_json(site_out / "build.json", {"revision": revision(), "built_for": today.isoformat(), "site": site_key})
    urls = [f"{site['base_url']}/", f"{site['base_url']}/archive/", f"{site['base_url']}/rootle/", f"{site['base_url']}/about/"]
    urls.extend(f"{site['base_url']}/archive/{entry['slug']}/" for _, entry in published)
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
        f"<url><loc>{esc(url)}</loc></url>" for url in urls
    ) + "</urlset>\n"
    (site_out / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (site_out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site['base_url']}/sitemap.xml\n", encoding="utf-8")
    (site_out / "404.html").write_text(
        page(
            site_key,
            site,
            f"Word not found — {site['title_plain']}",
            "This word wandered off.",
            f"{site['base_url']}/404.html",
            '<header class="simple-hero"><p class="eyebrow">404</p><h1>This word wandered off.</h1><p>Try the <a href="/archive/">archive</a>; it keeps better notes.</p></header>',
            feed=False,
        ),
        encoding="utf-8",
    )


def build(out_root: Path, today: date) -> None:
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True)
    state = load_json(CONTENT_DIR / "state.json")
    for site_key in SITE_KEYS:
        site = load_json(CONTENT_DIR / f"{site_key}.json")
        build_site(site_key, site, state, out_root, today)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "dist")
    parser.add_argument("--today", type=date.fromisoformat, default=today_sydney())
    args = parser.parse_args()
    build(args.out.resolve(), args.today)
    print(f"Built {', '.join(SITE_KEYS)} for {args.today} in {args.out.resolve()}")


if __name__ == "__main__":
    main()
