import { corsHeaders, jsonResponse } from "../_shared/cors.ts";

const MAX_BYTES = 8 * 1024 * 1024;
const ALLOWED_MIME = new Set([
  "image/jpeg",
  "image/jpg",
  "image/png",
  "image/webp",
]);

const EXTRACTION_PROMPT = `You are analyzing a user-uploaded grocery deal photo for a community deal feed. Extract only information visible or strongly inferable from the image. Do not hallucinate. If a field is unclear, return an empty string or explain uncertainty in notes.

Return JSON with:
- item_name: concise product name including brand and size/count if visible
- price: user-friendly deal price text. Include regular price, sale price, discount, and promo requirement if visible.
- store: store name only if visible or strongly inferable
- location: empty unless visible
- notes: short helpful note, such as coupon requirement, club card requirement, limit, size/count, aisle clue, or uncertainty
- confidence: object with scores item_name, price, and store from 0 to 1

Examples:
For a photo showing Keebler Fudge Stripes Minis 10 pack with a 50% off sticker and regular price $7.99:
item_name = Keebler Fudge Stripes Minis, 10 pack
price = 50% off, reg. $7.99, approx. $3.99
store = empty unless Safeway is visible/inferred from UI context
notes = Club card price/clearance-style tag. 10 pouches, 10 oz total.`;

const MOCK_EXTRACTION = {
  item_name: "Keebler Fudge Stripes Minis, 10 pack",
  price: "50% off, reg. $7.99, approx. $3.99 (Club Card price)",
  store: "",
  location: "",
  notes:
    "Orange in-store sticker: NOW 50% OFF, Club Card price. 10-1 oz (28g) pouches, net wt 10 oz (283g).",
  confidence: {
    item_name: 0.92,
    price: 0.85,
    store: 0.2,
  },
  raw_extraction: { mock: true },
};

type ExtractionResult = {
  item_name: string;
  price: string;
  store: string;
  location: string;
  notes: string;
  confidence: { item_name: number; price: number; store: number };
  raw_extraction: unknown;
};

function clampConfidence(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function normalizeExtraction(raw: Record<string, unknown>): ExtractionResult {
  const conf = (raw.confidence as Record<string, unknown>) || {};
  return {
    item_name: String(raw.item_name ?? "").trim(),
    price: String(raw.price ?? "").trim(),
    store: String(raw.store ?? "").trim(),
    location: String(raw.location ?? "").trim(),
    notes: String(raw.notes ?? "").trim(),
    confidence: {
      item_name: clampConfidence(conf.item_name),
      price: clampConfidence(conf.price),
      store: clampConfidence(conf.store),
    },
    raw_extraction: raw.raw_extraction ?? raw,
  };
}

function parseJsonFromModelText(text: string): Record<string, unknown> {
  const trimmed = text.trim();
  const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const candidate = fenced ? fenced[1].trim() : trimmed;
  return JSON.parse(candidate) as Record<string, unknown>;
}

function extractMessageText(payload: {
  choices?: Array<{ message?: { content?: string | Array<{ type: string; text?: string }> } }>;
}): string {
  const choice = payload?.choices?.[0]?.message?.content;
  if (typeof choice === "string") return choice;
  if (Array.isArray(choice)) {
    return choice
      .filter((p) => p.type === "text")
      .map((p) => p.text ?? "")
      .join("\n");
  }
  return "";
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
  }
  return btoa(binary);
}

async function analyzeWithOpenAI(
  bytes: Uint8Array,
  mime: string,
  apiKey: string
): Promise<ExtractionResult> {
  const base64 = bytesToBase64(bytes);
  const dataUrl = `data:${mime};base64,${base64}`;

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: EXTRACTION_PROMPT },
            { type: "image_url", image_url: { url: dataUrl } },
          ],
        },
      ],
      max_tokens: 800,
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    const message =
      (payload as { error?: { message?: string } })?.error?.message ||
      "OpenAI request failed";
    throw new Error(message);
  }

  const text = extractMessageText(payload);
  const parsed = parseJsonFromModelText(text);
  return normalizeExtraction({ ...parsed, raw_extraction: parsed });
}

function inferMimeFromFilename(name: string): string {
  const lower = name.toLowerCase();
  if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
  if (lower.endsWith(".png")) return "image/png";
  if (lower.endsWith(".webp")) return "image/webp";
  return "";
}

function resolveImageMime(file: File): string {
  const fromType = (file.type || "").toLowerCase();
  if (ALLOWED_MIME.has(fromType)) return fromType;
  const fromName = inferMimeFromFilename(file.name || "");
  if (ALLOWED_MIME.has(fromName)) return fromName;
  return fromType || "application/octet-stream";
}

function getImageFromFormData(formData: FormData): File | null {
  const image = formData.get("image");
  if (image instanceof File) return image;
  return null;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  try {
    const contentType = req.headers.get("content-type") || "";
    if (!contentType.includes("multipart/form-data")) {
      return jsonResponse(
        { error: "Expected multipart/form-data with image field" },
        400
      );
    }

    const formData = await req.formData();
    const image = getImageFromFormData(formData);

    if (!image) {
      return jsonResponse({ error: "Missing image file (field: image)" }, 400);
    }

    const mime = resolveImageMime(image);
    if (!ALLOWED_MIME.has(mime)) {
      return jsonResponse(
        { error: "Invalid file type. Use JPG, PNG, or WebP." },
        400
      );
    }

    if (image.size > MAX_BYTES) {
      return jsonResponse({ error: "Image must be 8MB or smaller." }, 400);
    }

    const apiKey = Deno.env.get("OPENAI_API_KEY");
    if (!apiKey) {
      return jsonResponse(MOCK_EXTRACTION);
    }

    const bytes = new Uint8Array(await image.arrayBuffer());
    const result = await analyzeWithOpenAI(bytes, mime, apiKey);
    return jsonResponse(result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Could not analyze photo";
    console.error("analyze-find-photo:", message);
    return jsonResponse({ error: message }, 500);
  }
});
