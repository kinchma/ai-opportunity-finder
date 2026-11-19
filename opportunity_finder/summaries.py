"""Plain-code summaries the UIs share. No model calls: everything here is derived from the final state."""

ANGLE_MEANING = {
    "quick_win": "Lowest-effort ideas first",
    "highest_value": "Highest-value ideas first",
    "lowest_risk": "Lowest-risk ideas first",
    "enabler": "Foundational ideas (enablers) first",
    "balanced": "Best overall scores first",
    "blend": "Best overall scores",   # older saved runs
}


def left_out_ideas(opportunities: list, recommended: list) -> list:
    """Ideas that are not in the recommended roadmap, best score first, each with a derived reason."""
    picked = [o for o in opportunities if o["name"] in set(recommended)]
    if not picked:
        return []
    lowest = min(o["score"] for o in picked)
    process_owner = {}
    for o in sorted(picked, key=lambda o: -o["score"]):
        process_owner.setdefault(o.get("process"), o)

    rows = []
    for o in sorted((o for o in opportunities if o["name"] not in set(recommended)), key=lambda o: -o["score"]):
        reasons = []
        owner = process_owner.get(o.get("process")) if o.get("process") else None
        if owner and owner["score"] >= o["score"]:
            reasons.append(f"Same process as {owner['name']} ({o['process']}), which scored higher")
        if o["score"] < lowest:
            gap = round(lowest - o["score"], 3)
            reasons.append(f"Scored {o['score']}, {gap} below the lowest pick ({lowest})"
                           + (" - a close call" if gap <= 0.05 else ""))
        if o.get("risk", 0) >= 7:
            reasons.append(f"High risk ({o['risk']}/10)")
        if o.get("effort", 0) >= 7:
            reasons.append(f"High effort ({o['effort']}/10)")
        if not reasons:
            reasons.append(f"Scored {o['score']}, level with the picks, but the roadmap holds at most "
                           f"{len(picked)} ideas")
        rows.append({"name": o["name"], "score": o["score"], "process": o.get("process") or "General",
                     "reason": "; ".join(reasons)})
    return rows


def pruned_rows(pruned_log: list) -> list:
    """The pruned roadmaps, with a plain-English meaning for each angle."""
    return [{"roadmap": p.get("id"), "strategy": ANGLE_MEANING.get(p.get("angle"), p.get("angle")),
             "score": p.get("score"), "why dropped": p.get("reason")} for p in (pruned_log or [])]


def website_check_view(assessment: dict | None) -> dict | None:
    """Display-ready pieces of the website check, shared by the three UIs. None if there is none."""
    if not assessment:
        return None
    rating = assessment["rating"]
    word = "strong" if rating >= 7.5 else "fair" if rating >= 5 else "weak"
    notes = []
    if assessment.get("partial"):
        notes.append("The model's content ratings were unavailable, so this rating uses only the facts code could check.")
    if assessment.get("linkedin_used"):
        notes.append("Text the owner pasted from LinkedIn was used as extra evidence.")
    notes.append(assessment.get("caveat", ""))
    return {"rating": rating, "headline": f"{rating} / 10 ({word})",
            "rows": [{"Check": r["name"], "Score": r["score"],
                      "Rated by": "AI model" if r["basis"] == "model" else "code",
                      "What it found": r["reason"]} for r in assessment["sub_ratings"]],
            "chatbot": assessment["chatbot"]["message"], "chatbot_status": assessment["chatbot"]["status"],
            "prompts": assessment.get("starter_prompts", []), "notes": [n for n in notes if n]}


# ---------------------------------------------------------------- Strategist / Critic / Verifier views

FLAG_LABEL = {
    "injection": "Possible hidden instruction removed from fetched text",
    "close_call": "Close call between the top two roadmaps",
    "practices_empty": "No best practices found",
    "critic_same_model": "Critic ran on the same model as the Strategist",
}


def roadmap_rows(roadmaps: list, pruned_log: list | None = None) -> list:
    """Every roadmap the run compared, best first, then the pruned ones."""
    rows = []
    for r in sorted(roadmaps or [], key=lambda r: -r.get("score", 0)):
        rubric = r.get("rubric")
        rows.append({
            "roadmap": r["id"], "strategy": ANGLE_MEANING.get(r.get("angle"), r.get("angle")),
            "ideas (in order)": " → ".join(r.get("opportunities", [])), "score": r.get("score"),
            "idea average": r.get("base_score"), "penalties": r.get("penalty"),
            "critic rubric (1-5)": (f"{rubric['avg']} (feasibility {rubric['feasibility']}, sequencing "
                                    f"{rubric['sequencing']}, fit {rubric['fit']})" if rubric else "none (coded checks only)"),
            "critic evidence": ", ".join(rubric["evidence"]) if rubric else "",
            "findings": "; ".join(f["message"] for f in r.get("findings", [])) or "none",
            "revised": "; ".join(r.get("changes", [])),
            "narrative by": r.get("narrative_by", ""), "status": "kept"})
    for p in pruned_log or []:
        rows.append({"roadmap": p.get("id"), "strategy": ANGLE_MEANING.get(p.get("angle"), p.get("angle")),
                     "ideas (in order)": "", "score": p.get("score"), "status": f"pruned: {p.get('reason')}"})
    return rows


def evidence_rows(recommendation: dict | None) -> list:
    """One row per recommended idea: what stands behind it, as checked by the Verifier."""
    rows = []
    for c in ((recommendation or {}).get("verification") or {}).get("claims", []):
        parts = []
        for b in c.get("basis", []):
            if b["type"] == "practice":
                parts.append(f"best practice [{b['id']}]")
            elif b["type"] == "process":
                parts.append(f"process '{b['id']}' ({'stated' if b.get('stated') else 'typical for the industry: confirm'})")
            else:
                parts.append(f"website check: {b['id']}")
        cite = c.get("citation")
        rows.append({"idea": c["idea"], "grounded": "yes" if c["grounded"] else "NO",
                     "evidence": "; ".join(parts) or c.get("note", ""),
                     "citation check": f"{cite['status']}: {cite['detail']}" if cite else "no practice cited",
                     "assumption": "yes: owner must confirm" if c.get("assumption") else ""})
    return rows


def flag_rows(flags: list | None) -> list:
    seen, rows = set(), []
    for f in flags or []:
        key = (f.get("type"), f.get("where"), f.get("detail"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"flag": FLAG_LABEL.get(f.get("type"), f.get("type")), "where": f.get("where", ""),
                     "detail": f.get("detail", "")})
    return rows


def run_summary_rows(summary: dict) -> list:
    """Per-agent table of real model calls, tokens and seconds, with a total row."""
    rows = [{"agent": a, "model": ", ".join(v["models"]), "calls": v["calls"], "tokens in": v["input_tokens"],
             "tokens out": v["output_tokens"], "seconds": v["seconds"], "errors": v["errors"]}
            for a, v in summary.get("by_agent", {}).items()]
    rows.append({"agent": "TOTAL", "model": "", "calls": summary.get("calls", 0),
                 "tokens in": summary.get("input_tokens", 0), "tokens out": summary.get("output_tokens", 0),
                 "seconds": summary.get("seconds", 0), "errors": summary.get("errors", 0)})
    return rows
