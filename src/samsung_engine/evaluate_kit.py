"""Run every supplied Theme 02 complaint through the production pipeline."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import tempfile
from pathlib import Path

from .pipeline import TroubleshootingEngine
from .schema import ApiResponse


SUPPLIED_SCHEMA = Path(__file__).resolve().parents[2] / "source" / "theme02" / "schema.py"


def _source_response_model():
    spec = importlib.util.spec_from_file_location("theme02_supplied_schema", SUPPLIED_SCHEMA)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load supplied schema: {SUPPLIED_SCHEMA}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ContextDeeplinkResponse


def _normalized_query(query: str) -> str:
    return " ".join(re.sub(r"^\s*\d+[.)]\s*", "", query).split()).casefold()


def _run_cases(engine: TroubleshootingEngine, entries: list[dict], source_response_model) -> dict:
    cases = []
    for index, entry in enumerate(entries, 1):
        query = entry["query"]
        case = {"index": index, **entry}
        try:
            result = engine.troubleshoot({"query": query})
            ApiResponse.model_validate(result.model_dump())
            actions = [action for goal in result.response.contexts for action in goal.actions]
            if actions:
                source_response_model.model_validate(result.response.model_dump())
            case.update({
                "status": "matched" if actions else "no_match",
                "goals": len(result.response.contexts),
                "actions": len(actions),
                "cache_hit": result.meta.cache_hit,
                "supplied_schema_valid": True if actions else None,
            })
        except Exception as exc:
            case.update({"status": "validation_failure", "error": f"{type(exc).__name__}: {exc}"})
        cases.append(case)
    return {
        "input_cases": len(entries),
        "matched": sum(case["status"] == "matched" for case in cases),
        "no_match": sum(case["status"] == "no_match" for case in cases),
        "validation_failures": sum(case["status"] == "validation_failure" for case in cases),
        "cases": cases,
    }


def evaluate(data_dir: Path) -> dict:
    source = json.loads((data_dir / "siis_responses.json").read_text(encoding="utf-8"))
    rows = source["responses"] if isinstance(source, dict) else source
    input_lines = [line.strip() for line in (data_dir / "theme02_input.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    row_by_query = {_normalized_query(row["original_query"]): row for row in rows}
    input_entries = [
        {"query": line, "mapped_siis_id": row_by_query.get(_normalized_query(line), {}).get("id")}
        for line in input_lines
    ]
    mapping_gaps = [
        {"line": index, "query": entry["query"]}
        for index, entry in enumerate(input_entries, 1) if entry["mapped_siis_id"] is None
    ]
    input_keys = {_normalized_query(line) for line in input_lines}
    unrepresented_siis_ids = [row.get("id") for row in rows if _normalized_query(row["original_query"]) not in input_keys]
    source_response_model = _source_response_model()
    with tempfile.TemporaryDirectory(prefix="samsung-evaluate-") as temporary:
        input_engine = TroubleshootingEngine(data_dir, Path(temporary) / "input-cache.sqlite3")
        input_result = _run_cases(input_engine, input_entries, source_response_model)
        json_engine = TroubleshootingEngine(data_dir, Path(temporary) / "siis-cache.sqlite3")
        json_result = _run_cases(
            json_engine,
            [{"id": row.get("id", f"row_{index}"), "query": row["original_query"]} for index, row in enumerate(rows, 1)],
            source_response_model,
        )
    return {
        "method": "in_process_api_pipeline_with_supplied_siis_lookup",
        "supplied_schema": str(SUPPLIED_SCHEMA),
        "input_file": "theme02_input.txt",
        **input_result,
        "mapping_gap_count": len(mapping_gaps),
        "mapping_gaps": mapping_gaps,
        "unrepresented_siis_ids": unrepresented_siis_ids,
        "siis_json": json_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, help="write the JSON report to a file")
    args = parser.parse_args()
    report = evaluate(args.data_dir)
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    raise SystemExit(1 if report["validation_failures"] or report["siis_json"]["validation_failures"] or report["mapping_gap_count"] else 0)


if __name__ == "__main__":
    main()
