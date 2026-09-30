"""Complaint to fully validated API response."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from pathlib import Path

from .cache import SemanticCache
from .data import DataStore, load_data
from .enrichment import enrich, intent_signature
from .extraction import ExplicitSiisProvider, LocalReferenceProvider
from .ordering import ActionNode, order_actions
from .retrieval import PLACEHOLDER, Retriever, SourceRetriever
from .schema import Action, ActionCategory, ApiResponse, ContextDeepLinkResponse, Goal, Meta, StepGroup, TroubleshootRequest
from .state import StateProvider, UnknownStateProvider, skip_satisfied
from .validation import validate_api_response, validate_plan


LOG = logging.getLogger(__name__)


def _title(query: str, drafts: list) -> str:
    lowered = query.casefold()
    if "crack" in lowered or "broken" in lowered:
        return "Screen damage"
    if "touch" in lowered or "input" in lowered:
        return "Touchscreen response"
    if any(word in lowered for word in ("blank", "black", "dark", "no image")):
        return "Blank display"
    if drafts and drafts[0].category == ActionCategory.auto:
        target = drafts[0].target
        words = len(target.split())
        if words in (2, 3):
            return target.capitalize()
        if words == 1:
            return f"{target} settings".capitalize()
        return "Device settings"
    return "Device troubleshooting"


def _description(target: str) -> str:
    candidate = f"It will let you inspect {target.lower()}"
    return candidate if 5 <= len(candidate.split()) <= 7 else "It will show the selected settings screen"


class TroubleshootingEngine:
    def __init__(self, data_dir: Path, cache_path: Path, *, cache_threshold: float = 0.45, state_provider: StateProvider | None = None):
        self.data: DataStore = load_data(data_dir)
        self.retriever = Retriever(self.data.catalog)
        self.reference = LocalReferenceProvider(self.data.references)
        self.extractor = ExplicitSiisProvider()
        self.siis_retriever = SourceRetriever(self.data.siis) if self.data.siis else None
        self.state_provider = state_provider or UnknownStateProvider()
        self.cache = SemanticCache(cache_path, self.data.catalog, threshold=cache_threshold)
        self._prewarm()

    def _reference_plan(self, query: str) -> ContextDeepLinkResponse | None:
        plan = self.reference.plan(query)
        if not plan:
            return None
        # A real exact catalog entry takes precedence over the PDF placeholder.
        resolved = self.retriever.resolve("Navigation bar", allow_pdf_placeholder=True)
        if not resolved:
            return None
        for goal in plan.contexts:
            for action in goal.actions:
                for group in action.stepGroups:
                    if group.actionableDeeplink and group.actionableDeeplink.deeplink == PLACEHOLDER:
                        group.actionableDeeplink = resolved.link
        validate_plan(plan, self.data.catalog)
        return plan

    def _prewarm(self) -> None:
        for case in self.data.references:
            plan = self._reference_plan(case.canonical_query)
            if not plan:
                continue
            for query in (case.canonical_query, *case.aliases):
                self.cache.put(query, case.intent, None, plan)

    def _find_siis(self, query: str) -> str | None:
        exact = self.data.siis.get(query.casefold())
        if exact:
            return exact
        if self.siis_retriever is None:
            return None
        return self.siis_retriever.resolve(query)

    def _siis_plan(self, query: str, source: str) -> ContextDeepLinkResponse:
        drafts = self.extractor.extract(query, source)
        nodes: list[ActionNode] = []
        for index, draft in enumerate(drafts):
            resolution = (self.retriever.resolve(draft.target, allow_source_placeholder=True)
                          if draft.category == ActionCategory.auto else None)
            if draft.category == ActionCategory.auto and not resolution:
                LOG.info("unresolved target", extra={"phase": "retrieval", "target": draft.target})
                continue
            action = Action(
                actionName=draft.name or f"Open {draft.target} Settings",
                description=draft.description or _description(draft.target),
                stepGroups=[StepGroup(steps=list(draft.steps), actionableDeeplink=resolution.link if resolution else None)],
                category=draft.category,
            )
            nodes.append(ActionNode(f"{index}:{draft.target.casefold()}", action,
                                    disruptiveness=draft.disruptiveness))
        actions = skip_satisfied(order_actions(nodes), self.state_provider) if nodes else []
        if actions:
            title = _title(query, drafts)
            topic = title.title()
            plan = ContextDeepLinkResponse(contexts=[Goal(
                goal=f"Follow these steps to perform this {topic} Troubleshooting",
                title=title, actions=actions, score=0.75,
            )])
        else:
            plan = ContextDeepLinkResponse()
        validate_plan(plan, self.data.catalog)
        return plan

    def troubleshoot(self, request: TroubleshootRequest | dict) -> ApiResponse:
        started = time.perf_counter()
        request = TroubleshootRequest.model_validate(request)
        enriched = enrich(request.query)
        reference_case = self.reference.match(request.query) if request.siis_response is None else None
        source = request.siis_response or (None if reference_case else self._find_siis(request.query))
        # A cache entry from the same SIIS article must not turn an unrelated
        # complaint into a plan.  The supplied kit reuses articles across
        # materially different complaints, so recheck extraction first.
        drafts = self.extractor.extract(request.query, source) if source else []
        if reference_case:
            intent = reference_case.intent
        elif drafts:
            # Two complaints can reuse the same article but require different
            # subsets of its steps.  Include the extracted procedure shape in
            # the cache guard so one cannot inherit the other's plan.
            procedure = [(d.target, d.name, d.steps, d.category.value) for d in drafts]
            source_hash = hashlib.sha256(source.encode()).hexdigest()
            procedure_hash = hashlib.sha256(json.dumps(procedure).encode()).hexdigest()
            intent = f"siis:{source_hash}:{procedure_hash}"
        else:
            intent = "no_match"
        hit = (self.cache.get(request.query, intent, source,
                              classified_reference=reference_case is not None)
               if intent != "no_match" else None)
        if hit:
            plan, hit_type = hit
            LOG.info("cache hit", extra={"phase": "cache", "kind": hit_type})
        elif reference_case:
            plan = self._reference_plan(request.query) or ContextDeepLinkResponse()
            if plan.contexts:
                self.cache.put(request.query, intent, None, plan)
        elif source:
            plan = self._siis_plan(request.query, source)
            if plan.contexts:
                self.cache.put(request.query, intent, source, plan)
        else:
            plan = ContextDeepLinkResponse()
        fallback = None if plan.contexts else "no_match"
        canonical_query = reference_case.canonical_query if reference_case else " ".join(request.query.split())
        result = ApiResponse(
            query=canonical_query,
            query_variations=list(enriched.variations),
            response=plan,
            meta=Meta(latency_ms=0, cache_hit=bool(hit), model="deterministic-hybrid-v2", cost_usd=0.0),
            fallback=fallback,
        )
        validate_api_response(result, self.data.catalog)
        result.meta.latency_ms = math.ceil((time.perf_counter() - started) * 1000)
        return result
