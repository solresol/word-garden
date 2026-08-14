#!/usr/bin/env python3
"""Verify generated XML, JSON, and internal static links."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit


LINK_RE = re.compile(r'(?:href|src)="([^"]+)"')
SITE_KEYS = ("pie", "esperanto", "toki", "solresol")


def target_for(site_dir: Path, url: str) -> Path | None:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or url.startswith(("mailto:", "#")):
        return None
    path = parsed.path
    if not path.startswith("/"):
        return None
    target = site_dir / path.lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    return target


def verify(dist: Path) -> list[str]:
    errors: list[str] = []
    for key in SITE_KEYS:
        site_dir = dist / key
        for required in ("index.html", "archive/index.html", "rootle/index.html", "about/index.html", "feed.xml", "feed.json", "api/today.json"):
            if not (site_dir / required).is_file():
                errors.append(f"{key}: missing {required}")
        for xml_name in ("feed.xml", "sitemap.xml"):
            try:
                ET.parse(site_dir / xml_name)
            except (ET.ParseError, OSError) as exc:
                errors.append(f"{key}: invalid {xml_name}: {exc}")
        for json_name in ("feed.json", "api/today.json"):
            try:
                json.loads((site_dir / json_name).read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                errors.append(f"{key}: invalid {json_name}: {exc}")
        for html_path in site_dir.rglob("*.html"):
            text = html_path.read_text(encoding="utf-8")
            if "<main" not in text or "<title>" not in text:
                errors.append(f"{html_path}: incomplete document")
            for url in LINK_RE.findall(text):
                target = target_for(site_dir, url)
                if target is not None and not target.exists():
                    errors.append(f"{html_path}: broken {url}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dist", type=Path, nargs="?", default=Path(__file__).resolve().parents[1] / "dist")
    args = parser.parse_args()
    errors = verify(args.dist.resolve())
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"Verified generated sites in {args.dist.resolve()}")


if __name__ == "__main__":
    main()
