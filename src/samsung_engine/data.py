"""Load only supplied or explicitly configured troubleshooting evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .schema import ContextDeepLinkResponse, Deeplink, ValidationDeepLink, require_safe_text


class DataError(ValueError):
    pass


@dataclass(frozen=True)
class CatalogEntry:
    link: Deeplink
    screen: str | None = None
    qna_description: str = ""
    control_type: int | str | None = None
    validation: ValidationDeepLink | None = None
    identifier: str | None = None

    @property
    def metadata(self) -> str:
        return " ".join(str(value) for value in (self.screen, self.link.description, self.link.message, self.qna_description, self.control_type, self.validation.key if self.validation else None) if value is not None and value != "")


@dataclass(frozen=True)
class ReferenceCase:
    intent: str
    canonical_query: str
    aliases: tuple[str, ...]
    target: str
    response: ContextDeepLinkResponse


@dataclass
class DataStore:
    catalog: dict[str, CatalogEntry] = field(default_factory=dict)
    references: list[ReferenceCase] = field(default_factory=list)
    siis: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DataError(f"cannot load {path}: {exc}") from exc


def load_catalog(path: Path) -> dict[str, CatalogEntry]:
    """Index the supplied catalog while preserving its authoritative URI bytes."""
    raw = _json_file(path)
    declared_count = raw.get("count") if isinstance(raw, dict) else None
    if isinstance(raw, dict):
        raw = raw.get("deeplinks", raw.get("deepLinks", raw.get("data")))
    if not isinstance(raw, list):
        raise DataError("deeplinks.json must contain a list or a deeplinks list")
    if declared_count is not None and (not isinstance(declared_count, int) or declared_count != len(raw)):
        raise DataError("catalog count does not match the supplied records")
    result: dict[str, CatalogEntry] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise DataError(f"catalog record {index} is not an object")
        uri = item.get("deeplink", item.get("deepLink"))
        if not isinstance(uri, str) or not uri.startswith("bixby://"):
            raise DataError(f"catalog record {index} has an invalid URI")
        if uri == "bixby://dummy_positive":
            # The supplied catalog documents the placeholder as a reserved
            # entry. It is never a retrievable actionable target.
            if item.get("originalType") != "placeholder":
                raise DataError("reserved placeholder must not be a catalog entry")
            continue
        if uri in result:
            raise DataError(f"duplicate catalog URI at record {index}")
        description = item.get("description")
        if not isinstance(description, str) or not description.strip():
            raise DataError(f"catalog record {index} has no description")
        message = item.get("message", "")
        screen = item.get("screen", item.get("targetScreen"))
        qna = item.get("qna_description", item.get("qnaDescription", ""))
        control = item.get("control_type", item.get("controlType"))
        identifier = item.get("id")
        for field_name, value in (("message", message), ("screen", screen), ("qna_description", qna), ("id", identifier)):
            if value is not None and not isinstance(value, str):
                raise DataError(f"catalog record {index} has non-string {field_name}")
            if value:
                require_safe_text(value)
        if control is not None and not isinstance(control, (str, int)):
            raise DataError(f"catalog record {index} has invalid control_type")
        try:
            link = Deeplink(
                deeplink=uri,
                description=description,
                message=message,
                classes=item.get("classes"),
                originalType=item.get("originalType"),
            )
            validation = item.get("validation")
            validation = ValidationDeepLink.model_validate(validation) if validation is not None else None
        except Exception as exc:
            raise DataError(f"catalog record {index} failed schema validation: {exc}") from exc
        result[uri] = CatalogEntry(link, screen, qna or "", control, validation, identifier)
    return result


def load_references(path: Path) -> list[ReferenceCase]:
    raw = _json_file(path)
    if isinstance(raw, dict):
        raw = [raw]
    if not isinstance(raw, list):
        raise DataError("reference data must be an object or list")
    result = []
    for index, item in enumerate(raw):
        try:
            result.append(ReferenceCase(
                intent=require_safe_text(item["intent"]),
                canonical_query=require_safe_text(item["canonical_query"]),
                aliases=tuple(require_safe_text(alias) for alias in item["aliases"]),
                target=require_safe_text(item["target"]),
                response=ContextDeepLinkResponse.model_validate(item["response"]),
            ))
        except Exception as exc:
            raise DataError(f"reference {index} failed validation: {exc}") from exc
    return result


def load_siis(path: Path) -> dict[str, str]:
    raw = _json_file(path)
    declared_count = raw.get("count") if isinstance(raw, dict) else None
    result: dict[str, str] = {}
    if isinstance(raw, dict):
        if isinstance(raw.get("responses"), list):
            raw = raw["responses"]
        else:
            raw = [{"query": key, "response": value} for key, value in raw.items()]
    if not isinstance(raw, list):
        raise DataError("SIIS data must be a list, mapping, or responses list")
    if declared_count is not None and (not isinstance(declared_count, int) or declared_count != len(raw)):
        raise DataError("SIIS count does not match the supplied records")
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise DataError(f"SIIS record {index} is not an object")
        query = item.get("original_query", item.get("query"))
        response = item.get("response", item.get("siis_response"))
        if isinstance(response, dict):
            title, content = response.get("title"), response.get("content")
            if not isinstance(title, str) or not title.strip() or not isinstance(content, str):
                raise DataError(f"SIIS record {index} requires title and content strings")
            response = content
        if not isinstance(query, str) or not isinstance(response, str):
            raise DataError(f"SIIS record {index} requires string query and response")
        query, response = require_safe_text(query), require_safe_text(response)
        if query.casefold() in result:
            raise DataError(f"duplicate SIIS query at record {index}")
        result[query.casefold()] = response
    return result


def load_data(data_dir: Path) -> DataStore:
    store = DataStore()
    reference = data_dir / "reference_navigation.json"
    if reference.exists():
        store.references = load_references(reference)
    else:
        store.warnings.append("PDF reference_navigation.json is missing")
    supplied_sample = data_dir / "reference_sample.json"
    if supplied_sample.exists():
        store.references.extend(load_references(supplied_sample))
    catalog = data_dir / "deeplinks.json"
    if catalog.exists():
        store.catalog = load_catalog(catalog)
    else:
        store.warnings.append("authoritative deeplinks.json is missing; broad link resolution unavailable")
    siis = data_dir / "siis_responses.json"
    if siis.exists():
        store.siis = load_siis(siis)
    else:
        store.warnings.append("siis_responses.json is missing; only supplied request context/reference cases are available")
    return store
