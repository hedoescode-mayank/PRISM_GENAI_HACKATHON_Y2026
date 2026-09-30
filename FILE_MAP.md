# File map

| Path | Purpose | Direction / coverage |
|---|---|---|
| `source/` | Original Theme 02 PDF, research note, and preserved kit schema/sample | Static evidence |
| `data/deeplinks.json` | Supplied 578-record catalog, including one reserved placeholder | Loader and exact-link tests |
| `data/siis_responses.json` | Supplied 20 complaint/SIIS pairs | Extraction and evaluation input |
| `data/reference_navigation.json` | PDF worked example, transcribed | Golden fixture and cache seed |
| `data/reference_sample.json` | Curated supplied damage sample | Catalog-backed action/validation fixture |
| `data/theme02_input.txt`, `data/theme02_sample_output.json` | Supplied query list and response example | Reference artifacts |
| `src/samsung_engine/schema.py` | Strict contract models using the kit's exact field casing | Imported by all core modules; schema tests |
| `src/samsung_engine/data.py` | Catalog and SIIS ingestion with integrity checks | Reads configured data; ingestion tests |
| `src/samsung_engine/enrichment.py` | Query normalization, intent signatures, paraphrases | Pure; enrichment tests |
| `src/samsung_engine/retrieval.py` | Metadata-based candidate ranking and exact-screen gate | Catalog dependent; retrieval tests |
| `src/samsung_engine/extraction.py` | Source-backed extraction provider boundary and local reference parser | Provider tests |
| `src/samsung_engine/ordering.py` | Dependency graph and category ordering | Pure; ordering tests |
| `src/samsung_engine/validation.py` | Whole-plan rule and link checks | Pure; contract tests |
| `src/samsung_engine/cache.py` | Validated semantic cache | Local persistence; cache tests |
| `src/samsung_engine/pipeline.py` | Orchestrates the service | Integration tests |
| `src/samsung_engine/api.py` | Standard-library JSON HTTP service | API tests |
| `src/samsung_engine/benchmark.py` | In-process and localhost HTTP latency percentiles | Benchmark script |
| `src/samsung_engine/evaluate_kit.py` | Sweep all supplied Theme 02 complaints and validate matched output against the original schema | Evaluation script |
| `src/samsung_engine/export_results.py` | Export all actual input-file complaints as validated API JSONL | Export script |
| `examples/` | Verified black-screen and cracked/flashing-screen HTTP request/response pairs, plus 20-line JSONL export | Demo artifacts |
| `Dockerfile`, `.dockerignore` | Optional containerized service and compact build context | Container smoke test |
| `benchmark-results.json`, `kit-evaluation-results.json` | Measured latency and 20-case coverage reports | Reproducible command output |
| `tests/` | Unit and end-to-end checks | `unittest` |
| `scripts/` | Bootstrap, doctor, run, test, benchmark, evaluate-kit, export-results | Executable entry points |
| Root `.md` files | Interpretation, setup, contract, progress, decisions, limitations | Static docs |

The Theme 02 starter assets are present in `data/`. The all-themes participant harness is a separate challenge protocol and is not used by this engine.
