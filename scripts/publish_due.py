#!/usr/bin/env python3
"""Publish the next queued words by changing only content/state.json."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SITE_KEYS = ("pie", "esperanto", "toki")


def local_today() -> date:
    return datetime.now(ZoneInfo("Australia/Sydney")).date()


def publish(today: date, *, force: set[str] | None = None) -> list[tuple[str, str, date]]:
    state_path = CONTENT / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    changes: list[tuple[str, str, date]] = []
    force = force or set()
    for key in SITE_KEYS:
        site = json.loads((CONTENT / f"{key}.json").read_text(encoding="utf-8"))
        records = state[key]
        latest = max((date.fromisoformat(item["published"]) for item in records), default=None)
        due = key in force or (site["cadence"] == "daily" and (latest is None or latest < today))
        if site["cadence"] == "weekly" and today.weekday() == site.get("publish_weekday", 0):
            due = latest is None or latest < today
        if not due:
            continue
        published_slugs = {item["slug"] for item in records}
        next_entry = next((entry for entry in site["entries"] if entry["slug"] not in published_slugs), None)
        if next_entry is None:
            print(f"QUEUE_EMPTY {key}")
            continue
        records.append({"slug": next_entry["slug"], "published": today.isoformat()})
        changes.append((key, next_entry["slug"], today))
    if changes:
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--today", type=date.fromisoformat, default=local_today())
    parser.add_argument("--force", action="append", choices=SITE_KEYS, default=[])
    args = parser.parse_args()
    changes = publish(args.today, force=set(args.force))
    if changes:
        for key, slug, published in changes:
            print(f"PUBLISHED {key} {slug} {published.isoformat()}")
    else:
        print(f"NO_CHANGES {args.today.isoformat()}")


if __name__ == "__main__":
    main()
