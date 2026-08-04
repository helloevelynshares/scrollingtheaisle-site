"""Tests for the public AisleCheck homepage UI (Variation 4)."""

from __future__ import annotations

import json
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTO = ROOT / "aislecheck-prototype"
INDEX = ROOT / "index.html"
JS = PROTO / "aislecheck.js"
CSS = PROTO / "aislecheck.css"
README = PROTO / "README.md"
PKG = ROOT / "package.json"


class TestAisleCheckPublicShip(unittest.TestCase):
    def test_no_github_actions_deploy_workflows_added(self) -> None:
        workflows = ROOT / ".github" / "workflows"
        self.assertFalse(
            workflows.exists(),
            msg="Must not add GitHub Actions deploy workflows",
        )

    def test_cname_unchanged(self) -> None:
        live = (ROOT / "CNAME").read_text(encoding="utf-8").strip()
        self.assertEqual(live, "scrollingtheaisle.com")

    def test_package_json_has_no_new_deploy_scripts(self) -> None:
        pkg = json.loads(PKG.read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        for name in scripts:
            lower = name.lower()
            self.assertFalse(
                any(token in lower for token in ("deploy", "gh-pages", "publish")),
                msg=f"Unexpected deploy-like script: {name}",
            )


class TestAisleCheckPublicAssets(unittest.TestCase):
    def test_public_variant_four_default(self) -> None:
        text = JS.read_text(encoding="utf-8")
        self.assertIn("PUBLIC_VARIANT = 4", text)
        self.assertIn("aislecheckProto", text)

    def test_shared_copy_present(self) -> None:
        text = JS.read_text(encoding="utf-8")
        for needle in (
            "AisleCheck",
            "Is this a good deal?",
            "Paste a deal you saw. We’ll confirm the product and price",
            "What product did you see, and what was the deal?",
            "Check deal",
            "Doritos are $2.49 each when I buy four.",
            "Works with products in our Bay Area Safeway price tracker.",
            "Looking this up…",
            "Here’s what AisleCheck understood",
            "AisleCheck is almost ready",
            "We couldn’t check that deal right now",
            "AisleCheck may still be waking up. Try again in a moment.",
            "Submit as an example",
            "/api/aislecheck",
        ):
            self.assertIn(needle, text)
        self.assertNotIn("Day 1", text)
        self.assertNotIn("Submit this example", text)

    def test_no_internal_plan_language(self) -> None:
        text = JS.read_text(encoding="utf-8")
        self.assertNotIn("deal_assistant", text)
        self.assertNotIn('"Good deal"', text)
        self.assertNotIn("coming next", text.lower())
        self.assertNotIn("NEXT STEP PLACEHOLDER", text)
        self.assertIn("almost ready", text.lower())
        self.assertIn("showAlmostReady", text)

    def test_index_loads_publicly(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        self.assertIn('id="aislecheck-root"', html)
        self.assertIn("aislecheck-prototype/aislecheck.js", html)
        self.assertIn("__AISLECHECK_CONFIG__", html)
        self.assertIn("apiBaseUrl", html)
        self.assertIn('apiBaseUrl: "https://aislecheck-api.onrender.com"', html)
        self.assertIn("liveApiEnabled: true", html)
        self.assertIn("exampleSubmitEnabled: true", html)
        self.assertNotIn("if (!local) return;", html)
        lead_idx = html.index("hub-hero-lead")
        root_idx = html.index('id="aislecheck-root"')
        trackers_idx = html.index('id="hub-tracker-module"')
        self.assertLess(lead_idx, root_idx)
        self.assertLess(root_idx, trackers_idx)

    def test_fallback_copy_contracts(self) -> None:
        text = JS.read_text(encoding="utf-8")
        self.assertIn("AisleCheck is almost ready", text)
        self.assertIn(
            "We’re testing how shoppers describe deals before turning on live price checks.",
            text,
        )
        self.assertIn("We couldn’t check that deal right now", text)
        self.assertIn("AisleCheck may still be waking up. Try again in a moment.", text)
        self.assertIn("Submit as an example", text)
        self.assertIn(
            "Submitted examples may be reviewed to improve AisleCheck. Don’t include personal information.",
            text,
        )
        self.assertIn("showAlmostReady", text)
        self.assertIn("showTemporaryUnavailable", text)
        self.assertIn("p_client_submission_id", text)
        self.assertIn("exampleSubmitEnabled: cfg.exampleSubmitEnabled === true", text)
        self.assertNotIn("Submit this example", text)
        self.assertNotIn('"Good deal"', text)
        self.assertNotIn("deal_assistant", text)

    def test_temporary_vs_disabled_fallback_behavior(self) -> None:
        harness = ROOT / "tests" / "aislecheck_fallback_harness.cjs"
        result = subprocess.run(
            ["node", str(harness), str(JS), str(CSS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "harness failed")
        data = json.loads(result.stdout)
        self.assertTrue(data["liveBefore"])
        self.assertEqual(data["failView"], "temporary_unavailable")
        self.assertEqual(data["failQuery"], "Doritos are $2.49 each when I buy four")
        self.assertGreaterEqual(data["failFetchCount"], 1)
        self.assertEqual(data["failRpcCount"], 0)
        self.assertTrue(data["failHasTempCopy"])
        self.assertTrue(data["failHasTryAgain"])
        self.assertTrue(data["failTryIsPrimary"])
        self.assertTrue(data["failSubmitSecondary"])
        self.assertTrue(data["failNoVerdict"])
        self.assertTrue(data["failNoAutoStore"])
        self.assertEqual(data["timeoutView"], "temporary_unavailable")
        self.assertEqual(data["timeoutQuery"], "Doritos are $2.49 each when I buy four")
        self.assertTrue(data["timeoutNoVerdict"])
        self.assertEqual(data["lockedCalls"], 1)
        self.assertTrue(data["locked"])
        self.assertEqual(data["retryBodies"], ["Doritos are $2.49 each when I buy four"])
        self.assertEqual(data["retryView"], "temporary_unavailable")
        self.assertEqual(data["retryQuery"], "Doritos are $2.49 each when I buy four")
        self.assertEqual(data["successView"], "understood")
        self.assertTrue(data["successHasTracker"])
        self.assertEqual(data["optInRpcName"], "submit_aislecheck_example")
        self.assertEqual(data["optInQuery"], "Doritos are $2.49 each when I buy four")
        self.assertEqual(data["disabledView"], "almost_ready")
        self.assertEqual(data["disabledFetchCalls"], 0)
        self.assertTrue(data["disabledHasAlmost"])
        self.assertTrue(data["disabledNoTryAgain"])
        self.assertTrue(data["disabledHasSubmit"])
        self.assertTrue(data["disabledNoVerdict"])
        self.assertTrue(data["optInCopy"])
        self.assertTrue(data["privacy"])
        self.assertTrue(data["almostHtmlAtFailHasNoTry"])
        self.assertTrue(data["mobileCss"])
        self.assertTrue(data["hasClientTimeout"])

    def test_css_and_readme_exist(self) -> None:
        self.assertTrue(CSS.is_file())
        self.assertTrue(README.is_file())
        readme = README.read_text(encoding="utf-8")
        self.assertIn("Variation 4", readme)


class TestAisleCheckPublicLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        harness = r"""
const fs = require("fs");
const vm = require("vm");
const path = process.argv[1];
const code = fs.readFileSync(path, "utf8");
const document = {
  readyState: "complete",
  body: { classList: { add() {}, remove() {} }, setAttribute() {}, appendChild() {} },
  getElementById() { return null; },
  addEventListener() {},
  createElement() { return { appendChild() {} }; },
  head: { appendChild() {} },
};
const window = {
  location: { hostname: "scrollingtheaisle.com", protocol: "https:", search: "", href: "https://scrollingtheaisle.com/", pathname: "/", hash: "", origin: "https://scrollingtheaisle.com" },
  history: { replaceState() {} },
  sessionStorage: { store: {}, getItem(k){ return this.store[k] || null; }, setItem(k,v){ this.store[k]=String(v);} },
  setTimeout,
  fetch() { return Promise.reject(new Error("no fetch in test")); },
  AisleCheckPrototype: undefined,
};
window.window = window;
window.document = document;
const sandbox = {
  window, document, URL, URLSearchParams, Number, String, Array, Object,
  parseInt, setTimeout, console, Math, Date, Promise,
};
vm.runInNewContext(code + "\n;this.API = window.AisleCheckPrototype;", sandbox);
const API = sandbox.API;
const out = {
  publicVariant: API.PUBLIC_VARIANT,
  parse: {
    one: API.parseVariantParam("1"),
    six: API.parseVariantParam("6"),
    bad: API.parseVariantParam("99"),
    empty: API.parseVariantParam(""),
  },
  resolve: {
    publicDefault: API.resolveInitialVariant("", null),
    ignoredUrlWithoutProto: API.resolveInitialVariant("?aislecheckVariant=2", "3"),
    protoUrl: API.resolveInitialVariant("?aislecheckProto=1&aislecheckVariant=2", "3"),
    protoStored: API.resolveInitialVariant("?aislecheckProto=1", "5"),
  },
  hosts: {
    localIp: API.isLocalHost("127.0.0.1", "http:"),
    prod: API.isLocalHost("scrollingtheaisle.com", "https:"),
  },
  proto: {
    off: API.isProtoControlsEnabled(""),
    on: API.isProtoControlsEnabled("?aislecheckProto=1"),
  },
  views: {
    continue: API.viewFromResponse({ next_action: "continue" }),
    clarifyField: API.viewFromResponse({ next_action: "clarify", clarify_kind: "missing_field" }),
    clarifyProduct: API.viewFromResponse({ next_action: "clarify", clarify_kind: "ambiguous_product" }),
    unsupported: API.viewFromResponse({ next_action: "unsupported" }),
    invalid: API.viewFromResponse({ next_action: "invalid" }),
  },
  mountedVariant: API.getState().variant,
  example: API.EXAMPLE_QUERY,
  apiUrl: API.API_URL,
};
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

    def test_public_variant_locked(self) -> None:
        self.assertEqual(self.logic["publicVariant"], 4)
        self.assertEqual(self.logic["resolve"]["publicDefault"], 4)
        self.assertEqual(self.logic["resolve"]["ignoredUrlWithoutProto"], 4)
        self.assertEqual(self.logic["mountedVariant"], 4)
        self.assertFalse(self.logic["proto"]["off"])
        self.assertTrue(self.logic["proto"]["on"])
        self.assertEqual(self.logic["resolve"]["protoUrl"], 2)
        self.assertEqual(self.logic["resolve"]["protoStored"], 5)

    def test_parse_and_hosts(self) -> None:
        self.assertEqual(self.logic["parse"]["one"], 1)
        self.assertEqual(self.logic["parse"]["six"], 6)
        self.assertEqual(self.logic["parse"]["bad"], 4)
        self.assertTrue(self.logic["hosts"]["localIp"])
        self.assertFalse(self.logic["hosts"]["prod"])

    def test_response_view_mapping(self) -> None:
        self.assertEqual(self.logic["views"]["continue"], "understood")
        self.assertEqual(self.logic["views"]["clarifyField"], "clarify_field")
        self.assertEqual(self.logic["views"]["clarifyProduct"], "clarify_product")
        self.assertEqual(self.logic["views"]["unsupported"], "unsupported")
        self.assertEqual(self.logic["views"]["invalid"], "invalid")
        self.assertIn("Doritos", self.logic["example"])
        self.assertEqual(self.logic["apiUrl"], "/api/aislecheck")


class TestAisleCheckMarkupContracts(unittest.TestCase):
    def test_variation_4_layout_hooks(self) -> None:
        html = INDEX.read_text(encoding="utf-8")
        css = CSS.read_text(encoding="utf-8")
        self.assertIn('id="hub-hero-actions-split"', html)
        self.assertIn('body[data-aislecheck-variant="4"] .hub-hero-actions-split', css)
        self.assertIn('"signup signup"', css)
        self.assertIn('"side aislecheck"', css)

    def test_no_ask_ai_or_chatbot_language(self) -> None:
        blob = "\n".join(
            [
                JS.read_text(encoding="utf-8"),
                CSS.read_text(encoding="utf-8"),
                INDEX.read_text(encoding="utf-8"),
            ]
        ).lower()
        for banned in ("ask ai", "chatbot", "chat bubble", "openai"):
            self.assertNotIn(banned, blob)

    def test_six_renderers_still_present_for_proto_mode(self) -> None:
        text = JS.read_text(encoding="utf-8")
        ids = re.findall(r"id:\s*([1-6])\s*,", text)
        self.assertEqual(sorted(ids), ["1", "2", "3", "4", "5", "6"])


if __name__ == "__main__":
    unittest.main()
