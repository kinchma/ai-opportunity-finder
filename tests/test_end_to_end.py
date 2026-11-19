"""End-to-end runs through the real graph and case folders, with a scripted fake model per agent.

Two customers: Carmate (replies taken from saved run 5) and Brightline Bookkeeping (synthetic,
with planted traps). These prove the wiring and the coded rules; they say nothing about how
good a real model's answers are (that is what the runs on the Omen are for).
"""
import re

from opportunity_finder import case_runner, cases
from opportunity_finder.observability import summarize
from opportunity_finder.tools.scoring import risk_limit


def narrator(prompt):
    return {"roadmaps": [{"id": i, "rationale": f"Order for {i} fits this business.", "pilot_reason": "Quick start.",
                          "assumption": "Staff will use it."} for i in re.findall(r"Roadmap id: (\S+)", prompt)]}


def reviewer(evidence, ratings=(4, 4, 4)):
    f, s, fit = ratings
    return lambda p: {"reviews": [{"id": i, "feasibility": f, "sequencing": s, "fit": fit, "evidence": [evidence],
                                   "objection": "", "weakest_item": None}
                                  for i in re.findall(r"Roadmap id: (\S+)", p)]}


def citation_checker(reject=()):
    """Supports every idea with a real quote from its passage, except the ideas in `reject`."""
    def reply(prompt):
        checks = []
        for name, passage in re.findall(r"Idea: (.+)\n.*\nPassage \[[^\]]+\]:\n(.+)", prompt):
            ok = name not in reject
            checks.append({"name": name, "supported": ok, "reason": "matches" if ok else "different practice",
                           "quote": " ".join(passage.split()[:8]) if ok else ""})
        return {"checks": checks}
    return reply


def script_for(fx, **overrides):
    return {"discovery_research": {"practices": fx["practices"]}, "process_mapper": {"processes": fx["processes"]},
            "matcher": {"candidates": fx["candidates"]}, "strategist": narrator,
            "critic": reviewer(fx["processes"][0]["name"]), "planner": citation_checker(), **overrides}


def run_case(tmp_path, fx, discovery=None):
    cid = cases.create_case(fx["company_input"].get("name") or fx["profile"]["name"], fx["company_input"], tmp_path)
    if discovery:   # a case whose Discovery already ran (website cases): seed what it saved
        cases.save(cid, "discovery.json", discovery, tmp_path)
        cases.save(cid, "profile.json", discovery["profile"], tmp_path)
        cases.set_stage(cid, "discovered", tmp_path)   # as a real Discovery run would leave it
    else:           # no website: the synthetic profile path, no model call
        case_runner.discover(cid, tmp_path)
    case_runner.confirm(cid, {}, tmp_path)
    return cid, case_runner.analyze(cid, tmp_path)


def common_checks(result):
    """Things that must hold for every finished run."""
    log = result["call_log"]
    assert result["model_calls"] == len(log) and not any(c.get("stub") for c in log)   # honest counting
    assert summarize(log)["calls"] == result["model_calls"]
    final = result["roadmaps"]
    assert len({frozenset(r["opportunities"]) for r in final} | {tuple(r["opportunities"]) for r in final}) >= len(final)
    assert len({tuple(r["opportunities"]) for r in final}) == len(final)               # no identical roadmaps
    assert not any(r["id"].startswith("blend") for r in final)


def test_carmate_end_to_end(tmp_path, scripted, fixture_case, monkeypatch):
    fx = fixture_case("carmate")
    monkeypatch.setenv("LLM_CRITIC_MODEL", "critic-model")     # the Critic on a different model
    seen = scripted(script_for(fx))
    disc = {"profile": fx["profile"], "site_text": fx["company_input"]["description"],
            "website_assessment": fx["website_assessment"], "model_calls": 0, "call_log": [], "trace": []}
    cid, result = run_case(tmp_path, fx, disc)
    common_checks(result)

    assert result["status"] == "complete" and result["verified"] is True and not result.get("verification_failures")
    rec = result["final_recommendation"]
    assert rec["roadmap"]["opportunities"][0] == "Spec-to-Quote Extractor Agent"       # the top-scored idea leads
    assert rec["verification"]["coverage"] == 1.0 and rec["verification"]["passed"]
    assert all(c["grounded"] for c in rec["verification"]["claims"])
    assert rec["roadmap"]["narrative_by"] == "model" and rec["roadmap"]["rubric"]["evidence"]
    assert rec["runner_up"] and rec["runner_up"]["opportunities"] != rec["roadmap"]["opportunities"]

    # round 1 offered four different sets of ideas (the old code offered the same top three twice)
    first = re.findall(r"Roadmap id: (\S+)", seen["strategist"][0])
    assert first == ["highest_value", "quick_win", "lowest_risk", "enabler"]
    s = summarize(result["call_log"])
    assert set(s["calls_by_agent"]) == {"discovery_research", "process_mapper", "matcher", "strategist", "critic", "planner"}
    assert s["by_agent"]["critic"]["models"] == ["critic-model"] != s["by_agent"]["strategist"]["models"]
    assert not any(f["type"] == "critic_same_model" for f in result["flags"])
    assert result["model_calls"] <= 12                          # well under the cap of 40
    assert cases.load_case(cid, tmp_path)["status"] == "Recommendation ready."
    assert list((cases.case_dir(cid, tmp_path) / "runs").glob("*.json"))


def test_brightline_cautious_owner_gets_a_safe_grounded_roadmap(tmp_path, scripted, fixture_case):
    fx = fixture_case("brightline")
    scripted(script_for(fx))
    cid, result = run_case(tmp_path, fx)
    common_checks(result)
    by = {o["name"]: o for o in result["scored_opportunities"]}

    assert "Crypto portfolio advisor" not in by                 # no real process or practice: dropped by the Matcher
    assert "1 candidate(s) dropped" in " ".join(result["trace"])
    assert result["status"] == "complete" and result["verified"] is True
    picks = result["final_recommendation"]["roadmap"]["opportunities"]
    limit = risk_limit(0.2)
    assert "Autonomous tax return filer" not in picks           # highest value, but far above this owner's risk limit
    assert all(by[n]["risk"] <= limit for n in picks)
    assert sum(by[n]["effort"] for n in picks) <= fx["company_input"]["effort_budget"]
    # Evaluation-log example: the picks written BEFORE the run expected the knowledge base; the
    # agent chose the quicker invoice follow-up instead (2 of 3 agree) and flagged a close call
    # whose runner-up is the roadmap with the knowledge base. That goes in the evaluation log.
    assert len(set(picks) & set(fx["expected_top_picks"])) == 2
    rec = result["final_recommendation"]
    assert rec["close_call"] and "Engagement knowledge base" in rec["runner_up"]["opportunities"]
    assert "Engagement knowledge base" in rec["close_call_detail"]
    # the risky roadmap was penalised by a coded check, not by the model
    risky = [p for p in result["pruned_log"] if p["id"] == "highest_value"] or \
            [r for r in result["roadmaps"] if r["id"] == "highest_value"]
    assert risky and risky[0]["score"] < result["final_recommendation"]["roadmap"]["score"]


def test_brightline_bad_citations_fail_then_the_retry_passes(tmp_path, scripted, fixture_case):
    """The retry path is real: the Verifier rejects two ideas whose cited passage does not support
    them, the Strategist rebuilds without them, and the second verification passes."""
    fx = fixture_case("brightline")
    for c in fx["candidates"]:                                  # two ideas that rest ONLY on a citation
        if c["name"] in ("Client document chaser", "New-client intake summarizer"):
            c["process"] = "Front desk"                         # not in the process map
    bad = ("Client document chaser", "New-client intake summarizer")
    scripted(script_for(fx, planner=citation_checker(reject=bad)))
    cid, result = run_case(tmp_path, fx)
    common_checks(result)

    assert result["verification_failures"] == 1 and result["verified"] is True and result["status"] == "complete"
    assert sorted(result["failed_claims"]) == sorted(bad)
    assert not set(bad) & set(result["final_recommendation"]["roadmap"]["opportunities"])
    trace = " | ".join(result["trace"])
    assert "verification failed (1)" in trace and "left out 2 idea(s)" in trace
    assert trace.index("verification failed (1)") < trace.index("planner: verified")


def test_two_failures_escalate_with_a_decision_card(tmp_path, scripted, fixture_case):
    fx = fixture_case("brightline")
    for c in fx["candidates"]:                                  # every idea rests only on a citation ...
        c["process"], c["supporting_chunk_id"] = "Front desk", c["supporting_chunk_id"] or "smb-ai-adoption#2"
    reject_all = lambda p: {"checks": [{"name": n, "supported": False, "quote": "", "reason": "unrelated"}   # noqa: E731
                                       for n in re.findall(r"Idea: (.+)", p)]}
    scripted(script_for(fx, planner=reject_all))                # ... and the Verifier rejects them all
    cid, result = run_case(tmp_path, fx)
    assert result["status"] == "needs_owner_help" and result["verified"] is False
    assert result["verification_failures"] == 2
    card = result["escalation"]
    assert [c["id"] for c in card["choices"]] == ["accept_draft", "add_information", "stop"]
    assert "failed verification 2 time(s)" in card["reason"] and card["what_is_uncertain"]
    assert result["final_recommendation"]["unverified_draft"] is True
    assert cases.load_case(cid, tmp_path)["status"].startswith("Needs the owner")
    case_runner.owner_decision(cid, "add_information", tmp_path)
    assert cases.load(cid, "decisions.json", [], tmp_path)[-1]["detail"] == {"choice": "add_information"}


def test_empty_practices_escalate_on_the_first_failure(tmp_path, scripted, fixture_case):
    fx = fixture_case("brightline")
    scripted(script_for(fx, discovery_research={"practices": []}))
    cid, result = run_case(tmp_path, fx)
    assert result["status"] == "needs_owner_help" and result["verification_failures"] == 1
    assert any(f["type"] == "practices_empty" for f in result["flags"])
    assert "No best practices" in result["escalation"]["reason"]


def test_ranking_is_stable_across_risk_settings(tmp_path, scripted, fixture_case):
    """Ranking-stability metric (Checkpoint 6.1): the same business under a cautious, a middle and
    a risk-tolerant owner. The top roadmap holds, and the risk-9 idea is never recommended."""
    picks = {}
    for tolerance in (0.2, 0.5, 0.9):
        fx = fixture_case("brightline")
        fx["company_input"]["risk_tolerance"] = tolerance
        scripted(script_for(fx))
        cid, result = run_case(tmp_path / str(tolerance), fx)
        picks[tolerance] = result["final_recommendation"]["roadmap"]["opportunities"]
        assert "Autonomous tax return filer" not in picks[tolerance]
    assert picks[0.2] == picks[0.5] == picks[0.9]


def test_unreachable_model_server_is_named_as_the_cause(tmp_path, scripted, fixture_case):
    """Real run on Nov 14: the Mac was unreachable, every call timed out, and the card blamed
    missing best practices. The card must lead with the failed model calls."""
    fx = fixture_case("brightline")
    down = RuntimeError("Request timed out.")
    scripted({a: down for a in ("discovery_research", "process_mapper", "matcher", "strategist", "critic", "planner")})
    cid, result = run_case(tmp_path, fx)
    card = result["escalation"]
    assert result["status"] == "needs_owner_help"
    assert "model call(s) failed" in card["reason"] and "model server" in card["reason"]
    assert any("Request timed out" in u for u in card["what_is_uncertain"])
