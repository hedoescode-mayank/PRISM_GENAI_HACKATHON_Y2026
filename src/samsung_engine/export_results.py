"""Export one validated API response per supplied Theme 02 input line."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from .evaluate_kit import _source_response_model
from .pipeline import TroubleshootingEngine
from .schema import ApiResponse


def export(data_dir: Path, output: Path) -> dict:
    queries = [line.strip() for line in (data_dir / "theme02_input.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    supplied_model = _source_response_model()
    lines: list[str] = []
    matched = no_match = 0
    with tempfile.TemporaryDirectory(prefix="samsung-export-") as temporary:
        engine = TroubleshootingEngine(data_dir, Path(temporary) / "plans.sqlite3")
        for query in queries:
            response = engine.troubleshoot({"query": query})
            ApiResponse.model_validate(response.model_dump())
            if response.response.contexts:
                supplied_model.model_validate(response.response.model_dump())
                matched += 1
            else:
                no_match += 1
            lines.append(response.model_dump_json(exclude_none=True))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"output": str(output), "responses": len(lines), "matched": matched, "no_match": no_match}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output", type=Path, default=Path("examples/theme02_results.jsonl"))
    args = parser.parse_args()
    print(json.dumps(export(args.data_dir, args.output), indent=2))


if __name__ == "__main__":
    main()
