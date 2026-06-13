const TOKEN_TTL_MS = 8 * 60 * 60 * 1000;

function bytesToBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlToBytes(value: string): Uint8Array {
  const padded = value.replace(/-/g, "+").replace(/_/g, "/");
  const padLength = (4 - (padded.length % 4)) % 4;
  const binary = atob(padded + "=".repeat(padLength));
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function signPayload(payload: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(payload),
  );
  return bytesToBase64Url(new Uint8Array(signature));
}

export async function createAdminToken(secret: string): Promise<string> {
  const expiresAt = Date.now() + TOKEN_TTL_MS;
  const payload = `${expiresAt}`;
  const signature = await signPayload(payload, secret);
  return `${payload}.${signature}`;
}

export async function verifyAdminToken(
  token: string | null,
  secret: string,
): Promise<boolean> {
  if (!token || !secret) {
    return false;
  }

  const [expiresRaw, signature] = token.split(".");
  if (!expiresRaw || !signature) {
    return false;
  }

  const expiresAt = Number(expiresRaw);
  if (!Number.isFinite(expiresAt) || expiresAt < Date.now()) {
    return false;
  }

  const expected = await signPayload(expiresRaw, secret);
  return expected === signature;
}

export function getBearerToken(req: Request): string | null {
  const header = req.headers.get("authorization") ?? req.headers.get("Authorization");
  if (!header) {
    return null;
  }
  const match = header.match(/^Bearer\s+(.+)$/i);
  return match?.[1]?.trim() ?? null;
}

export function getAdminPassword(): string | null {
  return Deno.env.get("ADMIN_PASSWORD") ?? null;
}
