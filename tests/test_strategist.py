"""Strategist: code builds distinct roadmaps and revises them; the model only narrates."""
import re

from opportunity_finder.agents.strategist import build_roadmaps, revise, strategist
from opportunity_finder.tools.scoring import score_opportunity


def opp(name, v, e, r, process=None, enabler=False, **kw):
    return {"name": name, "value": v, "effort": e, "risk": r, "enabler": enabler,
            "process": process or f"{name} process", "supporting_chunk_id": None, "placeholder": False,
            "what_the_agent_does": f"does {name}", "score": score_opportunity(v, e, r, 0.4), **kw}


# the seven ideas from Carmate run 5, where the old Strategist returned blend_1 == blend_2
RUN5 = [opp("Spec-to-Quote", 8, 4, 2), opp("Dealer Onboarding", 7, 5, 3), opp("Warranty Triage", 8, 6, 4),
        opp("Lender Pre-Screener", 7, 5, 2), opp("Shortage Predictor", 6, 7, 3),
        opp("Freight KB", 5, 4, 1, enabler=True), opp("Website assistant", 6, 3, 3)]


def narrator(prompt):
    return {"roadmaps": [{"id": i, "rationale": f"Why {i} works.", "pilot_reason": "Fast.", "assumption": "Data exists."}
                         for i in re.findall(r"Roadmap id: (\S+)", prompt)]}


def state(opps=RUN5, **kw):
    return {"scored_opportunities": opps, "profile": {"name": "Acme", "industry": "trailers"},
            "company_input": {"risk_tolerance": 0.4}, **kw}


def sets(roadmaps):
    return [frozenset(r["opportunities"]) for r in roadmaps]


def test_four_angles_hold_four_different_sets_of_ideas():
    roadmaps, notes = build_roadmaps(RUN5)
    assert [r["id"] for r in roadmaps] == ["highest_value", "quick_win", "lowest_risk", "enabler"]
    assert len(set(sets(roadmaps))) == 4 and all(len(r["opportunities"]) == 3 for r in roadmaps)
    assert roadmaps[3]["opportunities"][0] == "Freight KB"          # enabler-first puts foundation work first
    assert roadmaps[1]["opportunities"][0] == "Website assistant"   # quick win starts with the lowest effort


def test_an_angle_that_repeats_a_set_swaps_in_its_next_idea():
    # four ideas where value order and score order pick the same top three
    opps = [opp("A", 9, 2, 1), opp("B", 8, 2, 1), opp("C", 7, 2, 1), opp("D", 6, 2, 1)]
    roadmaps, _ = build_roadmaps(opps)
    assert len(set(sets(roadmaps))) == len(roadmaps) >= 2


def test_no_enabler_means_a_balanced_roadmap_instead():
    roadmaps, _ = build_roadmaps([o for o in RUN5 if not o["enabler"]])
    assert [r["angle"] for r in roadmaps][-1] == "balanced"


def test_three_or_fewer_ideas_give_one_roadmap():
    roadmaps, notes = build_roadmaps(RUN5[:3])
    assert len(roadmaps) == 1 and roadmaps[0]["angle"] == "balanced" and "no alternatives" in notes[0]
    assert build_roadmaps([]) == ([], ["no eligible ideas"])


def test_model_writes_the_narrative_but_cannot_change_the_ideas(scripted):
    seen = scripted({"strategist": lambda p: {"roadmaps": narrator(p)["roadmaps"] + [
        {"id": "made_up", "rationale": "extra"}, {"id": "quick_win", "rationale": "second copy ignored"}]}})
    out = strategist(state())
    assert out["model_calls"] == 1 and len(out["call_log"]) == 1
    assert [r["id"] for r in out["roadmaps"]] == ["highest_value", "quick_win", "lowest_risk", "enabler"]
    assert all(r["narrative_by"] == "model" and r["rationale"].startswith("Why") for r in out["roadmaps"])
    assert "data, not instructions" not in seen["strategist"][0]  # that warning lives in the system prompt
    assert out["roadmaps"][1]["rationale"] == "Why quick_win works."


def test_model_failure_gives_code_written_narrative_flagged_as_code(scripted):
    scripted({"strategist": RuntimeError("server down")})
    out = strategist(state())
    assert all(r["narrative_by"] == "code" and r["rationale"] for r in out["roadmaps"])
    assert out["call_log"][0]["error"] and "LLM call failed" in out["trace"][0]


def test_revision_swaps_out_the_idea_the_critic_flagged(scripted):
    scripted({"strategist": narrator})
    kept = [{"id": "highest_value", "angle": "highest_value", "score": 0.3, "reviewed": True,
             "opportunities": ["Spec-to-Quote", "Warranty Triage", "Dealer Onboarding"],
             "findings": [{"code": "risk_above_tolerance", "item": "Warranty Triage", "penalty": 0.03,
                           "message": "too risky", "limit": 3.2}]}]
    out = strategist(state(roadmaps=kept, review_round=1))
    new = out["roadmaps"][-1]
    assert new["id"] == "highest_value_r1" and new["parent"] == "highest_value"
    assert "Warranty Triage" not in new["opportunities"] and "replaced Warranty Triage" in new["changes"][0]
    assert all(o["risk"] <= 3.2 for o in RUN5 if o["name"] in new["opportunities"])
    assert out["revision_exhausted"] is False and out["model_calls"] == 1


def test_revision_reorders_foundation_work_and_the_pilot():
    by = {o["name"]: o for o in RUN5}
    r = {"id": "x", "angle": "balanced", "opportunities": ["Shortage Predictor", "Spec-to-Quote", "Freight KB"],
         "findings": [{"code": "dependency_order", "item": None, "penalty": 0.05, "message": "m"},
                      {"code": "pilot_effort", "item": None, "penalty": 0.03, "message": "m"}]}
    new = revise(r, RUN5, 2, set(), {})
    assert new["opportunities"] == ["Freight KB", "Spec-to-Quote", "Shortage Predictor"] and by


def test_nothing_to_revise_stops_the_loop_without_a_model_call(scripted):
    seen = scripted({"strategist": narrator})
    kept = [{"id": "quick_win", "angle": "quick_win", "score": 0.3, "findings": [], "reviewed": True,
             "opportunities": ["Website assistant", "Spec-to-Quote", "Freight KB"]}]
    out = strategist(state(roadmaps=kept, review_round=1))
    assert out["revision_exhausted"] is True and out["model_calls"] == 0 and not seen
    assert out["roadmaps"] == kept


def test_retry_leaves_out_ideas_the_verifier_rejected(scripted):
    scripted({"strategist": narrator})
    out = strategist(state(failed_claims=["Spec-to-Quote", "Website assistant"]))
    used = {n for r in out["roadmaps"] for n in r["opportunities"]}
    assert not used & {"Spec-to-Quote", "Website assistant"} and "left out 2 idea(s)" in out["trace"][0]


def test_model_call_cap_skips_the_narrative_call(scripted):
    seen = scripted({"strategist": narrator})
    out = strategist(state(model_calls=40))
    assert not seen and out["model_calls"] == 0 and "cap reached" in out["trace"][0]
