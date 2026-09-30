# Setup

## Requirements

- Python 3.10 or newer with `venv` and `pip`.
- Local access to the bundled `data/` inputs. No API key, GPU, external database, or network service is used at runtime.

## Install and verify

```bash
./scripts/bootstrap
./scripts/doctor
./scripts/test
./scripts/benchmark
./scripts/evaluate-kit
./scripts/export-results
```

`bootstrap` creates `.venv` and installs this package in editable mode. If dependency installation is unavailable but Pydantic 2 is already installed, the other scripts fall back to `PYTHONPATH=src python3`.

`doctor` reports Python and Pydantic versions, data counts, cache writability, and warnings. A `ready` status indicates files parsed successfully. It does not guarantee every complaint has a plan.

## Start the service

```bash
./scripts/run
```

Defaults: `127.0.0.1:8000`, `data/`, `.cache/plans.sqlite3`. Override with `SAMSUNG_HOST`, `SAMSUNG_PORT`, `SAMSUNG_DATA_DIR`, and `SAMSUNG_CACHE_PATH`. See `.env.example`; the shell scripts do not source `.env` automatically.

## Optional container

```bash
docker build -t samsung-theme02 .
docker run --rm -p 8000:8000 samsung-theme02
```

The image packages the Python service and Theme 02 data, binds port 8000 inside the container, and stores its SQLite cache in the container's temporary directory. A local smoke test returned `200` from `/health` and a `200` catalog-backed sample response. The container was stopped after verification.

## Inputs

`data/deeplinks.json` and `data/siis_responses.json` originate from `Theme02_Input_Kit.zip` and are treated as read-only evidence. Keep the original URI bytes and source wording. `data/reference_navigation.json` transcribes the PDF's Navigation bar example; `data/reference_sample.json` records the supplied damage sample. The kit's reserved placeholder is governed by the exact-screen and literal Settings-path checks described in [Domain knowledge](DOMAIN_KNOWLEDGE.md).

You can point `SAMSUNG_DATA_DIR` at another directory containing the same named JSON files. Run `./scripts/doctor` before starting the service to catch incompatible input shapes.

## Troubleshooting

| Symptom | Action |
|---|---|
| `Permission denied` on a script | Run `bash scripts/<name>` or restore execute permissions with `chmod +x scripts/*`. |
| `ModuleNotFoundError: pydantic` | Run `./scripts/bootstrap` in a network-enabled environment. |
| Doctor reports missing catalog/SIIS | Confirm `SAMSUNG_DATA_DIR` points to the extracted Theme 02 data files. |
| `/health` is degraded | Check doctor warnings, then restart after correcting the data. |
| `fallback: "no_match"` | Supply relevant SIIS text or inspect whether the source names an exact catalog target. This is a supported outcome. |

The benchmark creates and deletes only its own temporary SQLite cache. It never clears the service cache.
