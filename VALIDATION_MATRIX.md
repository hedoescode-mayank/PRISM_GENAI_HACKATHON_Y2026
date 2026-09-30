# Validation matrix

This matrix maps the Theme 02 requirements to executable checks and the remaining limits. Run `./scripts/test`, `./scripts/doctor`, and `./scripts/benchmark` for current results.

| Requirement | Implemented check | Limit |
|---|---|---|
| Exact kit response field names | Pydantic models and response validation use `deeplink`, `actionableDeeplink`, and `validationDeeplink`; schema tests exercise serialization. | The PDF printed a conflicting spelling; the supplied standalone `schema.py` governs field casing. |
| Catalog integrity | Doctor indexes 577 actionable Bixby URIs from 578 source records; the reserved placeholder is excluded. Ingestion rejects malformed and duplicate actionable URIs. | A structurally valid catalog entry is not proof that a device can execute it. |
| SIIS evidence | Doctor loads 20 source records; extraction uses matched or explicitly supplied SIIS text. | SIIS content may be broad or mismatched to a complaint; unsupported targets yield no match. |
| Safe deep links | Plan validator accepts exact catalog URIs and the reserved placeholder for a vetted concrete Settings screen in a literal SIIS path, or the PDF Navigation bar reference, after exact catalog lookup fails. Placeholder metadata must name the screen in 5–7 words. | Live Samsung/Bixby invocation is outside this local test; catalog or placeholder presence does not prove device viability. |
| One physical screen per action | Metadata lexical and character n-gram ranking proposes candidates; extraction/retrieval tests verify an exact-screen gate and reject parent-screen substitutions. | No BM25 or dense embedding retrieval is implemented; some SIIS prose lacks a clear settings path. |
| Category ordering | Ordering tests verify safe actions precede critical actions and detect invalid dependencies. | Device state is unknown without a state provider. |
| 8–10 query variations | Model validation and enrichment tests require distinct, safe variations. | Variations are phrasing aids, not fresh evidence. |
| Multiple intents | Splitter tests cover some independent symptoms; extraction can use multiple explicit SIIS Settings paths. | Broad multi-intent diagnosis and merging are incomplete. |
| No web or Markdown links in returned plans | Schema and plan validation reject embedded web links. | Source text may contain web links but is never returned verbatim as a step. |
| No unsupported action | Pipeline returns empty `contexts` with an explicit fallback. | Coverage is bounded by the 20 supplied examples and retrievable targets. |
| Cache validity | Cache tests exercise source/catalog fingerprint guards and revalidate cached plans. | SQLite is local; cross-host cache sharing is not implemented. |
| Semantic paraphrase hit target | Cache tests cover exact, semantic, and false-hit guards. | The hit-rate target is not measured on a held-out paraphrase set. |
| API contract | Integration tests cover health, success, bad JSON/media type/input, and JSON serialization. | Authentication and deployment hardening are not part of this demo. |
| Plan score | Schema requires a numeric value from 0 to 1; curated and SIIS plans provide one. | Scores are heuristic and uncalibrated, not diagnostic probabilities. |
| Latency | `./scripts/benchmark` measures at least 30 cold and 30 cached requests for both the in-process pipeline and localhost HTTP; report records p50, p95, and p99. | Excludes process/server startup, network distance, device execution, and any future model call. |
| Supplied complaint sweep | `./scripts/evaluate-kit` separately runs all 20 `theme02_input.txt` lines and the 20 paired SIIS JSON queries, checks mapping gaps, and validates every matched response against the preserved kit schema. | Automatic matching is not a relevance judgment; inspect each returned action manually. |

The local benchmark is a reproducible engineering measurement, not a claim of overall contest performance. In particular, a low latency for a `no_match` response does not demonstrate useful troubleshooting coverage.
