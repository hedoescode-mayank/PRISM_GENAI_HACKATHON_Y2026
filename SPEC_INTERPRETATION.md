# Specification interpretation

## Evidence and precedence

1. **[THEME 02 INPUT KIT]** The later, directly supplied `Theme02_Input_Kit.zip` is the authoritative machine-readable source for Theme 02. Its exact `schema.py` and `sample_output.json` are preserved in `source/theme02/`; the 578-entry catalog, 20 paired SIIS records, and query input are preserved under `data/`. The embedded Theme 02 ZIP in `participant-kit-all-themes.zip` is byte-identical to the direct ZIP (SHA-256 `799ba9c16221b3761ee7648cf6b6c083aafcb4f358685884f322b290e064a1f5`). The other files in that outer archive describe a separate theme and do not govern this service.
2. **[PDF]** `source/Theme 2_Troubleshooting_Smart Guided Troubleshooting Engine.pdf`, all nine image-only pages, describes task behavior and metrics. Pages 1–4 define behavior; page 5 prints a schema; page 6 gives one worked response; pages 7–9 contain a metrics template. The directly supplied standalone schema settles exact JSON field spelling where the PDF transcription or earlier implementation differs.
3. **[RESEARCH]** `source/research.txt` offers implementation ideas and unverified Samsung claims. It does not override the input kit or PDF.
4. **[PACK]** The supplied Codex spec pack is planning guidance and documentation templates. It incorrectly calls the PDF two pages; the actual PDF has nine.

## Contract extracted from the PDF

| Area | Requirement | Source |
|---|---|---|
| Objective | Transform colloquial Galaxy complaints and optional SIIS text into validated, screen-specific troubleshooting plans | p. 1 |
| Pipeline | Enrich query; extract goal/actions/steps; map exact screens and order; cache validated plans; serve REST API | pp. 1–2 |
| Inputs | `query` and optional `siis_response`; the later kit supplies 20 paired SIIS records, 20 query lines, and a 578-entry catalog | pp. 2–3; input kit |
| Inner model | `ContextDeepLinkResponse.contexts` contains `Goal` objects with `goal`, `title`, `actions`, `score`; actions contain `actionName`, `description`, `stepGroups`, `category`; step groups contain `steps`, optional validation and actionable deep links | p. 5 |
| Wording | Goal begins `Follow these steps to perform this <Topic> Troubleshooting` or `Configuration`; title is 2–3 words, sentence case; description is 5–7 words beginning `It will`; score is 0–1 | p. 2 |
| Action granularity | One action is one physical screen or feature; one physical interaction per step | pp. 2–3 |
| Categories | `auto` settings actions use catalog-backed links; `critical` disruptive actions go last; `manual` physical interventions have no actionable link | p. 2 |
| Links | Catalog URIs are authoritative and must not be altered or invented; use metadata, never masked URI text, for matching | pp. 2–3; input kit |
| Placeholder | The catalog's `DL-DUMMY` record reserves `bixby://dummy_positive` for a concrete Settings screen with no dedicated catalog entry; it is excluded from ordinary catalog retrieval | p. 2; input kit |
| Variations | Produce 8–10 distinct paraphrases in varied registers | pp. 1–2 |
| Leakage | No web URLs, `www.`, or Markdown links in the returned plan | pp. 2–3 |
| No source-backed steps | Return `contexts: []` with `fallback: "no_match"` | p. 3 |
| API | `POST /v1/troubleshoot`, `GET /health`; return JSON plus latency, cache-hit, and cost metadata | p. 3, p. 6 |
| Performance | Cached p95 <=300 ms; cold p95 <=8 s; semantic paraphrase hit target >=80%, each measured with >=30 requests | pp. 3, 8 |

## Ambiguities and safe resolution

| Area | Ambiguity | Decision |
|---|---|---|
| Later starter data | The initial uploads omitted assets; the later Theme 02 kit provides them | Load the supplied 577 real links plus 20 SIIS records and keep unsupported cases as explicit no-match. Do not fabricate Samsung URIs or SIIS knowledge. |
| Outer API shape | Page 5 defines only the nested response model; page 6 shows the outer `query`, `query_variations`, `response`, `meta` envelope | Preserve the page 6 envelope and add `fallback` only when empty per page 3. |
| `dummy_positive` | The PDF example uses it for Navigation bar; the kit includes a generic `DL-DUMMY` entry | Allow it for a concrete Settings screen after a dedicated-entry miss, following the kit's 5–7-word description/message rule. |
| Schema strictness | Printed Pydantic classes have defaults and permit extra keys by default | Keep field names/types, reject extra keys and invalid rule values at API boundary to satisfy strict conformance. |
| State | `ValidationDeepLink` exists, but no state provider or live device is supplied | Preserve validation link fields; support unknown/mock state; never claim a live observation. |
| Research claims | Research proposes `maintenance mode` as a synonym for `safe mode`, which is unestablished and potentially wrong | Do not encode that equivalence. |

## Delivery boundary

This repository implements the service and locally testable pipeline using the supplied kit. A successful no-match response is an honest contract result when source evidence cannot support a step.

## Input kit shape and discrepancies

- `deeplinks.json`: `{_readme, count: 578, deeplinks: [...]}`. Each item has `id`, lowercase `deeplink`, `description`, `message`, `originalType`, `control_type`, `qna_description`, and optional nested `validation`. The 578 records include one reserved `DL-DUMMY` placeholder and 577 distinct real action URIs. `control_type` is an integer or null. Nested validation URIs are separate from action URIs.
- `siis_responses.json`: `{_readme, count: 20, responses: [...]}`. Each row has `id`, `original_query`, and `siis_response: {title, content}`. The content is the supplied source for steps. It sometimes contains unrelated article fragments, so plans must stay relevant to the complaint.
- `input.txt` has 20 complaint lines. The kit supplies no `queries.json` or `samples/` directory; it supplies one `sample_output.json` instead.
- The standalone schema uses lowercase `deeplink` and `actionableDeeplink`/`validationDeeplink`. The supplied sample is a format example, not reliable golden content: its backup description has nine words, violating the PDF's 5–7-word rule; its service step mentions peeling film and green display lines absent from the sample's cracked/flashing-screen query. The sample also omits the PDF's outer `query_variations` and `meta` fields.
