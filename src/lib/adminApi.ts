import { SUPABASE_URL } from "./supabase";

const ADMIN_TOKEN_KEY = "sta_admin_token";

export function getEdgeFunctionUrl(name: string): string {
  const projectRef = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "");
  return `https://${projectRef}.functions.supabase.co/${name}`;
}

export function readAdminToken(): string | null {
  try {
    return sessionStorage.getItem(ADMIN_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function writeAdminToken(token: string): void {
  sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
}

export function clearAdminToken(): void {
  sessionStorage.removeItem(ADMIN_TOKEN_KEY);
}

function adminUnauthorizedMessage(payload: Record<string, unknown>): string {
  const code = typeof payload.code === "string" ? payload.code : "";
  if (code.includes("JWT") || code.includes("AUTH")) {
    return "Admin API rejected the session token. Redeploy admin-store-actions with verify_jwt disabled.";
  }
  return "Session expired. Sign in again.";
}

async function parseAdminResponse(response: Response): Promise<Record<string, unknown>> {
  return (await response.json().catch(() => ({}))) as Record<string, unknown>;
}

export async function validateAdminPassword(password: string): Promise<string> {
  const response = await fetch(getEdgeFunctionUrl("validate-admin"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ password }),
  });

  const payload = await parseAdminResponse(response);
  if (!response.ok) {
    throw new Error(
      typeof payload.error === "string" ? payload.error : "Invalid password",
    );
  }

  if (typeof payload.token !== "string" || !payload.token) {
    throw new Error("Admin login did not return a token");
  }

  writeAdminToken(payload.token);
  return payload.token;
}

type AdminSuggestionActionsBody = Record<string, unknown>;

export async function callAdminSuggestionActions(
  body: AdminSuggestionActionsBody,
): Promise<unknown> {
  const token = readAdminToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(getEdgeFunctionUrl("admin-suggestion-actions"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  const payload = await parseAdminResponse(response);
  if (response.status === 401) {
    clearAdminToken();
    throw new Error(adminUnauthorizedMessage(payload));
  }
  if (!response.ok) {
    throw new Error(
      typeof payload.error === "string" ? payload.error : "Request failed",
    );
  }

  return payload;
}

export type PendingSuggestion = {
  id: string;
  raw_text: string;
  public_name: string | null;
  normalized_name: string;
  created_at: string;
};

export type ApprovedSuggestion = {
  id: string;
  public_name: string | null;
  raw_text: string;
  vote_count: number;
};

export function suggestionDisplayName(item: {
  public_name: string | null;
  raw_text: string;
}): string {
  return item.public_name?.trim() || item.raw_text;
}

export async function fetchAdminSuggestions(): Promise<{
  pending: PendingSuggestion[];
  approved: ApprovedSuggestion[];
}> {
  const payload = (await callAdminSuggestionActions({ action: "list" })) as {
    pending?: PendingSuggestion[];
    approved?: ApprovedSuggestion[];
  };

  return {
    pending: payload.pending ?? [],
    approved: payload.approved ?? [],
  };
}

export async function callAdminStoreActions(
  body: AdminSuggestionActionsBody,
): Promise<unknown> {
  const token = readAdminToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(getEdgeFunctionUrl("admin-store-actions"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  const payload = await parseAdminResponse(response);
  if (response.status === 401) {
    clearAdminToken();
    throw new Error(adminUnauthorizedMessage(payload));
  }
  if (!response.ok) {
    throw new Error(
      typeof payload.error === "string" ? payload.error : "Request failed",
    );
  }

  return payload;
}

export type PendingStoreSuggestion = {
  id: string;
  raw_text: string;
  public_name: string | null;
  normalized_name: string;
  city: string | null;
  created_at: string;
};

export type ApprovedStoreSuggestion = {
  id: string;
  public_name: string | null;
  raw_text: string;
  city: string | null;
  vote_count: number;
};

export function storeSuggestionDisplayName(item: {
  public_name: string | null;
  raw_text: string;
  city?: string | null;
}): string {
  const name = item.public_name?.trim() || item.raw_text;
  const city = item.city?.trim();
  return city ? `${name} (${city})` : name;
}

export async function fetchAdminStoreSuggestions(): Promise<{
  pending: PendingStoreSuggestion[];
  approved: ApprovedStoreSuggestion[];
}> {
  const payload = (await callAdminStoreActions({ action: "list" })) as {
    pending?: PendingStoreSuggestion[];
    approved?: ApprovedStoreSuggestion[];
  };

  return {
    pending: payload.pending ?? [],
    approved: payload.approved ?? [],
  };
}

export async function callAdminFindActions(
  body: AdminSuggestionActionsBody,
): Promise<unknown> {
  const token = readAdminToken();
  if (!token) {
    throw new Error("Not authenticated");
  }

  const response = await fetch(getEdgeFunctionUrl("admin-find-actions"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  const payload = await parseAdminResponse(response);
  if (response.status === 401) {
    clearAdminToken();
    throw new Error(adminUnauthorizedMessage(payload));
  }
  if (!response.ok) {
    throw new Error(
      typeof payload.error === "string" ? payload.error : "Request failed",
    );
  }

  return payload;
}

export type PendingFind = {
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

export async function fetchAdminFinds(): Promise<{
  pending: PendingFind[];
}> {
  const payload = (await callAdminFindActions({ action: "list" })) as {
    pending?: PendingFind[];
  };

  return {
    pending: payload.pending ?? [],
  };
}
