"""Conservative source-backed extraction from the supplied SIIS passages."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from .data import ReferenceCase
from .enrichment import is_navigation_wrong_axis_after_app, split_intents
from .schema import ActionCategory, ContextDeepLinkResponse


@dataclass(frozen=True)
class DraftAction:
    target: str
    steps: tuple[str, ...]
    category: ActionCategory
    source: str
    name: str | None = None
    description: str | None = None
    disruptiveness: int = 0


class ExtractionProvider(Protocol):
    def extract(self, query: str, siis_response: str | None) -> list[DraftAction]: ...


class LocalReferenceProvider:
    """Recognizes supplied worked cases by exact query or curated alias.

    Only the PDF navigation case has a broader symptom signature.  The
    supplied cracked/flashing sample includes a specific backup action, so
    applying it to arbitrary cracked-screen complaints would overreach.
    """

    def __init__(self, references: list[ReferenceCase]):
        self.references = references

    def match(self, query: str) -> ReferenceCase | None:
        if len(split_intents(query)) > 1:
            return None
        for case in self.references:
            if query.casefold().strip(" .?!") in {text.casefold().strip(" .?!") for text in (case.canonical_query, *case.aliases)}:
                return case
            if case.intent == "navigation_wrong_axis_after_app" and is_navigation_wrong_axis_after_app(query):
                return case
        return None

    def plan(self, query: str) -> ContextDeepLinkResponse | None:
        case = self.match(query)
        return case.response.model_copy(deep=True) if case else None


def _has(text: str, *terms: str) -> bool:
    return any(term in text for term in terms)


def _manual(result: list[DraftAction], source: str, evidence: str, target: str,
            name: str, description: str, *steps: str, disruptiveness: int = 0) -> None:
    if evidence in source:
        result.append(DraftAction(target, steps, ActionCategory.manual, evidence,
                                  name, description, disruptiveness))


class ExplicitSiisProvider:
    """Finds literal Settings paths and narrowly supported physical procedures."""

    PATH = re.compile(r"\bSettings\s*>\s*([^\n.;:]+)", re.I)

    def extract(self, query: str, siis_response: str | None) -> list[DraftAction]:
        if not siis_response:
            return []
        source = siis_response.casefold()
        complaint = query.casefold()
        result: list[DraftAction] = []

        for match in self.PATH.finditer(siis_response):
            parts = [part.strip(" ,\t") for part in match.group(1).split(">")]
            if not parts or any(not part or len(part.split()) > 4 for part in parts):
                continue
            target = parts[-1]
            words = set(re.findall(r"[a-z]{4,}", target.casefold())) - {"settings", "screen"}
            relevant = bool(words & set(re.findall(r"[a-z]{4,}", complaint)))
            if target.casefold() == "navigation bar" and _has(complaint, "swipe", "gesture", "navigation"):
                relevant = True
            if not relevant:
                continue
            steps = ("Open Settings.",) + tuple(f"Tap {part}." for part in parts)
            result.append(DraftAction(target, steps, ActionCategory.auto, match.group(0)))

        blank_complaint = _has(complaint, "blank", "black", "dark", "no image", "not turn on", "won't turn on")
        # A half-visible panel or boot screen with text is a different failure
        # from a fully blank display; the generic SIIS article is too broad.
        if _has(complaint, "half black", "one side", "tiny text", "blue screen"):
            blank_complaint = False
        power_confirmed = _has(complaint, "powers on", "rings", "otherwise works", "phone is on", "device is on")
        blank_source = _has(source, "blank or black display", "blank or black screen",
                            "nothing is visible on the screen", "screen still fails to turn on")
        if blank_complaint and blank_source:
            if not _has(complaint, "no physical damage", "without physical damage"):
                _manual(result, source, "check for physical damage", "Device inspection",
                        "Inspect Device for Damage", "It will identify visible device damage",
                        "Inspect the device for physical damage.")
            if not power_confirmed:
                _manual(result, source, "charger, and usb cable for", "Charger inspection",
                        "Inspect Charger and Cable", "It will identify damaged charging equipment",
                        "Inspect the charger and USB cable for damage.")
            if "power" in source and "volume down" in source and ("force a restart" in source or "forcing a restart" in source):
                seconds = "20" if "20 seconds" in source else "10" if "10 seconds" in source else None
                if seconds:
                    result.append(DraftAction("Force restart",
                        (f"Press and hold Power and Volume down together for {seconds} seconds.",),
                        ActionCategory.critical, "force a restart", "Force Restart Device",
                        "It will restart the unresponsive device", 2))
            if not power_confirmed and "charge" in source and "at least 1 hour" in source:
                result.append(DraftAction("Charging",
                    ("Connect the device to its charger.", "Charge it for at least one hour."),
                    ActionCategory.manual, "at least 1 hour", "Charge the Device",
                    "It will restore power to device", 1))
            if not power_confirmed and "pressing and holding the power button" in source and "15 to 20 seconds" in source:
                result.append(DraftAction("Power on",
                    ("Disconnect the device from the charger.", "Hold the Power or Side button for 15 to 20 seconds."),
                    ActionCategory.manual, "15 to 20 seconds", "Attempt to Power On",
                    "It will test whether device starts", 2))
            if "usb-c to hdmi adapter" in source and "connect the adapter to your phone" in source:
                result.append(DraftAction("External display",
                    ("Connect a compatible adapter to the phone.", "Connect an HDMI cable to the adapter.",
                     "Connect the HDMI cable to the TV or monitor.", "Select the connected input on the TV or monitor."),
                    ActionCategory.manual, "connect the adapter to your phone", "Connect an External Display",
                    "It will display the phone externally", 1))
            elif _has(complaint, "transfer", "back up", "backup") and "back up your device's data by connecting it to a monitor" in source:
                result.append(DraftAction("External display",
                    ("Connect the device to a compatible monitor.",),
                    ActionCategory.manual, "connecting it to a monitor", "Connect to a Monitor",
                    "It will support backing up data", 1))
            # The article presents service only after the restart check.  A
            # critical restart must serialize last, so omit that conditional
            # follow-up rather than present it in the wrong order.
            if (_has(source, "contact the samsung support center", "samsung walk-in service center")
                    and not any(action.name == "Force Restart Device" for action in result)):
                result.append(DraftAction("Repair service",
                    ("Contact Samsung Support or visit a Samsung service center.",),
                    ActionCategory.manual, "service center", "Request Screen Service",
                    "It will arrange professional screen service", 5))

        if _has(complaint, "crack", "broken", "half black") and _has(source, "cracked or bleeding screen", "service options for cracked screens"):
            _manual(result, source, "authorized service center", "Repair service",
                    "Visit an Authorized Service Center", "It will arrange professional screen repair",
                    "Visit a Samsung Authorized Service Center.", disruptiveness=5)

        if _has(complaint, "touch", "input", "responsiveness") and "touchscreen issues" in source:
            _manual(result, source, "screen protector is peeling", "Screen protector",
                    "Inspect the Screen Protector", "It will identify a touch obstruction",
                    "Inspect the screen protector for peeling or debris.")
            _manual(result, source, "lint-free, soft microfiber cloth", "Screen cleaning",
                    "Clean the Touchscreen", "It will remove moisture and debris",
                    "Gently wipe the screen with a soft microfiber cloth.")
            if "force a restart" in source and "volume down" in source and "10 seconds" in source:
                result.append(DraftAction("Force restart",
                    ("Hold Volume down and Power together for about 10 seconds.",),
                    ActionCategory.critical, "force a restart", "Force Restart Device",
                    "It will restart the unresponsive device", 2))

        # Retain the earliest evidence for a repeated procedure.
        unique: dict[tuple[str, str | None], DraftAction] = {}
        for action in result:
            unique.setdefault((action.target.casefold(), action.name), action)
        return list(unique.values())


def parse_generated_plan(raw: str, catalog: dict) -> ContextDeepLinkResponse:
    """Parse untrusted provider JSON through every deterministic gate."""
    from .validation import PlanValidationError, validate_plan

    try:
        plan = ContextDeepLinkResponse.model_validate(json.loads(raw))
        validate_plan(plan, catalog)
        return plan
    except (ValueError, TypeError) as exc:
        raise PlanValidationError(f"generated plan was rejected: {exc}") from exc
