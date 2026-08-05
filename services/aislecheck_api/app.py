"""Hosted AisleCheck query API — deterministic shopper_query (no LLM).

Run locally:
  PYTHONPATH=scripts uvicorn services.aislecheck_api.app:app --reload --port 8080
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shopper_query.aislecheck_contract import (  # noqa: E402
    AISLECHECK_CONTRACT_VERSION,
    run_aislecheck_query,
)
from deal_assessment.service import assess_deal_dict  # noqa: E402
from deal_assessment.policy import POLICY_VERSION  # noqa: E402

MAX_QUERY_CHARS = int(os.environ.get("AISLECHECK_MAX_QUERY_CHARS", "500"))
REQUEST_TIMEOUT_MS = int(os.environ.get("AISLECHECK_TIMEOUT_MS", "8000"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("AISLECHECK_RATE_LIMIT_PER_MINUTE", "30"))
DEBUG_LOG = os.environ.get("AISLECHECK_DEBUG_LOG", "").lower() in {"1", "true", "yes"}

DEFAULT_ORIGINS = (
    "https://scrollingtheaisle.com",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
)


def _cors_origins() -> list[str]:
    raw = os.environ.get("AISLECHECK_CORS_ORIGINS", "").strip()
    if not raw:
        return list(DEFAULT_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="AisleCheck Query API", version="1.0.0", docs_url=None, redoc_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

_metrics_lock = Lock()
_metrics: dict[str, Any] = {
    "request_count": 0,
    "error_count": 0,
    "behavior_counts": defaultdict(int),
    "latency_ms_total": 0.0,
}
_rate_lock = Lock()
_rate_buckets: dict[str, deque] = defaultdict(deque)


class QueryBody(BaseModel):
    query: str = Field(..., min_length=1, max_length=MAX_QUERY_CHARS)
    apply_normalization: bool = True
    session_id: Optional[str] = Field(default=None, max_length=80)
    # Digests from prior clarify turns — used to break non-progressing loops.
    prior_clarify_digests: Optional[list[str]] = None
    # Opt-in structured clarification UX (candidate picks on loop terminal).
    # Public homepage keeps this false until activation.
    structured_clarification: bool = False


class AssessBody(BaseModel):
    tracker_id: str = Field(..., min_length=1, max_length=120)
    retailer: str = Field(default="Safeway", min_length=1, max_length=80)
    submitted_offer: dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = Field(default=None, max_length=80)


def _new_request_id() -> str:
    return str(uuid.uuid4())


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()[:80]
    if request.client:
        return request.client.host
    return "unknown"


def _rate_limit(request: Request) -> None:
    if RATE_LIMIT_PER_MINUTE <= 0:
        return
    now = time.time()
    key = _client_key(request)
    with _rate_lock:
        bucket = _rate_buckets[key]
        while bucket and now - bucket[0] > 60.0:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Too many requests. Please try again soon.")
        bucket.append(now)


def _record(behavior: str | None, latency_ms: float, *, error: bool = False) -> None:
    with _metrics_lock:
        _metrics["request_count"] += 1
        _metrics["latency_ms_total"] += latency_ms
        if error:
            _metrics["error_count"] += 1
        if behavior:
            _metrics["behavior_counts"][behavior] += 1


def _attach_meta(result: dict[str, Any], request_id: str) -> dict[str, Any]:
    out = dict(result)
    out["contract_version"] = out.get("contract_version") or AISLECHECK_CONTRACT_VERSION
    out["request_id"] = request_id
    if not DEBUG_LOG:
        out.pop("debug", None)
    return out


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> Response:
    # Never echo the submitted query (or other input) back in error payloads.
    safe_errors = []
    for err in exc.errors():
        item = {
            "type": err.get("type"),
            "loc": err.get("loc"),
            "msg": err.get("msg"),
        }
        safe_errors.append(item)
    return JSONResponse(
        status_code=422,
        content={
            "detail": "invalid_request",
            "errors": safe_errors,
            "request_id": _new_request_id(),
            "contract_version": AISLECHECK_CONTRACT_VERSION,
        },
    )


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "aislecheck-api",
        "contracts": {
            "query": AISLECHECK_CONTRACT_VERSION,
            "assessment": POLICY_VERSION,
        },
        "endpoints": ["/api/aislecheck", "/api/aislecheck/assess"],
    }


@app.get("/api/aislecheck/health")
def health_alias() -> dict[str, Any]:
    return health()


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    with _metrics_lock:
        count = max(_metrics["request_count"], 1)
        return {
            "request_count": _metrics["request_count"],
            "error_count": _metrics["error_count"],
            "behavior_counts": dict(_metrics["behavior_counts"]),
            "avg_latency_ms": round(_metrics["latency_ms_total"] / count, 2),
        }


@app.post("/api/aislecheck")
def aislecheck(body: QueryBody, request: Request) -> dict[str, Any]:
    request_id = _new_request_id()
    _rate_limit(request)
    query = (body.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="empty_query")
    if len(query) > MAX_QUERY_CHARS:
        raise HTTPException(status_code=400, detail="query_too_long")

    started = time.perf_counter()
    try:
        prior = body.prior_clarify_digests or []
        prior = [str(x)[:32] for x in prior[:8] if x]
        result = run_aislecheck_query(
            query,
            session_id=body.session_id,
            apply_normalization=body.apply_normalization,
            prior_clarify_digests=prior or None,
            structured_clarification=bool(body.structured_clarification),
        )
        result = _attach_meta(result, request_id)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > REQUEST_TIMEOUT_MS:
            _record(None, elapsed_ms, error=True)
            raise HTTPException(status_code=504, detail="request_timeout")
        _record(str(result.get("next_action") or "unknown"), elapsed_ms)
        if DEBUG_LOG:
            # Never log raw query text.
            print(
                f"aislecheck ok request_id={request_id} "
                f"action={result.get('next_action')} latency_ms={elapsed_ms:.1f}"
            )
        return result
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        _record(None, elapsed_ms, error=True)
        if DEBUG_LOG:
            print(f"aislecheck error request_id={request_id} latency_ms={elapsed_ms:.1f}")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong checking that deal. Please try again.",
        ) from None


@app.post("/api/aislecheck/assess")
def aislecheck_assess(body: AssessBody, request: Request) -> dict[str, Any]:
    """Deterministic historical assessment from confirmed structured fields.

    Never reparses a free-text query. Never uses an LLM.
    """
    request_id = _new_request_id()
    _rate_limit(request)
    tracker_id = (body.tracker_id or "").strip()
    retailer = (body.retailer or "Safeway").strip() or "Safeway"
    if not tracker_id:
        raise HTTPException(status_code=400, detail="missing_tracker_id")
    if not isinstance(body.submitted_offer, dict):
        raise HTTPException(status_code=400, detail="missing_submitted_offer")

    started = time.perf_counter()
    try:
        result = assess_deal_dict(tracker_id, retailer, body.submitted_offer)
        result = dict(result)
        result["contract_version"] = POLICY_VERSION
        result["request_id"] = request_id
        # Never echo raw free-text query even if a client sent one.
        result.pop("query", None)
        result.pop("raw_query", None)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if elapsed_ms > REQUEST_TIMEOUT_MS:
            _record("assess_timeout", elapsed_ms, error=True)
            raise HTTPException(status_code=504, detail="request_timeout")
        _record(f"assess:{result.get('verdict') or 'unknown'}", elapsed_ms)
        if DEBUG_LOG:
            print(
                f"aislecheck assess ok request_id={request_id} "
                f"verdict={result.get('verdict')} latency_ms={elapsed_ms:.1f}"
            )
        return result
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        _record("assess_error", elapsed_ms, error=True)
        if DEBUG_LOG:
            print(
                f"aislecheck assess error request_id={request_id} "
                f"latency_ms={elapsed_ms:.1f}"
            )
        raise HTTPException(
            status_code=500,
            detail="Something went wrong assessing that deal. Please try again.",
        ) from None


@app.exception_handler(Exception)
async def unhandled(_request: Request, _exc: Exception) -> Response:
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Something went wrong checking that deal. Please try again.",
            "request_id": _new_request_id(),
            "contract_version": AISLECHECK_CONTRACT_VERSION,
        },
    )
