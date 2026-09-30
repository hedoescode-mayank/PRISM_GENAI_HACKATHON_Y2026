"""Smoke checks for the supplied Theme 02 input kit."""

import json
import unittest
from pathlib import Path

from samsung_engine.data import load_data


ROOT = Path(__file__).resolve().parents[1]


class SuppliedAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw_catalog = json.loads((ROOT / "data/deeplinks.json").read_text(encoding="utf-8"))
        cls.raw_siis = json.loads((ROOT / "data/siis_responses.json").read_text(encoding="utf-8"))
        cls.store = load_data(ROOT / "data")

    def test_full_catalog_loaded_with_exact_links_and_validation(self):
        records = self.raw_catalog["deeplinks"]
        self.assertEqual(self.raw_catalog["count"], len(records))
        self.assertEqual(len(records), 578)
        self.assertEqual(len(self.store.catalog), 577)
        self.assertNotIn("bixby://dummy_positive", self.store.catalog)
        for item in records:
            if item["deeplink"] == "bixby://dummy_positive":
                continue
            entry = self.store.catalog[item["deeplink"]]
            self.assertEqual(entry.link.deeplink, item["deeplink"])
            self.assertEqual(entry.identifier, item["id"])
            self.assertEqual(entry.control_type, item["control_type"])
            self.assertEqual(entry.validation.deeplink if entry.validation else None,
                             item["validation"]["deeplink"] if item["validation"] else None)

    def test_paired_siis_source_content_available(self):
        records = self.raw_siis["responses"]
        self.assertEqual(self.raw_siis["count"], len(records))
        self.assertEqual(len(records), 20)
        self.assertEqual(len(self.store.siis), 20)
        for item in records:
            self.assertEqual(self.store.siis[item["original_query"].casefold()],
                             item["siis_response"]["content"].strip())
        self.assertEqual(self.store.warnings, [])


if __name__ == "__main__":
    unittest.main()
