"""Run the pipeline one stage at a time, saving to the case folder after each stage.

    discover(case_id)            -> Discovery (profile + website check), saved; waits for the owner
    confirm(case_id, corrections)-> owner confirms or corrects the profile, saved
    analyze(case_id)             -> the rest of the pipeline from the saved profile (and any documents)

Each stage can run in a fresh Python process: it loads what it needs from disk. The graph is
re-entered after `owner_confirm` with the saved state (graph.update_state), so the agents and
Supervisor logic are exactly the ones in graph.py.
"""
from . import cases
from .graph import build_graph
from .observability import write_run_log


def discover(case_id: str, base=None) -> dict:
    meta = cases.load_case(case_id, base)
    graph, cfg = build_graph(), {"configurable": {"thread_id": case_id}}
    graph.invoke({"company_input": meta["company_input"], "status": "running"}, cfg)  # pauses at owner_confirm
    vals = graph.get_state(cfg).values
    keep = ("profile", "site_text", "website_assessment", "model_calls", "call_log", "trace", "flags")
    cases.save(case_id, "discovery.json", {k: vals[k] for k in keep if k in vals}, base)
    profile = {**vals.get("profile", {}), "confirmed_by_owner": False}
    cases.save(case_id, "profile.json", profile, base)
    cases.set_stage(case_id, "discovered", base)  # a fresh Discovery always needs a fresh confirmation
    return profile


class ConfirmationRequired(RuntimeError):
    """Raised when the analysis is asked to run before the owner has confirmed the profile (or
    after the owner rejected it). The gate is enforced here, in the one function every entry
    point (UI, CLI, tests, a resumed case) goes through, not only shown as a button."""


def confirm(case_id: str, corrections: dict | None = None, base=None, note: str = "") -> dict:
    """The owner accepts the discovered profile, with or without corrections. A correction is
    kept on the profile as owner-provided evidence (it outranks the website guess). Accepting
    again after a rejection is the renewed acceptance that lets the case proceed."""
    meta = cases.load_case(case_id, base)
    if meta["stage"] not in ("discovered", "rejected", "confirmed", "analyzed"):
        raise ConfirmationRequired("run Discovery before confirming the profile")
    corrections = {k: v for k, v in (corrections or {}).items() if v not in (None, "")}
    profile = {**cases.load(case_id, "profile.json", {}, base), **corrections}
    profile["confirmed_by_owner"] = True
    profile["owner_corrections"] = {**profile.get("owner_corrections", {}), **corrections}
    if corrections:
        profile["confidence"] = "owner-confirmed"
        profile["evidence"] = (f"Owner corrected: {', '.join(f'{k} = {v}' for k, v in corrections.items())}. "
                               + (profile.get("evidence") or "")).strip()
    if note:
        profile["owner_note"] = note
    cases.save(case_id, "profile.json", profile, base)
    cases.add_decision(case_id, "profile_confirmed", {"corrections": corrections, "note": note,
                                                      "after_rejection": meta["stage"] == "rejected"}, base)
    cases.set_stage(case_id, "confirmed", base)
    return profile


def reject(case_id: str, reason: str = "", base=None) -> dict:
    """The owner rejects the discovered profile. The case stops here: analyze() refuses to run
    until the owner confirms a corrected profile."""
    meta = cases.load_case(case_id, base)
    if meta["stage"] == "new":
        raise ConfirmationRequired("nothing to reject: run Discovery first")
    profile = cases.load(case_id, "profile.json", {}, base)
    profile["confirmed_by_owner"] = False
    cases.save(case_id, "profile.json", profile, base)
    cases.add_decision(case_id, "profile_rejected", {"reason": reason}, base)
    return cases.set_stage(case_id, "rejected", base)


def confirmation_ok(case_id: str, base=None) -> tuple[bool, str]:
    """(True, "") when the owner's acceptance is on record and newer than the last Discovery run,
    otherwise (False, why). Read from disk so a restored case is judged by what was saved."""
    meta = cases.load_case(case_id, base)
    if meta["stage"] in ("new", "discovered"):
        return False, "the owner has not confirmed the discovered profile"
    if meta["stage"] == "rejected":
        return False, "the owner rejected the discovered profile; confirm a corrected profile to continue"
    profile = cases.load(case_id, "profile.json", {}, base)
    if not profile.get("confirmed_by_owner"):
        return False, "profile.json does not carry the owner's confirmation"
    kinds = [d["kind"] for d in cases.load(case_id, "decisions.json", [], base)]
    if "profile_confirmed" not in kinds:
        return False, "no profile_confirmed decision on record"
    if "profile_rejected" in kinds and kinds[::-1].index("profile_rejected") < kinds[::-1].index("profile_confirmed"):
        return False, "the latest owner decision is a rejection"
    return True, ""


def analyze(case_id: str, base=None) -> dict:
    ok, why = confirmation_ok(case_id, base)
    if not ok:
        raise ConfirmationRequired(why)
    meta = cases.load_case(case_id, base)
    disc = cases.load(case_id, "discovery.json", {}, base)
    docs = cases.load_documents(case_id, base)
    chunks = cases.document_chunks(case_id, base)
    seed = {"company_input": meta["company_input"], "profile": cases.load(case_id, "profile.json", {}, base),
            "site_text": disc.get("site_text", ""), "documents": docs, "document_chunks": chunks,
            "intake_confirmed": True,
            "status": "running", "model_calls": disc.get("model_calls", 0),
            "call_log": disc.get("call_log", []), "trace": disc.get("trace", []),
            "flags": disc.get("flags", [])}
    if disc.get("website_assessment"):
        seed["website_assessment"] = disc["website_assessment"]
    graph, cfg = build_graph(), {"configurable": {"thread_id": case_id}}
    graph.update_state(cfg, seed, as_node="owner_confirm")  # continue as if the owner just confirmed
    graph.invoke(None, cfg)
    result = graph.get_state(cfg).values
    pmap = result.get("process_map", {})
    note = (f"built from {len(docs)} owner document(s)" if docs else "built from the website and description only")
    cases.save_process_map(case_id, pmap, note, base)
    cases.save(case_id, "result.json", result, base)
    write_run_log(result, case_id, cases.case_dir(case_id, base) / "runs")
    cases.set_stage(case_id, "analyzed", base)
    if result.get("status") == "needs_owner_help":  # the Supervisor escalated: say so on the case
        cases.update_case(case_id, base, status="Needs the owner: " + result.get("escalation", {}).get("reason", ""))
    return result


def owner_decision(case_id: str, choice: str, base=None) -> None:
    """Record the owner's answer to an escalation card (accept_draft | add_information | stop)."""
    cases.add_decision(case_id, "escalation_answer", {"choice": choice}, base)
    text = {"accept_draft": "Owner accepted the draft as an UNVERIFIED starting point.",
            "add_information": "Owner will add information; re-run the analysis when it arrives.",
            "stop": "Owner stopped this case."}.get(choice, f"Owner chose: {choice}")
    cases.update_case(case_id, base, status=text)


def share(case_id: str, source_root, include=None, base=None) -> dict:
    """Owner authorizes company material for the analysis. Allowed only once the owner has
    confirmed the profile, so documents never reach a case the owner has not accepted."""
    ok, why = confirmation_ok(case_id, base)
    if not ok:
        raise ConfirmationRequired(f"share material after the owner confirms the profile ({why})")
    return cases.share_materials(case_id, source_root, include, base)
