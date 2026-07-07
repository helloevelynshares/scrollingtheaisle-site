import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  callAdminStoreActions,
  clearAdminToken,
  fetchAdminStoreSuggestions,
  readAdminToken,
  storeSuggestionDisplayName,
  validateAdminPassword,
  type ApprovedStoreSuggestion,
  type PendingStoreSuggestion,
} from "../../lib/adminApi";

type PendingDraft = {
  publicName: string;
  mergeIntoId: string;
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

function emptyDraft(): PendingDraft {
  return {
    publicName: "",
    mergeIntoId: "",
    adminNotes: "",
  };
}

export function AdminStoresApp() {
  const [authenticated, setAuthenticated] = useState(() => Boolean(readAdminToken()));
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState<PendingStoreSuggestion[]>([]);
  const [approved, setApproved] = useState<ApprovedStoreSuggestion[]>([]);
  const [drafts, setDrafts] = useState<Record<string, PendingDraft>>({});
  const [loading, setLoading] = useState(false);
  const [signingIn, setSigningIn] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const loadSuggestions = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchAdminStoreSuggestions();
      setPending(data.pending);
      setApproved(data.approved);
      setDrafts((current) => {
        const next: Record<string, PendingDraft> = {};
        for (const item of data.pending) {
          next[item.id] = current[item.id] ?? {
            ...emptyDraft(),
            publicName: item.raw_text,
          };
        }
        return next;
      });
    } catch (loadError) {
      const text =
        loadError instanceof Error ? loadError.message : "Could not load store suggestions";
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
      void loadSuggestions();
    }
  }, [authenticated, loadSuggestions]);

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
    setApproved([]);
    setDrafts({});
    setMessage("");
    setError("");
  }

  function updateDraft(itemId: string, patch: Partial<PendingDraft>) {
    setDrafts((current) => ({
      ...current,
      [itemId]: {
        ...(current[itemId] ?? emptyDraft()),
        ...patch,
      },
    }));
  }

  async function runAction(
    itemId: string,
    body: Record<string, unknown>,
    successMessage: string,
  ) {
    setBusyId(itemId);
    setError("");
    setMessage("");
    try {
      await callAdminStoreActions(body);
      setMessage(successMessage);
      await loadSuggestions();
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
          <h1>Review suggested grocery stores</h1>
          <p className="admin-suggestions-lead">
            Sign in to review pending store suggestions from the homepage.
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
            <h1>Review suggested grocery stores</h1>
            <p className="admin-suggestions-lead">
              Approve new stores for the public voting list, reject duplicates, or merge
              into an existing approved store.
            </p>
          </div>
          <button type="button" className="btn btn-secondary btn-sm" onClick={handleSignOut}>
            Sign out
          </button>
        </header>

        {message ? <p className="admin-suggestions-message">{message}</p> : null}
        {error ? <p className="admin-suggestions-error">{error}</p> : null}

        {loading ? (
          <p className="admin-suggestions-loading">Loading pending store suggestions…</p>
        ) : pending.length === 0 ? (
          <p className="admin-suggestions-empty">No pending store suggestions right now.</p>
        ) : (
          <ul className="admin-suggestions-list">
            {pending.map((item) => {
              const draft = drafts[item.id] ?? emptyDraft();
              const isBusy = busyId === item.id;
              return (
                <li key={item.id} className="admin-suggestions-item">
                  <div className="admin-suggestions-item-meta">
                    <strong>{item.raw_text}</strong>
                    {item.city ? <span>City: {item.city}</span> : null}
                    <span>Submitted {formatTimestamp(item.created_at)}</span>
                    <span>Normalized: {item.normalized_name}</span>
                  </div>

                  <label className="admin-suggestions-field">
                    Public name
                    <input
                      type="text"
                      value={draft.publicName}
                      onChange={(event) =>
                        updateDraft(item.id, { publicName: event.target.value })
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
                        updateDraft(item.id, { adminNotes: event.target.value })
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
                          item.id,
                          {
                            action: "approve",
                            itemId: item.id,
                            publicName: draft.publicName.trim() || item.raw_text,
                          },
                          `Approved “${draft.publicName.trim() || item.raw_text}”.`,
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
                          item.id,
                          {
                            action: "reject",
                            itemId: item.id,
                            adminNotes: draft.adminNotes.trim() || null,
                          },
                          `Rejected “${item.raw_text}”.`,
                        )
                      }
                    >
                      Reject
                    </button>
                  </div>

                  <div className="admin-suggestions-merge">
                    <label className="admin-suggestions-field">
                      Merge into approved store
                      <select
                        value={draft.mergeIntoId}
                        onChange={(event) =>
                          updateDraft(item.id, { mergeIntoId: event.target.value })
                        }
                        disabled={isBusy}
                      >
                        <option value="">Select approved store…</option>
                        {approved.map((target) => (
                          <option key={target.id} value={target.id}>
                            {storeSuggestionDisplayName(target)} ({target.vote_count} votes)
                          </option>
                        ))}
                      </select>
                    </label>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={isBusy || !draft.mergeIntoId}
                      onClick={() =>
                        void runAction(
                          item.id,
                          {
                            action: "merge",
                            itemId: item.id,
                            mergeIntoId: draft.mergeIntoId,
                            adminNotes: draft.adminNotes.trim() || null,
                            addVoteOnMerge: true,
                          },
                          `Merged “${item.raw_text}” into an approved store.`,
                        )
                      }
                    >
                      Merge (+1 vote)
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
