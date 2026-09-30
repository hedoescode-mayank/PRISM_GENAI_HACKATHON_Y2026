"""Optional device-state checks; unknown observations never skip actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from .schema import Action, Condition, ResultTypes, ValidationDeepLink


class StateMode(str, Enum):
    LIVE = "LIVE"
    MOCK = "MOCK"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Observation:
    mode: StateMode
    value: Any = None


class StateProvider(Protocol):
    def read(self, link: ValidationDeepLink) -> Observation: ...


class UnknownStateProvider:
    def read(self, link: ValidationDeepLink) -> Observation:
        return Observation(StateMode.UNKNOWN)


class MockStateProvider:
    def __init__(self, values: dict[tuple[str, str], Any]):
        self.values = values

    def read(self, link: ValidationDeepLink) -> Observation:
        key = (link.deeplink, link.key)
        return Observation(StateMode.MOCK, self.values[key]) if key in self.values else Observation(StateMode.UNKNOWN)


def _convert(value: Any, result_type: ResultTypes | None) -> Any:
    if result_type == ResultTypes.boolean:
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.casefold() in {"true", "false"}:
            return value.casefold() == "true"
        raise ValueError("invalid boolean state")
    if result_type == ResultTypes.intNum:
        return int(value)
    if result_type == ResultTypes.floatNum:
        return float(value)
    return str(value)


def condition_satisfied(link: ValidationDeepLink, observation: Observation) -> bool | None:
    if observation.mode == StateMode.UNKNOWN or link.condition is None or link.value is None:
        return None
    try:
        actual = _convert(observation.value, link.resultType)
        expected = _convert(link.value, link.resultType)
        if link.condition == Condition.equal:
            return actual == expected
        if isinstance(actual, bool) or isinstance(expected, bool):
            return None
        return actual > expected if link.condition == Condition.greater else actual < expected
    except (ValueError, TypeError):
        return None


def skip_satisfied(actions: list[Action], provider: StateProvider) -> list[Action]:
    remaining = []
    for action in actions:
        links = [group.validationDeeplink for group in action.stepGroups]
        if not links or any(link is None for link in links):
            remaining.append(action)
            continue
        if not all(condition_satisfied(link, provider.read(link)) is True for link in links if link):
            remaining.append(action)
    return remaining
