import { corsHeaders, jsonResponse } from "../_shared/cors.ts";
import {
  createAdminToken,
  getAdminPassword,
} from "../_shared/adminAuth.ts";

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return jsonResponse({ error: "Method not allowed" }, 405);
  }

  try {
    const adminPassword = getAdminPassword();
    if (!adminPassword) {
      return jsonResponse({ error: "Admin access is not configured" }, 503);
    }

    const body = await req.json().catch(() => null);
    const password =
      typeof body?.password === "string" ? body.password.trim() : "";

    if (!password || password !== adminPassword) {
      return jsonResponse({ error: "Invalid password" }, 401);
    }

    const token = await createAdminToken(adminPassword);
    return jsonResponse({
      ok: true,
      token,
      expiresIn: 8 * 60 * 60,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Validation failed";
    console.error("validate-admin:", message);
    return jsonResponse({ error: message }, 500);
  }
});
