import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  callAdminFindActions,
  clearAdminToken,
  fetchAdminFinds,
  readAdminToken,
  validateAdminPassword,
  type PendingFind,
} from "../../lib/adminApi";

type PendingDraft = {
  itemName: string;
  priceDisplay: string;
  storeName: string;
  locationLabel: string;
  notes: string;
  adminNotes: string;
};

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function emptyDraft(find: PendingFind): PendingDraft {
  return {
    itemName: find.item_name,
    priceDisplay: find.price_display ?? String(find.price),
    storeName: find.store_name,
    locationLabel: find.location_label ?? "",
    notes: find.notes ?? "",
    adminNotes: "",
  };
}

export function AdminFindsApp() {
  const [authenticated, setAuthenticated] = useState(() => Boolean(readAdminToken()));
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState<PendingFind[]>([]);
  const [drafts, setDrafts] = useState<Record<string, PendingDraft>>({});
  const [loading, setLoading] = useState(false);
  const [signingIn, setSigningIn] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadFinds = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchAdminFinds();
      setPending(data.pending);
      setDrafts((current) => {
        const next: Record<string, PendingDraft> = {};
        for (const find of data.pending) {
          next[find.id] = current[find.id] ?? emptyDraft(find);
        }
        return next;
      });
    } catch (loadError) {
      const text =
        loadError instanceof Error ? loadError.message : "Could not load pending finds";
      setError(text);
      if (text.includes("Sign in again")) {
        setAuthenticated(false);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authenticated) {
      void loadFinds();
    }
  }, [authenticated, loadFinds]);

  async function handleSignIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSigningIn(true);
    setError("");
    try {
      await validateAdminPassword(password);
      setPassword("");
      setAuthenticated(true);
    } catch (signInError) {
      setError(
        signInError instanceof Error ? signInError.message : "Sign in failed",
      );
    } finally {
      setSigningIn(false);
    }
  }

  function handleSignOut() {
    clearAdminToken();
    setAuthenticated(false);
    setPending([]);
    setDrafts({});
    setMessage("");
    setError("");
  }

  function updateDraft(findId: string, patch: Partial<PendingDraft>) {
    setDrafts((current) => ({
      ...current,
      [findId]: {
        ...(current[findId] ?? emptyDraft(pending.find((item) => item.id === findId)!)),
        ...patch,
      },
    }));
  }

  async function runAction(
    findId: string,
    body: Record<string, unknown>,
    successMessage: string,
  ) {
    setBusyId(findId);
    setError("");
    setMessage("");
    try {
      await callAdminFindActions(body);
      setMessage(successMessage);
      await loadFinds();
    } catch (actionError) {
      const text =
        actionError instanceof Error ? actionError.message : "Action failed";
      setError(text);
      if (text.includes("Sign in again")) {
        setAuthenticated(false);
      }
    } finally {
      setBusyId(null);
    }
  }

  if (!authenticated) {
    return (
      <main className="page-main admin-suggestions-main">
        <section className="admin-suggestions-panel">
          <h1>Review grocery finds</h1>
          <p className="admin-suggestions-lead">
            Sign in to approve or reject pending finds before they go live.
          </p>
          <form className="admin-suggestions-signin" onSubmit={handleSignIn}>
            <label htmlFor="admin-password">Admin password</label>
            <input
              id="admin-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              disabled={signingIn}
            />
            <button type="submit" className="btn btn-primary" disabled={signingIn || !password}>
              {signingIn ? "Signing in…" : "Sign in"}
            </button>
          </form>
          {error ? <p className="admin-suggestions-error">{error}</p> : null}
        </section>
      </main>
    );
  }

  return (
    <main className="page-main admin-suggestions-main">
      <section className="admin-suggestions-panel">
        <header className="admin-suggestions-header">
          <div>
            <h1>Review grocery finds</h1>
            <p className="admin-suggestions-lead">
              Approve finds for the public feed or reject spam and duplicates. Edit
              details before approving if needed.
            </p>
          </div>
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleSignOut}>
            Sign out
          </button>
        </header>

        {message ? <p className="admin-suggestions-message">{message}</p> : null}
        {error ? <p className="admin-suggestions-error">{error}</p> : null}

        {loading ? (
          <p className="admin-suggestions-loading">Loading pending finds…</p>
        ) : pending.length === 0 ? (
          <p className="admin-suggestions-empty">No pending grocery finds right now.</p>
        ) : (
          <ul className="admin-suggestions-list">
            {pending.map((find) => {
              const draft = drafts[find.id] ?? emptyDraft(find);
              const isBusy = busyId === find.id;
              return (
                <li key={find.id} className="admin-suggestions-item admin-finds-item">
                  {find.photo_url ? (
                    <a
                      href={find.photo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="admin-finds-photo-link"
                    >
                      <img
                        src={find.photo_url}
                        alt={`Photo for ${find.item_name}`}
                        className="admin-finds-photo"
                      />
                    </a>
                  ) : null}

                  <div className="admin-suggestions-item-meta">
                    <strong>{find.item_name}</strong>
                    <span>
                      {find.price_display ?? `$${find.price}`} · {find.store_name}
                    </span>
                    {find.location_label ? <span>Location: {find.location_label}</span> : null}
                    {find.notes ? <span>Notes: {find.notes}</span> : null}
                    <span>Submitted {formatTimestamp(find.created_at)}</span>
                    {find.ai_extracted ? <span>AI-assisted submission</span> : null}
                  </div>

                  <label className="admin-suggestions-field">
                    Item name
                    <input
                      type="text"
                      value={draft.itemName}
                      onChange={(event) =>
                        updateDraft(find.id, { itemName: event.target.value })
                      }
                      disabled={isBusy}
                    />
                  </label>

                  <label className="admin-suggestions-field">
                    Price
                    <input
                      type="text"
                      value={draft.priceDisplay}
                      onChange={(event) =>
                        updateDraft(find.id, { priceDisplay: event.target.value })
                      }
                      disabled={isBusy}
                    />
                  </label>

                  <label className="admin-suggestions-field">
                    Store
                    <input
                      type="text"
                      value={draft.storeName}
                      onChange={(event) =>
                        updateDraft(find.id, { storeName: event.target.value })
                      }
                      disabled={isBusy}
                    />
                  </label>

                  <label className="admin-suggestions-field">
                    Location
                    <input
                      type="text"
                      value={draft.locationLabel}
                      onChange={(event) =>
                        updateDraft(find.id, { locationLabel: event.target.value })
                      }
                      disabled={isBusy}
                    />
                  </label>

                  <label className="admin-suggestions-field">
                    Notes
                    <input
                      type="text"
                      value={draft.notes}
                      onChange={(event) =>
                        updateDraft(find.id, { notes: event.target.value })
                      }
                      disabled={isBusy}
                    />
                  </label>

                  <label className="admin-suggestions-field">
                    Admin notes
                    <input
                      type="text"
                      value={draft.adminNotes}
                      onChange={(event) =>
                        updateDraft(find.id, { adminNotes: event.target.value })
                      }
                      disabled={isBusy}
                    />
                  </label>

                  <div className="admin-suggestions-actions">
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      disabled={isBusy}
                      onClick={() =>
                        void runAction(
                          find.id,
                          {
                            action: "approve",
                            findId: find.id,
                            itemName: draft.itemName.trim(),
                            priceDisplay: draft.priceDisplay.trim(),
                            storeName: draft.storeName.trim(),
                            locationLabel: draft.locationLabel.trim() || null,
                            notes: draft.notes.trim() || null,
                            adminNotes: draft.adminNotes.trim() || null,
                          },
                          `Approved “${draft.itemName.trim() || find.item_name}”.`,
                        )
                      }
                    >
                      Approve
                    </button>

                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={isBusy}
                      onClick={() =>
                        void runAction(
                          find.id,
                          {
                            action: "reject",
                            findId: find.id,
                            adminNotes: draft.adminNotes.trim() || null,
                          },
                          `Rejected “${find.item_name}”.`,
                        )
                      }
                    >
                      Reject
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </main>
  );
}
