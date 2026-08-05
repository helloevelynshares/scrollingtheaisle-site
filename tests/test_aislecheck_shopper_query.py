"""Tests for AisleCheck ↔ deterministic shopper_query integration."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PROTO = ROOT / "aislecheck-prototype"
JS = PROTO / "aislecheck.js"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from shopper_query.aislecheck_contract import (  # noqa: E402
    build_aislecheck_response,
    run_aislecheck_query,
)
from shopper_query.pipeline import process_query  # noqa: E402


class TestAisleCheckContractCases(unittest.TestCase):
    def test_explicit_supported_query(self) -> None:
        result = run_aislecheck_query(
            "Safeway Doritos 9.75 oz are $2.49 each when I buy four"
        )
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["original_query"].startswith("Safeway Doritos"), True)
        self.assertTrue(result["normalized_query"])
        self.assertEqual(result["extracted"]["price"], 2.49)
        self.assertIn("doritos", result["extracted"]["product_text"].lower())
        self.assertEqual(result["matcher_status"], "matched")
        self.assertEqual(result["selected_tracker"]["id"], "doritos_5_13oz")
        self.assertIn("Doritos", result["selected_tracker"]["display_name"])
        self.assertIn("unique_tracker_match", result["reason_codes"])

    def test_conversational_supported_query(self) -> None:
        result = run_aislecheck_query(
            "Doritos are five bucks when you buy two at Safeway"
        )
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["extracted"]["price"], 5.0)
        self.assertTrue(
            any(
                s.get("normalization_type") == "bucks_to_dollar"
                for s in result["normalizations_applied"]
            )
        )
        self.assertEqual(result["selected_tracker"]["id"], "doritos_5_13oz")

    def test_multi_buy_query(self) -> None:
        result = run_aislecheck_query("Safeway Doritos 2 for $5")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["extracted"]["promotion_type"], "multi_buy")
        self.assertEqual(result["extracted"]["required_quantity"], 2)
        self.assertEqual(result["extracted"]["price"], 5.0)
        self.assertEqual(result["extracted"]["price_basis"], "multi_buy")

    def test_bogo_query(self) -> None:
        result = run_aislecheck_query("Oreo family size BOGO at Safeway $3.99")
        self.assertEqual(result["next_action"], "continue")
        self.assertEqual(result["extracted"]["promotion_type"], "bogo")
        self.assertEqual(result["extracted"]["price"], 3.99)
        self.assertEqual(result["selected_tracker"]["id"], "oreo_family_size")

    def test_missing_price(self) -> None:
        result = run_aislecheck_query("Safeway Doritos on sale")
        self.assertEqual(result["next_action"], "clarify")
        self.assertEqual(result["clarify_kind"], "missing_field")
        self.assertEqual(result["clarify_field"], "price")
        self.assertIn("advertised price", result["clarify_prompt"].lower())
        self.assertEqual(result["selected_tracker"]["id"], "doritos_5_13oz")

    def test_ambiguous_product(self) -> None:
        result = run_aislecheck_query("General Mills cereal $3.99 at Safeway")
        self.assertEqual(result["next_action"], "clarify")
        self.assertEqual(result["clarify_kind"], "ambiguous_product")
        self.assertTrue(result["plausible_trackers"])
        self.assertLessEqual(len(result["plausible_trackers"]), 3)
        self.assertIn("ambiguous_tracker_match", result["reason_codes"])

    def test_unsupported_product(self) -> None:
        result = run_aislecheck_query("quinoa crackers $2.99 at Safeway")
        self.assertEqual(result["next_action"], "unsupported")
        self.assertIsNone(result["selected_tracker"])

    def test_malformed_or_conflicting_price(self) -> None:
        result = run_aislecheck_query("Doritos $1.99 or $2.49")
        self.assertEqual(result["next_action"], "invalid")
        self.assertTrue(
            "conflicting_or_malformed_price" in result["reason_codes"]
            or "conflicting_prices" in result["reason_codes"]
        )

    def test_response_contract_keys(self) -> None:
        result = run_aislecheck_query("Safeway Doritos $2.49")
        for key in (
            "original_query",
            "normalized_query",
            "normalizations_applied",
            "extracted",
            "missing_fields",
            "matcher_status",
            "selected_tracker",
            "plausible_trackers",
            "next_action",
            "reason_codes",
            "debug",
        ):
            self.assertIn(key, result)
        for key in (
            "product_text",
            "price",
            "promotion_type",
            "required_quantity",
            "price_basis",
            "package_size",
        ):
            self.assertIn(key, result["extracted"])

    def test_price_basis_prompt_helper(self) -> None:
        # Force unclear basis on a matched multi-buy-ish parse via pipeline + patch.
        pipeline = process_query(
            "Safeway Doritos $5 when you buy 4", apply_normalization=True
        )
        pipeline.parsed.price_basis = "each"
        pipeline.parsed.promotion_type = "simple_sale"
        pipeline.parsed.required_quantity = 4
        # Behavior may still say continue; contract should escalate.
        response = build_aislecheck_response(pipeline)
        self.assertEqual(response["next_action"], "clarify")
        self.assertEqual(response["clarify_field"], "price_basis")
        self.assertIn("total for", response["clarify_prompt"].lower())


class TestAisleCheckLocalLogging(unittest.TestCase):
    def test_append_record_local_only(self) -> None:
        sys.path.insert(0, str(PROTO))
        import server as aislecheck_server  # type: ignore

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            records = tmp_path / "records.jsonl"
            with mock.patch.object(aislecheck_server, "RECORDS_DIR", tmp_path), mock.patch.object(
                aislecheck_server, "RECORDS_FILE", records
            ):
                response = run_aislecheck_query(
                    "Safeway Doritos $2.49", session_id="test_session"
                )
                path = aislecheck_server.append_record(
                    aislecheck_server._record_from_response(response, event="query")
                )
                self.assertTrue(path.exists())
                row = json.loads(path.read_text(encoding="utf-8").strip())
                self.assertEqual(row["session_id"], "test_session")
                self.assertEqual(row["raw_query"], "Safeway Doritos $2.49")
                self.assertEqual(row["analytics_destination"], "local_file_only")
                self.assertIn("parser_output", row)
                self.assertIn("routing_outcome", row)


class TestAisleCheckJsHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        harness = r"""
const fs = require("fs");
const vm = require("vm");
const path = process.argv[1];
const code = fs.readFileSync(path, "utf8");
const document = {
  readyState: "complete",
  body: { classList: { add() {} }, setAttribute() {}, appendChild() {} },
  getElementById() { return null; },
  addEventListener() {},
  createElement() { return { appendChild() {} }; },
  head: { appendChild() {} },
};
const window = {
  location: { hostname: "127.0.0.1", protocol: "http:", search: "", href: "http://127.0.0.1:8000/", pathname: "/", hash: "", origin: "http://127.0.0.1:8000" },
  history: { replaceState() {} },
  sessionStorage: { store: {}, getItem(k){ return this.store[k] || null; }, setItem(k,v){ this.store[k]=String(v);} },
  setTimeout,
  fetch() { return Promise.reject(new Error("no fetch in test")); },
  AisleCheckPrototype: undefined,
};
window.window = window;
window.document = document;
const sandbox = { window, document, URL, URLSearchParams, Number, String, Array, Object, parseInt, setTimeout, console, Math, Date, Promise };
vm.runInNewContext(code + "\n;this.API = window.AisleCheckPrototype;", sandbox);
const API = sandbox.API;
const continueResp = {
  next_action: "continue",
  clarify_kind: null,
  extracted: {
    product_text: "Doritos",
    price: 2.49,
    price_basis: "each",
    promotion_label: "Buy 4",
    required_quantity: 4,
    package_size: "9.75 oz",
    retailer: "safeway",
  },
  selected_tracker: { id: "doritos_5_13oz", display_name: "Doritos · regular size", name: "Doritos" },
};
const clarifyField = { next_action: "clarify", clarify_kind: "missing_field", clarify_field: "price" };
const clarifyProduct = { next_action: "clarify", clarify_kind: "ambiguous_product" };
const out = {
  views: {
    continue: API.viewFromResponse(continueResp),
    field: API.viewFromResponse(clarifyField),
    product: API.viewFromResponse(clarifyProduct),
    unsupported: API.viewFromResponse({ next_action: "unsupported" }),
    invalid: API.viewFromResponse({ next_action: "invalid" }),
  },
  correction: API.correctionFromResponse(continueResp),
  rebuilt: API.buildQueryFromCorrection(API.correctionFromResponse(continueResp)),
  apiUrl: API.API_URL,
  noDealAssistant: !fs.readFileSync(path, "utf8").includes("deal_assistant"),
  hasUnderstood: fs.readFileSync(path, "utf8").includes("Here’s what AisleCheck understood"),
  hasPlaceholder: fs.readFileSync(path, "utf8").includes("still in progress"),
  hasAlmostReady: fs.readFileSync(path, "utf8").includes("AisleCheck is almost ready"),
  hasTemporaryUnavailable: fs.readFileSync(path, "utf8").includes("We couldn’t check that deal right now"),
  hasOptIn: fs.readFileSync(path, "utf8").includes("Submit as an example"),
  noOldOptIn: !fs.readFileSync(path, "utf8").includes("Submit this example"),
  debugGated: fs.readFileSync(path, "utf8").includes('get("aislecheckDebug") === "1"'),
  debugOffByDefault: API.isDebugEnabled() === false,
  noGoodDealVerdict: !fs.readFileSync(path, "utf8").includes('"Good deal"'),
  noInternalPlan: !fs.readFileSync(path, "utf8").includes("Day 1") && !fs.readFileSync(path, "utf8").toLowerCase().includes("coming next"),
  hasReset: typeof API.resetToEmpty === "function",
  hasCorrectionFields: fs.readFileSync(path, "utf8").includes("ac-corr-product"),
  liveApiFlag: typeof API.isLiveApiEnabled === "function",
};
API.applyResponse(continueResp);
const afterApply = API.getState().view;
API.resetToEmpty();
const afterReset = API.getState().view;
out.afterApply = afterApply;
out.afterReset = afterReset;
process.stdout.write(JSON.stringify(out));
"""
        result = subprocess.run(
            ["node", "-e", harness, str(JS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        cls.logic = json.loads(result.stdout)

    def test_view_mapping(self) -> None:
        self.assertEqual(self.logic["views"]["continue"], "understood")
        self.assertEqual(self.logic["views"]["field"], "clarify_field")
        self.assertEqual(self.logic["views"]["product"], "clarify_product")
        self.assertEqual(self.logic["views"]["unsupported"], "unsupported")
        self.assertEqual(self.logic["views"]["invalid"], "invalid")

    def test_correction_rebuild_and_copy(self) -> None:
        corr = self.logic["correction"]
        self.assertEqual(corr["product"], "Doritos")
        self.assertIn("2.49", corr["price"])
        self.assertIn("Doritos", self.logic["rebuilt"])
        self.assertIn("$2.49", self.logic["rebuilt"])
        self.assertTrue(self.logic["hasCorrectionFields"])

    def test_reset_check_another(self) -> None:
        self.assertTrue(self.logic["hasReset"])
        self.assertEqual(self.logic["afterApply"], "understood")
        self.assertEqual(self.logic["afterReset"], "empty")

    def test_ui_contracts(self) -> None:
        self.assertEqual(self.logic["apiUrl"], "/api/aislecheck")
        self.assertTrue(self.logic["noDealAssistant"])
        self.assertTrue(self.logic["hasUnderstood"])
        self.assertTrue(self.logic["hasPlaceholder"])
        self.assertTrue(self.logic["hasAlmostReady"])
        self.assertTrue(self.logic["hasTemporaryUnavailable"])
        self.assertTrue(self.logic["hasOptIn"])
        self.assertTrue(self.logic["noOldOptIn"])
        self.assertTrue(self.logic["debugGated"])
        self.assertTrue(self.logic["debugOffByDefault"])
        self.assertTrue(self.logic["noGoodDealVerdict"])
        self.assertTrue(self.logic["noInternalPlan"])
        self.assertTrue(self.logic["liveApiFlag"])


class TestAisleCheckServerEndpoint(unittest.TestCase):
    def test_run_query_via_handler_helpers(self) -> None:
        sys.path.insert(0, str(PROTO))
        import server as aislecheck_server  # type: ignore

        response = run_aislecheck_query("Safeway Doritos $2.49 each", session_id="s1")
        row = aislecheck_server._record_from_response(
            response,
            user_confirmed=True,
            fields_corrected=["price"],
            final_confirmed_interpretation={"ok": True},
            event="check_price_placeholder",
        )
        self.assertEqual(row["user_confirmed"], True)
        self.assertEqual(row["fields_corrected"], ["price"])
        self.assertEqual(row["final_confirmed_interpretation"], {"ok": True})
        self.assertEqual(row["analytics_destination"], "local_file_only")


if __name__ == "__main__":
    unittest.main()
