import { useId, useState, type FormEvent } from "react";
import { getSupabase, getVisitorId } from "../lib/supabase";

const MAX_PHOTO_BYTES = 8 * 1024 * 1024;
const ALLOWED_PHOTO_TYPES = new Set([
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
]);

function formatError(error: unknown): string {
  const message =
    error instanceof Error
      ? error.message
      : typeof error === "object" && error && "message" in error
        ? String((error as { message: unknown }).message)
        : "";

  if (message.includes("tracker_suggestions")) {
    return "Suggestion storage isn’t set up yet. Run supabase/migrations/20260607_tracker_suggestions.sql in Supabase.";
  }
  if (message.includes("Bucket not found")) {
    return "Photo storage isn’t set up yet. Submit without a photo, or create the find-photos bucket (see README).";
  }
  return message || "Something went wrong. Please try again.";
}

async function uploadPhoto(file: File): Promise<string> {
  const supabase = getSupabase();
  const visitorId = getVisitorId();
  const ext = (file.name.split(".").pop() || "jpg").toLowerCase();
  const path = `tracker-suggestions/${visitorId}/${crypto.randomUUID()}.${ext}`;

  const { error } = await supabase.storage.from("find-photos").upload(path, file, {
    cacheControl: "3600",
    upsert: false,
  });

  if (error) {
    throw new Error(formatError(error));
  }

  const { data } = supabase.storage.from("find-photos").getPublicUrl(path);
  return data.publicUrl;
}

export function TrackSuggestionForm() {
  const formId = useId();
  const itemNameId = `${formId}-item-name`;
  const notesId = `${formId}-notes`;
  const photoId = `${formId}-photo`;

  const [itemName, setItemName] = useState("");
  const [notes, setNotes] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">(
    "idle",
  );
  const [statusMessage, setStatusMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedName = itemName.trim();
    if (!trimmedName) {
      setStatus("error");
      setStatusMessage("Add a product name so we know what to track.");
      return;
    }

    if (photo) {
      if (!ALLOWED_PHOTO_TYPES.has(photo.type)) {
        setStatus("error");
        setStatusMessage("Photo must be JPEG, PNG, or WebP.");
        return;
      }
      if (photo.size > MAX_PHOTO_BYTES) {
        setStatus("error");
        setStatusMessage("Photo must be 8 MB or smaller.");
        return;
      }
    }

    setStatus("submitting");
    setStatusMessage("");

    try {
      let photoUrl: string | null = null;
      if (photo) {
        photoUrl = await uploadPhoto(photo);
      }

      const supabase = getSupabase();
      const { error } = await supabase.from("tracker_suggestions").insert({
        item_name: trimmedName,
        notes: notes.trim() || null,
        photo_url: photoUrl,
        submitted_by: getVisitorId(),
      });

      if (error) {
        throw error;
      }

      setItemName("");
      setNotes("");
      setPhoto(null);
      setStatus("success");
      setStatusMessage("Thanks — we’ll review your suggestion.");
    } catch (error) {
      setStatus("error");
      setStatusMessage(formatError(error));
    }
  }

  return (
    <section className="price-tracker-suggest" aria-labelledby="price-tracker-suggest-title">
      <h2 id="price-tracker-suggest-title">Suggest a product to track</h2>
      <p className="price-tracker-suggest-lead">
        Tell us what Costco-comparable item you want on the chart. Optional: add a
        shelf tag or product photo.
      </p>

      <form className="submit-form price-tracker-suggest-form" onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor={itemNameId}>Product name</label>
          <input
            id={itemNameId}
            name="item_name"
            type="text"
            required
            autoComplete="off"
            placeholder="e.g. Kirkland-style organic eggs, 24 ct"
            value={itemName}
            onChange={(event) => setItemName(event.target.value)}
            disabled={status === "submitting"}
          />
        </div>

        <div className="form-group">
          <label htmlFor={notesId}>
            Why track this? <span className="label-muted">(optional)</span>
          </label>
          <textarea
            id={notesId}
            name="notes"
            placeholder="Size, brand, or why it’s a good Costco compare…"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            disabled={status === "submitting"}
          />
        </div>

        <div className="form-group">
          <label htmlFor={photoId}>
            Photo <span className="label-muted">(optional)</span>
          </label>
          <input
            id={photoId}
            name="photo"
            type="file"
            accept="image/jpeg,image/jpg,image/png,image/webp"
            onChange={(event) => setPhoto(event.target.files?.[0] ?? null)}
            disabled={status === "submitting"}
          />
          {photo ? (
            <p className="price-tracker-suggest-photo-name">{photo.name}</p>
          ) : null}
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={status === "submitting"}
          >
            {status === "submitting" ? "Sending…" : "Send suggestion"}
          </button>
        </div>

        {statusMessage ? (
          <p
            className={`submit-status price-tracker-suggest-status price-tracker-suggest-status--${status}`}
            role="status"
            aria-live="polite"
          >
            {statusMessage}
          </p>
        ) : null}
      </form>

      <p className="price-tracker-suggest-alt">
        Or DM{" "}
        <a
          href="https://www.tiktok.com/@scrollingtheaisle"
          target="_blank"
          rel="noopener noreferrer"
        >
          @scrollingtheaisle
        </a>{" "}
        on TikTok.
      </p>
    </section>
  );
}
