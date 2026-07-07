import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import {
  getAdminPassword,
  getBearerToken,
  verifyAdminToken,
} from "../_shared/adminAuth.ts";
import { getServiceSupabase } from "../_shared/supabaseAdmin.ts";

type AdminAction = "list" | "approve" | "reject" | "merge";

type PendingStore = {
  id: string;
  raw_text: string;
  public_name: string | null;
  normalized_name: string;
  city: string | null;
  created_at: string;
};

type ApprovedStore = {
  id: string;
  public_name: string | null;
  raw_text: string;
  city: string | null;
  vote_count: number;
};

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

function displayName(item: { public_name: string | null; raw_text: string }): string {
  return item.public_name?.trim() || item.raw_text;
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
      const [{ data: pending, error: pendingError }, { data: approved, error: approvedError }] =
        await Promise.all([
          supabase
            .from("store_vote_items")
            .select("id, raw_text, public_name, normalized_name, city, created_at")
            .eq("status", "pending")
            .order("created_at", { ascending: true }),
          supabase
            .from("store_vote_items")
            .select("id, public_name, raw_text, city, vote_count")
            .eq("status", "approved")
            .order("public_name", { ascending: true })
            .order("raw_text", { ascending: true }),
        ]);

      if (pendingError) {
        throw pendingError;
      }
      if (approvedError) {
        throw approvedError;
      }

      return jsonResponse({
        pending: (pending ?? []) as PendingStore[],
        approved: (approved ?? []) as ApprovedStore[],
      });
    }

    const itemId = typeof body?.itemId === "string" ? body.itemId : "";
    if (!itemId) {
      return jsonResponse({ error: "Missing itemId" }, 400);
    }

    if (action === "approve") {
      const publicName =
        typeof body?.publicName === "string" && body.publicName.trim()
          ? body.publicName.trim()
          : null;

      const { data: existing, error: fetchError } = await supabase
        .from("store_vote_items")
        .select("id, raw_text, status")
        .eq("id", itemId)
        .maybeSingle();

      if (fetchError) {
        throw fetchError;
      }
      if (!existing || existing.status !== "pending") {
        return jsonResponse({ error: "Pending store suggestion not found" }, 404);
      }

      const { error: updateError } = await supabase
        .from("store_vote_items")
        .update({
          status: "approved",
          public_name: publicName ?? existing.raw_text,
          approved_at: new Date().toISOString(),
          vote_count: 0,
        })
        .eq("id", itemId)
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
        .from("store_vote_items")
        .select("id, status")
        .eq("id", itemId)
        .maybeSingle();

      if (fetchError) {
        throw fetchError;
      }
      if (!existing || existing.status !== "pending") {
        return jsonResponse({ error: "Pending store suggestion not found" }, 404);
      }

      const { error: updateError } = await supabase
        .from("store_vote_items")
        .update({
          status: "rejected",
          rejected_at: new Date().toISOString(),
          admin_notes: adminNotes || null,
        })
        .eq("id", itemId)
        .eq("status", "pending");

      if (updateError) {
        throw updateError;
      }

      return jsonResponse({ ok: true });
    }

    if (action === "merge") {
      const mergeIntoId =
        typeof body?.mergeIntoId === "string" ? body.mergeIntoId : "";
      const addVoteOnMerge = body?.addVoteOnMerge !== false;
      const adminNotes =
        typeof body?.adminNotes === "string" ? body.adminNotes.trim() : null;

      if (!mergeIntoId) {
        return jsonResponse({ error: "Missing mergeIntoId" }, 400);
      }
      if (mergeIntoId === itemId) {
        return jsonResponse({ error: "Cannot merge an item into itself" }, 400);
      }

      const [{ data: pendingItem, error: pendingError }, { data: targetItem, error: targetError }] =
        await Promise.all([
          supabase
            .from("store_vote_items")
            .select("id, status")
            .eq("id", itemId)
            .maybeSingle(),
          supabase
            .from("store_vote_items")
            .select("id, status, vote_count, public_name, raw_text")
            .eq("id", mergeIntoId)
            .maybeSingle(),
        ]);

      if (pendingError) {
        throw pendingError;
      }
      if (targetError) {
        throw targetError;
      }
      if (!pendingItem || pendingItem.status !== "pending") {
        return jsonResponse({ error: "Pending store suggestion not found" }, 404);
      }
      if (!targetItem || targetItem.status !== "approved") {
        return jsonResponse({ error: "Merge target must be an approved store" }, 400);
      }

      const { error: mergeError } = await supabase
        .from("store_vote_items")
        .update({
          status: "merged",
          merged_into_id: mergeIntoId,
          admin_notes: adminNotes || null,
        })
        .eq("id", itemId)
        .eq("status", "pending");

      if (mergeError) {
        throw mergeError;
      }

      if (addVoteOnMerge) {
        const { error: voteError } = await supabase
          .from("store_vote_items")
          .update({ vote_count: (targetItem.vote_count ?? 0) + 1 })
          .eq("id", mergeIntoId)
          .eq("status", "approved");

        if (voteError) {
          throw voteError;
        }
      }

      return jsonResponse({
        ok: true,
        mergedInto: displayName(targetItem),
      });
    }

    return jsonResponse({ error: "Unknown action" }, 400);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Admin action failed";
    console.error("admin-store-actions:", message);
    return jsonResponse({ error: message }, 500);
  }
});
