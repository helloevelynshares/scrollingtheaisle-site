"""Local AisleCheck prototype server: static homepage + shopper_query API.

Local development only. Serves the site from the repo root and exposes
deterministic AisleCheck endpoints. Does not deploy, and does not call LLMs.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import uuid
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shopper_query.aislecheck_contract import run_aislecheck_query  # noqa: E402

RECORDS_DIR = ROOT / "output" / "aislecheck_query_records"
RECORDS_FILE = RECORDS_DIR / "records.jsonl"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ensure_records_dir() -> None:
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)


def append_record(row: dict[str, Any]) -> Path:
    """Append one privacy-conscious local test row (raw query kept local only)."""
    _ensure_records_dir()
    payload = dict(row)
    payload.setdefault("recorded_at", _utc_now())
    with RECORDS_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return RECORDS_FILE


def _record_from_response(
    response: dict[str, Any],
    *,
    user_confirmed: bool | None = None,
    fields_corrected: list[str] | None = None,
    final_confirmed_interpretation: dict[str, Any] | None = None,
    event: str = "query",
) -> dict[str, Any]:
    return {
        "session_id": response.get("session_id") or "anonymous",
        "event": event,
        "raw_query": response.get("original_query"),
        "parser_output": {
            "normalized_query": response.get("normalized_query"),
            "normalizations_applied": response.get("normalizations_applied"),
            "extracted": response.get("extracted"),
            "missing_fields": response.get("missing_fields"),
            "reason_codes": response.get("reason_codes"),
        },
        "selected_tracker": response.get("selected_tracker"),
        "routing_outcome": response.get("next_action"),
        "user_confirmed": user_confirmed,
        "fields_corrected": fields_corrected or [],
        "final_confirmed_interpretation": final_confirmed_interpretation,
        # Explicit: these records stay on disk for local testing only.
        "analytics_destination": "local_file_only",
    }


class AisleCheckHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON object required")
        return data

    def do_OPTIONS(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/aislecheck"):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/aislecheck/health":
            self._send_json(
                200,
                {
                    "ok": True,
                    "service": "aislecheck-local",
                    "records_file": str(RECORDS_FILE.relative_to(ROOT)),
                },
            )
            return
        if path == "/api/aislecheck/records":
            _ensure_records_dir()
            rows: list[dict[str, Any]] = []
            if RECORDS_FILE.exists():
                for line in RECORDS_FILE.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            self._send_json(200, {"count": len(rows), "records": rows[-200:]})
            return
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/aislecheck":
            try:
                payload = self._read_json()
            except ValueError:
                self._send_json(400, {"error": "invalid_json"})
                return
            query = str(payload.get("query") or "").strip()
            if not query:
                self._send_json(400, {"error": "empty_query"})
                return
            session_id = str(payload.get("session_id") or "").strip() or str(uuid.uuid4())
            try:
                response = run_aislecheck_query(query, session_id=session_id)
            except Exception as exc:  # noqa: BLE001
                self._send_json(
                    500,
                    {
                        "error": "pipeline_failed",
                        "message": "Something went wrong checking that deal. Try again.",
                        "detail": f"{type(exc).__name__}",
                    },
                )
                return
            append_record(_record_from_response(response, event="query"))
            self._send_json(200, response)
            return

        if path == "/api/aislecheck/event":
            try:
                payload = self._read_json()
            except ValueError:
                self._send_json(400, {"error": "invalid_json"})
                return
            event = str(payload.get("event") or "feedback")
            response_like = {
                "session_id": payload.get("session_id") or "anonymous",
                "original_query": payload.get("raw_query"),
                "normalized_query": (payload.get("parser_output") or {}).get(
                    "normalized_query"
                ),
                "normalizations_applied": (payload.get("parser_output") or {}).get(
                    "normalizations_applied"
                ),
                "extracted": (payload.get("parser_output") or {}).get("extracted"),
                "missing_fields": (payload.get("parser_output") or {}).get(
                    "missing_fields"
                ),
                "reason_codes": (payload.get("parser_output") or {}).get("reason_codes"),
                "selected_tracker": payload.get("selected_tracker"),
                "next_action": payload.get("routing_outcome"),
            }
            path_written = append_record(
                _record_from_response(
                    response_like,
                    user_confirmed=payload.get("user_confirmed"),
                    fields_corrected=list(payload.get("fields_corrected") or []),
                    final_confirmed_interpretation=payload.get(
                        "final_confirmed_interpretation"
                    ),
                    event=event,
                )
            )
            self._send_json(
                200,
                {
                    "ok": True,
                    "records_file": str(path_written.relative_to(ROOT)),
                },
            )
            return

        self.send_error(404)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("text/css", ".css")

    httpd = ThreadingHTTPServer((args.host, args.port), AisleCheckHandler)
    print(
        f"AisleCheck local server at http://{args.host}:{args.port}/ "
        f"(API /api/aislecheck · records → {RECORDS_FILE.relative_to(ROOT)})"
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
