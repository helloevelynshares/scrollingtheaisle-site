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
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "aislecheck-api")
        self.assertIn("query", data["contracts"])
        self.assertIn("assessment", data["contracts"])
        self.assertIn("/api/aislecheck/assess", data["endpoints"])
        self.assertIn("versions", data)
        self.assertEqual(data["versions"]["baseline_id"], "deterministic-baseline-v1")
        self.assertIs(data["versions"]["llm_used"], False)

    def test_assess_each_price(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "doritos_5_13oz",
                "retailer": "Safeway",
                "submitted_offer": {
                    "price": 2.49,
                    "price_basis": "each",
                    "required_quantity": 4,
                    "package_size": "9.75 oz",
                },
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["request_id"])
        self.assertEqual(data["verdict"], "normal_sale")
        self.assertEqual(data["normalized_offer"]["comparable_unit_price"], 2.49)
        self.assertEqual(data["evidence"]["history_tier"], "full")
        self.assertNotIn("query", data)
        self.assertNotIn("debug", data)
        blob = res.text.lower()
        self.assertNotIn("traceback", blob)
        self.assertNotIn("/users/", blob)

    def test_assess_multi_buy(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "doritos_5_13oz",
                "retailer": "Safeway",
                "submitted_offer": {
                    "price": 10.0,
                    "price_basis": "multi_buy",
                    "required_quantity": 4,
                },
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["normalized_offer"]["comparable_unit_price"], 2.5)

    def test_assess_bogo(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "doritos_5_13oz",
                "retailer": "Safeway",
                "submitted_offer": {"price": 4.98, "price_basis": "bogo"},
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["normalized_offer"]["comparable_unit_price"], 2.49)

    def test_assess_limited_data(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "beef_short_ribs_per_lb",
                "retailer": "Safeway",
                "submitted_offer": {"price": 5.0, "price_basis": "per_lb"},
            },
        )
        data = res.json()
        self.assertEqual(data["verdict"], "limited_data")
        self.assertEqual(data["verdict_label"], "Early price signal")

    def test_assess_insufficient_data(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "chobani_yogurt_tub",
                "retailer": "Safeway",
                "submitted_offer": {"price": 1.25, "price_basis": "each"},
            },
        )
        self.assertEqual(res.json()["verdict"], "insufficient_data")

    def test_assess_unknown_tracker(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "not_a_real_tracker_xyz",
                "retailer": "Safeway",
                "submitted_offer": {"price": 2.49, "price_basis": "each"},
            },
        )
        data = res.json()
        self.assertEqual(data["verdict"], "not_comparable")
        self.assertIn("unknown_tracker", data["comparability"]["reasons"])

    def test_assess_invalid_offer(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            json={
                "tracker_id": "doritos_5_13oz",
                "retailer": "Safeway",
                "submitted_offer": {"price": None, "price_basis": "each"},
            },
        )
        self.assertEqual(res.json()["verdict"], "invalid_offer")

    def test_assess_malformed_json(self) -> None:
        res = self.client.post(
            "/api/aislecheck/assess",
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(res.status_code, 422)
        self.assertNotIn("traceback", res.text.lower())

    def test_assess_cors(self) -> None:
        res = self.client.options(
            "/api/aislecheck/assess",
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
        self.assertEqual(data["contract_version"], "aislecheck.v1")
        self.assertTrue(data.get("request_id"))
        self.assertNotIn("debug", data)
        blob = res.text.lower()
        self.assertNotIn("traceback", blob)
        self.assertNotIn("/users/", blob)
        self.assertNotIn("scripts/shopper_query", blob)

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
        oversized = "x" * 600
        res = self.client.post(
            "/api/aislecheck",
            json={"query": oversized},
        )
        self.assertIn(res.status_code, {400, 422})
        body = res.text
        self.assertNotIn(oversized, body)
        self.assertNotIn("xxxx", body)
        data = res.json()
        self.assertEqual(data.get("detail"), "invalid_request")
        self.assertTrue(data.get("request_id"))
        self.assertEqual(data.get("contract_version"), "aislecheck.v1")

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
