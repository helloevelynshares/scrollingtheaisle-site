"""Tests for the hosted AisleCheck FastAPI service."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from fastapi.testclient import TestClient
    from services.aislecheck_api.app import app
except ImportError as exc:  # pragma: no cover
    raise unittest.SkipTest(f"fastapi not installed: {exc}") from exc


class TestAisleCheckApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health(self) -> None:
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["service"], "aislecheck-query")
        self.assertEqual(res.json()["status"], "ok")

    def test_valid_explicit_query(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={
                "query": "Safeway Doritos 9.75 oz are $2.49 each when I buy four",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["next_action"], "continue")
        self.assertEqual(data["selected_tracker"]["id"], "doritos_5_13oz")
        self.assertNotIn("debug", data)

    def test_conversational_query(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "Doritos are five bucks when you buy two at Safeway"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["next_action"], "continue")

    def test_multi_buy(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "Safeway Doritos 2 for $5"},
        )
        data = res.json()
        self.assertEqual(data["extracted"]["promotion_type"], "multi_buy")

    def test_bogo(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "Oreo family size BOGO at Safeway $3.99"},
        )
        self.assertEqual(res.json()["extracted"]["promotion_type"], "bogo")

    def test_missing_price(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "Safeway Doritos on sale"},
        )
        data = res.json()
        self.assertEqual(data["next_action"], "clarify")

    def test_ambiguous_product(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "General Mills cereal $3.99 at Safeway"},
        )
        data = res.json()
        self.assertEqual(data["next_action"], "clarify")
        self.assertEqual(data["clarify_kind"], "ambiguous_product")

    def test_unsupported_product(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "quinoa crackers $2.99 at Safeway"},
        )
        self.assertEqual(res.json()["next_action"], "unsupported")

    def test_conflicting_price(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "Doritos $1.99 or $2.49"},
        )
        self.assertEqual(res.json()["next_action"], "invalid")

    def test_empty_query(self) -> None:
        res = self.client.post("/api/aislecheck", json={"query": "   "})
        self.assertIn(res.status_code, {400, 422})

    def test_oversized_query(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            json={"query": "x" * 600},
        )
        self.assertIn(res.status_code, {400, 422})

    def test_malformed_json(self) -> None:
        res = self.client.post(
            "/api/aislecheck",
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(res.status_code, 422)

    def test_cors_allowed_origin(self) -> None:
        res = self.client.options(
            "/api/aislecheck",
            headers={
                "Origin": "https://scrollingtheaisle.com",
                "Access-Control-Request-Method": "POST",
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers.get("access-control-allow-origin"),
            "https://scrollingtheaisle.com",
        )

    def test_cors_rejected_origin(self) -> None:
        res = self.client.options(
            "/api/aislecheck",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "POST",
            },
        )
        # Starlette CORSMiddleware omits allow-origin for disallowed origins.
        self.assertNotEqual(
            res.headers.get("access-control-allow-origin"),
            "https://evil.example",
        )


if __name__ == "__main__":
    unittest.main()
