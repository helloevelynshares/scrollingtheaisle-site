const SUPABASE_URL = "https://wurmdtqysegytsjcudve.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_8Wt-it-oIHHIkQOi0D9y_g_qMoH51ZX";

const VISITOR_ID_KEY = "sta_visitor_id";

let supabaseClient = null;

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
  return stagingBase ? `${stagingBase}?posted=1` : "finds.html?posted=1";
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
  const submitBtn = form.querySelector('button[type="submit"]');

  const itemName = form.item_name.value.trim();
  const price = parseFloat(form.price.value);
  const storeName = form.store_name.value.trim();
  const locationLabel = form.location_label.value.trim();
  const notes = form.notes.value.trim();
  const photoInput = form.photo;

  if (!itemName || !storeName || Number.isNaN(price)) {
    statusEl.textContent = "Please fill in all required fields.";
    statusEl.className = "submit-status error";
    return;
  }

  submitBtn.disabled = true;
  statusEl.textContent = "Posting your find…";
  statusEl.className = "submit-status";

  try {
    let photoUrl = null;
    if (photoInput.files && photoInput.files[0]) {
      photoUrl = await uploadFindPhoto(photoInput.files[0]);
    }

    const supabase = getSupabase();
    const { error } = await supabase.from("finds").insert({
      item_name: itemName,
      price,
      store_name: storeName,
      location_label: locationLabel || null,
      photo_url: photoUrl,
      notes: notes || null,
      submitted_by: getVisitorId(),
      status: "approved",
    });

    if (error) throw error;

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
  const card = document.createElement("article");
  card.className = "find-card";
  card.dataset.findId = find.id;

  if (find.photo_url) {
    const photoWrap = document.createElement("div");
    photoWrap.className = "find-card-photo";
    const img = document.createElement("img");
    img.src = find.photo_url;
    img.alt = find.item_name || "Grocery find photo";
    img.loading = "lazy";
    photoWrap.appendChild(img);
    card.appendChild(photoWrap);
  }

  const body = document.createElement("div");
  body.className = "find-card-body";

  const title = document.createElement("h2");
  title.className = "find-card-title";
  title.textContent = find.item_name;

  const priceEl = document.createElement("p");
  priceEl.className = "find-card-price";
  priceEl.textContent = formatPrice(find.price);

  const meta = document.createElement("p");
  meta.className = "find-card-meta";
  const metaParts = [find.store_name];
  if (find.location_label) metaParts.push(find.location_label);
  metaParts.push(timeAgo(find.created_at));
  meta.textContent = metaParts.join(" · ");

  body.appendChild(title);
  body.appendChild(priceEl);
  body.appendChild(meta);

  if (find.notes) {
    const notesEl = document.createElement("p");
    notesEl.className = "find-card-notes";
    notesEl.textContent = find.notes;
    body.appendChild(notesEl);
  }

  const actions = document.createElement("div");
  actions.className = "find-card-actions";

  const stillBtn = document.createElement("button");
  stillBtn.type = "button";
  stillBtn.className = "btn btn-secondary btn-sm still-there-btn";
  stillBtn.textContent = "Still there";
  stillBtn.addEventListener("click", () => voteStillThere(find.id));

  const reportBtn = document.createElement("button");
  reportBtn.type = "button";
  reportBtn.className = "btn btn-ghost btn-sm report-btn";
  reportBtn.textContent = "Report";
  reportBtn.addEventListener("click", () => reportFind(find.id));

  actions.appendChild(stillBtn);
  actions.appendChild(reportBtn);
  body.appendChild(actions);
  card.appendChild(body);

  return card;
}

async function loadFinds() {
  const feed = document.getElementById("finds-feed");
  if (!feed) return;

  feed.innerHTML = "";
  const loading = document.createElement("p");
  loading.className = "feed-status";
  loading.textContent = "Loading finds…";
  feed.appendChild(loading);

  try {
    const supabase = getSupabase();
    const { data, error } = await supabase
      .from("finds")
      .select("*")
      .eq("status", "approved")
      .gt("expires_at", new Date().toISOString())
      .order("created_at", { ascending: false })
      .limit(50);

    if (error) throw error;

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

function initPhotoPreview() {
  const photoInput = document.getElementById("photo");
  const preview = document.getElementById("photo-preview");
  if (!photoInput || !preview) return;

  photoInput.addEventListener("change", () => {
    preview.innerHTML = "";
    const file = photoInput.files && photoInput.files[0];
    if (!file) return;

    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.alt = "Photo preview";
    preview.appendChild(img);
  });
}

function initSuccessBanner() {
  const banner = document.getElementById("success-banner");
  if (!banner) return;

  const params = new URLSearchParams(window.location.search);
  if (params.get("posted") === "1") {
    banner.hidden = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initSuccessBanner();

  const submitForm = document.getElementById("submit-form");
  if (submitForm) {
    submitForm.addEventListener("submit", submitFind);
    initPhotoPreview();
  }

  if (document.getElementById("finds-feed")) {
    loadFinds();
  }
});
