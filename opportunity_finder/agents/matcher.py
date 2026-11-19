"""Matcher: fan-in. Proposes candidate AI use cases from the profile, process map and best
practices (LLM), then scores them with exact code. The LLM only gives rough 1-10 ratings."""
from ..tools.scoring import score_opportunity
from .common import ask_json, match_chunk_id

SYSTEM_PROMPT = (
    "You propose AI agent use cases for a small business. Reply with ONLY a JSON object: "
    '{"candidates": [{"name": string, "what_the_agent_does": string, "process": string, '
    '"gap": string, "supporting_chunk_id": string|null, "value": integer, "effort": integer, '
    '"risk": integer, "enabler": boolean, "rating_reason": string}]}. '
    "Propose 5 to 8 candidates. \"process\" must be one of the listed process names. "
    "\"supporting_chunk_id\" must be a chunk id from the listed practices, or null. "
    "\"gap\" is one line on what is manual or missing today. value, effort and risk are integers "
    "from 1 to 10 (value: benefit to the business; effort: how hard to build; risk: harm if the "
    "agent makes a mistake). \"enabler\" is true only for foundation work such as data cleanup or a "
    "knowledge base. Avoid generic ideas that fit any business; tie each one to a listed process."
)

PLACEHOLDER = [  # used only if the model gives too few valid candidates, and flagged as such
    {"name": "Invoice triage", "value": 7, "effort": 3, "risk": 2, "enabler": False},
    {"name": "Dealer Q&A bot", "value": 8, "effort": 5, "risk": 4, "enabler": False},
    {"name": "Order status agent", "value": 6, "effort": 2, "risk": 2, "enabler": False},
    {"name": "Document search (RAG)", "value": 5, "effort": 4, "risk": 2, "enabler": True},
    {"name": "Demand forecast agent", "value": 9, "effort": 8, "risk": 6, "enabler": False},
]
MIN_CANDIDATES = 3
# Fixed, code-set ratings for the website-assistant idea (the LLM did not rate it): moderate
# value, low effort (off-the-shelf widget), low-moderate risk (answers are limited to approved info).
ASSISTANT_RATINGS = {"value": 6, "effort": 3, "risk": 3}


def website_assistant_candidate(assessment: dict | None, tolerance: float) -> dict | None:
    """When the website check found no chat assistant, propose one, scored by the same calculator."""
    if not assessment or assessment.get("chatbot", {}).get("status") != "not_found":
        return None
    prompts = assessment.get("starter_prompts") or []
    c = {"name": "Website AI assistant",
         "what_the_agent_does": "Greets visitors and offers starting choices (" + "; ".join(prompts)
         + "), answers common questions from approved business information, and hands off to a person.",
         "process": None, "gap": assessment["chatbot"]["message"], "supporting_chunk_id": None,
         "enabler": False, "rating_reason": "ratings set by code (fixed defaults), not by the model",
         "placeholder": False, "from_website_check": True, "starter_prompts": prompts, **ASSISTANT_RATINGS}
    c["score"] = score_opportunity(c["value"], c["effort"], c["risk"], tolerance)
    return c


def _rating(v) -> int | None:
    try:
        return max(1, min(10, int(round(float(v)))))
    except (TypeError, ValueError):
        return None


def _make_validator(process_names: list, chunk_ids: set):
    canon = {n.lower(): n for n in process_names}

    def validate(data: dict | None):
        if not data or not isinstance(data.get("candidates"), list):
            return None
        kept, dropped, seen = [], 0, set()
        for c in data["candidates"]:
            if not isinstance(c, dict):
                dropped += 1
                continue
            name = str(c.get("name", "")).strip()
            proc = canon.get(str(c.get("process", "")).strip().lower())
            chunk = match_chunk_id(c.get("supporting_chunk_id"), {i: i for i in chunk_ids})
            v, e, r = _rating(c.get("value")), _rating(c.get("effort")), _rating(c.get("risk"))
            if not name or name.lower() in seen or None in (v, e, r) or not (proc or chunk):
                dropped += 1  # needs a name, valid ratings and a real process or practice behind it
                continue
            seen.add(name.lower())
            kept.append({"name": name, "what_the_agent_does": str(c.get("what_the_agent_does", "")).strip(),
                         "process": proc, "gap": str(c.get("gap", "")).strip(), "supporting_chunk_id": chunk,
                         "value": v, "effort": e, "risk": r, "enabler": bool(c.get("enabler")),
                         "rating_reason": str(c.get("rating_reason", "")).strip()})
        return {"kept": kept[:8], "dropped": dropped}
    return validate


def matcher(state: dict) -> dict:
    profile = state.get("profile", {})
    tolerance = state.get("company_input", {}).get("risk_tolerance", 0.5)
    processes = state.get("process_map", {}).get("processes", [])
    practices = state.get("best_practices", {}).get("practices", [])
    names = [p["name"] for p in processes]
    chunk_ids = {p["chunk_id"] for p in practices}

    proc_txt = "\n".join(f"- {p['name']}: {p['description']} (pain points: {', '.join(p['pain_points']) or 'none listed'})"
                         for p in processes) or "(none identified)"
    prac_txt = "\n".join(f"- [{p['chunk_id']}] {p['practice']}" for p in practices) or "(none)"
    user_msg = (f"Business: {profile.get('name', 'unknown')}\nIndustry: {profile.get('industry', 'unknown')}\n\n"
                f"Processes:\n{proc_txt}\n\nBest practices:\n{prac_txt}")
    raw: list = []
    result, records, note = ask_json("matcher", [("system", SYSTEM_PROMPT), ("human", user_msg)],
                                     _make_validator(names, chunk_ids), raw_out=raw)

    candidates, placeholder = (result or {}).get("kept", []), False
    if result and result["dropped"]:
        note = (note + f" {result['dropped']} candidate(s) dropped (no valid process or practice, or bad ratings).").strip()
    if len(candidates) < MIN_CANDIDATES:
        placeholder = True
        candidates = [{**c, "process": None, "supporting_chunk_id": None, "what_the_agent_does": "",
                       "gap": "", "rating_reason": "placeholder"} for c in PLACEHOLDER]
        note = (note + " too few valid candidates: using PLACEHOLDER opportunities.").strip()
    if chunk_ids and candidates and not placeholder and not any(c["supporting_chunk_id"] for c in candidates):
        note = (note + f" no candidate cites a practice ({len(chunk_ids)} available).").strip()
        if records and raw:  # keep a sample of the raw reply so the cause can be diagnosed
            records[-1]["reply_sample"] = raw[-1]
    for c in candidates:  # scoring is exact code, not the LLM
        c["placeholder"] = placeholder
        c["score"] = score_opportunity(c["value"], c["effort"], c["risk"], tolerance)
    extra = website_assistant_candidate(state.get("website_assessment"), tolerance)
    if extra and extra["name"].lower() not in {c["name"].lower() for c in candidates}:
        candidates.append(extra)
        note = (note + " added a website AI assistant (no chat widget found on the site).").strip()
    gap_report = [{"process": c["process"], "gap": c["gap"], "opportunity": c["name"],
                   "supporting_chunk_id": c["supporting_chunk_id"]} for c in candidates if c["gap"]]
    return {"gap_report": gap_report, "scored_opportunities": candidates,
            "model_calls": len(records), "call_log": records,
            "trace": [f"matcher: {len(candidates)} candidates scored" + (f" [{note}]" if note else "")]}
