# Samsung Smart Guided Troubleshooting Engine — Theme 02

Local, source-backed prototype for turning a Galaxy complaint into a structured troubleshooting plan. The response follows the **Theme02_Input_Kit** schema and uses the supplied SIIS text and Bixby deep-link catalog as evidence. A request with no supported action returns an explicit fallback.

## Run it

Requires Python 3.10 or newer. From this directory:

```bash
./scripts/bootstrap
./scripts/doctor
./scripts/test
./scripts/run
```

In another terminal:

```bash
curl -sS http://127.0.0.1:8000/health
curl -sS http://127.0.0.1:8000/v1/troubleshoot \
  -H 'Content-Type: application/json' \
  -d @examples/theme02_black_screen_request.json
```

The Theme 02 kit contains 578 catalog records (577 actionable URIs and one reserved placeholder) and 20 complaint/SIIS pairs. Run `./scripts/doctor` to confirm these were loaded. The PDF navigation example is a separate golden fixture for contract testing. The all-themes participant kit belongs to a different agent protocol and does not govern this service.

Optional container run:

```bash
docker build -t samsung-theme02 .
docker run --rm -p 8000:8000 samsung-theme02
```

Verified HTTP artifacts: [black-screen request](examples/theme02_black_screen_request.json) and [response](examples/theme02_black_screen_response.json); [cracked/flashing-screen request](examples/theme02_sample_damage_request.json) and [response](examples/theme02_sample_damage_response.json). The second response demonstrates a catalog-backed backup action with its paired validation deep link, followed by manual service.

## What the prototype does

1. Validates a complaint and optional `siis_response` text.
2. Generates nine query variations without using them as new evidence.
3. Finds the corresponding supplied SIIS content, or uses explicit request context.
4. Extracts supported actions, ranks catalog metadata with lexical and character n-gram scores, applies an exact-screen gate, orders actions, and validates the result.
5. Caches only valid, source-guarded plans in SQLite.

The service is deterministic and does not use a hosted model or network calls. Retrieval has no BM25 or dense embedding model. It does not claim a live device state or verify that Samsung deep links execute on a device. The catalog's masked Bixby URIs are copied as supplied. The reserved `bixby://dummy_positive` URI can be used for a vetted concrete Settings screen named in a literal SIIS path after exact catalog lookup fails, or for the PDF's Navigation bar reference when that screen is unindexed; its description and message name that screen in 5–7 words. Unsupported requests return `response.contexts: []` and `fallback: "no_match"`.

The splitter recognizes some independent symptoms and multiple explicit SIIS Settings paths. It does not provide comprehensive multi-intent diagnosis or merging. The semantic paraphrase cache-hit target has not been measured on a held-out query set.

## More information

- [Setup and troubleshooting](SETUP.md)
- [HTTP API](API.md)
- [Validation matrix](VALIDATION_MATRIX.md)
- [Domain knowledge and source boundaries](DOMAIN_KNOWLEDGE.md)
- [Measured progress](PROGRESS.md)

Run `./scripts/benchmark` for a local 30 cold / 30 cached request latency report using the supplied Galaxy S24 Ultra complaint. It reports both in-process pipeline timing and localhost HTTP round trips. Process and server startup are excluded.

Run `./scripts/evaluate-kit` to process all 20 lines of `theme02_input.txt` and the paired SIIS JSON queries separately. It reports matched plans, explicit no-matches, validation failures, and mapping gaps. A high match count alone does not establish that a plan is relevant to the user's symptom.

Run `./scripts/export-results` to regenerate [the 20-line JSONL response artifact](examples/theme02_results.jsonl) from the actual input file. Every line is a validated API response, including explicit no-match rows.

The latest [benchmark report](benchmark-results.json) and [20-case report](kit-evaluation-results.json) are included for review.
