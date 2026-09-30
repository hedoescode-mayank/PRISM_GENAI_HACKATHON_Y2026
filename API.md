# HTTP API

The local service accepts and returns JSON. Start it with `./scripts/run`.

## `GET /health`

Returns `200` with `status: "ok"` when the catalog and SIIS inputs are loaded, or `503` with `status: "degraded"` and warnings when either is missing. Fields include `catalog_entries`, `cache`, and `provider`. This is a readiness signal, not a coverage score.

## `POST /v1/troubleshoot`

```bash
curl -sS http://127.0.0.1:8000/v1/troubleshoot \
  -H 'Content-Type: application/json' \
  -d @examples/theme02_black_screen_request.json
```

For a catalog-backed deep-link example, use `-d @examples/theme02_sample_damage_request.json`. The verified [sample response](examples/theme02_sample_damage_response.json) includes a backup action with the catalog's actionable and validation deep links, followed by manual repair service. The [black-screen response](examples/theme02_black_screen_response.json) demonstrates a plan with manual and critical actions.

Request JSON:

| Field | Type | Meaning |
|---|---|---|
| `query` | string, required | Complaint, 3–2000 characters. |
| `siis_response` | string, optional | Additional trusted SIIS text, up to 50,000 characters. Use the kit record's `content` text when supplying it directly. |

Successful responses have `query`, `query_variations` (8–10), `response.contexts`, and `meta`. Each context has `goal`, `title`, `score`, and `actions`. Each action has `actionName`, `description`, `category`, and `stepGroups`. Groups have `steps` and optional `actionableDeeplink` and `validationDeeplink`. A deep link object uses the kit's lowercase `deeplink` key. `meta` reports `latency_ms`, `cache_hit`, `model`, and `cost_usd`.

When no supported plan can be established, the endpoint still returns `200`:

```json
{
  "query": "example unsupported complaint",
  "query_variations": ["... eight or more distinct variations ..."],
  "response": {"contexts": []},
  "meta": {"latency_ms": 0, "cache_hit": false, "model": "local-source-backed", "cost_usd": 0.0},
  "fallback": "no_match"
}
```

The ellipsis above explains the shape; it is not a literal response. Source-backed plans omit `fallback`.

## Errors

| Status | Error | Cause |
|---|---|---|
| `400` | `invalid_json` or `invalid_body_length` | Malformed or empty/oversized body. |
| `404` | `not_found` | Unknown route. |
| `415` | `unsupported_media_type` | Content type is not JSON. |
| `422` | `invalid_request` | Query, SIIS text, or extra request fields fail validation. |
| `500` | `plan_validation_failed` or `internal_error` | Internal failure; inspect server logs by request ID. |

This API has no authentication. Bind to loopback for the local demo; add an authentication and deployment layer before exposing it publicly.
