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

export async function validateAdminPassword(password: string): Promise<string> {
  const response = await fetch(getEdgeFunctionUrl("validate-admin"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ password }),
  });

  const payload = await response.json().catch(() => ({}));
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

  const payload = await response.json().catch(() => ({}));
  if (response.status === 401) {
    clearAdminToken();
    throw new Error("Session expired. Sign in again.");
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
