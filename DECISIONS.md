# Decisions

## D1 — Theme 02 kit fixes the machine-readable contract

The later, directly supplied Theme 02 kit provides `schema.py`, `sample_output.json`, 20 SIIS response rows, and a catalog. Its exact lowercase link field names govern serialization. The nine-page PDF governs task behavior and validation rules; its Appendix B provides a separate reference plan. The spec pack's statement that the PDF has two pages is wrong. Research suggestions such as `title <=7 words` and `maintenance mode` ↔ `safe mode` are not adopted.

## D2 — Load the later supplied assets verbatim

The initial ZIPs lacked the named assets; `Theme02_Input_Kit.zip` supplied the catalog, SIIS responses, query lines, standalone schema, and one sample output. Its 578 catalog records include 577 actionable entries and the reserved `DL-DUMMY` placeholder. The 20 SIIS rows pair `original_query` with `siis_response: {title, content}`. The service loads those files and emits `no_match` when it has no source-backed plan. No guessed Bixby URI, activity, or step is permitted.

## D3 — Dependency-light local service

Use Python, Pydantic for the PDF model, and the standard-library HTTP server. This avoids a paid LLM or external database for local testing. Extraction is behind a provider interface for later integration.

## D4 — Reserved Settings fallback

The catalog's `DL-DUMMY` record explicitly allows `bixby://dummy_positive` for a concrete Settings screen that lacks a dedicated catalog entry. It is excluded from ordinary catalog matching and can be emitted only after such a miss, with a 5–7-word description and message that name the screen.

## D5 — Exact target over semantic similarity

Metadata retrieval proposes candidates; exact target evidence is required before a link is emitted. Parent screen similarity cannot satisfy a child-screen request.
