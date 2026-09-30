# Implementation plan

The Theme 02 PDF and later input kit define the contract. All seven local implementation phases below are complete.

1. **Specification and provenance:** audited both archives and all nine PDF pages; recorded source conflicts.
2. **Contract and ingestion:** implemented the supplied standalone schema with strict validation; loaded the catalog and SIIS assets; reject malformed or duplicate records.
3. **Enrichment and extraction:** normalized terms, split selected independent intents, generated 8–10 variations, and extracted source-backed actions. The PDF worked example and supplied sample are curated references.
4. **Retrieval and ordering:** rank by catalog metadata, require the exact physical screen, constrain the documented reserved fallback, and order safe actions before critical ones.
5. **Validation and cache:** check returned fields, URLs, links, categories, and order; cache only validated plans behind intent and source guards.
6. **API and operations:** implemented the PDF endpoints, setup/doctor scripts, tests, and measured benchmarks.
7. **Kit integration:** loaded the actual `schema.py`, `deeplinks.json`, SIIS data, queries, and sample; reconciled shapes and ran the 20-case sweep and golden tests.

The requested Theme 02 deliverable is the engine and REST API. Any UI or broader Samsung-specific heuristics are future extensions and require separate evidence and testing.
