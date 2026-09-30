# Domain knowledge and evidence boundary

## Source set

- `Theme02_Input_Kit.zip` supplies the authoritative response schema, 578 catalog records (577 actionable Bixby URIs and one reserved placeholder), 20 complaint examples, 20 SIIS response records, and one sample output.
- The Theme 02 PDF defines the overall guided troubleshooting task, ordering and safety constraints, an example Navigation bar plan, and latency targets.
- `data/reference_navigation.json` transcribes that PDF example. Its `bixby://dummy_positive` value is a reserved Settings-screen fallback also documented by the kit's `DL-DUMMY` catalog record.

The larger `participant-kit-all-themes.zip` includes a separate agent harness with audio, vision, tools, and scenario scoring. Its submission protocol is not the Theme 02 troubleshooting API contract.

## What the supplied complaints cover

The 20 sample complaints focus on black or blank screens, flicker, cracked or partially working displays, touch delay, a small display area, and a floating accessibility shortcut. Some mention Gmail, Smart Switch, and other apps as triggering context. A symptom can have several causes; the complaint alone does not establish which settings path or repair step is correct.

The SIIS record paired with a complaint is evidence to inspect, not proof that all its advice applies. For example, the first flashing/blank-screen complaint is paired with email-connection troubleshooting text. The engine must check that an extracted action addresses the complaint and maps to an exact catalog target before returning it. It should prefer an empty result to an unrelated email or settings plan.

## Deep-link policy

Catalog metadata (`description`, `message`, `qna_description`, validation metadata) describes a Bixby URI. The masked URI text itself has no semantic meaning. Matching a broad parent screen such as Display does not authorize a child-screen link. The engine copies exact catalog URI bytes into the output; it does not reconstruct or guess them.

Retrieval scores metadata with lexical overlap and character n-grams, then requires an exact screen target. No BM25 index or dense embedding model is implemented. These scores propose candidates; they do not establish device causality or link viability.

An `auto` action needs a supported actionable target. A `manual` action describes a physical intervention and carries no actionable link. Potentially disruptive `critical` actions come last. The response must not expose web URLs or Markdown links in its plan text.

The reserved placeholder is eligible after no exact catalog screen matches, for a concrete screen label vetted from the supplied SIIS material and named in a literal `Settings > ...` path, or for the PDF's Navigation bar reference. The action must have a step tapping that screen, and the generated placeholder description and message must each be 5–7 words naming it. An arbitrary target or parent-screen similarity cannot authorize the placeholder. It is still a placeholder and has no demonstrated on-device behavior.

## Device state and limits

The local service cannot observe a Galaxy device, confirm that a Samsung deep link launched, verify that a screen is currently accessible, or diagnose hardware damage. Validation deep links are carried as source metadata; they are not live measurements. Model, carrier, firmware, and region differences may affect real behavior. A technician or official support path remains appropriate when the source cannot safely resolve an issue.

Plan `score` values are heuristic and uncalibrated. The SIIS-derived default of `0.75` and the curated sample scores are not measured probabilities that a diagnosis or repair will succeed.

The query splitter handles selected independent symptoms, and the extractor can follow multiple explicit Settings paths in SIIS text. Broad multi-intent diagnosis and merging are incomplete. A held-out set has not been used to measure the PDF's semantic paraphrase cache-hit target.
