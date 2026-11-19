"""What stands behind an idea (rule 3: cite or drop). Shared by the Critic and the Verifier.

An idea is grounded when at least one of these is true:
  - it names a process that is in the process map,
  - it cites a best practice that Discovery kept (so the passage id was really retrieved),
  - it came from the website check (code found no chat assistant on the site).
Placeholder ideas are never grounded. A process the mapper marked "typical" still counts, but
is reported as an assumption the owner must confirm.

RAG seam: when company documents and interviews get their own collections, add them here as
new basis types; callers only read `grounded`, `basis` and `assumption`.
"""


def grounding(opp: dict, process_map: dict | None, best_practices: dict | None,
              website_assessment: dict | None = None) -> dict:
    if opp.get("placeholder"):
        return {"grounded": False, "basis": [], "assumption": False, "note": "placeholder idea"}
    processes = {p["name"]: p for p in (process_map or {}).get("processes", [])}
    practices = {p["chunk_id"]: p for p in (best_practices or {}).get("practices", [])}
    basis = []
    cid = opp.get("supporting_chunk_id")
    if cid and cid in practices:
        basis.append({"type": "practice", "id": cid, "source": practices[cid].get("source", "")})
    proc = processes.get(opp.get("process"))
    if proc:
        basis.append({"type": "process", "id": proc["name"], "stated": proc.get("basis") == "stated"})
    if opp.get("from_website_check") and (website_assessment or {}).get("chatbot", {}).get("status") == "not_found":
        basis.append({"type": "website_check", "id": "no chat assistant found on the site"})
    only_typical = bool(basis) and all(b["type"] == "process" and not b["stated"] for b in basis)
    return {"grounded": bool(basis), "basis": basis, "assumption": only_typical,
            "note": "" if basis else "no process, cited practice or website finding"}


def grounded_map(opps: list, state: dict) -> dict:
    """{idea name: True/False} for a list of ideas, using the run's state."""
    return {o["name"]: grounding(o, state.get("process_map"), state.get("best_practices"),
                                 state.get("website_assessment"))["grounded"] for o in opps}
