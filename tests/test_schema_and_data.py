import json
import importlib.util
import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from samsung_engine.data import DataError, load_catalog, load_references, load_siis
from samsung_engine.schema import Action, ApiResponse, ContextDeepLinkResponse, Goal, TroubleshootRequest
from samsung_engine.validation import validate_plan
from samsung_engine.data import load_data


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.sample = load_references(ROOT / "data/reference_navigation.json")[0].response

    def test_pdf_reference_obeys_contract(self):
        self.assertEqual(len(self.sample.contexts), 1)
        self.assertEqual(self.sample.contexts[0].actions[0].stepGroups[0].actionableDeeplink.deeplink, "bixby://dummy_positive")

    def test_output_matches_supplied_theme02_schema(self):
        source = ROOT / "source/theme02/schema.py"
        self.assertTrue(source.exists(), "preserved authoritative schema is required")
        spec = importlib.util.spec_from_file_location("theme02_supplied_schema", source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.ContextDeeplinkResponse.model_validate(self.sample.model_dump())
        link = self.sample.contexts[0].actions[0].stepGroups[0].actionableDeeplink
        self.assertIn("deeplink", link.model_dump())
        self.assertNotIn("deepLink", link.model_dump())

    def test_supplied_sample_link_and_validation_pair(self):
        # Supplied prose exceeds the PDF's word count, so only the prose is
        # shortened here; both catalog URIs and their metadata stay verbatim.
        raw = json.loads((ROOT / "data/theme02_sample_output.json").read_text(encoding="utf-8"))["response"]
        raw["contexts"][0]["actions"][0]["description"] = "It will help preserve your phone data"
        raw["contexts"][0]["actions"][1]["description"] = "It will arrange a screen repair visit"
        plan = ContextDeepLinkResponse.model_validate(raw)
        validate_plan(plan, load_data(ROOT / "data").catalog)

    def test_rule_fields_reject_bad_shapes(self):
        raw = self.sample.model_dump()
        raw["contexts"][0]["actions"][0]["description"] = "It helps"
        with self.assertRaises(ValidationError):
            ContextDeepLinkResponse.model_validate(raw)
        raw = self.sample.model_dump()
        raw["contexts"][0]["title"] = "A title that has too many words"
        with self.assertRaises(ValidationError):
            ContextDeepLinkResponse.model_validate(raw)
        raw = self.sample.model_dump()
        raw["contexts"][0]["score"] = 2.0
        with self.assertRaises(ValidationError):
            ContextDeepLinkResponse.model_validate(raw)
        raw = self.sample.model_dump()
        raw["contexts"][0]["extra"] = 1
        with self.assertRaises(ValidationError):
            ContextDeepLinkResponse.model_validate(raw)

    def test_urls_rejected_at_input_and_output(self):
        with self.assertRaises(ValidationError):
            TroubleshootRequest(query="Visit https://example.com to fix phone")
        raw = self.sample.model_dump()
        raw["contexts"][0]["actions"][0]["stepGroups"][0]["steps"][0] = "Visit www.example.com"
        with self.assertRaises(ValidationError):
            ContextDeepLinkResponse.model_validate(raw)

    def test_empty_response_requires_fallback(self):
        with self.assertRaises(ValidationError):
            ApiResponse(query="missing issue", query_variations=[f"variant {i}" for i in range(9)], response=ContextDeepLinkResponse(), meta={"latency_ms": 1, "cache_hit": False, "model": "local", "cost_usd": 0.0})


class DataTests(unittest.TestCase):
    def _write(self, value):
        self.temp = tempfile.TemporaryDirectory()
        path = Path(self.temp.name) / "data.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        self.addCleanup(self.temp.cleanup)
        return path

    def test_catalog_duplicate_and_invalid_link(self):
        valid = {"deeplink": "bixby://masked/act/1", "description": "Open Battery usage settings", "screen": "Battery usage"}
        self.assertEqual(len(load_catalog(self._write([valid]))), 1)
        with self.assertRaises(DataError):
            load_catalog(self._write([valid, valid]))
        with self.assertRaises(DataError):
            load_catalog(self._write([{"deeplink": "https://example.com", "description": "Battery"}]))
        with self.assertRaises(DataError):
            load_catalog(self._write({"count": 2, "deeplinks": [valid]}))

    def test_siis_duplicate_and_malformed(self):
        self.assertEqual(load_siis(self._write([{"query": "battery", "response": "Open Settings > Battery > Usage"}])), {"battery": "Open Settings > Battery > Usage"})
        with self.assertRaises(DataError):
            load_siis(self._write([{"query": "battery", "response": "one"}, {"query": "Battery", "response": "two"}]))
        with self.assertRaises(DataError):
            load_siis(self._write([{"query": "battery"}]))
        with self.assertRaises(DataError):
            load_siis(self._write({"count": 2, "responses": [{"query": "battery", "response": "one"}]}))
