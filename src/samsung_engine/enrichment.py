"""Deterministic query enrichment without unsupported Samsung equivalences."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


TOKEN = re.compile(r"[a-z0-9]+")
STOP = {"a", "an", "the", "my", "me", "i", "is", "it", "to", "on", "in", "of", "and", "or", "for", "after", "that", "this", "phone", "mobile", "galaxy", "samsung"}
SYNONYMS = {
    "gestures": "gesture", "swipes": "swipe", "swiping": "swipe", "swiped": "swipe",
    "sideways": "horizontal", "left": "horizontal", "right": "horizontal",
    "up": "vertical", "down": "vertical", "vertically": "vertical",
    "installed": "install", "installing": "install", "installation": "install", "downloading": "install", "downloaded": "install", "application": "app",
    "direction": "axis", "directions": "axis", "wrong": "axis", "way": "axis",
    "draining": "drain", "drains": "drain", "battery": "battery", "slowly": "slow",
}


def tokens(text: str) -> tuple[str, ...]:
    return tuple(SYNONYMS.get(token, token) for token in TOKEN.findall(text.casefold()) if token not in STOP)


def intent_signature(text: str) -> frozenset[str]:
    return frozenset(tokens(text))


def is_navigation_wrong_axis_after_app(text: str) -> bool:
    t = intent_signature(text)
    return bool(t & {"swipe", "gesture"}) and bool(t & {"axis", "vertical", "horizontal", "scroll"}) and bool(t & {"app", "install"})


def split_intents(query: str) -> tuple[str, ...]:
    """Split only clear independent symptoms; preserve ambiguous conjunctions."""
    pieces = re.split(r"\s+(?:and also|as well as|plus)\s+|[;]", query, flags=re.I)
    if len(pieces) == 1:
        both = re.split(r"\s+and\s+", query, maxsplit=1, flags=re.I)
        domains = ({"screen", "display", "flicker", "touch", "swipe", "gesture"},
                   {"battery", "drain", "power", "charging"},
                   {"camera", "photo", "video"},
                   {"slow", "lag", "performance", "update"})
        if len(both) == 2:
            left, right = set(tokens(both[0])), set(tokens(both[1]))
            left_domains = {i for i, group in enumerate(domains) if left & group}
            right_domains = {i for i, group in enumerate(domains) if right & group}
            if left_domains and right_domains and left_domains.isdisjoint(right_domains):
                pieces = both
    pieces = [piece.strip(" .") for piece in pieces if piece.strip(" .")]
    return tuple(pieces) if pieces else (query,)


def variations(query: str) -> list[str]:
    base = query.strip().rstrip(".?!")
    typo = re.sub(r"\b([A-Za-z]{6,})\b", lambda m: m.group(1)[:3] + m.group(1)[4:], base, count=1)
    # Varied registers. Generated text is never used as new troubleshooting evidence.
    candidates = [
        f"I am experiencing this issue: {base}.",
        f"My Galaxy phone has this problem: {base}.",
        f"How can I troubleshoot this: {base}?",
        f"Please diagnose the device symptom: {base}.",
        f"The issue in brief: {base}.",
        f"Help, {base} and I cannot fix it.",
        f"{base} - what setting should I check?",
        f"Device complaint keywords: {base}.",
        f"Plz help with this: {typo}.",
    ]
    return candidates


@dataclass(frozen=True)
class EnrichedQuery:
    raw: str
    canonical: str
    variations: tuple[str, ...]
    signature: frozenset[str]
    cache_key: str
    intents: tuple[str, ...]


def enrich(query: str) -> EnrichedQuery:
    normalized = " ".join(query.split())
    signature = intent_signature(normalized)
    canonical = " ".join(sorted(signature)) or normalized.casefold()
    key = hashlib.sha256(canonical.encode()).hexdigest()
    return EnrichedQuery(query, canonical, tuple(variations(normalized)), signature, key, split_intents(normalized))
