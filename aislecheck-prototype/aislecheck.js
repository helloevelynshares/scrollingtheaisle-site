/**
 * AisleCheck homepage UI — Variation 4 is the public default.
 * Optional local controls: ?aislecheckProto=1 (variation switcher).
 * Optional debug: ?aislecheckDebug=1.
 * Talks to /api/aislecheck when available (deterministic shopper_query; no LLM).
 */
(function () {
  "use strict";

  var EXAMPLE_QUERY = "Doritos are $2.49 each when I buy four.";
  var STORAGE_KEY = "sta_aislecheck_variant";
  var SESSION_KEY = "sta_aislecheck_session";
  var DEFAULT_API_PATH = "/api/aislecheck";
  var EVENT_PATH = "/api/aislecheck/event";
  var ASSESS_PATH = "/api/aislecheck/assess";
  var PUBLIC_VARIANT = 4;
  var MAX_QUERY_CHARS = 500;
  /** Client abort for cold-start / hung Render free-tier wakes. */
  var API_TIMEOUT_MS = 15000;
  var SUPABASE_URL = "https://wurmdtqysegytsjcudve.supabase.co";
  var SUPABASE_ANON_KEY = "sb_publishable_8Wt-it-oIHHIkQOi0D9y_g_qMoH51ZX";

  var COPY = {
    brand: "AisleCheck",
    heading: "Is this a good deal?",
    description:
      "Paste a deal you saw. We’ll confirm the product and price, then help you check it.",
    placeholder: "What product did you see, and what was the deal?",
    button: "Check deal",
    exampleLabel: "Try:",
    exampleText: EXAMPLE_QUERY,
    scopeNote:
      "Works with products in our Bay Area Safeway price tracker. We’ll ask if anything’s unclear.",
    loading: "Looking this up…",
    conversationalPrompt: "What deal did you see?",
    understoodHeading: "Here’s what AisleCheck understood",
    checkPrice: "Check this price",
    assessing: "Checking price history…",
    fixIt: "Fix it",
    checkAnother: "Check another deal",
    noneOfThese: "None of these",
    clarifyLoopHeading: "I still need a clearer product name",
    clarifyLoopBody:
      "Try brand plus size or form (for example: Chobani tub, Cheetos party size). Price history was not checked.",
    requestProduct: "Request this product",
    unsupportedHeading: "We don’t track this product yet.",
    unsupportedBody: "You can request it for a future price tracker.",
    invalidHeading: "We couldn’t read that deal clearly.",
    invalidBody:
      "Try again with the product name, the advertised price, and any buy requirement (for example: Doritos $2.49 when I buy 4).",
    placeholderVerdict:
      "Price history for this deal is still in progress. Historical scoring stays off in production until the assess API is deployed.",
    assessmentEvidenceLabel: "Evidence from tracked ads",
    assessmentUnitPriceLabel: "Comparable unit price",
    assessmentAtlLabel: "All-time low",
    assessmentMedianLabel: "Median ad price",
    assessmentWeeksLabel: "Comparable weeks",
    almostReadyHeading: "AisleCheck is almost ready",
    almostReadyBody:
      "We’re testing how shoppers describe deals before turning on live price checks.",
    temporaryUnavailableHeading: "We couldn’t check that deal right now",
    temporaryUnavailableBody:
      "AisleCheck may still be waking up. Try again in a moment.",
    tryAgain: "Try again",
    submitExample: "Submit as an example",
    exampleSubmitted: "Thanks — example submitted",
    privacyNote:
      "Submitted examples may be reviewed to improve AisleCheck. Don’t include personal information.",
    thanksNoStore:
      "Thanks for trying AisleCheck. Live checks are coming soon.",
    clarifySubmit: "Continue",
    preservedQueryLabel: "Your query",
  };

  var VARIATION_META = [
    {
      id: 1,
      name: "Variation 1",
      title: "Minimal inline search",
      intent: "Lightweight utility tucked into the homepage flow.",
      advantage: "Lowest friction; feels like search, not a promo.",
      risk: "Easy to miss; may under-communicate AisleCheck value.",
      expectedBehavior: "Type a deal, hit Check deal, scan a quick answer.",
      mobile: "Single-column compact row; button full-width under input.",
    },
    {
      id: 2,
      name: "Variation 2",
      title: "Featured card",
      intent: "Primary homepage feature in a contained card.",
      advantage: "Clear branding and room for example + scope.",
      risk: "Competes with signup and aisle CTAs for attention.",
      expectedBehavior: "Read card, try example, submit from the card.",
      mobile: "Card pads shrink; stacked input then button.",
    },
    {
      id: 3,
      name: "Variation 3",
      title: "Hero-integrated",
      intent: "Extend the existing hero promise into the check action.",
      advantage: "AisleCheck feels central to entering the site.",
      risk: "Crowds the hero; signup and aisles may feel secondary.",
      expectedBehavior: "Natural continuation after the intro lead.",
      mobile: "Tight spacing under lead; avoid competing with h1 size.",
    },
    {
      id: 4,
      name: "Variation 4",
      title: "Conversational prompt card",
      intent:
        "Friendly prompt in a two-column band under a full-width email signup, beside aisle hop links and store voting.",
      advantage:
        "Subscribe stays primary across the top; AisleCheck shares the next row with aisles and vote.",
      risk: "Two-column density may compete for attention on mid-width screens.",
      expectedBehavior:
        "Subscribe first, then answer “What deal did you see?” or hop into an aisle / vote from the row below.",
      mobile: "Stacks as signup → aisles/vote → AisleCheck under ~840px; soft tone, no bubbles.",
    },
    {
      id: 5,
      name: "Variation 5",
      title: "Evidence-led design",
      intent: "Lead with tracked-history value before the query.",
      advantage: "Builds trust; clarifies what a result looks like.",
      risk: "Preview may look like a real result before submit.",
      expectedBehavior: "Glance at evidence preview, then enter a deal.",
      mobile: "Evidence chips wrap; fixture labels stay visible.",
    },
    {
      id: 6,
      name: "Variation 6",
      title: "Compact branded tool",
      intent: "Named utility with stronger AisleCheck wordmark.",
      advantage: "Memorable product identity within the site.",
      risk: "Feels like a separate product if branding is too strong.",
      expectedBehavior: "Recognize tool name, paste deal, run check.",
      mobile: "Wordmark row + tool shell; icon stays small.",
    },
  ];

  var state = {
    variant: PUBLIC_VARIANT,
    view: "empty",
    // empty | loading | understood | clarify_field | clarify_product |
    // unsupported | invalid | correction | placeholder | almost_ready |
    // temporary_unavailable | assessing | assessed | error
    query: "",
    loadingLocked: false,
    requestedProduct: false,
    exampleSubmitted: false,
    exampleSubmitBusy: false,
    exampleClientSubmissionId: null,
    response: null,
    assessment: null,
    clarifyAnswer: "",
    clarifyDigests: [],
    lastError: "",
    debugOpen: false,
    fieldsCorrected: [],
    correction: {
      product: "",
      price: "",
      priceBasis: "each",
      promotion: "",
      requiredQuantity: "",
      packageSize: "",
      store: "Safeway",
    },
  };

  function readConfig() {
    var cfg = (window.__AISLECHECK_CONFIG__ || {});
    return {
      apiBaseUrl: String(cfg.apiBaseUrl || "").replace(/\/$/, ""),
      // Require explicit true — safer public default is fallback-only.
      liveApiEnabled: cfg.liveApiEnabled === true,
      exampleSubmitEnabled: cfg.exampleSubmitEnabled === true,
      // Historical scoring stays off until assess is intentionally enabled.
      assessEnabled: cfg.assessEnabled === true,
      apiTimeoutMs:
        typeof cfg.apiTimeoutMs === "number" && cfg.apiTimeoutMs > 0
          ? cfg.apiTimeoutMs
          : null,
    };
  }

  function apiUrl(path) {
    var cfg = readConfig();
    if (!cfg.apiBaseUrl) return path;
    return cfg.apiBaseUrl + path;
  }

  function isLiveApiEnabled() {
    return readConfig().liveApiEnabled;
  }

  function isAssessEnabled() {
    return readConfig().assessEnabled;
  }

  function isLocalHost(hostname, protocol) {
    var host = String(hostname || "").toLowerCase();
    var proto = String(protocol || "");
    if (proto === "file:") return true;
    return host === "127.0.0.1" || host === "localhost";
  }

  /** @deprecated Use isLocalHost — kept for tests / older callers. */
  function isPrototypeHost(hostname, protocol) {
    return isLocalHost(hostname, protocol);
  }

  function isProtoControlsEnabled(search) {
    try {
      return new URLSearchParams(search || "").get("aislecheckProto") === "1";
    } catch (err) {
      return false;
    }
  }

  function parseVariantParam(raw) {
    var n = parseInt(String(raw == null ? "" : raw).trim(), 10);
    if (!Number.isFinite(n) || n < 1 || n > 6) return PUBLIC_VARIANT;
    return n;
  }

  function resolveInitialVariant(search, stored) {
    if (!isProtoControlsEnabled(search)) {
      return PUBLIC_VARIANT;
    }
    var params = new URLSearchParams(search || "");
    if (params.has("aislecheckVariant")) {
      return parseVariantParam(params.get("aislecheckVariant"));
    }
    if (stored != null && stored !== "") {
      return parseVariantParam(stored);
    }
    return PUBLIC_VARIANT;
  }

  function getSessionId() {
    try {
      var existing = window.sessionStorage.getItem(SESSION_KEY);
      if (existing) return existing;
      var id =
        "ac_" +
        Math.random().toString(36).slice(2, 10) +
        "_" +
        Date.now().toString(36);
      window.sessionStorage.setItem(SESSION_KEY, id);
      return id;
    } catch (err) {
      return "ac_anonymous";
    }
  }

  function newClientSubmissionId() {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === "function") {
        return window.crypto.randomUUID();
      }
    } catch (err) {
      /* fall through */
    }
    var hex = "";
    for (var i = 0; i < 32; i++) {
      hex += Math.floor(Math.random() * 16).toString(16);
    }
    return (
      hex.slice(0, 8) +
      "-" +
      hex.slice(8, 12) +
      "-4" +
      hex.slice(13, 16) +
      "-a" +
      hex.slice(17, 20) +
      "-" +
      hex.slice(20, 32)
    );
  }

  function ensureExampleClientSubmissionId() {
    if (!state.exampleClientSubmissionId) {
      state.exampleClientSubmissionId = newClientSubmissionId();
    }
    return state.exampleClientSubmissionId;
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function viewFromResponse(response) {
    if (!response) return "error";
    var action = response.next_action;
    if (action === "continue") return "understood";
    if (action === "unsupported") return "unsupported";
    if (action === "invalid") return "invalid";
    if (action === "clarify") {
      if (response.clarify_kind === "ambiguous_product") return "clarify_product";
      return "clarify_field";
    }
    return "error";
  }

  function correctionFromResponse(response) {
    var ex = (response && response.extracted) || {};
    var tracker = (response && response.selected_tracker) || {};
    return {
      product: ex.product_text || tracker.name || "",
      price: ex.price != null ? String(ex.price) : "",
      priceBasis: ex.price_basis && ex.price_basis !== "unknown" ? ex.price_basis : "each",
      promotion: ex.promotion_label || ex.promotion_type || "",
      requiredQuantity:
        ex.required_quantity != null ? String(ex.required_quantity) : "",
      packageSize: ex.package_size || "",
      store: ex.retailer
        ? ex.retailer.charAt(0).toUpperCase() + ex.retailer.slice(1)
        : "Safeway",
    };
  }

  function buildQueryFromCorrection(c) {
    var parts = [];
    if (c.store) parts.push(c.store);
    if (c.product) parts.push(c.product);
    if (c.packageSize) parts.push(c.packageSize);
    if (c.price) {
      var priceBit = "$" + String(c.price).replace(/^\$/, "");
      if (c.priceBasis === "multi_buy" && c.requiredQuantity) {
        parts.push(c.requiredQuantity + " for " + priceBit);
      } else if (c.priceBasis === "bogo") {
        parts.push("BOGO " + priceBit);
      } else {
        parts.push(priceBit + (c.priceBasis ? " " + c.priceBasis : ""));
      }
    }
    if (c.requiredQuantity && c.priceBasis !== "multi_buy") {
      parts.push("when you buy " + c.requiredQuantity);
    } else if (c.promotion && c.promotion.toLowerCase().indexOf("bogo") !== -1) {
      parts.push("BOGO");
    } else if (c.promotion) {
      parts.push(c.promotion);
    }
    return parts.join(" ").replace(/\s+/g, " ").trim();
  }

  function getApiTimeoutMs() {
    var cfg = readConfig();
    if (cfg.apiTimeoutMs != null) return cfg.apiTimeoutMs;
    return API_TIMEOUT_MS;
  }

  function postJson(url, body, opts) {
    opts = opts || {};
    var timeoutMs =
      typeof opts.timeoutMs === "number" ? opts.timeoutMs : getApiTimeoutMs();
    var controller =
      typeof AbortController !== "undefined" ? new AbortController() : null;
    var timer = null;
    if (controller && timeoutMs > 0) {
      timer = setTimeout(function () {
        try {
          controller.abort();
        } catch (err) {
          /* ignore */
        }
      }, timeoutMs);
    }
    var fetchOpts = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    };
    if (controller) fetchOpts.signal = controller.signal;
    return fetch(url, fetchOpts)
      .then(function (res) {
        return res
          .json()
          .catch(function () {
            return {};
          })
          .then(function (data) {
            if (!res.ok) {
              var err = new Error(
                (data && data.message) ||
                  (data && data.detail) ||
                  "request_failed"
              );
              err.payload = data;
              err.status = res.status;
              throw err;
            }
            return data;
          });
      })
      .catch(function (err) {
        if (
          err &&
          (err.name === "AbortError" ||
            (typeof DOMException !== "undefined" &&
              err instanceof DOMException &&
              err.name === "AbortError"))
        ) {
          var timeoutErr = new Error("request_timeout");
          timeoutErr.code = "timeout";
          throw timeoutErr;
        }
        throw err;
      })
      .finally(function () {
        if (timer) clearTimeout(timer);
      });
  }

  function getSupabaseClient() {
    try {
      if (window.supabase && typeof window.supabase.createClient === "function") {
        return window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
      }
    } catch (err) {
      /* ignore */
    }
    return null;
  }

  function submitExampleOptIn(query) {
    var q = String(query || "").trim();
    if (!q || q.length > MAX_QUERY_CHARS) {
      return Promise.reject(new Error("invalid_query"));
    }
    var client = getSupabaseClient();
    if (!client) {
      return Promise.reject(new Error("storage_unavailable"));
    }
    return client
      .rpc("submit_aislecheck_example", {
        p_query: q,
        p_client_submission_id: ensureExampleClientSubmissionId(),
      })
      .then(function (result) {
        if (result.error) throw result.error;
        return result.data;
      });
  }

  function logEvent(event, extra) {
    extra = extra || {};
    var response = state.response || {};
    var body = {
      event: event,
      session_id: getSessionId(),
      raw_query: state.query,
      parser_output: {
        normalized_query: response.normalized_query,
        normalizations_applied: response.normalizations_applied,
        extracted: response.extracted,
        missing_fields: response.missing_fields,
        reason_codes: response.reason_codes,
      },
      selected_tracker: response.selected_tracker,
      routing_outcome: response.next_action,
      user_confirmed: extra.user_confirmed,
      fields_corrected: extra.fields_corrected || state.fieldsCorrected || [],
      final_confirmed_interpretation: extra.final_confirmed_interpretation || null,
    };
    return postJson(apiUrl(EVENT_PATH), body).catch(function () {
      /* local logging best-effort */
    });
  }

  function iconCheckSvg() {
    return (
      '<svg class="ac-tool-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">' +
      '<rect x="1" y="1" width="18" height="18" rx="4" fill="none" stroke="currentColor" stroke-width="1.5"/>' +
      '<path d="M5.5 10.2l2.8 2.8 6.2-6.4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>' +
      "</svg>"
    );
  }

  function sharedFormFields(opts) {
    opts = opts || {};
    var labelClass = opts.hideLabel ? "visually-hidden" : "ac-label";
    var prompt = opts.promptHtml || "";
    var disabled = state.loadingLocked ? " disabled" : "";
    var placeholder =
      ' placeholder="' + escapeHtml(COPY.placeholder) + '"';
    var field;
    if (opts.multiline) {
      field =
        '<textarea id="ac-deal-input" name="deal" rows="2" class="ac-input ac-input--area"' +
        placeholder +
        disabled +
        ">" +
        escapeHtml(state.query) +
        "</textarea>";
    } else {
      field =
        '<input type="text" id="ac-deal-input" name="deal" class="ac-input" autocomplete="off"' +
        placeholder +
        ' value="' +
        escapeHtml(state.query) +
        '"' +
        disabled +
        " />";
    }
    return (
      prompt +
      '<label class="' +
      labelClass +
      '" for="ac-deal-input">' +
      (opts.labelText || COPY.placeholder) +
      "</label>" +
      field +
      '<div class="ac-actions">' +
      '<button type="submit" class="btn btn-primary ac-submit" id="ac-submit"' +
      (state.loadingLocked || !String(state.query).trim() ? " disabled" : "") +
      ">" +
      escapeHtml(COPY.button) +
      "</button>" +
      "</div>"
    );
  }

  function exampleAndScope(opts) {
    opts = opts || {};
    return (
      '<p class="ac-example">' +
      escapeHtml(COPY.exampleLabel) +
      ' <button type="button" class="ac-example-btn" id="ac-example-btn">' +
      "“" +
      escapeHtml(COPY.exampleText) +
      "”</button>" +
      "</p>" +
      (opts.hideScope
        ? ""
        : '<p class="ac-scope">' + escapeHtml(COPY.scopeNote) + "</p>")
    );
  }

  function isDebugEnabled() {
    try {
      return new URLSearchParams(window.location.search || "").get("aislecheckDebug") === "1";
    } catch (err) {
      return false;
    }
  }

  function renderDebugPanel() {
    if (!isDebugEnabled()) return "";
    var response = state.response;
    if (!response) return "";
    var debug = response.debug || {};
    var open = state.debugOpen ? "" : " hidden";
    return (
      '<details class="ac-debug" id="ac-debug"' +
      (state.debugOpen ? " open" : "") +
      ">" +
      "<summary>Developer debug</summary>" +
      '<div class="ac-debug-body"' +
      open +
      ">" +
      "<pre>" +
      escapeHtml(
        JSON.stringify(
          {
            raw_query: response.original_query,
            normalized_query: response.normalized_query,
            normalizations_applied: response.normalizations_applied,
            extracted: response.extracted,
            matcher: debug.match || {
              status: response.matcher_status,
              selected: response.selected_tracker,
              plausible: response.plausible_trackers,
            },
            routing: debug.routing || {
              next_action: response.next_action,
              clarify_kind: response.clarify_kind,
              clarify_field: response.clarify_field,
            },
            reason_codes: response.reason_codes,
          },
          null,
          2
        )
      ) +
      "</pre>" +
      "</div>" +
      "</details>"
    );
  }

  function renderLoading() {
    return (
      '<div class="ac-state ac-state--loading" role="status" aria-live="polite">' +
      '<p class="ac-loading-text">' +
      escapeHtml(COPY.loading) +
      "</p>" +
      "</div>"
    );
  }

  function renderUnderstood() {
    var r = state.response || {};
    var ex = r.extracted || {};
    var tracker = r.selected_tracker || {};
    var rows = [
      ["Product", tracker.display_name || ex.product_text || "—"],
      ["Price", ex.price_display || "—"],
    ];
    if (ex.promotion_label) rows.push(["Promotion", ex.promotion_label]);
    else if (ex.required_quantity)
      rows.push(["Purchase requirement", "Buy " + ex.required_quantity]);
    if (ex.package_size) rows.push(["Package size", ex.package_size]);
    rows.push([
      "Store",
      ex.retailer
        ? ex.retailer.charAt(0).toUpperCase() + ex.retailer.slice(1)
        : "—",
    ]);
    var list = rows
      .map(function (pair) {
        return (
          "<li><span class=\"ac-ev-label\">" +
          escapeHtml(pair[0]) +
          '</span> <span class="ac-ev-value">' +
          escapeHtml(pair[1]) +
          "</span></li>"
        );
      })
      .join("");
    return (
      '<div class="ac-state ac-state--understood" role="region" aria-label="Understood deal">' +
      '<h3 class="ac-understood-heading">' +
      escapeHtml(COPY.understoodHeading) +
      "</h3>" +
      '<ul class="ac-evidence">' +
      list +
      "</ul>" +
      '<div class="ac-result-actions">' +
      '<button type="button" class="btn btn-primary" id="ac-check-price">' +
      escapeHtml(COPY.checkPrice) +
      "</button>" +
      '<button type="button" class="btn btn-secondary" id="ac-fix-it">' +
      escapeHtml(COPY.fixIt) +
      "</button>" +
      "</div>" +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      renderDebugPanel() +
      "</div>"
    );
  }

  function renderPlaceholder() {
    return (
      '<div class="ac-state ac-state--placeholder" role="region" aria-label="Deal assessment placeholder">' +
      '<p class="ac-placeholder-tag">Still in progress</p>' +
      '<p class="ac-placeholder-text">' +
      escapeHtml(COPY.placeholderVerdict) +
      "</p>" +
      '<div class="ac-result-actions">' +
      '<button type="button" class="btn btn-secondary" id="ac-fix-it">' +
      escapeHtml(COPY.fixIt) +
      "</button>" +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      "</div>" +
      renderDebugPanel() +
      "</div>"
    );
  }

  function formatMoney(value) {
    if (value == null || value === "") return "—";
    var n = Number(value);
    if (!isFinite(n)) return "—";
    return "$" + n.toFixed(2);
  }

  function renderAssessment() {
    var a = state.assessment || {};
    var evidence = a.evidence || {};
    var rows =
      '<dl class="ac-assessment-evidence">' +
      "<div><dt>" +
      escapeHtml(COPY.assessmentUnitPriceLabel) +
      "</dt><dd>" +
      escapeHtml(formatMoney(evidence.comparable_unit_price)) +
      "</dd></div>" +
      "<div><dt>" +
      escapeHtml(COPY.assessmentAtlLabel) +
      "</dt><dd>" +
      escapeHtml(formatMoney(evidence.all_time_low_unit_price)) +
      "</dd></div>" +
      "<div><dt>" +
      escapeHtml(COPY.assessmentMedianLabel) +
      "</dt><dd>" +
      escapeHtml(formatMoney(evidence.median_unit_price)) +
      "</dd></div>" +
      "<div><dt>" +
      escapeHtml(COPY.assessmentWeeksLabel) +
      "</dt><dd>" +
      escapeHtml(
        evidence.observation_count != null ? String(evidence.observation_count) : "—"
      ) +
      "</dd></div>" +
      "</dl>";
    return (
      '<div class="ac-state ac-state--assessed" role="region" aria-label="Deal assessment result">' +
      '<p class="ac-assessment-tag">' +
      escapeHtml(a.verdict_label || a.verdict || "Result") +
      "</p>" +
      '<h3 class="ac-assessment-heading">' +
      escapeHtml(a.headline || "") +
      "</h3>" +
      "<p>" +
      escapeHtml(a.summary || "") +
      "</p>" +
      '<p class="ac-ev-label">' +
      escapeHtml(COPY.assessmentEvidenceLabel) +
      "</p>" +
      rows +
      '<div class="ac-result-actions">' +
      '<button type="button" class="btn btn-secondary" id="ac-fix-it">' +
      escapeHtml(COPY.fixIt) +
      "</button>" +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      "</div>" +
      renderDebugPanel() +
      "</div>"
    );
  }

  function renderAssessing() {
    return (
      '<div class="ac-state ac-state--loading" role="status" aria-live="polite">' +
      '<p class="ac-loading-text">' +
      escapeHtml(COPY.assessing) +
      "</p>" +
      "</div>"
    );
  }

  function renderPreservedQuery() {
    if (!state.query) return "";
    return (
      '<p class="ac-preserved-query"><span class="ac-ev-label">' +
      escapeHtml(COPY.preservedQueryLabel) +
      "</span> " +
      '<span class="ac-ev-value">“' +
      escapeHtml(state.query) +
      "”</span></p>"
    );
  }

  function renderExampleActions(opts) {
    opts = opts || {};
    var canSubmit = readConfig().exampleSubmitEnabled && !!getSupabaseClient();
    var primaryRetry = opts.includeTryAgain === true;
    var parts = [];

    if (state.exampleSubmitted) {
      parts.push(
        '<p class="ac-example-thanks" role="status">' +
          escapeHtml(COPY.exampleSubmitted) +
          "</p>"
      );
      parts.push('<div class="ac-result-actions">');
      if (primaryRetry) {
        parts.push(
          '<button type="button" class="btn btn-primary" id="ac-try-again"' +
            (state.loadingLocked ? " disabled" : "") +
            ">" +
            escapeHtml(COPY.tryAgain) +
            "</button>"
        );
      }
      parts.push(
        '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
          escapeHtml(COPY.checkAnother) +
          "</button>"
      );
      parts.push("</div>");
      return parts.join("");
    }

    if (!canSubmit && !primaryRetry) {
      return (
        '<p class="ac-example-thanks">' +
        escapeHtml(COPY.thanksNoStore) +
        "</p>" +
        '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
        escapeHtml(COPY.checkAnother) +
        "</button>"
      );
    }

    parts.push('<div class="ac-result-actions">');
    if (primaryRetry) {
      parts.push(
        '<button type="button" class="btn btn-primary" id="ac-try-again"' +
          (state.loadingLocked ? " disabled" : "") +
          ">" +
          escapeHtml(COPY.tryAgain) +
          "</button>"
      );
    }
    if (canSubmit) {
      parts.push(
        '<button type="button" class="btn btn-secondary" id="ac-submit-example"' +
          (state.exampleSubmitBusy ? " disabled" : "") +
          ">" +
          escapeHtml(COPY.submitExample) +
          "</button>"
      );
    }
    parts.push(
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
        escapeHtml(COPY.checkAnother) +
        "</button>"
    );
    parts.push("</div>");
    if (canSubmit) {
      parts.push(
        '<p class="ac-privacy-note">' + escapeHtml(COPY.privacyNote) + "</p>"
      );
    }
    return parts.join("");
  }

  function renderAlmostReady() {
    return (
      '<div class="ac-state ac-state--almost-ready" role="region" aria-label="AisleCheck almost ready">' +
      '<h3 class="ac-almost-heading">' +
      escapeHtml(COPY.almostReadyHeading) +
      "</h3>" +
      "<p>" +
      escapeHtml(COPY.almostReadyBody) +
      "</p>" +
      renderPreservedQuery() +
      renderExampleActions({ includeTryAgain: false }) +
      "</div>"
    );
  }

  function renderTemporaryUnavailable() {
    return (
      '<div class="ac-state ac-state--temporary-unavailable" role="region" aria-label="AisleCheck temporarily unavailable">' +
      '<h3 class="ac-temp-heading">' +
      escapeHtml(COPY.temporaryUnavailableHeading) +
      "</h3>" +
      "<p>" +
      escapeHtml(COPY.temporaryUnavailableBody) +
      "</p>" +
      renderPreservedQuery() +
      renderExampleActions({ includeTryAgain: true }) +
      "</div>"
    );
  }

  function renderClarifyField() {
    var r = state.response || {};
    var prompt = r.clarify_prompt || "Can you add a bit more detail?";
    return (
      '<div class="ac-state ac-state--clarify" role="region" aria-label="Clarify deal">' +
      '<h3 class="ac-clarify-heading">' +
      escapeHtml(prompt) +
      "</h3>" +
      '<form class="ac-clarify-form" id="ac-clarify-form">' +
      '<label class="visually-hidden" for="ac-clarify-input">Your answer</label>' +
      '<input type="text" id="ac-clarify-input" class="ac-input" autocomplete="off" value="' +
      escapeHtml(state.clarifyAnswer) +
      '" />' +
      '<button type="submit" class="btn btn-primary">' +
      escapeHtml(COPY.clarifySubmit) +
      "</button>" +
      "</form>" +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      renderDebugPanel() +
      "</div>"
    );
  }

  function renderClarifyProduct() {
    var r = state.response || {};
    var options = (r.plausible_trackers || []).slice(0, 3);
    var opts = options
      .map(function (opt, i) {
        return (
          '<li><button type="button" class="btn btn-secondary ac-clarify-option" data-tracker-id="' +
          escapeHtml(opt.id) +
          '" data-clarify-index="' +
          i +
          '">' +
          escapeHtml(opt.display_name || opt.name || opt.id) +
          "</button></li>"
        );
      })
      .join("");
    return (
      '<div class="ac-state ac-state--clarify" role="region" aria-label="Clarify product">' +
      '<h3 class="ac-clarify-heading">' +
      escapeHtml(r.clarify_prompt || "Which product did you mean?") +
      "</h3>" +
      '<ul class="ac-clarify-list">' +
      opts +
      '<li><button type="button" class="btn btn-ghost ac-clarify-none" id="ac-clarify-none">' +
      escapeHtml(COPY.noneOfThese) +
      "</button></li>" +
      "</ul>" +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      renderDebugPanel() +
      "</div>"
    );
  }

  function renderUnsupported() {
    var r = state.response || {};
    var codes = r.reason_codes || [];
    var loopTerminal = codes.indexOf("clarify_loop_broken") !== -1;
    var heading = loopTerminal ? COPY.clarifyLoopHeading : COPY.unsupportedHeading;
    var body = loopTerminal ? COPY.clarifyLoopBody : COPY.unsupportedBody;
    return (
      '<div class="ac-state ac-state--unsupported" role="region" aria-label="Unsupported product">' +
      '<h3 class="ac-unsupported-heading">' +
      escapeHtml(heading) +
      "</h3>" +
      "<p>" +
      escapeHtml(body) +
      "</p>" +
      (loopTerminal
        ? ""
        : '<button type="button" class="btn btn-primary" id="ac-request-product"' +
          (state.requestedProduct ? " disabled" : "") +
          ">" +
          (state.requestedProduct ? "Requested" : escapeHtml(COPY.requestProduct)) +
          "</button>") +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      renderDebugPanel() +
      "</div>"
    );
  }

  function renderInvalid() {
    return (
      '<div class="ac-state ac-state--invalid" role="region" aria-label="Invalid deal query">' +
      '<h3 class="ac-invalid-heading">' +
      escapeHtml(COPY.invalidHeading) +
      "</h3>" +
      "<p>" +
      escapeHtml(COPY.invalidBody) +
      "</p>" +
      '<button type="button" class="btn btn-primary ac-reset" id="ac-check-another">Try again</button>' +
      renderDebugPanel() +
      "</div>"
    );
  }

  function renderError() {
    return (
      '<div class="ac-state ac-state--error" role="alert">' +
      "<p>" +
      escapeHtml(state.lastError || COPY.thanksNoStore) +
      "</p>" +
      '<button type="button" class="btn btn-primary ac-reset" id="ac-check-another">Try again</button>' +
      "</div>"
    );
  }

  function renderCorrection() {
    var c = state.correction;
    return (
      '<div class="ac-state ac-state--correction" role="region" aria-label="Correct deal details">' +
      '<p class="ac-correction-lead">Adjust the details, then check again.</p>' +
      '<div class="ac-correction-grid">' +
      field("Product", "ac-corr-product", c.product) +
      field("Price", "ac-corr-price", c.price) +
      field("Price basis", "ac-corr-basis", c.priceBasis) +
      field("Promotion", "ac-corr-promo", c.promotion) +
      field("Required quantity", "ac-corr-qty", c.requiredQuantity) +
      field("Package size", "ac-corr-size", c.packageSize) +
      field("Store", "ac-corr-store", c.store) +
      "</div>" +
      '<div class="ac-result-actions">' +
      '<button type="button" class="btn btn-primary" id="ac-correction-submit">Check deal</button>' +
      '<button type="button" class="btn btn-ghost ac-reset" id="ac-check-another">' +
      escapeHtml(COPY.checkAnother) +
      "</button>" +
      "</div>" +
      renderDebugPanel() +
      "</div>"
    );

    function field(label, id, value) {
      return (
        '<label class="ac-corr-field">' +
        '<span class="ac-corr-label">' +
        escapeHtml(label) +
        "</span>" +
        '<input class="ac-input ac-input--sm" id="' +
        id +
        '" type="text" value="' +
        escapeHtml(value) +
        '" />' +
        "</label>"
      );
    }
  }

  function renderBodyPanel() {
    if (state.view === "loading") return renderLoading();
    if (state.view === "understood") return renderUnderstood();
    if (state.view === "placeholder") return renderPlaceholder();
    if (state.view === "assessing") return renderAssessing();
    if (state.view === "assessed") return renderAssessment();
    if (state.view === "almost_ready") return renderAlmostReady();
    if (state.view === "temporary_unavailable") return renderTemporaryUnavailable();
    if (state.view === "clarify_field") return renderClarifyField();
    if (state.view === "clarify_product") return renderClarifyProduct();
    if (state.view === "unsupported") return renderUnsupported();
    if (state.view === "invalid") return renderInvalid();
    if (state.view === "correction") return renderCorrection();
    if (state.view === "error") return renderError();
    return "";
  }

  function brandBlock(extraClass) {
    return (
      '<p class="ac-brand ' +
      (extraClass || "") +
      '">' +
      escapeHtml(COPY.brand) +
      "</p>"
    );
  }

  function headingBlock() {
    return (
      '<h2 class="ac-heading">' +
      escapeHtml(COPY.heading) +
      "</h2>" +
      '<p class="ac-desc">' +
      escapeHtml(COPY.description) +
      "</p>"
    );
  }

  function formShell(inner) {
    if (state.view !== "empty") return renderBodyPanel();
    return (
      '<form class="ac-form" id="ac-form" action="#" method="get">' +
      inner +
      exampleAndScope() +
      "</form>"
    );
  }

  function renderVariation1() {
    return (
      '<section class="ac-panel ac-v1" aria-label="AisleCheck">' +
      brandBlock("ac-brand--sm") +
      headingBlock() +
      formShell(
        sharedFormFields({ hideLabel: true, labelText: COPY.placeholder })
      ) +
      "</section>"
    );
  }

  function renderVariation2() {
    return (
      '<section class="ac-panel ac-v2 ac-card" aria-label="AisleCheck">' +
      brandBlock() +
      headingBlock() +
      formShell(sharedFormFields({ hideLabel: true })) +
      "</section>"
    );
  }

  function renderVariation3() {
    return (
      '<section class="ac-panel ac-v3" aria-label="AisleCheck">' +
      '<div class="ac-v3-row">' +
      '<div class="ac-v3-copy">' +
      brandBlock("ac-brand--inline") +
      '<p class="ac-v3-kicker">' +
      escapeHtml(COPY.heading) +
      " " +
      escapeHtml(COPY.description) +
      "</p>" +
      "</div>" +
      "</div>" +
      formShell(sharedFormFields({ hideLabel: true })) +
      "</section>"
    );
  }

  function renderVariation4() {
    var prompt =
      '<p class="ac-convo-prompt" id="ac-convo-prompt">' +
      escapeHtml(COPY.conversationalPrompt) +
      "</p>";
    return (
      '<section class="ac-panel ac-v4 ac-card ac-card--soft" aria-label="AisleCheck">' +
      brandBlock("ac-brand--soft") +
      headingBlock() +
      formShell(
        sharedFormFields({
          multiline: true,
          hideLabel: true,
          labelText: COPY.conversationalPrompt,
          promptHtml: prompt,
        })
      ) +
      "</section>"
    );
  }

  function renderVariation5() {
    var emptyExtras =
      state.view === "empty"
        ? '<aside class="ac-evidence-preview" aria-label="What you’ll see">' +
          '<p class="ac-preview-label">What you’ll see</p>' +
          '<ul class="ac-evidence ac-evidence--preview">' +
          '<li class="ac-preview-item"><span class="ac-ev-label">Product</span><span class="ac-ev-value ac-ev-value--muted">—</span></li>' +
          '<li class="ac-preview-item"><span class="ac-ev-label">Price</span><span class="ac-ev-value ac-ev-value--muted">—</span></li>' +
          '<li class="ac-preview-item"><span class="ac-ev-label">Promotion</span><span class="ac-ev-value ac-ev-value--muted">—</span></li>' +
          "</ul>" +
          "</aside>"
        : "";
    return (
      '<section class="ac-panel ac-v5" aria-label="AisleCheck">' +
      brandBlock() +
      headingBlock() +
      emptyExtras +
      formShell(sharedFormFields({ hideLabel: true })) +
      "</section>"
    );
  }

  function renderVariation6() {
    return (
      '<section class="ac-panel ac-v6 ac-tool" aria-label="AisleCheck">' +
      '<div class="ac-tool-header">' +
      iconCheckSvg() +
      '<div class="ac-tool-titles">' +
      '<p class="ac-brand ac-brand--wordmark">' +
      escapeHtml(COPY.brand) +
      "</p>" +
      '<p class="ac-tool-sub">Scrolling the Aisle</p>' +
      "</div>" +
      "</div>" +
      '<h2 class="ac-heading ac-heading--tool">' +
      escapeHtml(COPY.heading) +
      "</h2>" +
      '<p class="ac-desc">' +
      escapeHtml(COPY.description) +
      "</p>" +
      formShell(sharedFormFields({ hideLabel: true })) +
      "</section>"
    );
  }

  var RENDERERS = [
    renderVariation1,
    renderVariation2,
    renderVariation3,
    renderVariation4,
    renderVariation5,
    renderVariation6,
  ];

  function renderSwitcher() {
    var meta = VARIATION_META[state.variant - 1];
    var buttons = VARIATION_META.map(function (v) {
      var selected = v.id === state.variant;
      return (
        '<button type="button" class="ac-switch-btn' +
        (selected ? " is-active" : "") +
        '" role="radio" aria-checked="' +
        (selected ? "true" : "false") +
        '" data-variant="' +
        v.id +
        '" id="ac-switch-' +
        v.id +
        '">' +
        escapeHtml(v.name) +
        "</button>"
      );
    }).join("");

    return (
      '<div class="ac-proto-toolbar" id="ac-proto-toolbar" role="region" aria-label="AisleCheck prototype controls">' +
      '<div class="ac-proto-toolbar-main">' +
      '<p class="ac-proto-title">AisleCheck prototype</p>' +
      '<div class="ac-switcher" role="radiogroup" aria-label="Design variation">' +
      buttons +
      "</div>" +
      '<button type="button" class="btn btn-sm btn-secondary" id="ac-copy-link">Copy variation link</button>' +
      '<button type="button" class="btn btn-sm btn-ghost" id="ac-toggle-notes" aria-expanded="false" aria-controls="ac-notes-panel">Notes</button>' +
      "</div>" +
      '<div class="ac-notes-panel" id="ac-notes-panel" hidden>' +
      "<p><strong>" +
      escapeHtml(meta.name) +
      ":</strong> " +
      escapeHtml(meta.title) +
      "</p>" +
      "<p><strong>Intent:</strong> " +
      escapeHtml(meta.intent) +
      "</p>" +
      "<p><strong>Advantage:</strong> " +
      escapeHtml(meta.advantage) +
      "</p>" +
      "<p><strong>Risk:</strong> " +
      escapeHtml(meta.risk) +
      "</p>" +
      "<p><strong>Expected behavior:</strong> " +
      escapeHtml(meta.expectedBehavior) +
      "</p>" +
      "<p><strong>Mobile:</strong> " +
      escapeHtml(meta.mobile) +
      "</p>" +
      "<p><strong>Backend:</strong> deterministic shopper_query via /api/aislecheck (no LLM).</p>" +
      "</div>" +
      '<p class="ac-proto-hint" id="ac-copy-status" role="status" aria-live="polite"></p>' +
      "</div>"
    );
  }

  function syncUrl(variant) {
    if (!isProtoControlsEnabled(window.location.search)) return;
    try {
      var url = new URL(window.location.href);
      url.searchParams.set("aislecheckVariant", String(variant));
      window.history.replaceState({}, "", url.pathname + url.search + url.hash);
    } catch (err) {
      /* ignore */
    }
  }

  function rememberVariant(variant) {
    if (!isProtoControlsEnabled(window.location.search)) return;
    try {
      window.sessionStorage.setItem(STORAGE_KEY, String(variant));
    } catch (err) {
      /* ignore */
    }
  }

  function readInputValue() {
    var el = document.getElementById("ac-deal-input");
    return el ? el.value : state.query;
  }

  function persistQueryFromDom() {
    state.query = readInputValue();
  }

  function setVariant(next) {
    persistQueryFromDom();
    state.variant = parseVariantParam(next);
    rememberVariant(state.variant);
    syncUrl(state.variant);
    render();
  }

  function resetToEmpty() {
    state.view = "empty";
    state.loadingLocked = false;
    state.requestedProduct = false;
    state.exampleSubmitted = false;
    state.exampleSubmitBusy = false;
    state.exampleClientSubmissionId = null;
    state.response = null;
    state.assessment = null;
    state.clarifyAnswer = "";
    state.clarifyDigests = [];
    state.lastError = "";
    state.fieldsCorrected = [];
    render();
    var input = document.getElementById("ac-deal-input");
    if (input) input.focus();
  }

  function showAlmostReady() {
    state.loadingLocked = false;
    state.view = "almost_ready";
    state.response = null;
    state.lastError = "";
    render();
    // Preserve the typed query; Check another clears back to empty.
  }

  function showTemporaryUnavailable() {
    state.loadingLocked = false;
    state.view = "temporary_unavailable";
    state.response = null;
    state.lastError = "";
    render();
  }

  function applyResponse(response) {
    state.response = response;
    state.assessment = null;
    state.view = viewFromResponse(response);
    state.loadingLocked = false;
    state.correction = correctionFromResponse(response);
    if (response && response.clarify_fingerprint) {
      var digests = state.clarifyDigests || [];
      if (digests.indexOf(response.clarify_fingerprint) === -1) {
        digests = digests.concat([response.clarify_fingerprint]).slice(-8);
      }
      state.clarifyDigests = digests;
    } else if (response && response.next_action === "continue") {
      state.clarifyDigests = [];
    }
    render();
  }

  function startAssess() {
    if (state.loadingLocked) return;
    var response = state.response || {};
    var tracker = response.selected_tracker || {};
    var extracted = response.extracted || {};
    var trackerId = tracker.id || tracker.tracker_id || "";
    if (!trackerId) {
      state.view = "placeholder";
      render();
      return;
    }
    if (!isAssessEnabled()) {
      logEvent("check_price_placeholder", {
        user_confirmed: true,
        final_confirmed_interpretation: {
          extracted: extracted,
          selected_tracker: tracker,
        },
      });
      state.view = "placeholder";
      render();
      return;
    }

    var submittedOffer = {
      price: extracted.price,
      price_basis: extracted.price_basis,
      required_quantity: extracted.required_quantity,
      promotion_type: extracted.promotion_type,
      package_size: extracted.package_size,
      product_text: extracted.product_text,
      retailer: extracted.retailer,
    };
    var retailer =
      extracted.retailer ||
      (state.correction && state.correction.store) ||
      "Safeway";

    state.view = "assessing";
    state.loadingLocked = true;
    state.assessment = null;
    render();

    logEvent("check_price_assess", {
      user_confirmed: true,
      final_confirmed_interpretation: {
        extracted: extracted,
        selected_tracker: tracker,
      },
    });

    postJson(apiUrl(ASSESS_PATH), {
      tracker_id: trackerId,
      retailer: retailer,
      submitted_offer: submittedOffer,
      session_id: getSessionId(),
    })
      .then(function (assessment) {
        state.assessment = assessment;
        state.view = "assessed";
        state.loadingLocked = false;
        render();
      })
      .catch(function () {
        state.loadingLocked = false;
        // Live assess path failed — reuse temporary-unavailable recovery.
        if (isLiveApiEnabled()) {
          showTemporaryUnavailable();
        } else {
          state.view = "placeholder";
          render();
        }
      });
  }

  function startCheck(query, opts) {
    opts = opts || {};
    var q = String(query || "").trim();
    if (!q || state.loadingLocked) return;
    if (q.length > MAX_QUERY_CHARS) {
      state.query = q.slice(0, MAX_QUERY_CHARS);
      q = state.query;
    }
    state.query = q;
    state.view = "loading";
    state.loadingLocked = true;
    state.requestedProduct = false;
    state.exampleSubmitted = false;
    state.exampleClientSubmissionId = null;
    state.assessment = null;
    state.lastError = "";
    state.clarifyAnswer = "";
    if (opts.fieldsCorrected) {
      state.fieldsCorrected = opts.fieldsCorrected;
    } else {
      // Fresh submit — drop prior clarify fingerprints.
      state.clarifyDigests = [];
      state.fieldsCorrected = [];
    }
    render();

    if (!isLiveApiEnabled()) {
      // Launch-preview path: never store the query here. Opt-in submit is separate.
      showAlmostReady();
      return;
    }

    postJson(apiUrl(DEFAULT_API_PATH), {
      query: q,
      session_id: getSessionId(),
      apply_normalization: true,
      prior_clarify_digests: state.clarifyDigests || [],
    })
      .then(function (response) {
        applyResponse(response);
      })
      .catch(function () {
        // Preserve query; temporary outage/cold-start — no fake interpretation.
        showTemporaryUnavailable();
      });
  }

  function bindPanelEvents(root) {
    var form = root.querySelector("#ac-form");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        persistQueryFromDom();
        startCheck(state.query);
      });
    }

    var input = root.querySelector("#ac-deal-input");
    if (input) {
      input.addEventListener("input", function () {
        state.query = input.value;
        var btn = root.querySelector("#ac-submit");
        if (btn) btn.disabled = state.loadingLocked || !String(state.query).trim();
      });
    }

    var exampleBtn = root.querySelector("#ac-example-btn");
    if (exampleBtn) {
      exampleBtn.addEventListener("click", function () {
        state.query = EXAMPLE_QUERY;
        var el = root.querySelector("#ac-deal-input");
        if (el) {
          el.value = EXAMPLE_QUERY;
          el.focus();
        }
        var btn = root.querySelector("#ac-submit");
        if (btn) btn.disabled = false;
      });
    }

    root.querySelectorAll(".ac-reset").forEach(function (btn) {
      btn.addEventListener("click", resetToEmpty);
    });

    var checkPrice = root.querySelector("#ac-check-price");
    if (checkPrice) {
      checkPrice.addEventListener("click", function () {
        startAssess();
      });
    }

    var fixBtn = root.querySelector("#ac-fix-it");
    if (fixBtn) {
      fixBtn.addEventListener("click", function () {
        if (state.response) {
          state.correction = correctionFromResponse(state.response);
        }
        state.view = "correction";
        render();
      });
    }

    var corrSubmit = root.querySelector("#ac-correction-submit");
    if (corrSubmit) {
      corrSubmit.addEventListener("click", function () {
        var next = {
          product: valueOf("ac-corr-product", state.correction.product),
          price: valueOf("ac-corr-price", state.correction.price),
          priceBasis: valueOf("ac-corr-basis", state.correction.priceBasis),
          promotion: valueOf("ac-corr-promo", state.correction.promotion),
          requiredQuantity: valueOf("ac-corr-qty", state.correction.requiredQuantity),
          packageSize: valueOf("ac-corr-size", state.correction.packageSize),
          store: valueOf("ac-corr-store", state.correction.store),
        };
        var corrected = [];
        Object.keys(next).forEach(function (key) {
          if (String(next[key]) !== String(state.correction[key] || "")) {
            corrected.push(key);
          }
        });
        state.correction = next;
        state.query = buildQueryFromCorrection(next);
        logEvent("correction_submit", {
          fields_corrected: corrected,
          user_confirmed: false,
        });
        startCheck(state.query, { fieldsCorrected: corrected });
      });
    }

    var clarifyForm = root.querySelector("#ac-clarify-form");
    if (clarifyForm) {
      clarifyForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var answerEl = root.querySelector("#ac-clarify-input");
        var answer = answerEl ? String(answerEl.value || "").trim() : "";
        if (!answer) return;
        state.clarifyAnswer = answer;
        var field = (state.response && state.response.clarify_field) || "detail";
        var merged = String(state.query || "").trim() + " " + answer;
        logEvent("clarify_field_answer", {
          fields_corrected: [field],
          user_confirmed: false,
        });
        startCheck(merged, { fieldsCorrected: [field] });
      });
    }

    root.querySelectorAll("[data-tracker-id]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var id = btn.getAttribute("data-tracker-id") || "";
        var label = btn.textContent || id;
        var merged =
          String(state.query || "").trim() +
          " (" +
          label.replace(/\s·\s.*/, "") +
          ")";
        logEvent("clarify_product_select", {
          user_confirmed: true,
          final_confirmed_interpretation: {
            selected_tracker_id: id,
            selected_label: label,
          },
        });
        // Re-run with the chosen product name for a cleaner parse.
        var productName = label.split("·")[0].trim();
        var priceBit = "";
        var ex = (state.response && state.response.extracted) || {};
        if (ex.price_display) priceBit = " " + ex.price_display;
        var qtyBit = ex.required_quantity
          ? " when you buy " + ex.required_quantity
          : "";
        var storeBit = ex.retailer ? " at " + ex.retailer : " at Safeway";
        startCheck(productName + priceBit + qtyBit + storeBit, {
          fieldsCorrected: ["product"],
        });
        void merged;
      });
    });

    var noneBtn = root.querySelector("#ac-clarify-none");
    if (noneBtn) {
      noneBtn.addEventListener("click", function () {
        logEvent("clarify_product_none", { user_confirmed: false });
        state.view = "unsupported";
        if (state.response) {
          state.response = Object.assign({}, state.response, {
            next_action: "unsupported",
            reason_codes: (state.response.reason_codes || []).concat([
              "user_rejected_candidates",
            ]),
          });
        }
        render();
      });
    }

    var requestBtn = root.querySelector("#ac-request-product");
    if (requestBtn) {
      requestBtn.addEventListener("click", function () {
        state.requestedProduct = true;
        logEvent("request_product", { user_confirmed: false });
        render();
      });
    }

    var tryAgainBtn = root.querySelector("#ac-try-again");
    if (tryAgainBtn) {
      tryAgainBtn.addEventListener("click", function () {
        if (state.loadingLocked) return;
        startCheck(state.query);
      });
    }

    var submitExampleBtn = root.querySelector("#ac-submit-example");
    if (submitExampleBtn) {
      submitExampleBtn.addEventListener("click", function () {
        if (state.exampleSubmitBusy || state.exampleSubmitted) return;
        state.exampleSubmitBusy = true;
        render();
        submitExampleOptIn(state.query)
          .then(function () {
            state.exampleSubmitted = true;
            state.exampleSubmitBusy = false;
            render();
          })
          .catch(function () {
            state.exampleSubmitBusy = false;
            // Storage failed — stay friendly, keep query, no silent retry loop.
            state.exampleSubmitted = false;
            render();
            var note = root.querySelector(".ac-privacy-note");
            if (note) {
              note.textContent = COPY.thanksNoStore;
            }
          });
      });
    }

    var debug = root.querySelector("#ac-debug");
    if (debug) {
      debug.addEventListener("toggle", function () {
        state.debugOpen = debug.open;
      });
    }

    function valueOf(id, fallback) {
      var el = root.querySelector("#" + id);
      return el ? el.value : fallback;
    }
  }

  function bindToolbarEvents(toolbar) {
    toolbar.querySelectorAll("[data-variant]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setVariant(btn.getAttribute("data-variant"));
      });
    });

    var switcher = toolbar.querySelector(".ac-switcher");
    if (switcher) {
      switcher.addEventListener("keydown", function (e) {
        var keys = ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown", "Home", "End"];
        if (keys.indexOf(e.key) === -1) return;
        e.preventDefault();
        var buttons = Array.prototype.slice.call(
          switcher.querySelectorAll("[data-variant]")
        );
        var idx = buttons.findIndex(function (b) {
          return b.getAttribute("aria-checked") === "true";
        });
        if (e.key === "Home") idx = 0;
        else if (e.key === "End") idx = buttons.length - 1;
        else if (e.key === "ArrowLeft" || e.key === "ArrowUp")
          idx = (idx - 1 + buttons.length) % buttons.length;
        else idx = (idx + 1) % buttons.length;
        buttons[idx].focus();
        setVariant(buttons[idx].getAttribute("data-variant"));
      });
    }

    var notesBtn = toolbar.querySelector("#ac-toggle-notes");
    var notesPanel = toolbar.querySelector("#ac-notes-panel");
    if (notesBtn && notesPanel) {
      notesBtn.addEventListener("click", function () {
        var open = notesPanel.hasAttribute("hidden");
        if (open) notesPanel.removeAttribute("hidden");
        else notesPanel.setAttribute("hidden", "");
        notesBtn.setAttribute("aria-expanded", open ? "true" : "false");
      });
    }

    var copyBtn = toolbar.querySelector("#ac-copy-link");
    var status = toolbar.querySelector("#ac-copy-status");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        var url =
          window.location.origin +
          window.location.pathname +
          "?aislecheckVariant=" +
          state.variant;
        function done(ok) {
          if (status) status.textContent = ok ? "Copied: " + url : "Could not copy link";
        }
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(
            function () {
              done(true);
            },
            function () {
              done(false);
            }
          );
        } else {
          done(false);
        }
      });
    }
  }

  function render() {
    var mount = document.getElementById("aislecheck-root");
    var toolbarHost = document.getElementById("aislecheck-toolbar-host");
    if (!mount) return;

    document.body.classList.add("ac-public");
    document.body.setAttribute("data-aislecheck-variant", String(state.variant));

    var renderer = RENDERERS[state.variant - 1] || RENDERERS[PUBLIC_VARIANT - 1];
    mount.hidden = false;
    mount.innerHTML = renderer();
    bindPanelEvents(mount);

    if (isProtoControlsEnabled(window.location.search)) {
      if (!toolbarHost) {
        toolbarHost = document.createElement("div");
        toolbarHost.id = "aislecheck-toolbar-host";
        document.body.appendChild(toolbarHost);
      }
      toolbarHost.innerHTML = renderSwitcher();
      bindToolbarEvents(toolbarHost);
      document.body.classList.add("ac-prototype-active");
    } else if (toolbarHost) {
      toolbarHost.innerHTML = "";
      document.body.classList.remove("ac-prototype-active");
    }

    if (state.view === "empty") {
      var input = mount.querySelector("#ac-deal-input");
      if (input && state.query && input.value !== state.query) {
        input.value = state.query;
      }
    }
  }

  function mountAisleCheck() {
    var stored = null;
    try {
      stored = window.sessionStorage.getItem(STORAGE_KEY);
    } catch (err) {
      stored = null;
    }
    state.variant = resolveInitialVariant(window.location.search, stored);
    rememberVariant(state.variant);
    syncUrl(state.variant);
    getSessionId();
    render();
  }

  // Expose for tests (Node / browser)
  window.AisleCheckPrototype = {
    isPrototypeHost: isPrototypeHost,
    isLocalHost: isLocalHost,
    isProtoControlsEnabled: isProtoControlsEnabled,
    parseVariantParam: parseVariantParam,
    resolveInitialVariant: resolveInitialVariant,
    viewFromResponse: viewFromResponse,
    correctionFromResponse: correctionFromResponse,
    buildQueryFromCorrection: buildQueryFromCorrection,
    isDebugEnabled: isDebugEnabled,
    PUBLIC_VARIANT: PUBLIC_VARIANT,
    readConfig: readConfig,
    apiUrl: apiUrl,
    isLiveApiEnabled: isLiveApiEnabled,
    isAssessEnabled: isAssessEnabled,
    VARIATION_META: VARIATION_META,
    COPY: COPY,
    EXAMPLE_QUERY: EXAMPLE_QUERY,
    API_URL: DEFAULT_API_PATH,
    ASSESS_PATH: ASSESS_PATH,
    getState: function () {
      return state;
    },
    // Test helper: snapshot of mutable UI state (getState returns a live reference).
    snapshotState: function () {
      return {
        view: state.view,
        query: state.query,
        loadingLocked: state.loadingLocked,
        exampleSubmitted: state.exampleSubmitted,
        exampleSubmitBusy: state.exampleSubmitBusy,
        response: state.response,
        assessment: state.assessment,
      };
    },
    resetToEmpty: resetToEmpty,
    applyResponse: applyResponse,
    showAlmostReady: showAlmostReady,
    showTemporaryUnavailable: showTemporaryUnavailable,
    startCheck: startCheck,
    startAssess: startAssess,
    submitExampleOptIn: submitExampleOptIn,
    renderTemporaryUnavailable: renderTemporaryUnavailable,
    renderAlmostReady: renderAlmostReady,
    renderAssessment: renderAssessment,
    API_TIMEOUT_MS: API_TIMEOUT_MS,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAisleCheck);
  } else {
    mountAisleCheck();
  }
})();
