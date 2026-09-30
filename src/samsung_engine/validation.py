"""Programmatic validation after extraction, retrieval, and ordering."""

from __future__ import annotations

import json
import re

from .data import CatalogEntry
from .retrieval import PLACEHOLDER, Retriever, placeholder_link
from .schema import ActionCategory, ApiResponse, ContextDeepLinkResponse, WEB_LINK


class PlanValidationError(ValueError):
    pass


def validate_plan(
    plan: ContextDeepLinkResponse,
    catalog: dict[str, CatalogEntry],
    *,
    allow_pdf_placeholder: bool = True,
) -> None:
    try:
        plan = ContextDeepLinkResponse.model_validate(plan.model_dump())
    except Exception as exc:
        raise PlanValidationError(f"schema validation failed: {exc}") from exc
    if WEB_LINK.search(json.dumps(plan.model_dump())):
        raise PlanValidationError("web URL leakage")
    retriever = Retriever(catalog)
    for goal in plan.contexts:
        seen_names: set[str] = set()
        critical_seen = False
        for action in goal.actions:
            name = action.actionName.casefold()
            if name in seen_names:
                raise PlanValidationError("duplicate action")
            seen_names.add(name)
            if action.category == ActionCategory.critical:
                critical_seen = True
            elif critical_seen:
                raise PlanValidationError("critical actions must be last")
            links = [group.actionableDeeplink for group in action.stepGroups if group.actionableDeeplink]
            unique_uris = {link.deeplink for link in links}
            if len(unique_uris) > 1:
                raise PlanValidationError("one action spans multiple screens")
            if action.category == ActionCategory.manual and links:
                raise PlanValidationError("manual actions cannot have an actionable deep link")
            if action.category == ActionCategory.auto and not links:
                raise PlanValidationError("auto actions require an actionable deep link")
            opened_screen = re.fullmatch(r"open (.+) settings", name)
            if opened_screen and links and links[0].deeplink != PLACEHOLDER:
                resolved_screen = retriever.resolve(opened_screen.group(1))
                if not resolved_screen or resolved_screen.link.deeplink != links[0].deeplink:
                    raise PlanValidationError("actionable deep link targets a different screen")
            for group in action.stepGroups:
                if group.validationDeeplink:
                    action_link = group.actionableDeeplink
                    if not action_link or action_link.deeplink not in catalog:
                        raise PlanValidationError("validation requires a catalog-backed action")
                    expected = catalog[action_link.deeplink].validation
                    if expected is None or group.validationDeeplink != expected:
                        raise PlanValidationError("validation deep link is not paired with this catalog action")
            for link in links:
                if link.deeplink == PLACEHOLDER:
                    if not allow_pdf_placeholder:
                        raise PlanValidationError("reserved fallback is disabled")
                    if name == "configure navigation bar settings":
                        target = "Navigation bar"
                        permitted_links = [retriever.resolve(target, allow_pdf_placeholder=True).link]
                    else:
                        matched = re.fullmatch(r"open (.+) settings", name)
                        target = matched.group(1) if matched else ""
                        canonical = placeholder_link(target)
                        permitted_links = [canonical] if canonical else []
                    if not permitted_links or link not in permitted_links:
                        raise PlanValidationError("reserved fallback lacks vetted screen metadata")
                    tap = re.compile(rf"tap (?:on )?{re.escape(target.casefold())}\.")
                    if not any(tap.fullmatch(step.casefold()) for group in action.stepGroups for step in group.steps):
                        raise PlanValidationError("reserved fallback lacks a target-screen step")
                    if retriever.resolve(target) and retriever.resolve(target).source == "catalog":
                        raise PlanValidationError("reserved fallback used despite indexed exact screen")
                elif link.deeplink not in catalog:
                    raise PlanValidationError("actionable deep link is absent from catalog")
                elif catalog[link.deeplink].link != link:
                    raise PlanValidationError("catalog deep link metadata was altered")


def validate_api_response(value: ApiResponse, catalog: dict[str, CatalogEntry]) -> None:
    try:
        value = ApiResponse.model_validate(value.model_dump())
    except Exception as exc:
        raise PlanValidationError(f"API schema validation failed: {exc}") from exc
    if WEB_LINK.search(json.dumps(value.model_dump())):
        raise PlanValidationError("web URL leakage in API response")
    validate_plan(value.response, catalog)
