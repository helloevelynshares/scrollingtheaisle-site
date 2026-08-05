/**
 * Node harness for AisleCheck temporary-failure vs disabled-fallback behavior.
 * Invoked by tests/test_aislecheck_prototype.py
 *
 * Usage: node tests/aislecheck_fallback_harness.cjs path/to/aislecheck.js [path/to/aislecheck.css]
 *
 * IMPORTANT: API.getState() returns the live state object. Snapshot primitive
 * fields immediately after each wait — later steps mutate the same object.
 */
const fs = require("fs");
const vm = require("vm");

const jsPath = process.argv[2];
const cssPath = process.argv[3] || null;
if (!jsPath) {
  console.error(
    "Usage: node aislecheck_fallback_harness.cjs <aislecheck.js> [aislecheck.css]"
  );
  process.exit(2);
}

const code = fs.readFileSync(jsPath, "utf8");
const css = cssPath ? fs.readFileSync(cssPath, "utf8") : "";

const fetchCalls = [];
const rpcCalls = [];

const document = {
  readyState: "complete",
  body: {
    classList: { add() {}, remove() {} },
    setAttribute() {},
    appendChild() {},
  },
  getElementById() {
    return null;
  },
  addEventListener() {},
  createElement() {
    return { appendChild() {} };
  },
  head: { appendChild() {} },
  querySelector() {
    return null;
  },
};

const sessionStore = {};
const windowObj = {
  location: {
    hostname: "scrollingtheaisle.com",
    protocol: "https:",
    search: "",
    href: "https://scrollingtheaisle.com/",
    pathname: "/",
    hash: "",
    origin: "https://scrollingtheaisle.com",
  },
  history: { replaceState() {} },
  sessionStorage: {
    getItem(k) {
      return sessionStore[k] || null;
    },
    setItem(k, v) {
      sessionStore[k] = String(v);
    },
  },
  setTimeout,
  clearTimeout,
  AbortController,
  __AISLECHECK_CONFIG__: {
    apiBaseUrl: "https://aislecheck-api.onrender.com",
    liveApiEnabled: true,
    exampleSubmitEnabled: true,
  },
  fetch(url, init) {
    fetchCalls.push({
      url: String(url),
      method: (init && init.method) || "GET",
      body: init && init.body,
    });
    return Promise.reject(new Error("network_down"));
  },
  supabase: {
    createClient() {
      return {
        rpc(name, args) {
          rpcCalls.push({ name, args });
          return Promise.resolve({ data: { ok: true }, error: null });
        },
      };
    },
  },
  AisleCheckPrototype: undefined,
};
windowObj.window = windowObj;
windowObj.document = document;

const sandbox = {
  window: windowObj,
  document,
  URL,
  URLSearchParams,
  Number,
  String,
  Array,
  Object,
  parseInt,
  setTimeout,
  clearTimeout,
  console,
  Math,
  Date,
  Promise,
  AbortController,
  DOMException,
  fetch: (...args) => windowObj.fetch(...args),
};

vm.runInNewContext(code + "\n;this.API = window.AisleCheckPrototype;", sandbox);
const API = sandbox.API;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function waitView(pred, ms = 800) {
  const start = Date.now();
  while (Date.now() - start < ms) {
    const s = API.getState();
    if (pred(s)) return s;
    await sleep(10);
  }
  return API.getState();
}

function snapState(s) {
  return {
    view: s.view,
    query: s.query,
    response: s.response,
    loadingLocked: s.loadingLocked,
  };
}

const continueResponse = {
  original_query: "Doritos are $2.49 each when I buy four",
  normalized_query: "Doritos are $2.49 each when I buy four",
  next_action: "continue",
  matcher_status: "matched",
  selected_tracker: {
    tracker_id: "doritos_nacho_cheese",
    display_name: "Doritos",
  },
  extracted: { product: "Doritos", price: 2.49, store: "Safeway" },
  missing_fields: [],
  reason_codes: [],
};

(async () => {
  const q = "Doritos are $2.49 each when I buy four";

  // Live enabled + network failure => temporary unavailable
  windowObj.__AISLECHECK_CONFIG__.liveApiEnabled = true;
  windowObj.__AISLECHECK_CONFIG__.exampleSubmitEnabled = true;
  delete windowObj.__AISLECHECK_CONFIG__.apiTimeoutMs;
  fetchCalls.length = 0;
  rpcCalls.length = 0;
  API.resetToEmpty();
  const liveBefore = API.isLiveApiEnabled();
  API.startCheck(q);
  const afterFail = snapState(
    await waitView(
      (s) => s.view === "temporary_unavailable" || s.view === "almost_ready"
    )
  );
  const failHtml = API.renderTemporaryUnavailable();
  const almostHtmlAtFail = API.renderAlmostReady();
  const failFetchCount = fetchCalls.length;
  const failRpcCount = rpcCalls.length;

  // Live enabled + client timeout => temporary unavailable
  fetchCalls.length = 0;
  rpcCalls.length = 0;
  API.resetToEmpty();
  windowObj.__AISLECHECK_CONFIG__.apiTimeoutMs = 40;
  windowObj.fetch = (url, init) => {
    fetchCalls.push({
      url: String(url),
      method: (init && init.method) || "GET",
      body: init && init.body,
    });
    return new Promise((_resolve, reject) => {
      const signal = init && init.signal;
      if (!signal) {
        reject(new Error("missing_abort_signal"));
        return;
      }
      if (signal.aborted) {
        reject(new DOMException("Aborted", "AbortError"));
        return;
      }
      signal.addEventListener("abort", () => {
        reject(new DOMException("Aborted", "AbortError"));
      });
    });
  };
  API.startCheck(q);
  const afterTimeout = snapState(
    await waitView((s) => s.view === "temporary_unavailable", 500)
  );
  delete windowObj.__AISLECHECK_CONFIG__.apiTimeoutMs;

  // Duplicate retries blocked while loading
  fetchCalls.length = 0;
  API.resetToEmpty();
  windowObj.__AISLECHECK_CONFIG__.apiTimeoutMs = 60000;
  windowObj.fetch = (url, init) => {
    fetchCalls.push({
      url: String(url),
      method: (init && init.method) || "GET",
      body: init && init.body,
    });
    return new Promise(() => {});
  };
  API.startCheck(q);
  API.startCheck(q);
  API.startCheck(q);
  const lockedCalls = fetchCalls.length;
  const locked = API.getState().loadingLocked === true;
  delete windowObj.__AISLECHECK_CONFIG__.apiTimeoutMs;
  API.showTemporaryUnavailable();
  const preserved = String(API.getState().query || "");

  // Retry reuses same query; query preserved after repeated failure
  fetchCalls.length = 0;
  windowObj.fetch = (url, init) => {
    fetchCalls.push({
      url: String(url),
      method: (init && init.method) || "GET",
      body: init && init.body,
    });
    return Promise.reject(new Error("still_down"));
  };
  API.startCheck(preserved);
  const afterRetry = snapState(
    await waitView((s) => s.view === "temporary_unavailable")
  );
  const retryBodies = fetchCalls.map((c) => {
    try {
      return JSON.parse(c.body || "{}").query;
    } catch (e) {
      return null;
    }
  });

  // Successful retry renders normal understood flow
  fetchCalls.length = 0;
  rpcCalls.length = 0;
  windowObj.fetch = (url, init) => {
    fetchCalls.push({
      url: String(url),
      method: (init && init.method) || "GET",
      body: init && init.body,
    });
    return Promise.resolve({
      ok: true,
      json: async () => continueResponse,
    });
  };
  API.startCheck(preserved);
  const afterSuccess = snapState(
    await waitView((s) => s.view === "understood")
  );

  // Explicit opt-in example submit (no auto-store before this)
  const autoStoreCount = rpcCalls.length;
  rpcCalls.length = 0;
  API.showTemporaryUnavailable();
  await API.submitExampleOptIn(API.getState().query);
  const optInRpc = rpcCalls[0];

  // Live disabled => almost ready, no Try again, no network
  windowObj.__AISLECHECK_CONFIG__.liveApiEnabled = false;
  fetchCalls.length = 0;
  rpcCalls.length = 0;
  API.resetToEmpty();
  API.startCheck(q);
  const disabledState = snapState(
    await waitView((s) => s.view === "almost_ready")
  );
  const almostHtml = API.renderAlmostReady();
  const tempHtml = failHtml;

  const mobileCss =
    !css ||
    (css.includes("@media (max-width: 639px)") &&
      css.includes(".ac-result-actions .btn") &&
      css.includes("width: 100%") &&
      css.includes(".ac-state--temporary-unavailable .ac-result-actions") &&
      css.includes("flex-wrap: wrap"));

  const out = {
    liveBefore,
    failView: afterFail.view,
    failQuery: afterFail.query,
    failFetchCount,
    failRpcCount,
    failHasTempCopy:
      tempHtml.includes("We couldn’t check that deal right now") &&
      tempHtml.includes("waking up"),
    failHasTryAgain:
      tempHtml.includes('id="ac-try-again"') && tempHtml.includes("Try again"),
    failTryIsPrimary: tempHtml.includes(
      'class="btn btn-primary" id="ac-try-again"'
    ),
    failSubmitSecondary:
      tempHtml.includes("btn-secondary") &&
      tempHtml.includes("Submit as an example"),
    failNoVerdict:
      !tempHtml.includes("Good deal") &&
      !tempHtml.includes("Here’s what AisleCheck understood"),
    failNoAutoStore: autoStoreCount === 0 && failRpcCount === 0,
    timeoutView: afterTimeout.view,
    timeoutQuery: afterTimeout.query,
    timeoutNoVerdict: afterTimeout.response == null,
    lockedCalls,
    locked,
    retryBodies,
    retryView: afterRetry.view,
    retryQuery: afterRetry.query,
    successView: afterSuccess.view,
    successHasTracker: !!(
      afterSuccess.response && afterSuccess.response.selected_tracker
    ),
    optInRpcName: optInRpc && optInRpc.name,
    optInQuery: optInRpc && optInRpc.args && optInRpc.args.p_query,
    disabledView: disabledState.view,
    disabledFetchCalls: fetchCalls.length,
    disabledHasAlmost: almostHtml.includes("AisleCheck is almost ready"),
    disabledNoTryAgain: !almostHtml.includes('id="ac-try-again"'),
    disabledHasSubmit: almostHtml.includes("Submit as an example"),
    disabledNoVerdict:
      !almostHtml.includes("Good deal") &&
      !almostHtml.includes("Here’s what AisleCheck understood"),
    optInCopy: API.COPY.submitExample === "Submit as an example",
    privacy: API.COPY.privacyNote.includes(
      "Don’t include personal information"
    ),
    almostHtmlAtFailHasNoTry: !almostHtmlAtFail.includes('id="ac-try-again"'),
    mobileCss,
    hasClientTimeout:
      code.includes("API_TIMEOUT_MS") && code.includes("AbortController"),
  };
  process.stdout.write(JSON.stringify(out));
  process.exit(0);
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
