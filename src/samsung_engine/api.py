"""JSON-only REST service matching PDF endpoints."""

from __future__ import annotations

import json
import logging
import os
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .pipeline import TroubleshootingEngine
from .schema import TroubleshootRequest, WEB_LINK
from .ui import UI_HTML
from .validation import PlanValidationError


LOG = logging.getLogger(__name__)


def create_engine() -> TroubleshootingEngine:
    return TroubleshootingEngine(
        Path(os.environ.get("SAMSUNG_DATA_DIR", "data")),
        Path(os.environ.get("SAMSUNG_CACHE_PATH", ".cache/plans.sqlite3")),
    )


def make_handler(engine: TroubleshootingEngine) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "SamsungEngine/0.1"

        def log_message(self, format: str, *args: Any) -> None:
            LOG.info(json.dumps({"event": "http", "client": self.client_address[0], "message": format % args}))

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def _html(self, status: int, content: str) -> None:
            body = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            self.send_response(HTTPStatus.NO_CONTENT)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:
            if self.path in ("/", "/index.html", "/ui"):
                self._html(HTTPStatus.OK, UI_HTML)
                return
            if self.path != "/health":
                self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            if engine.data.catalog and engine.data.siis:
                self._json(HTTPStatus.OK, {"status": "ok", "catalog_entries": len(engine.data.catalog), "cache": "ready", "provider": "local-source-backed"})
            else:
                self._json(HTTPStatus.SERVICE_UNAVAILABLE, {
                    "status": "degraded", "catalog_entries": 0, "cache": "ready",
                    "provider": "local-source-backed", "warnings": engine.data.warnings,
                })

        def do_POST(self) -> None:
            if self.path != "/v1/troubleshoot":
                self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                return
            request_id = uuid.uuid4().hex
            if not self.headers.get("Content-Type", "").lower().startswith("application/json"):
                self._json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "unsupported_media_type", "request_id": request_id})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > 60000:
                self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_body_length", "request_id": request_id})
                return
            try:
                payload = json.loads(self.rfile.read(length))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json", "request_id": request_id})
                return
            try:
                request = TroubleshootRequest.model_validate(payload)
                response = engine.troubleshoot(request)
            except ValidationError as exc:
                details = [
                    {
                        "loc": ["<redacted>" if WEB_LINK.search(str(part)) else part for part in item["loc"]],
                        "type": item["type"],
                        "message": item["msg"],
                    }
                    for item in exc.errors(include_url=False, include_input=False)
                ]
                self._json(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": "invalid_request", "detail": details, "request_id": request_id})
                return
            except PlanValidationError:
                LOG.exception(json.dumps({"event": "validation_failure", "request_id": request_id}))
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "plan_validation_failed", "request_id": request_id})
                return
            except Exception:
                LOG.exception(json.dumps({"event": "pipeline_failure", "request_id": request_id}))
                self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "request_id": request_id})
                return
            self._json(HTTPStatus.OK, response.model_dump(exclude_none=True))

    return Handler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    host = os.environ.get("SAMSUNG_HOST", "127.0.0.1")
    port = int(os.environ.get("SAMSUNG_PORT", "8000"))
    engine = create_engine()
    server = ThreadingHTTPServer((host, port), make_handler(engine))
    LOG.info(json.dumps({"event": "startup", "host": host, "port": port, "catalog_entries": len(engine.data.catalog), "warnings": engine.data.warnings}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
