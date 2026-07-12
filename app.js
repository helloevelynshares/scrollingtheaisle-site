const SUPABASE_URL = "https://wurmdtqysegytsjcudve.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_8Wt-it-oIHHIkQOi0D9y_g_qMoH51ZX";

function getSupabaseProjectRef() {
  const match = SUPABASE_URL.match(/https:\/\/([^.]+)\.supabase\.co/);
  return match ? match[1] : null;
}

/** Override for local: http://127.0.0.1:54321/functions/v1/analyze-find-photo */
const ANALYZE_PHOTO_ENDPOINT = (() => {
  const ref = getSupabaseProjectRef();
  return ref
    ? `https://${ref}.functions.supabase.co/analyze-find-photo`
    : "YOUR_ANALYZE_PHOTO_ENDPOINT";
})();

const VISITOR_ID_KEY = "sta_visitor_id";
const MAX_PHOTO_BYTES = 8 * 1024 * 1024;
const ALLOWED_PHOTO_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
const CONFIDENCE_THRESHOLDS = { item_name: 0.7, price: 0.7, store_name: 0.6 };

let supabaseClient = null;
let selectedPhotoFile = null;
let previewObjectUrl = null;
let aiExtractionState = null;
let isAnalyzingPhoto = false;
let photoAnalyzeGeneration = 0;
let loadFindsGeneration = 0;
const fieldTouched = {
  item_name: false,
  price: false,
  store_name: false,
  location_label: false,
  notes: false,
};

function getSupabase() {
  if (!supabaseClient && window.supabase) {
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return supabaseClient;
}

function getVisitorId() {
  let id = localStorage.getItem(VISITOR_ID_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(VISITOR_ID_KEY, id);
  }
  return id;
}

function getStagingLiveFindsBase() {
  const match = window.location.pathname.match(/^(.*\/staging-live-finds)\/?/);
  return match ? `${match[1]}/` : null;
}

function getSubmitPageUrl() {
  const stagingBase = getStagingLiveFindsBase();
  return stagingBase ? `${stagingBase}submit.html` : "submit.html";
}

function getFindsFeedAfterPostUrl() {
  const stagingBase = getStagingLiveFindsBase();
  return stagingBase ? `${stagingBase}?submitted=1` : "finds.html?submitted=1";
}

function escapeHtml(text) {
  if (text == null || text === "") return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function formatPrice(price) {
  const num = Number(price);
  if (Number.isNaN(num)) return "$0.00";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);
}

function displayFindPrice(find) {
  if (find.price_display) return find.price_display;
  if (find.price != null && find.price !== "") return formatPrice(find.price);
  return "";
}

function isAnalyzeEndpointConfigured() {
  return Boolean(
    ANALYZE_PHOTO_ENDPOINT && !ANALYZE_PHOTO_ENDPOINT.includes("YOUR_ANALYZE_PHOTO_ENDPOINT")
  );
}

function parsePriceNumeric(priceText) {
  if (!priceText) return 0;
  const dollarMatches = [...String(priceText).matchAll(/\$(\d+(?:\.\d{1,2})?)/g)].map((m) =>
    parseFloat(m[1])
  );
  if (dollarMatches.length > 0) {
    return Math.min(...dollarMatches.filter((n) => Number.isFinite(n)));
  }
  const plain = parseFloat(String(priceText).replace(/[^0-9.]/g, ""));
  return Number.isFinite(plain) ? plain : 0;
}

function normalizeStoreName(store) {
  const s = String(store || "").trim();
  if (!s || /^unknown$/i.test(s)) return "";
  return s;
}

function timeAgo(dateString) {
  const then = new Date(dateString).getTime();
  const now = Date.now();
  const seconds = Math.floor((now - then) / 1000);

  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "1 day ago";
  return `${days} days ago`;
}

function formatSubmitError(err) {
  const msg = err?.message || "";
  if (msg.includes("Bucket not found")) {
    return "Photo storage isn’t set up yet. In Supabase, create a public bucket named find-photos (see README), or submit without a photo.";
  }
  if (msg.includes("Could not find the table") && msg.includes("finds")) {
    return "Database tables aren’t set up yet. Run the SQL in README.md in Supabase → SQL Editor.";
  }
  return msg || "Something went wrong. Please try again.";
}

async function uploadFindPhoto(file) {
  const supabase = getSupabase();
  const visitorId = getVisitorId();
  const ext = (file.name.split(".").pop() || "jpg").toLowerCase();
  const path = `${visitorId}/${crypto.randomUUID()}.${ext}`;

  const { error } = await supabase.storage.from("find-photos").upload(path, file, {
    cacheControl: "3600",
    upsert: false,
  });

  if (error) {
    const e = new Error(formatSubmitError(error));
    e.cause = error;
    throw e;
  }

  const { data } = supabase.storage.from("find-photos").getPublicUrl(path);
  return data.publicUrl;
}

async function submitFind(event) {
  event.preventDefault();

  const form = event.target;
  const statusEl = document.getElementById("submit-status");
  const submitBtn = document.getElementById("submit-btn") || form.querySelector('button[type="submit"]');

  if (isAnalyzingPhoto) return;

  photoAnalyzeGeneration += 1;

  const itemName = form.item_name.value.trim();
  const priceDisplay = form.price.value.trim();
  const storeName = form.store_name.value.trim();
  const locationLabel = form.location_label.value.trim();
  const notes = form.notes.value.trim();

  if (!itemName || !storeName || !priceDisplay) {
    statusEl.textContent = "Please fill in item name, price, and store.";
    statusEl.className = "submit-status error";
    return;
  }

  submitBtn.disabled = true;
  statusEl.textContent = "Posting your find…";
  statusEl.className = "submit-status";

  try {
    let photoUrl = null;
    if (selectedPhotoFile) {
      photoUrl = await uploadFindPhoto(selectedPhotoFile);
    }

    const priceNumeric = parsePriceNumeric(priceDisplay);
    const insertRow = {
      item_name: itemName,
      price: priceNumeric > 0 ? priceNumeric : 0.01,
      price_display: priceDisplay,
      store_name: storeName,
      location_label: locationLabel || null,
      photo_url: photoUrl,
      notes: notes || null,
      submitted_by: getVisitorId(),
      status: "pending",
      ai_extracted: Boolean(aiExtractionState?.used),
      ai_confidence: aiExtractionState?.confidence
        ? JSON.parse(JSON.stringify(aiExtractionState.confidence))
        : null,
      raw_ai_extraction: aiExtractionState?.raw
        ? JSON.parse(JSON.stringify(aiExtractionState.raw))
        : null,
    };

    const supabase = getSupabase();
    const { data: inserted, error } = await supabase
      .from("finds")
      .insert(insertRow)
      .select("id, item_name")
      .single();

    if (!error && inserted?.item_name !== itemName) {
      console.warn("Insert item_name mismatch", { expected: itemName, got: inserted?.item_name });
    }

    if (error) throw error;

    selectedPhotoFile = null;
    aiExtractionState = null;
    window.location.href = getFindsFeedAfterPostUrl();
  } catch (err) {
    console.error(err);
    statusEl.textContent = formatSubmitError(err.cause || err);
    statusEl.className = "submit-status error";
    submitBtn.disabled = false;
  }
}

function renderEmptyState() {
  const empty = document.createElement("div");
  empty.className = "empty-state";
  empty.innerHTML = `
    <h2>No fresh finds yet</h2>
    <p>Be the first to post a grocery deal you spotted in-store.</p>
    <a href="${getSubmitPageUrl()}" class="btn btn-primary">Post a find</a>
  `;
  return empty;
}

function renderFindCard(find) {
  const row = { ...find };
  const card = document.createElement("article");
  card.className = "find-card";
  card.dataset.findId = row.id;

  if (row.photo_url) {
    const photoWrap = document.createElement("div");
    photoWrap.className = "find-card-photo";
    const img = document.createElement("img");
    img.src = row.photo_url;
    img.alt = row.item_name || "Grocery find photo";
    img.loading = "lazy";
    photoWrap.appendChild(img);
    card.appendChild(photoWrap);
  }

  const body = document.createElement("div");
  body.className = "find-card-body";

  const title = document.createElement("h2");
  title.className = "find-card-title";
  title.textContent = String(row.item_name ?? "");

  const priceEl = document.createElement("p");
  priceEl.className = "find-card-price";
  priceEl.textContent = displayFindPrice(row);

  const meta = document.createElement("p");
  meta.className = "find-card-meta";
  const metaParts = [row.store_name];
  if (row.location_label) metaParts.push(row.location_label);
  metaParts.push(timeAgo(row.created_at));
  meta.textContent = metaParts.join(" · ");

  body.appendChild(title);
  body.appendChild(priceEl);
  body.appendChild(meta);

  if (row.notes) {
    const notesEl = document.createElement("p");
    notesEl.className = "find-card-notes";
    notesEl.textContent = row.notes;
    body.appendChild(notesEl);
  }

  const actions = document.createElement("div");
  actions.className = "find-card-actions";

  const stillBtn = document.createElement("button");
  stillBtn.type = "button";
  stillBtn.className = "btn btn-secondary btn-sm still-there-btn";
  stillBtn.textContent = "Still there";
  stillBtn.addEventListener("click", () => voteStillThere(row.id));

  const reportBtn = document.createElement("button");
  reportBtn.type = "button";
  reportBtn.className = "btn btn-ghost btn-sm report-btn";
  reportBtn.textContent = "Report";
  reportBtn.addEventListener("click", () => reportFind(row.id));

  actions.appendChild(stillBtn);
  actions.appendChild(reportBtn);
  body.appendChild(actions);
  card.appendChild(body);

  return card;
}

async function loadFinds() {
  const feed = document.getElementById("finds-feed");
  if (!feed) return;

  const requestGeneration = ++loadFindsGeneration;

  feed.innerHTML = "";
  const loading = document.createElement("p");
  loading.className = "feed-status";
  loading.textContent = "Loading finds…";
  feed.appendChild(loading);

  try {
    const supabase = getSupabase();
    const { data, error } = await supabase
      .from("finds")
      .select(
        "id, item_name, price, price_display, store_name, location_label, photo_url, notes, created_at, expires_at"
      )
      .eq("status", "approved")
      .gt("expires_at", new Date().toISOString())
      .order("created_at", { ascending: false })
      .limit(50);

    if (error) throw error;
    if (requestGeneration !== loadFindsGeneration) return;

    feed.innerHTML = "";
    feed.className = "finds-feed";

    if (!data || data.length === 0) {
      feed.appendChild(renderEmptyState());
      return;
    }

    data.forEach((find) => {
      feed.appendChild(renderFindCard(find));
    });
  } catch (err) {
    if (requestGeneration !== loadFindsGeneration) return;
    console.error(err);
    feed.innerHTML = "";
    const errEl = document.createElement("p");
    errEl.className = "feed-status error";
    errEl.textContent = `Could not load finds. ${err.message || "Please try again later."}`;
    feed.appendChild(errEl);
  }
}

async function voteStillThere(findId) {
  try {
    const supabase = getSupabase();
    const { error } = await supabase.from("find_votes").insert({
      find_id: findId,
      voter_id: getVisitorId(),
      vote_type: "still_there",
    });

    if (error) {
      if (error.code === "23505") {
        alert("You already confirmed this find.");
        return;
      }
      throw error;
    }

    alert("Thanks for confirming!");
  } catch (err) {
    console.error(err);
    alert(err.message || "Could not record your vote. Please try again.");
  }
}

async function reportFind(findId) {
  const reason = prompt("Why are you reporting this find?");
  if (reason == null || !reason.trim()) return;

  try {
    const supabase = getSupabase();
    const { error } = await supabase.from("find_reports").insert({
      find_id: findId,
      reporter_id: getVisitorId(),
      reason: reason.trim(),
    });

    if (error) throw error;

    alert("Report submitted. Thank you.");
  } catch (err) {
    console.error(err);
    alert(err.message || "Could not submit report. Please try again.");
  }
}

function resolvePhotoMime(file) {
  const fromBrowser = (file?.type || "").toLowerCase();
  if (fromBrowser && ALLOWED_PHOTO_TYPES.includes(fromBrowser)) return fromBrowser;

  const name = (file?.name || "").toLowerCase();
  if (name.endsWith(".jpg") || name.endsWith(".jpeg")) return "image/jpeg";
  if (name.endsWith(".png")) return "image/png";
  if (name.endsWith(".webp")) return "image/webp";
  return fromBrowser || "";
}

function photoFileForUpload(file) {
  const mime = resolvePhotoMime(file);
  if (!mime || file.type === mime) return file;
  return new File([file], file.name, { type: mime });
}

function validatePhotoFile(file) {
  if (!file) return "No file selected.";
  const mime = resolvePhotoMime(file);
  if (!mime || !ALLOWED_PHOTO_TYPES.includes(mime)) {
    return "Please use a JPG, PNG, or WebP image.";
  }
  if (file.size > MAX_PHOTO_BYTES) {
    return "Image must be 8MB or smaller.";
  }
  return null;
}

function isExtractionEmpty(data) {
  if (!data) return true;
  const item = String(data.item_name || "").trim();
  const price = String(data.price || "").trim();
  const store = String(data.store || "").trim();
  return !item && !price && !store;
}

function setAnalyzingPhoto(active) {
  isAnalyzingPhoto = active;
  const submitBtn = document.getElementById("submit-btn");
  const dropzone = document.getElementById("photo-dropzone");
  if (submitBtn) submitBtn.disabled = active;
  if (dropzone) dropzone.classList.toggle("is-disabled", active);
}

function setPhotoAnalyzeStatus(message, isError = false) {
  const el = document.getElementById("photo-analyze-status");
  if (!el) return;
  el.textContent = message || "";
  el.classList.toggle("error", isError);
}

function showPhotoPreview(file) {
  const preview = document.getElementById("photo-preview");
  if (!preview) return;

  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = null;
  }

  preview.innerHTML = "";
  previewObjectUrl = URL.createObjectURL(file);
  const img = document.createElement("img");
  img.src = previewObjectUrl;
  img.alt = "Uploaded deal photo preview";
  preview.appendChild(img);
  preview.hidden = false;
}

function markFieldTouched(fieldName) {
  if (fieldTouched[fieldName] !== undefined) {
    fieldTouched[fieldName] = true;
  }
}

function setFieldWarning(fieldName, show) {
  const el = document.getElementById(`${fieldName}-warning`);
  if (el) el.hidden = !show;
}

function applyConfidenceWarnings(confidence) {
  if (!confidence) return;
  setFieldWarning("item_name", (confidence.item_name ?? 1) < CONFIDENCE_THRESHOLDS.item_name);
  setFieldWarning("price", (confidence.price ?? 1) < CONFIDENCE_THRESHOLDS.price);
  setFieldWarning("store_name", (confidence.store_name ?? confidence.store ?? 1) < CONFIDENCE_THRESHOLDS.store_name);
}

function fillFieldIfAllowed(fieldName, value) {
  if (fieldTouched[fieldName]) return;
  const el = document.getElementById(fieldName);
  if (!el) return;
  const next = String(value || "").trim();
  if (!next) return;
  el.value = next;
}

function applyAiExtraction(data) {
  if (!data) return;

  fillFieldIfAllowed("item_name", data.item_name);
  fillFieldIfAllowed("price", data.price);
  fillFieldIfAllowed("store_name", normalizeStoreName(data.store));
  fillFieldIfAllowed("location_label", data.location);
  fillFieldIfAllowed("notes", data.notes);

  const confidence = data.confidence || {};
  applyConfidenceWarnings({
    item_name: confidence.item_name,
    price: confidence.price,
    store_name: confidence.store_name ?? confidence.store,
  });

  aiExtractionState = {
    used: true,
    confidence,
    raw: data.raw_extraction ?? data,
  };

  const banner = document.getElementById("ai-fill-banner");
  if (banner) banner.hidden = false;
}

async function analyzePhotoFile(file) {
  if (!isAnalyzeEndpointConfigured()) {
    setPhotoAnalyzeStatus("AI photo analysis is not configured. Fill in the form manually.");
    return;
  }

  const generation = ++photoAnalyzeGeneration;
  setAnalyzingPhoto(true);
  setPhotoAnalyzeStatus("Analyzing photo…");

  try {
    const formData = new FormData();
    formData.append("image", photoFileForUpload(file));

    const response = await fetch(ANALYZE_PHOTO_ENDPOINT, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
        apikey: SUPABASE_ANON_KEY,
      },
      body: formData,
    });

    const data = await response.json();
    if (generation !== photoAnalyzeGeneration) return;

    if (!response.ok) {
      throw new Error(data?.error || "Could not analyze photo");
    }

    if (isExtractionEmpty(data)) {
      setPhotoAnalyzeStatus(
        "We couldn’t read details from this photo. Try a clearer shelf-tag shot, or fill in the form manually.",
        true
      );
      return;
    }

    applyAiExtraction(data);
    setPhotoAnalyzeStatus("Analysis complete — please review the fields below.");
  } catch (err) {
    if (generation !== photoAnalyzeGeneration) return;
    console.error(err);
    setPhotoAnalyzeStatus(
      "Could not extract details from your photo. You can still fill in the form manually.",
      true
    );
  } finally {
    if (generation === photoAnalyzeGeneration) {
      setAnalyzingPhoto(false);
    }
  }
}

function resetSubmitFormState() {
  photoAnalyzeGeneration += 1;
  isAnalyzingPhoto = false;
  selectedPhotoFile = null;
  aiExtractionState = null;
  Object.keys(fieldTouched).forEach((key) => {
    fieldTouched[key] = false;
  });
  setFieldWarning("item_name", false);
  setFieldWarning("price", false);
  setFieldWarning("store_name", false);
  setPhotoAnalyzeStatus("");
  const banner = document.getElementById("ai-fill-banner");
  if (banner) banner.hidden = true;
  const preview = document.getElementById("photo-preview");
  if (preview) {
    preview.innerHTML = "";
    preview.hidden = true;
  }
  if (previewObjectUrl) {
    URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = null;
  }
  const photoInput = document.getElementById("photo");
  if (photoInput) photoInput.value = "";
}

async function handlePhotoSelected(file) {
  const validationError = validatePhotoFile(file);
  if (validationError) {
    setPhotoAnalyzeStatus(validationError, true);
    return;
  }

  photoAnalyzeGeneration += 1;
  Object.keys(fieldTouched).forEach((key) => {
    fieldTouched[key] = false;
  });
  setFieldWarning("item_name", false);
  setFieldWarning("price", false);
  setFieldWarning("store_name", false);

  document.querySelectorAll("[data-ai-field]").forEach((el) => {
    el.value = "";
  });

  selectedPhotoFile = file;
  aiExtractionState = null;
  showPhotoPreview(file);
  setPhotoAnalyzeStatus("");
  const banner = document.getElementById("ai-fill-banner");
  if (banner) banner.hidden = true;

  if (isAnalyzeEndpointConfigured()) {
    await analyzePhotoFile(file);
  } else {
    setPhotoAnalyzeStatus("Photo added. Fill in the details below, or configure AI analysis in app.js.");
  }
}

function initPhotoUploadFlow() {
  const photoInput = document.getElementById("photo");
  const dropzone = document.getElementById("photo-dropzone");
  if (!photoInput || !dropzone) return;
  if (dropzone.dataset.staPhotoInit === "1") return;
  dropzone.dataset.staPhotoInit = "1";

  document.querySelectorAll("[data-ai-field]").forEach((el) => {
    const name = el.name || el.id;
    el.addEventListener("input", () => markFieldTouched(name));
    el.addEventListener("change", () => markFieldTouched(name));
  });

  dropzone.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (!isAnalyzingPhoto) photoInput.click();
    }
  });

  photoInput.addEventListener("change", () => {
    const file = photoInput.files?.[0];
    if (file) handlePhotoSelected(file);
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    if (!isAnalyzingPhoto) dropzone.classList.add("is-dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("is-dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("is-dragover");
    if (isAnalyzingPhoto) return;
    const file = e.dataTransfer?.files?.[0];
    if (file) handlePhotoSelected(file);
  });
}

function initSuccessBanner() {
  const banner = document.getElementById("success-banner");
  if (!banner) return;

  const params = new URLSearchParams(window.location.search);
  if (params.get("submitted") === "1") {
    banner.hidden = false;
    banner.textContent =
      "Thanks! Your find is pending review and will appear on the feed once approved.";
  } else if (params.get("posted") === "1") {
    banner.hidden = false;
    banner.textContent = "Your find is live.";
  }
}

function initSubmitPage() {
  const form = document.getElementById("submit-form");
  if (!form) return;
  if (form.dataset.staSubmitInit !== "1") {
    form.addEventListener("submit", submitFind);
    initPhotoUploadFlow();
    form.dataset.staSubmitInit = "1";
  }
  form.reset();
  resetSubmitFormState();
}

document.addEventListener("DOMContentLoaded", () => {
  initSuccessBanner();
  initSubmitPage();

  if (document.getElementById("finds-feed")) {
    loadFinds();
  }
});

window.addEventListener("pageshow", (event) => {
  if (event.persisted) {
    initSubmitPage();
    if (document.getElementById("finds-feed")) {
      loadFinds();
    }
  }
});
