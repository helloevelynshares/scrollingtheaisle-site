/**
 * POST /api/analyze-find-photo
 * multipart/form-data field: image (jpg, jpeg, png, webp, max 8MB)
 * Deploy as separate Vercel project (see README).
 */

import formidable from "formidable";
import fs from "fs/promises";

export const config = {
  api: {
    bodyParser: false,
  },
};

const MAX_BYTES = 8 * 1024 * 1024;
const ALLOWED_MIME = new Set(["image/jpeg", "image/jpg", "image/png", "image/webp"]);

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

function setCors(res) {
  // TODO: restrict to https://scrollingtheaisle.com in production
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
}

function normalizeExtraction(raw) {
  const confidence = {
    item_name: clampConfidence(raw?.confidence?.item_name),
    price: clampConfidence(raw?.confidence?.price),
    store: clampConfidence(raw?.confidence?.store),
  };

  return {
    item_name: String(raw?.item_name || "").trim(),
    price: String(raw?.price || "").trim(),
    store: String(raw?.store || "").trim(),
    location: String(raw?.location || "").trim(),
    notes: String(raw?.notes || "").trim(),
    confidence,
    raw_extraction: raw?.raw_extraction ?? raw,
  };
}

function clampConfidence(value) {
  const n = Number(value);
  if (!Number.isFinite(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function parseJsonFromModelText(text) {
  if (!text || typeof text !== "string") {
    throw new Error("Empty model response");
  }
  const trimmed = text.trim();
  const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i);
  const candidate = fenced ? fenced[1].trim() : trimmed;
  return JSON.parse(candidate);
}

function extractMessageText(payload) {
  const choice = payload?.choices?.[0]?.message?.content;
  if (typeof choice === "string") return choice;
  if (Array.isArray(choice)) {
    return choice
      .filter((p) => p.type === "text")
      .map((p) => p.text)
      .join("\n");
  }
  return "";
}

async function parseMultipart(req) {
  const form = formidable({
    maxFileSize: MAX_BYTES,
    maxFiles: 1,
    allowEmptyFiles: false,
  });

  return new Promise((resolve, reject) => {
    form.parse(req, (err, _fields, files) => {
      if (err) reject(err);
      else resolve(files);
    });
  });
}

function getUploadedFile(files) {
  const candidate = files.image?.[0] || files.file?.[0] || files.photo?.[0];
  return candidate || null;
}

async function analyzeWithOpenAI(file, apiKey) {
  const buffer = await fs.readFile(file.filepath);
  const mime = file.mimetype || "image/jpeg";
  const base64 = buffer.toString("base64");
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
    const message = payload?.error?.message || "OpenAI request failed";
    throw new Error(message);
  }

  const text = extractMessageText(payload);
  const parsed = parseJsonFromModelText(text);
  return normalizeExtraction({ ...parsed, raw_extraction: parsed });
}

export default async function handler(req, res) {
  setCors(res);

  if (req.method === "OPTIONS") {
    return res.status(200).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  let uploadedFile = null;

  try {
    const files = await parseMultipart(req);
    uploadedFile = getUploadedFile(files);

    if (!uploadedFile) {
      return res.status(400).json({ error: "Missing image file (field: image)" });
    }

    if (!ALLOWED_MIME.has(uploadedFile.mimetype)) {
      return res.status(400).json({
        error: "Invalid file type. Use JPG, PNG, or WebP.",
      });
    }

    if (uploadedFile.size > MAX_BYTES) {
      return res.status(400).json({ error: "Image must be 8MB or smaller." });
    }

    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      return res.status(200).json(MOCK_EXTRACTION);
    }

    const result = await analyzeWithOpenAI(uploadedFile, apiKey);
    return res.status(200).json(result);
  } catch (error) {
    console.error("analyze-find-photo error:", error.message || error);
    const status = error.message?.includes("maxFileSize") ? 400 : 500;
    return res.status(status).json({
      error: error.message || "Could not analyze photo",
    });
  } finally {
    if (uploadedFile?.filepath) {
      await fs.unlink(uploadedFile.filepath).catch(() => {});
    }
  }
}
