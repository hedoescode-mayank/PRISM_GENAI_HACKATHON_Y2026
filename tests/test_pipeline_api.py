import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from samsung_engine.api import make_handler
from samsung_engine.pipeline import TroubleshootingEngine
from samsung_engine.schema import ApiResponse


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.data = self.base / "data"
        self.data.mkdir()
        shutil.copy(ROOT / "data/reference_navigation.json", self.data)
        self.cache = self.base / "cache.sqlite3"

    def engine(self):
        return TroubleshootingEngine(self.data, self.cache)

    def test_pdf_golden_api_plan(self):
        engine = self.engine()
        result = engine.troubleshoot({"query": "phone swipe gestures wrong direction after app install"})
        ApiResponse.model_validate(result.model_dump())
        self.assertTrue(result.meta.cache_hit)
        self.assertEqual(result.response.contexts[0].actions[0].stepGroups[0].actionableDeeplink.deeplink, "bixby://dummy_positive")
        self.assertEqual(result.response.contexts[0].title, "Swipe navigation settings")

    def test_classified_reference_paraphrase_uses_validated_cache(self):
        engine = self.engine()
        paraphrase = "My Galaxy swipes vertical rather than horizontal since installing another app"
        result = engine.troubleshoot({"query": paraphrase})
        self.assertTrue(result.meta.cache_hit)
        self.assertEqual(result.response.contexts[0].title, "Swipe navigation settings")
        unrelated = engine.troubleshoot({"query": "battery drains after installing another app"})
        self.assertFalse(unrelated.meta.cache_hit)
        self.assertEqual(unrelated.fallback, "no_match")

    def test_unbacked_multi_intent_is_no_match(self):
        result = self.engine().troubleshoot({"query": "screen flickers and battery drains very fast"})
        self.assertEqual(result.fallback, "no_match")
        self.assertEqual(result.response.contexts, [])
        self.assertFalse(result.meta.cache_hit)

    def test_explicit_siis_path_with_exact_catalog_target(self):
        entries = [
            {"deeplink": "bixby://masked/act/display", "description": "Open Display settings", "screen": "Display"},
            {"deeplink": "bixby://masked/act/nav", "description": "Open Navigation bar settings", "screen": "Navigation bar"},
        ]
        (self.data / "deeplinks.json").write_text(json.dumps(entries), encoding="utf-8")
        engine = self.engine()
        result = engine.troubleshoot({"query": "swipe direction problem", "siis_response": "Open Settings > Display > Navigation bar. Choose the navigation type."})
        self.assertEqual(len(result.response.contexts), 1)
        self.assertEqual(result.response.contexts[0].actions[0].stepGroups[0].actionableDeeplink.deeplink, "bixby://masked/act/nav")
        self.assertFalse(result.meta.cache_hit)
        second = engine.troubleshoot({"query": "swipe direction problem", "siis_response": "Open Settings > Display > Navigation bar. Choose the navigation type."})
        self.assertTrue(second.meta.cache_hit)
        self.assertEqual(engine.troubleshoot({"query": "swipe direction problem", "siis_response": "Open Settings > Display > Unknown screen."}).fallback, "no_match")

    def test_explicit_siis_vetted_missing_screen_uses_placeholder(self):
        engine = self.engine()
        response = engine.troubleshoot({
            "query": "Connections settings problem",
            "siis_response": "Open Settings > Connections.",
        })
        self.assertIsNone(response.fallback)
        link = response.response.contexts[0].actions[0].stepGroups[0].actionableDeeplink
        self.assertEqual(link.deeplink, "bixby://dummy_positive")
        self.assertIn("connections", link.description.casefold())
        self.assertTrue(5 <= len(link.description.split()) <= 7)
        self.assertTrue(5 <= len(link.message.split()) <= 7)
        unsupported = engine.troubleshoot({
            "query": "Unknown screen problem",
            "siis_response": "Open Settings > Display > Unknown screen.",
        })
        self.assertEqual(unsupported.fallback, "no_match")

        long_target = engine.troubleshoot({
            "query": "Screen lock and biometrics settings problem",
            "siis_response": "Open Settings > Screen lock and biometrics.",
        })
        self.assertEqual(long_target.response.contexts[0].title, "Device settings")
        self.assertEqual(
            long_target.response.contexts[0].actions[0].stepGroups[0].actionableDeeplink.deeplink,
            "bixby://dummy_positive",
        )

    def test_real_catalog_replaces_pdf_placeholder(self):
        (self.data / "deeplinks.json").write_text(json.dumps([
            {"deeplink": "bixby://masked/act/nav", "description": "Open Navigation bar settings", "screen": "Navigation bar"}
        ]), encoding="utf-8")
        result = self.engine().troubleshoot({"query": "phone swipe gestures wrong direction after app install"})
        self.assertEqual(result.response.contexts[0].actions[0].stepGroups[0].actionableDeeplink.deeplink, "bixby://masked/act/nav")

    def test_supplied_theme02_sources_and_catalog(self):
        supplied = ROOT / "data"
        if not (supplied / "siis_responses.json").exists():
            self.skipTest("Theme 02 starter assets not installed")
        engine = TroubleshootingEngine(supplied, self.cache)
        rows = {row["id"]: row for row in json.loads((supplied / "siis_responses.json").read_text())["responses"]}

        blank = engine.troubleshoot({"query": rows["row_2"]["original_query"]})
        self.assertIsNone(blank.fallback)
        self.assertIn("Force Restart Device", [a.actionName for a in blank.response.contexts[0].actions])
        self.assertEqual(blank.response.contexts[0].actions[-1].actionName, "Force Restart Device")
        self.assertEqual(blank.response.contexts[0].actions[-1].category.value, "critical")
        self.assertTrue(all(a.stepGroups[0].actionableDeeplink is None for a in blank.response.contexts[0].actions))

        # The same generic SIIS article backs row_16, but that complaint is
        # charger-triggered flashing rather than a fully blank display.
        unrelated_same_article = engine.troubleshoot({"query": rows["row_16"]["original_query"]})
        self.assertEqual(unrelated_same_article.fallback, "no_match")
        self.assertFalse(unrelated_same_article.meta.cache_hit)

        display_only = engine.troubleshoot({"query": rows["row_22"]["original_query"]})
        display_actions = [a.actionName for a in display_only.response.contexts[0].actions]
        self.assertIn("Force Restart Device", display_actions)
        self.assertNotIn("Inspect Device for Damage", display_actions)
        self.assertNotIn("Charge the Device", display_actions)
        self.assertNotIn("Attempt to Power On", display_actions)
        self.assertNotIn("Inspect Charger and Cable", display_actions)
        reverse = TroubleshootingEngine(supplied, self.base / "reverse-cache.sqlite3")
        first_display = reverse.troubleshoot({"query": rows["row_22"]["original_query"]})
        then_no_power = reverse.troubleshoot({"query": rows["row_4"]["original_query"]})
        self.assertNotIn("Charge the Device", [a.actionName for a in first_display.response.contexts[0].actions])
        self.assertIn("Charge the Device", [a.actionName for a in then_no_power.response.contexts[0].actions])
        self.assertFalse(then_no_power.meta.cache_hit)

        irrelevant = engine.troubleshoot({"query": rows["row_1"]["original_query"]})
        self.assertEqual(irrelevant.fallback, "no_match")
        self.assertEqual(irrelevant.response.contexts, [])

        damaged = engine.troubleshoot({"query": rows["row_19"]["original_query"]})
        self.assertEqual(damaged.response.contexts[0].actions[-1].actionName, "Visit an Authorized Service Center")
        self.assertIsNone(damaged.response.contexts[0].actions[-1].stepGroups[0].actionableDeeplink)

        nav = engine.troubleshoot({"query": "phone swipe gestures wrong direction after app install"})
        self.assertEqual(nav.response.contexts[0].actions[0].stepGroups[0].actionableDeeplink.deeplink,
                         "bixby://masked/act/2f3dd95259")

    def test_supplied_sample_is_a_narrow_catalog_backed_reference(self):
        if not (ROOT / "data/reference_sample.json").exists():
            self.skipTest("curated Theme 02 sample is not installed")
        engine = TroubleshootingEngine(ROOT / "data", self.cache)
        sample = json.loads((ROOT / "data/theme02_sample_output.json").read_text())
        result = engine.troubleshoot({"query": sample["query"]})
        self.assertIsNone(result.fallback)
        actions = result.response.contexts[0].actions
        self.assertEqual([action.category.value for action in actions], ["auto", "manual"])
        self.assertEqual(actions[0].stepGroups[0].actionableDeeplink.deeplink,
                         "bixby://masked/act/b3ed3ed663")
        self.assertEqual(actions[0].stepGroups[0].validationDeeplink.deeplink,
                         "bixby://masked/val/266037d0c5")
        self.assertIsNone(actions[1].stepGroups[0].actionableDeeplink)
        self.assertNotIn("peeling film", str(result.model_dump()).casefold())
        other = engine.troubleshoot({"query": "My phone has a cracked screen."})
        self.assertEqual(other.fallback, "no_match")

    def test_api_json_errors_and_degraded_health(self):
        engine = self.engine()
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(engine))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"
        with self.assertRaises(urllib.error.HTTPError) as captured:
            urllib.request.urlopen(base + "/health")
        self.assertEqual(captured.exception.code, 503)
        request = urllib.request.Request(base + "/v1/troubleshoot", data=json.dumps({"query": "phone swipe gestures wrong direction after app install"}).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)
            body = json.loads(response.read())
            self.assertEqual(response.headers["Content-Type"], "application/json; charset=utf-8")
            ApiResponse.model_validate(body)
        bad = urllib.request.Request(base + "/v1/troubleshoot", data=json.dumps({"query": "Visit www.example.com", "extra": 1}).encode(), headers={"Content-Type": "application/json"})
        with self.assertRaises(urllib.error.HTTPError) as captured:
            urllib.request.urlopen(bad)
        self.assertEqual(captured.exception.code, 422)
        injected = urllib.request.Request(
            base + "/v1/troubleshoot",
            data=json.dumps({"query": "blank screen", "https://evil.example": "payload"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(urllib.error.HTTPError) as captured:
            urllib.request.urlopen(injected)
        self.assertEqual(captured.exception.code, 422)
        self.assertNotIn(b"https://evil.example", captured.exception.read())
