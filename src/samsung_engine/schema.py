"""Strict implementation of the supplied Theme 02 schema.py contract.

Field spellings follow the actual student_kit/schema.py. The outer envelope
comes from the PDF's worked API example, plus its no-match fallback.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictStr, field_validator, model_validator


WEB_LINK = re.compile(r"(?i)(?:https?://|www\.|\[[^\]]+\]\([^)]*\))")
WORDS = re.compile(r"\b[\w'-]+\b", re.UNICODE)
GOAL = re.compile(r"^Follow these steps to perform this .+ (?:Troubleshooting|Configuration)$")


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def require_safe_text(value: str) -> str:
    if WEB_LINK.search(value):
        raise ValueError("web URLs and Markdown links are forbidden")
    if not value.strip():
        raise ValueError("text must not be empty")
    return value.strip()


class BaseDeeplink(ContractModel):
    deeplink: StrictStr

    @field_validator("deeplink")
    @classmethod
    def valid_link(cls, value: str) -> str:
        require_safe_text(value)
        if not value.startswith("bixby://"):
            raise ValueError("actionable deep links must use the Bixby scheme")
        return value


class Deeplink(BaseDeeplink):
    description: StrictStr
    message: Optional[StrictStr] = ""
    classes: Optional[dict[str, str]] = None
    originalType: Optional[StrictStr] = None

    @field_validator("description", "message")
    @classmethod
    def safe_copy(cls, value: str | None) -> str | None:
        return require_safe_text(value) if value else value


class Condition(str, Enum):
    greater = "greater"
    equal = "equal"
    less = "less"


class ResultTypes(str, Enum):
    boolean = "boolean"
    intNum = "integer"
    string = "str"
    floatNum = "float"


class ActionCategory(str, Enum):
    auto = "auto"
    manual = "manual"
    critical = "critical"


class ValidationDeepLink(BaseDeeplink):
    key: StrictStr
    resultType: Optional[ResultTypes] = None
    condition: Optional[Condition] = None
    value: Optional[StrictStr] = None

    @field_validator("key")
    @classmethod
    def safe_key(cls, value: str) -> str:
        return require_safe_text(value)


class StepGroup(ContractModel):
    steps: list[StrictStr]
    validationDeeplink: Optional[ValidationDeepLink] = None
    actionableDeeplink: Optional[Deeplink] = None

    @field_validator("steps")
    @classmethod
    def valid_steps(cls, values: list[str]) -> list[str]:
        if not values:
            raise ValueError("a step group must contain steps")
        return [require_safe_text(value) for value in values]


class Action(ContractModel):
    actionName: StrictStr
    description: StrictStr
    stepGroups: list[StepGroup]
    category: ActionCategory = ActionCategory.manual

    @field_validator("actionName")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return require_safe_text(value)

    @field_validator("description")
    @classmethod
    def valid_description(cls, value: str) -> str:
        value = require_safe_text(value)
        if not value.startswith("It will ") or not 5 <= len(WORDS.findall(value)) <= 7:
            raise ValueError("description must start 'It will' and contain 5–7 words")
        return value

    @field_validator("stepGroups")
    @classmethod
    def has_groups(cls, value: list[StepGroup]) -> list[StepGroup]:
        if not value:
            raise ValueError("an action must contain a step group")
        return value


class Goal(ContractModel):
    goal: StrictStr
    title: StrictStr
    actions: list[Action]
    score: StrictFloat = Field(ge=0.0, le=1.0)

    @field_validator("goal")
    @classmethod
    def valid_goal(cls, value: str) -> str:
        value = require_safe_text(value)
        if not GOAL.fullmatch(value):
            raise ValueError("goal does not follow required syntax")
        return value

    @field_validator("title")
    @classmethod
    def valid_title(cls, value: str) -> str:
        value = require_safe_text(value)
        words = WORDS.findall(value)
        if len(words) not in (2, 3) or value[0] != value[0].upper():
            raise ValueError("title must contain 2–3 words in sentence case")
        return value


class ContextDeeplinkResponse(ContractModel):
    contexts: list[Goal] = Field(default_factory=list)


# Python-only compatibility alias. Serialized field names follow the kit.
ContextDeepLinkResponse = ContextDeeplinkResponse


class Meta(ContractModel):
    latency_ms: int = Field(ge=0)
    cache_hit: StrictBool
    model: StrictStr
    cost_usd: StrictFloat = Field(ge=0.0)


class ApiResponse(ContractModel):
    query: StrictStr
    query_variations: list[StrictStr]
    response: ContextDeeplinkResponse
    meta: Meta
    fallback: Optional[str] = None

    @field_validator("query")
    @classmethod
    def safe_query(cls, value: str) -> str:
        return require_safe_text(value)

    @field_validator("query_variations")
    @classmethod
    def valid_variations(cls, values: list[str]) -> list[str]:
        if not 8 <= len(values) <= 10 or len({v.casefold() for v in values}) != len(values):
            raise ValueError("8–10 distinct query variations are required")
        return [require_safe_text(value) for value in values]

    @model_validator(mode="after")
    def valid_fallback(self) -> "ApiResponse":
        if self.response.contexts and self.fallback is not None:
            raise ValueError("matched plans must not have a fallback")
        if not self.response.contexts and self.fallback not in {"no_match", "no_siis_context"}:
            raise ValueError("empty contexts require explicit fallback metadata")
        return self


class TroubleshootRequest(ContractModel):
    query: StrictStr = Field(min_length=3, max_length=2000)
    siis_response: Optional[StrictStr] = Field(default=None, max_length=50000)

    @field_validator("query")
    @classmethod
    def valid_query(cls, value: str) -> str:
        return require_safe_text(value)

    @field_validator("siis_response")
    @classmethod
    def valid_siis(cls, value: str | None) -> str | None:
        return require_safe_text(value) if value else value
