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
    cases.save(case_id, "profile.json", vals.get("profile", {}), base)
    cases.set_stage(case_id, "discovered", base)
    return vals.get("profile", {})


def confirm(case_id: str, corrections: dict | None = None, base=None) -> dict:
    profile = {**cases.load(case_id, "profile.json", {}, base), **(corrections or {})}
    cases.save(case_id, "profile.json", profile, base)
    cases.add_decision(case_id, "profile_confirmed", corrections or {}, base)
    cases.set_stage(case_id, "confirmed", base)
    return profile


def analyze(case_id: str, base=None) -> dict:
    meta = cases.load_case(case_id, base)
    disc = cases.load(case_id, "discovery.json", {}, base)
    docs = cases.load_documents(case_id, base)
    seed = {"company_input": meta["company_input"], "profile": cases.load(case_id, "profile.json", {}, base),
            "site_text": disc.get("site_text", ""), "documents": docs, "intake_confirmed": True,
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
