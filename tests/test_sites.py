from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build  # noqa: E402
import publish_due  # noqa: E402
import verify  # noqa: E402


class ContentTests(unittest.TestCase):
    def test_content_has_unique_usable_entries(self) -> None:
        for key in build.SITE_KEYS:
            site = build.load_json(ROOT / "content" / f"{key}.json")
            slugs = [entry["slug"] for entry in site["entries"]]
            games = [entry["game"] for entry in site["entries"]]
            self.assertEqual(len(slugs), len(set(slugs)), key)
            self.assertGreaterEqual(len(slugs), 10, key)
            self.assertTrue(all(game.isascii() and game.isalpha() for game in games), key)
            for entry in site["entries"]:
                self.assertTrue(entry["sources"], entry["slug"])
                self.assertTrue(entry["sentence"]["note"], entry["slug"])

    def test_pie_reconstructions_are_marked(self) -> None:
        site = build.load_json(ROOT / "content" / "pie.json")
        for entry in site["entries"]:
            self.assertTrue(entry["headword"].startswith("*"), entry["headword"])
            self.assertTrue(entry["kerfuffle"]["left"], entry["slug"])
            self.assertTrue(entry["kerfuffle"]["right"], entry["slug"])
            self.assertTrue(entry["kerfuffle"]["note"], entry["slug"])
            note = entry["sentence"]["note"].lower()
            self.assertTrue("teaching" in note or "pedagogical" in note, entry["slug"])

    def test_solresol_entries_are_note_sequences(self) -> None:
        site = build.load_json(ROOT / "content" / "solresol.json")
        allowed = {"do", "re", "mi", "fa", "sol", "la", "si"}
        for entry in site["entries"]:
            self.assertTrue(entry["notes"], entry["slug"])
            self.assertTrue(set(entry["notes"]) <= allowed, entry["slug"])
            self.assertEqual(entry["game"], "".join(entry["notes"]), entry["slug"])


class BuildTests(unittest.TestCase):
    def test_build_and_internal_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            build.build(out, date(2026, 8, 12))
            self.assertEqual([], verify.verify(out))
            pie = (out / "pie" / "index.html").read_text(encoding="utf-8")
            self.assertIn("<s>day</s>", pie)
            self.assertIn("<ins>week</ins>", pie)
            self.assertIn("Cognate Kerfuffle", pie)
            self.assertIn("*bʰer-", pie)
            self.assertTrue((out / "pie" / "graphs" / "bher.svg").is_file())
            solresol = (out / "solresol" / "index.html").read_text(encoding="utf-8")
            self.assertIn("data-notes=\"sol,re,sol\"", solresol)
            self.assertIn("/assets/solresol.js", solresol)
            for key in build.SITE_KEYS:
                ET.parse(out / key / "feed.xml")
                rootle = (out / key / "rootle" / "index.html").read_text(encoding="utf-8")
                self.assertIn('"cadence": "weekly"', rootle)
                self.assertIn("Guess this week’s", rootle)
                today = json.loads((out / key / "api" / "today.json").read_text(encoding="utf-8"))
                self.assertEqual("2026-08-12", today["published"])

    def test_every_queued_entry_renders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "dist"
            out.mkdir()
            for key in build.SITE_KEYS:
                site = build.load_json(ROOT / "content" / f"{key}.json")
                records = [
                    {"slug": entry["slug"], "published": date(2026, 8, 12).isoformat()}
                    for entry in site["entries"]
                ]
                build.build_site(key, site, {key: records}, out, date(2026, 8, 12))
                for entry in site["entries"]:
                    self.assertTrue((out / key / "archive" / entry["slug"] / "index.html").is_file())


class PublisherTests(unittest.TestCase):
    def test_all_gardens_publish_weekly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            temp_content = Path(tmp) / "content"
            shutil.copytree(ROOT / "content", temp_content)
            baseline = {
                "pie": [{"slug": "bher", "published": "2026-08-12"}],
                "esperanto": [{"slug": "amiko", "published": "2026-08-12"}],
                "toki": [{"slug": "toki", "published": "2026-08-12"}],
                "solresol": [{"slug": "solresol", "published": "2026-08-12"}],
            }
            (temp_content / "state.json").write_text(
                json.dumps(baseline, indent=2) + "\n", encoding="utf-8"
            )
            original = publish_due.CONTENT
            publish_due.CONTENT = temp_content
            try:
                thursday = publish_due.publish(date(2026, 8, 13))
                self.assertEqual([], thursday)
                monday = publish_due.publish(date(2026, 8, 17))
                self.assertEqual(["pie", "esperanto", "toki", "solresol"], [item[0] for item in monday])
                self.assertEqual([], publish_due.publish(date(2026, 8, 17)))
            finally:
                publish_due.CONTENT = original


if __name__ == "__main__":
    unittest.main()
