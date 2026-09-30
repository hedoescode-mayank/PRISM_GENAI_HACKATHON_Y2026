"""Persistent validated semantic cache with deterministic query vectors and source guards."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .data import CatalogEntry
from .enrichment import intent_signature
from .schema import ContextDeepLinkResponse
from .validation import PlanValidationError, validate_plan


VECTOR_DIM = 128


def catalog_fingerprint(catalog: dict[str, CatalogEntry]) -> str:
    data = [(uri, entry.metadata) for uri, entry in sorted(catalog.items())]
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def source_fingerprint(source: str | None) -> str:
    return hashlib.sha256((source or "").encode()).hexdigest()


def _vector(text: str) -> list[float]:
    """Deterministic dense lexical-semantic representation for cache lookup.

    This is intentionally local and dependency-free. Tokens, token bigrams and
    character trigrams are hashed into a fixed dense vector, with the same
    synonym normalization used by query enrichment.
    """
    from .retrieval import _hashed_dense

    return _hashed_dense(text, VECTOR_DIM)


def _similarity(a: list[float], b: list[float]) -> float:
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b))))


class SemanticCache:
    def __init__(self, path: Path, catalog: dict[str, CatalogEntry], threshold: float = 0.78):
        if not 0 < threshold <= 1:
            raise ValueError("cache similarity threshold must be in (0, 1]")
        self.path = path
        self.catalog = catalog
        self.threshold = threshold
        self.catalog_hash = catalog_fingerprint(catalog)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS plans (
                query TEXT NOT NULL,
                intent TEXT NOT NULL,
                source_hash TEXT NOT NULL,
                signature TEXT NOT NULL,
                vector TEXT NOT NULL DEFAULT '[]',
                catalog_hash TEXT NOT NULL,
                plan TEXT NOT NULL,
                PRIMARY KEY(query, intent, source_hash, catalog_hash)
            )""")
            columns = {row[1] for row in db.execute("PRAGMA table_info(plans)").fetchall()}
            if "vector" not in columns:
                db.execute("ALTER TABLE plans ADD COLUMN vector TEXT NOT NULL DEFAULT '[]'")
            db.execute("CREATE INDEX IF NOT EXISTS plans_guard ON plans(intent, source_hash, catalog_hash)")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()

    def put(self, query: str, intent: str, source: str | None, plan: ContextDeepLinkResponse) -> None:
        validate_plan(plan, self.catalog)
        signature = sorted(intent_signature(query))
        vector = _vector(query)
        with self._connect() as db:
            db.execute(
                "REPLACE INTO plans(query,intent,source_hash,signature,vector,catalog_hash,plan) VALUES(?,?,?,?,?,?,?)",
                (
                    query.casefold().strip(), intent, source_fingerprint(source),
                    json.dumps(signature), json.dumps(vector, separators=(",", ":")),
                    self.catalog_hash, plan.model_dump_json(),
                ),
            )

    def get(self, query: str, intent: str, source: str | None,
            *, classified_reference: bool = False) -> tuple[ContextDeepLinkResponse, str] | None:
        query_key = query.casefold().strip()
        source_hash = source_fingerprint(source)
        with self._connect() as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(plans)").fetchall()}
            vector_column = "vector" if "vector" in columns else "NULL"
            rows = db.execute(
                f"SELECT query,signature,{vector_column},plan FROM plans WHERE intent=? AND source_hash=? AND catalog_hash=? ORDER BY query",
                (intent, source_hash, self.catalog_hash),
            ).fetchall()
        target_vector = _vector(query)
        ranked: list[tuple[int, float, str, str]] = []
        for cached_query, signature_json, vector_json, plan_json in rows:
            if cached_query == query_key:
                ranked.append((0, 1.0, cached_query, plan_json))
                continue
            try:
                cached_vector = json.loads(vector_json) if vector_json else []
            except (TypeError, json.JSONDecodeError):
                cached_vector = []
            similarity = _similarity(target_vector, cached_vector) if cached_vector else 0.0
            # Token overlap is a safety backstop against accidental hash/vector
            # collisions, while allowing genuine paraphrases to hit.
            try:
                signature = set(json.loads(signature_json))
            except (TypeError, json.JSONDecodeError):
                signature = set()
            target_signature = set(intent_signature(query))
            overlap = len(target_signature & signature) / max(1, len(target_signature | signature))
            if similarity >= self.threshold and overlap >= 0.22:
                ranked.append((1, similarity, cached_query, plan_json))
            elif classified_reference and (similarity >= max(0.40, self.threshold - 0.25) or overlap >= 0.18):
                ranked.append((2, similarity, cached_query, plan_json))
        for kind, _, cached_query, plan_json in sorted(ranked, key=lambda row: (row[0], -row[1], row[2])):
            try:
                plan = ContextDeepLinkResponse.model_validate_json(plan_json)
                validate_plan(plan, self.catalog)
                return plan, ("exact", "semantic", "classified")[kind]
            except (ValueError, PlanValidationError):
                with self._connect() as db:
                    db.execute(
                        "DELETE FROM plans WHERE query=? AND intent=? AND source_hash=? AND catalog_hash=?",
                        (cached_query, intent, source_hash, self.catalog_hash),
                    )
        return None
