"""Repeatable, local latency measurements for the troubleshooting pipeline.

The timer surrounds ``troubleshoot`` only.  Data loading and engine startup are
excluded, and each cold sample deletes the benchmark cache before the call.
The cache lives in a temporary directory, so normal application data is safe.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
import tempfile
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from .api import make_handler
from .pipeline import TroubleshootingEngine


DEFAULT_QUERY = (
    "My Galaxy S24 Ultra screen is completely black and won't turn on, even though "
    "the phone powers on, rings, and otherwise works; there is no physical damage."
)


def _percentile(samples: list[float], percentile: float) -> float:
    ordered = sorted(samples)
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _summary(samples: list[float], hits: int, matches: int) -> dict[str, float | int]:
    return {
        "requests": len(samples),
        "cache_hits": hits,
        "matched_plans": matches,
        "min_ms": round(min(samples), 3),
        "mean_ms": round(statistics.mean(samples), 3),
        "p50_ms": round(_percentile(samples, 0.50), 3),
        "p95_ms": round(_percentile(samples, 0.95), 3),
        "p99_ms": round(_percentile(samples, 0.99), 3),
        "max_ms": round(max(samples), 3),
    }


def benchmark(data_dir: Path, query: str = DEFAULT_QUERY, iterations: int = 30) -> dict:
    if iterations < 30:
        raise ValueError("at least 30 requests per mode are required")
    with tempfile.TemporaryDirectory(prefix="samsung-benchmark-") as temporary:
        engine = TroubleshootingEngine(data_dir, Path(temporary) / "plans.sqlite3")
        request = {"query": query}
        cold: list[float] = []
        cached: list[float] = []
        cold_hits = cached_hits = cold_matches = cached_matches = 0
        for _ in range(iterations):
            # This removes even the PDF reference seed, making the next call a
            # true pipeline cache miss without including startup in the timer.
            with sqlite3.connect(engine.cache.path) as connection:
                connection.execute("DELETE FROM plans")
            started = time.perf_counter_ns()
            result = engine.troubleshoot(request)
            cold.append((time.perf_counter_ns() - started) / 1_000_000)
            cold_hits += int(result.meta.cache_hit)
            cold_matches += int(bool(result.response.contexts))

            started = time.perf_counter_ns()
            result = engine.troubleshoot(request)
            cached.append((time.perf_counter_ns() - started) / 1_000_000)
            cached_hits += int(result.meta.cache_hit)
            cached_matches += int(bool(result.response.contexts))

        cold_result = _summary(cold, cold_hits, cold_matches)
        cached_result = _summary(cached, cached_hits, cached_matches)
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(engine))
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        http_cold: list[float] = []
        http_cached: list[float] = []
        http_cold_hits = http_cached_hits = http_cold_matches = http_cached_matches = 0
        payload = json.dumps(request).encode("utf-8")

        def http_call() -> dict:
            call = urllib.request.Request(
                f"http://127.0.0.1:{server.server_port}/v1/troubleshoot",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(call, timeout=10) as response:
                return json.loads(response.read())

        try:
            for _ in range(iterations):
                with sqlite3.connect(engine.cache.path) as connection:
                    connection.execute("DELETE FROM plans")
                started = time.perf_counter_ns()
                result = http_call()
                http_cold.append((time.perf_counter_ns() - started) / 1_000_000)
                http_cold_hits += int(result["meta"]["cache_hit"])
                http_cold_matches += int(bool(result["response"]["contexts"]))

                started = time.perf_counter_ns()
                result = http_call()
                http_cached.append((time.perf_counter_ns() - started) / 1_000_000)
                http_cached_hits += int(result["meta"]["cache_hit"])
                http_cached_matches += int(bool(result["response"]["contexts"]))
        finally:
            server.shutdown()
            server.server_close()
            server_thread.join(timeout=2)

        http_cold_result = _summary(http_cold, http_cold_hits, http_cold_matches)
        http_cached_result = _summary(http_cached, http_cached_hits, http_cached_matches)
        return {
            "method": "in_process_pipeline_excluding_startup",
            "query": query,
            "catalog_entries": len(engine.data.catalog),
            "siis_entries": len(engine.data.siis),
            "cold": cold_result,
            "cached": cached_result,
            "targets": {
                "cold_p95_le_8000_ms": cold_result["p95_ms"] <= 8000 if cold_matches == iterations else None,
                "cached_p95_le_300_ms": cached_result["p95_ms"] <= 300 if cached_hits == iterations and cached_matches == iterations else None,
            },
            "http_loopback": {
                "method": "localhost_http_roundtrip_excluding_server_startup",
                "cold": http_cold_result,
                "cached": http_cached_result,
                "targets": {
                    "cold_p95_le_8000_ms": http_cold_result["p95_ms"] <= 8000 if http_cold_matches == iterations else None,
                    "cached_p95_le_300_ms": http_cached_result["p95_ms"] <= 300 if http_cached_hits == iterations and http_cached_matches == iterations else None,
                },
            },
            "warnings": engine.data.warnings,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--iterations", type=int, default=30)
    parser.add_argument("--output", type=Path, help="write the JSON report to a file")
    args = parser.parse_args()
    report = benchmark(args.data_dir, args.query, args.iterations)
    payload = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
