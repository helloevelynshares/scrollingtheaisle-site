"""Reachability probes: can each active tracker be selected via reasonable NL?"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable

from .catalog import ActiveTracker, load_active_trackers
from .language_model import LanguageProfile, build_language_profiles, normalize_alias


@dataclass(frozen=True)
class ReachabilityProbe:
    tracker_id: str
    query: str
    probe_kind: str
    next_action: str | None
    selected_id: str | None
    reachable: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _candidate_queries(tracker: ActiveTracker, profile: LanguageProfile) -> list[tuple[str, str]]:
    """Return (probe_kind, query) pairs — reasonable shopper utterances."""
    price = "$2.49"
    store = "Safeway"
    names: list[tuple[str, str]] = []
    if profile.safe_short_name:
        names.append(("safe_short", profile.safe_short_name))
    if profile.brand and normalize_alias(profile.brand) != normalize_alias(
        profile.safe_short_name or ""
    ):
        names.append(("brand", profile.brand))
    names.append(("display", profile.display_name))
    if profile.protected_phrases:
        names.append(("protected", profile.protected_phrases[0]))
    for inc in list(tracker.include)[:4]:
        names.append(("include", inc))
    for alias in list(tracker.aliases)[:4]:
        names.append(("alias", alias))
    # Deduplicate
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for kind, name in names:
        n = (name or "").strip()
        if not n:
            continue
        key = normalize_alias(n)
        if key in seen:
            continue
        seen.add(key)
        out.append((kind, f"{store} {n} are {price}"))
    return out


def probe_reachability(
    *,
    run_query: Callable[[str], dict[str, Any]] | None = None,
    trackers: list[ActiveTracker] | None = None,
) -> list[ReachabilityProbe]:
    """Run NL probes for every active tracker via the production AisleCheck contract."""
    if run_query is None:
        from shopper_query.aislecheck_contract import run_aislecheck_query

        run_query = run_aislecheck_query

    trackers = trackers or load_active_trackers()
    profiles = {p.tracker_id: p for p in build_language_profiles(trackers)}
    results: list[ReachabilityProbe] = []

    for tracker in trackers:
        profile = profiles[tracker.id]
        probes = _candidate_queries(tracker, profile)
        if not probes:
            results.append(
                ReachabilityProbe(
                    tracker_id=tracker.id,
                    query="",
                    probe_kind="none",
                    next_action=None,
                    selected_id=None,
                    reachable=False,
                    notes="no_candidate_queries",
                )
            )
            continue
        best: ReachabilityProbe | None = None
        for kind, query in probes:
            try:
                resp = run_query(query)
            except Exception as exc:  # noqa: BLE001
                probe = ReachabilityProbe(
                    tracker_id=tracker.id,
                    query=query,
                    probe_kind=kind,
                    next_action="error",
                    selected_id=None,
                    reachable=False,
                    notes=str(exc)[:200],
                )
                results.append(probe)
                continue
            selected = (resp.get("selected_tracker") or {}).get("id")
            action = resp.get("next_action")
            plausible_ids = [
                p.get("id") for p in (resp.get("plausible_trackers") or []) if p.get("id")
            ]
            ok = selected == tracker.id and action in {"continue", "clarify"}
            # Clarify with correct selected tracker still counts as reachable.
            if selected == tracker.id and action == "clarify":
                ok = True
            # One structured product clarify that lists this tracker is reachable.
            if (
                not ok
                and action == "clarify"
                and tracker.id in plausible_ids
                and resp.get("clarify_kind") == "ambiguous_product"
            ):
                ok = True
                notes = "plausible_clarify:" + ",".join(resp.get("reason_codes") or [])
            else:
                notes = ",".join(resp.get("reason_codes") or [])[:200]
            probe = ReachabilityProbe(
                tracker_id=tracker.id,
                query=query,
                probe_kind=kind,
                next_action=action,
                selected_id=selected,
                reachable=ok,
                notes=notes[:200],
            )
            results.append(probe)
            if ok and best is None:
                best = probe
                # Still record other probes for audit; no early stop so we see gaps.
        if best is None and probes:
            # Mark summary row
            results.append(
                ReachabilityProbe(
                    tracker_id=tracker.id,
                    query="(summary)",
                    probe_kind="summary",
                    next_action=None,
                    selected_id=None,
                    reachable=False,
                    notes="no_probe_selected_this_tracker",
                )
            )
        elif best is not None:
            results.append(
                ReachabilityProbe(
                    tracker_id=tracker.id,
                    query=best.query,
                    probe_kind="summary",
                    next_action=best.next_action,
                    selected_id=best.selected_id,
                    reachable=True,
                    notes=f"via:{best.probe_kind}",
                )
            )
    return results


def summarize_reachability(probes: list[ReachabilityProbe]) -> dict[str, Any]:
    summaries = [p for p in probes if p.probe_kind == "summary"]
    reachable = [p for p in summaries if p.reachable]
    unreachable = [p for p in summaries if not p.reachable]
    return {
        "active_trackers": len(summaries),
        "reachable": len(reachable),
        "unreachable": len(unreachable),
        "unreachable_ids": [p.tracker_id for p in unreachable],
    }
