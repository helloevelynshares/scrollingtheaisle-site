import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import {
  getAdminPassword,
  getBearerToken,
  verifyAdminToken,
} from "../_shared/adminAuth.ts";
import { getServiceSupabase } from "../_shared/supabaseAdmin.ts";

type AdminAction = "list" | "approve" | "reject";

type PendingFind = {
  id: string;
  item_name: string;
  price: number;
  price_display: string | null;
  store_name: string;
  location_label: string | null;
  photo_url: string | null;
  notes: string | null;
  submitted_by: string | null;
  ai_extracted: boolean | null;
  created_at: string;
};

function parsePriceNumeric(priceText: string): number {
  const dollarMatches = [...priceText.matchAll(/\$(\d+(?:\.\d{1,2})?)/g)].map((match) =>
    parseFloat(match[1])
  );
  if (dollarMatches.length > 0) {
    const finite = dollarMatches.filter((value) => Number.isFinite(value));
    if (finite.length > 0) {
      return Math.min(...finite);
    }
  }
  const plain = parseFloat(priceText.replace(/[^0-9.]/g, ""));
  return Number.isFinite(plain) ? plain : 0;
}

async function requireAdmin(req: Request): Promise<Response | null> {
  const adminPassword = getAdminPassword();
  if (!adminPassword) {
    return jsonResponse({ error: "Admin access is not configured" }, 503);
  }

  const token = getBearerToken(req);
  const valid = await verifyAdminToken(token, adminPassword);
  if (!valid) {
    return jsonResponse({ error: "Unauthorized" }, 401);
  }

  return null;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  const authError = await requireAdmin(req);
  if (authError) {
    return authError;
  }

  try {
    const body = await req.json().catch(() => null);
    const action = body?.action as AdminAction | undefined;

    if (!action) {
      return jsonResponse({ error: "Missing action" }, 400);
    }

    const supabase = getServiceSupabase();

    if (action === "list") {
      const { data: pending, error: pendingError } = await supabase
        .from("finds")
        .select(
          "id, item_name, price, price_display, store_name, location_label, photo_url, notes, submitted_by, ai_extracted, created_at",
        )
        .eq("status", "pending")
        .order("created_at", { ascending: true });

      if (pendingError) {
        throw pendingError;
      }

      return jsonResponse({
        pending: (pending ?? []) as PendingFind[],
      });
    }

    const findId = typeof body?.findId === "string" ? body.findId : "";
    if (!findId) {
      return jsonResponse({ error: "Missing findId" }, 400);
    }

    if (action === "approve") {
      const { data: existing, error: fetchError } = await supabase
        .from("finds")
        .select("id, status, item_name, price, price_display, store_name")
        .eq("id", findId)
        .maybeSingle();

      if (fetchError) {
        throw fetchError;
      }
      if (!existing || existing.status !== "pending") {
        return jsonResponse({ error: "Pending find not found" }, 404);
      }

      const itemName =
        typeof body?.itemName === "string" && body.itemName.trim()
          ? body.itemName.trim()
          : existing.item_name;
      const priceDisplay =
        typeof body?.priceDisplay === "string" && body.priceDisplay.trim()
          ? body.priceDisplay.trim()
          : existing.price_display ?? String(existing.price);
      const storeName =
        typeof body?.storeName === "string" && body.storeName.trim()
          ? body.storeName.trim()
          : existing.store_name;
      const locationLabel =
        typeof body?.locationLabel === "string" && body.locationLabel.trim()
          ? body.locationLabel.trim()
          : null;
      const notes =
        typeof body?.notes === "string" && body.notes.trim()
          ? body.notes.trim()
          : null;
      const adminNotes =
        typeof body?.adminNotes === "string" && body.adminNotes.trim()
          ? body.adminNotes.trim()
          : null;

      const priceNumeric = parsePriceNumeric(priceDisplay);
      const approvedAt = new Date().toISOString();
      const expiresAt = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString();

      const { error: updateError } = await supabase
        .from("finds")
        .update({
          status: "approved",
          item_name: itemName,
          price: priceNumeric > 0 ? priceNumeric : existing.price,
          price_display: priceDisplay,
          store_name: storeName,
          location_label: locationLabel,
          notes,
          approved_at: approvedAt,
          expires_at: expiresAt,
          admin_notes: adminNotes,
        })
        .eq("id", findId)
        .eq("status", "pending");

      if (updateError) {
        throw updateError;
      }

      return jsonResponse({ ok: true });
    }

    if (action === "reject") {
      const adminNotes =
        typeof body?.adminNotes === "string" ? body.adminNotes.trim() : null;

      const { data: existing, error: fetchError } = await supabase
        .from("finds")
        .select("id, status")
        .eq("id", findId)
        .maybeSingle();

      if (fetchError) {
        throw fetchError;
      }
      if (!existing || existing.status !== "pending") {
        return jsonResponse({ error: "Pending find not found" }, 404);
      }

      const { error: updateError } = await supabase
        .from("finds")
        .update({
          status: "rejected",
          rejected_at: new Date().toISOString(),
          admin_notes: adminNotes || null,
        })
        .eq("id", findId)
        .eq("status", "pending");

      if (updateError) {
        throw updateError;
      }

      return jsonResponse({ ok: true });
    }

    return jsonResponse({ error: "Unknown action" }, 400);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Admin action failed";
    console.error("admin-find-actions:", message);
    return jsonResponse({ error: message }, 500);
  }
});
