"""Local setup and data diagnostics."""

from __future__ import annotations

import json
import os
import platform
import sys
from pathlib import Path

import pydantic

from .data import DataError, load_data


def diagnose(data_dir: Path, cache_path: Path) -> dict:
    output: dict = {
        "python": platform.python_version(),
        "pydantic": pydantic.__version__,
        "data_dir": str(data_dir),
        "cache_path": str(cache_path),
        "issues": [],
    }
    if sys.version_info < (3, 10):
        output["issues"].append("Python 3.10 or newer is required")
    try:
        store = load_data(data_dir)
        output["catalog_entries"] = len(store.catalog)
        output["reference_cases"] = len(store.references)
        output["siis_entries"] = len(store.siis)
        output["warnings"] = store.warnings
    except DataError as exc:
        output["issues"].append(str(exc))
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        probe = cache_path.parent / ".doctor-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        output["issues"].append(f"cache directory is not writable: {exc}")
    output["status"] = "error" if output["issues"] else "ready_with_data_gap" if output.get("warnings") else "ready"
    return output


def main() -> None:
    result = diagnose(Path(os.environ.get("SAMSUNG_DATA_DIR", "data")), Path(os.environ.get("SAMSUNG_CACHE_PATH", ".cache/plans.sqlite3")))
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["status"] == "error" else 0)


if __name__ == "__main__":
    main()
