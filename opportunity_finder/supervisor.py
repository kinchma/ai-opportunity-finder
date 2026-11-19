"""Rule-based Supervisor logic. No LLM anywhere in this file.

Pure functions so they can be unit tested without a model.
"""
from .config import SETTINGS, Settings


def prune_roadmaps(roadmaps: list, k: int):
    """Keep the top k by score. Return (kept, log_entries) for the pruned ones."""
    ranked = sorted(roadmaps, key=lambda r: r["score"], reverse=True)
    kept, dropped = ranked[:k], ranked[k:]
    log = [
        {"id": r["id"], "angle": r["angle"], "score": r["score"],
         "reason": f"ranked below top {k}"}
        for r in dropped
    ]
    return kept, log


def lead_margin(roadmaps: list) -> float:
    """How far the best roadmap leads the second best, as a fraction."""
    scores = sorted((r["score"] for r in roadmaps), reverse=True)
    if len(scores) < 2:
        return float("inf") if scores else 0.0
    top, second = scores[0], scores[1]
    if second <= 0:
        return float("inf") if top > 0 else 0.0
    return (top - second) / second


def review_gate(state: dict, settings: Settings = SETTINGS) -> dict:
    """Node: runs after the Critic. Prunes, logs, counts the round, flags the cap."""
    kept, log = prune_roadmaps(state.get("roadmaps", []), settings.keep_top_k)
    rnd = state.get("review_round", 0) + 1
    margin = lead_margin(kept)
    lead = "n/a" if margin == float("inf") else f"{margin:.1%}"
    update = {
        "roadmaps": kept,
        "pruned_log": log,
        "review_round": rnd,
        "trace": [f"review_gate: round {rnd}, kept {len(kept)}, pruned {len(log)}, best leads by {lead}"],
    }
    if state.get("model_calls", 0) >= settings.max_model_calls:
        update["status"] = "partially_complete"
    return update


def review_decision(state: dict, settings: Settings = SETTINGS) -> str:
    """Conditional edge after review_gate: 'revise' or 'finalize'."""
    if state.get("model_calls", 0) >= settings.max_model_calls:
        return "finalize"
    if state.get("review_round", 0) >= settings.max_review_rounds:
        return "finalize"
    if not state.get("roadmaps") or state.get("revision_exhausted"):
        return "finalize"  # nothing to compare, or the Strategist has no revision left to offer
    if lead_margin(state.get("roadmaps", [])) >= settings.early_stop_margin:
        return "finalize"
    return "revise"


def after_verification(state: dict, settings: Settings = SETTINGS) -> str:
    """Conditional edge after the Planner: 'done', 'revise' or 'escalate'."""
    if state.get("verified"):
        return "done"
    if state.get("escalate_now") or state.get("status") == "partially_complete":
        return "escalate"  # a retry cannot fix it (no practices), or the call budget is spent
    if state.get("verification_failures", 0) >= settings.max_verification_failures:
        return "escalate"
    return "revise"
