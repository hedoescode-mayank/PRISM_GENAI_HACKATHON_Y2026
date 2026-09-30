"""Hybrid metadata retrieval with BM25, dense local embeddings, and exact-screen gating."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Iterable

from .data import CatalogEntry
from .enrichment import TOKEN, SYNONYMS
from .schema import Deeplink


PLACEHOLDER = "bixby://dummy_positive"
PDF_KNOWN_UNINDEXED = {"navigation bar"}
SIIS_KNOWN_UNINDEXED = {
    "accounts and backup",
    "apps",
    "connections",
    "display",
    "factory data reset",
    "navigation bar",
    "security and privacy",
    "screen lock and biometrics",
    "storage",
}


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _normalized_tokens(text: str) -> tuple[str, ...]:
    values = []
    for token in TOKEN.findall(text.casefold()):
        values.append(SYNONYMS.get(token, token))
    return tuple(values)


def _trigrams(text: str) -> set[str]:
    text = f"  {_norm(text)}  "
    return {text[i:i + 3] for i in range(len(text) - 2)}


def _cosine_sets(left: set[str], right: set[str]) -> float:
    return len(left & right) / math.sqrt(len(left) * len(right)) if left and right else 0.0


def _exact_screen(entry: CatalogEntry, target: str) -> bool:
    target = _norm(target)
    if entry.screen:
        return _norm(entry.screen) == target
    description = _norm(entry.link.description)
    message = _norm(entry.link.message or "")
    screen = re.match(
        r"^(?:open|opens|launch|launches) (?:the )?(.+?) settings(?: page| screen)?(?: in| on|$)",
        description,
    )
    described = _norm(screen.group(1)) if screen else None
    return described == target or bool(re.fullmatch(rf"view {re.escape(target)}", message))


def placeholder_link(target: str) -> Deeplink | None:
    """Canonical placeholder metadata for a vetted, unindexed Settings screen."""
    name = _norm(target)
    if name not in SIIS_KNOWN_UNINDEXED:
        return None
    count = len(name.split())
    if count <= 3:
        description = f"Open {name} in device Settings"
        message = f"Show {name} in device Settings"
    else:
        description = f"Open {name} Settings"
        message = f"Show {name} Settings"
    for value in (description, message):
        if not 5 <= len(value.split()) <= 7:
            return None
    return Deeplink(deeplink=PLACEHOLDER, description=description, message=message)


class _BM25:
    """Small in-process BM25 index for the 577-entry catalog / 20-entry SIIS set."""

    def __init__(self, documents: list[str]) -> None:
        self.documents = documents
        self.tokens = [list(_normalized_tokens(doc)) for doc in documents]
        self.doc_len = [len(doc) for doc in self.tokens]
        self.avgdl = sum(self.doc_len) / len(self.doc_len) if self.doc_len else 1.0
        df: dict[str, int] = {}
        for doc in self.tokens:
            for token in set(doc):
                df[token] = df.get(token, 0) + 1
        n = len(self.tokens)
        self.idf = {
            token: math.log(1.0 + (n - freq + 0.5) / (freq + 0.5))
            for token, freq in df.items()
        }

    def scores(self, query: str, *, k1: float = 1.2, b: float = 0.75) -> list[float]:
        query_tokens = _normalized_tokens(query)
        if not query_tokens:
            return [0.0 for _ in self.tokens]
        result: list[float] = []
        for doc_tokens, dl in zip(self.tokens, self.doc_len):
            tf: dict[str, int] = {}
            for token in doc_tokens:
                tf[token] = tf.get(token, 0) + 1
            score = 0.0
            for token in set(query_tokens):
                if token not in tf or token not in self.idf:
                    continue
                freq = tf[token]
                denom = freq + k1 * (1.0 - b + b * dl / self.avgdl)
                score += self.idf[token] * (freq * (k1 + 1.0)) / denom
            result.append(score)
        return result


def _dense_vectors(documents: list[str]) -> tuple[object | None, object | None, list[list[float]]]:
    """Return a local dense embedding model and normalized document vectors.

    The preferred path is TF-IDF -> TruncatedSVD, which gives a dense local
    semantic-ish representation without a network model. A deterministic
    hashed vector fallback keeps the service functional when sklearn is absent.
    """
    try:
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(documents)
        if matrix.shape[0] >= 3 and matrix.shape[1] >= 3:
            components = min(64, matrix.shape[0] - 1, matrix.shape[1] - 1)
            if components >= 2:
                reducer = TruncatedSVD(n_components=components, random_state=0)
                dense = reducer.fit_transform(matrix)
            else:
                reducer = None
                dense = matrix.toarray()
        else:
            reducer = None
            dense = matrix.toarray()
        dense = normalize(dense, norm="l2", axis=1).tolist()
        return vectorizer, reducer, dense
    except Exception:
        return None, None, [_hashed_dense(doc) for doc in documents]


def _hashed_dense(text: str, dimensions: int = 128) -> list[float]:
    import hashlib

    vector = [0.0] * dimensions
    tokens = _normalized_tokens(text)
    features = list(tokens) + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])] + list(_trigrams(text))
    for feature in features:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def _query_dense(text: str, vectorizer: object | None, reducer: object | None,
                 fallback_documents: list[str]) -> list[float]:
    if vectorizer is None:
        return _hashed_dense(text)
    try:
        from sklearn.preprocessing import normalize

        matrix = vectorizer.transform([text])
        if reducer is not None:
            matrix = reducer.transform(matrix)
        return normalize(matrix, norm="l2", axis=1)[0].tolist()
    except Exception:
        return _hashed_dense(text)


def _cosine_vector(left: Iterable[float], right: Iterable[float]) -> float:
    score = sum(a * b for a, b in zip(left, right))
    return max(-1.0, min(1.0, score))


@dataclass(frozen=True)
class Candidate:
    uri: str
    lexical: float
    semantic: float
    exact: bool
    entry: CatalogEntry
    bm25: float = 0.0

    @property
    def score(self) -> float:
        # BM25 provides high-precision keyword evidence; the dense score helps
        # paraphrases without allowing a fuzzy parent-screen match to win the
        # exact-screen gate.
        dense = (self.semantic + 1.0) / 2.0
        lexical = self.bm25
        return 0.55 * lexical + 0.45 * dense


@dataclass(frozen=True)
class Resolution:
    link: Deeplink
    source: str
    score: float


class Retriever:
    def __init__(self, catalog: dict[str, CatalogEntry]):
        self.catalog = catalog
        self._uris = list(catalog)
        self._documents = [catalog[uri].metadata for uri in self._uris]
        self._bm25 = _BM25(self._documents)
        self._vectorizer, self._reducer, self._dense = _dense_vectors(self._documents)

    def _candidate_scores(self, target: str) -> list[Candidate]:
        bm25_raw = self._bm25.scores(target)
        bm25_max = max(bm25_raw) if bm25_raw else 0.0
        query_vector = _query_dense(target, self._vectorizer, self._reducer, self._documents)
        result = []
        for index, uri in enumerate(self._uris):
            entry = self.catalog[uri]
            lexical = len(set(_normalized_tokens(target)) & set(self._bm25.tokens[index])) / max(1, len(set(_normalized_tokens(target))))
            dense = _cosine_vector(query_vector, self._dense[index])
            bm25 = bm25_raw[index] / bm25_max if bm25_max else 0.0
            exact = _exact_screen(entry, target)
            result.append(Candidate(uri, lexical, dense, exact, entry, bm25))
        return result

    def candidates(self, target: str, limit: int = 10) -> list[Candidate]:
        result = [candidate for candidate in self._candidate_scores(target)
                  if candidate.lexical > 0 or candidate.bm25 > 0 or candidate.semantic >= 0.2]
        result.sort(key=lambda c: (-int(c.exact), -c.score, c.uri))
        return result[:limit]

    def resolve(self, target: str, *, allow_pdf_placeholder: bool = False,
                allow_source_placeholder: bool = False) -> Resolution | None:
        for candidate in self.candidates(target):
            if candidate.exact:
                return Resolution(candidate.entry.link, "catalog", candidate.score)
        if allow_source_placeholder:
            fallback = placeholder_link(target)
            if fallback:
                return Resolution(fallback, "source_screen_placeholder", 1.0)
        if allow_pdf_placeholder and _norm(target) in PDF_KNOWN_UNINDEXED:
            return Resolution(
                Deeplink(
                    deeplink=PLACEHOLDER,
                    description="Open navigation bar settings under Display",
                    message="Choose navigation type in Display settings",
                ),
                "pdf_reserved_placeholder",
                1.0,
            )
        return None


class SourceRetriever:
    """Hybrid retrieval over supplied SIIS complaint/title records.

    This never changes the evidence text. It only selects a source candidate;
    downstream extraction and relevance gates still decide whether any action
    may be returned.
    """

    def __init__(self, records: dict[str, str]):
        self._queries = list(records.keys())
        self._sources = [records[key] for key in self._queries]
        self._bm25 = _BM25(self._queries)
        self._vectorizer, self._reducer, self._dense = _dense_vectors(self._queries)

    def resolve(self, query: str, threshold: float = 0.42) -> str | None:
        bm25_raw = self._bm25.scores(query)
        max_bm25 = max(bm25_raw) if bm25_raw else 0.0
        if max_bm25 < 5.0:
            return None
        query_vector = _query_dense(query, self._vectorizer, self._reducer, self._queries)
        query_tokens = set(_normalized_tokens(query))
        ranked: list[tuple[float, int]] = []
        for i, score in enumerate(bm25_raw):
            bm25 = score / max_bm25 if max_bm25 else 0.0
            dense = (_cosine_vector(query_vector, self._dense[i]) + 1.0) / 2.0
            target_tokens = set(_normalized_tokens(self._queries[i]))
            overlap = len(query_tokens & target_tokens) / max(1, len(query_tokens | target_tokens))
            hybrid = 0.50 * bm25 + 0.30 * dense + 0.20 * overlap
            ranked.append((hybrid, i))
        ranked.sort(reverse=True)
        if not ranked:
            return None
        best_score, best_index = ranked[0]
        if best_score < threshold:
            return None
        target_tokens = set(_normalized_tokens(self._queries[best_index]))
        overlap = len(query_tokens & target_tokens) / max(1, len(query_tokens | target_tokens))
        if overlap < 0.15:
            return None
        return self._sources[best_index]

