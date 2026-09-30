import json
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from samsung_engine.cache import SemanticCache
from samsung_engine.data import CatalogEntry, load_catalog, load_references
from samsung_engine.enrichment import enrich, is_navigation_wrong_axis_after_app, split_intents
from samsung_engine.ordering import ActionNode, OrderingError, order_actions
from samsung_engine.retrieval import Retriever, placeholder_link
from samsung_engine.schema import Action, ContextDeepLinkResponse, Deeplink, Goal, StepGroup, ValidationDeepLink
from samsung_engine.state import MockStateProvider, UnknownStateProvider, condition_satisfied, skip_satisfied
from samsung_engine.extraction import parse_generated_plan
from samsung_engine.validation import PlanValidationError, validate_plan


ROOT = Path(__file__).resolve().parents[1]


def catalog():
    return {
        "bixby://masked/act/display": CatalogEntry(Deeplink(deeplink="bixby://masked/act/display", description="Open Display settings"), screen="Display"),
        "bixby://masked/act/nav": CatalogEntry(Deeplink(deeplink="bixby://masked/act/nav", description="Open Navigation bar settings"), screen="Navigation bar"),
    }


def action(name, category="auto", uri="bixby://masked/act/nav"):
    return Action(actionName=name, description="It will let you choose navigation type", category=category, stepGroups=[StepGroup(steps=["Tap Navigation bar."], actionableDeeplink=Deeplink(deeplink=uri, description="Open Navigation bar settings") if uri else None)])


class EnrichmentTests(unittest.TestCase):
    def test_paraphrases_and_intent(self):
        e = enrich("swipe navigation wrong direction after installing an app")
        self.assertEqual(len(e.variations), 9)
        self.assertEqual(len(set(e.variations)), 9)
        self.assertTrue(is_navigation_wrong_axis_after_app(e.raw))
        self.assertFalse(is_navigation_wrong_axis_after_app("battery draining after an app install"))

    def test_split_independent_intents(self):
        self.assertEqual(len(split_intents("screen flickers and also battery drains fast")), 2)
        self.assertEqual(len(split_intents("screen flickers and battery drains very fast")), 2)


class RetrievalTests(unittest.TestCase):
    def test_exact_child_beats_parent(self):
        result = Retriever(catalog()).resolve("Navigation bar")
        self.assertEqual(result.link.deeplink, "bixby://masked/act/nav")
        parent_only = {"bixby://masked/act/display": catalog()["bixby://masked/act/display"]}
        self.assertIsNone(Retriever(parent_only).resolve("Navigation bar"))

    def test_placeholder_is_narrow(self):
        self.assertIsNone(Retriever({}).resolve("Navigation bar"))
        self.assertEqual(Retriever({}).resolve("Navigation bar", allow_pdf_placeholder=True).link.deeplink, "bixby://dummy_positive")
        self.assertIsNone(Retriever({}).resolve("Battery usage", allow_pdf_placeholder=True))

    def test_explicit_source_screen_placeholder_and_parent_gate(self):
        parent = {"bixby://masked/act/display": catalog()["bixby://masked/act/display"]}
        self.assertIsNone(Retriever(parent).resolve("Navigation bar"))
        child = Retriever(parent).resolve("Navigation bar", allow_source_placeholder=True)
        self.assertEqual(child.link.deeplink, "bixby://dummy_positive")
        self.assertEqual(child.source, "source_screen_placeholder")
        self.assertIsNone(Retriever(parent).resolve("Unknown screen", allow_source_placeholder=True))
        misleading = CatalogEntry(
            Deeplink(deeplink="bixby://masked/act/apps-grid",
                     description="Opens the Apps screen grid settings page in device Settings."),
        )
        self.assertIsNone(Retriever({misleading.link.deeplink: misleading}).resolve("Apps"))
        for target in ("Apps", "Navigation bar", "Screen lock and biometrics"):
            link = placeholder_link(target)
            self.assertIsNotNone(link)
            self.assertTrue(5 <= len(link.description.split()) <= 7)
            self.assertTrue(5 <= len(link.message.split()) <= 7)
            self.assertIn(target.casefold(), link.description.casefold())


class OrderingAndValidationTests(unittest.TestCase):
    def test_critical_last_and_dependencies(self):
        nodes = [
            ActionNode("restart", action("Restart device", "critical", None), depends_on=frozenset({"nav"}), disruptiveness=5),
            ActionNode("nav", action("Configure Navigation bar settings")),
        ]
        ordered = order_actions(nodes)
        self.assertEqual([a.actionName for a in ordered], ["Configure Navigation bar settings", "Restart device"])
        with self.assertRaises(OrderingError):
            order_actions([ActionNode("a", action("One action"), depends_on=frozenset({"b"})), ActionNode("b", action("Two action"), depends_on=frozenset({"a"}))])

    def test_validation_rejects_manual_links_and_unknown_uris(self):
        sample = load_references(ROOT / "data/reference_navigation.json")[0].response
        validate_plan(sample, {})
        raw = sample.model_dump()
        raw["contexts"][0]["actions"][0]["category"] = "manual"
        with self.assertRaises(PlanValidationError):
            validate_plan(ContextDeepLinkResponse.model_validate(raw), {})
        raw = sample.model_dump()
        raw["contexts"][0]["actions"][0]["stepGroups"][0]["actionableDeeplink"]["deeplink"] = "bixby://invented"
        with self.assertRaises(PlanValidationError):
            validate_plan(ContextDeepLinkResponse.model_validate(raw), {})

    def test_placeholder_rejected_when_catalog_has_exact_screen(self):
        sample = load_references(ROOT / "data/reference_navigation.json")[0].response
        with self.assertRaises(PlanValidationError):
            validate_plan(sample, catalog())

    def test_parent_screen_link_rejected_for_child_action(self):
        sample = load_references(ROOT / "data/reference_navigation.json")[0].response.model_copy(deep=True)
        a = sample.contexts[0].actions[0]
        a.actionName = "Open Navigation bar Settings"
        a.stepGroups[0].actionableDeeplink = catalog()["bixby://masked/act/display"].link
        with self.assertRaises(PlanValidationError):
            validate_plan(sample, {"bixby://masked/act/display": catalog()["bixby://masked/act/display"]})

    def test_malformed_generated_output_rejected(self):
        with self.assertRaises(PlanValidationError):
            parse_generated_plan("```json\n{}\n```", {})
        with self.assertRaises(PlanValidationError):
            parse_generated_plan('{"contexts":[],"extra":true}', {})

    def test_state_skip_only_when_known_and_satisfied(self):
        link = ValidationDeepLink(deeplink="bixby://masked/act/nav", key="enabled", resultType="boolean", condition="equal", value="true")
        a = action("Configure Navigation bar settings")
        a.stepGroups[0].validationDeeplink = link
        self.assertEqual(len(skip_satisfied([a], UnknownStateProvider())), 1)
        self.assertEqual(len(skip_satisfied([a], MockStateProvider({(link.deeplink, link.key): False}))), 1)
        self.assertEqual(len(skip_satisfied([a], MockStateProvider({(link.deeplink, link.key): True}))), 0)


class CacheTests(unittest.TestCase):
    def test_exact_semantic_and_false_hit_guards(self):
        sample = load_references(ROOT / "data/reference_navigation.json")[0].response
        with tempfile.TemporaryDirectory() as temp:
            cache = SemanticCache(Path(temp) / "plans.sqlite3", {})
            q = "swipe gestures wrong direction after installing app"
            cache.put(q, "nav", None, sample)
            self.assertEqual(cache.get(q, "nav", None)[1], "exact")
            self.assertEqual(cache.get("gestures swipe wrong direction after app installation", "nav", None)[1], "semantic")
            self.assertIsNone(cache.get("battery drains fast", "battery", None))
            self.assertIsNone(cache.get(q, "nav", "different SIIS text"))

    def test_invalid_cached_plan_is_not_served(self):
        sample = load_references(ROOT / "data/reference_navigation.json")[0].response
        with tempfile.TemporaryDirectory() as temp:
            cache = SemanticCache(Path(temp) / "plans.sqlite3", {})
            cache.put("swipe app wrong direction", "nav", None, sample)
            import sqlite3
            with closing(sqlite3.connect(cache.path)) as db:
                with db:
                    db.execute("UPDATE plans SET plan=?", ('{"contexts":[{"bad":1}]}',))
            self.assertIsNone(cache.get("swipe app wrong direction", "nav", None))
