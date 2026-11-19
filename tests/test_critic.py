"""Critic: exact coded checks, then a rubric from a different model that must cite evidence."""
import re

from opportunity_finder.agents.critic import critic
from opportunity_finder.tools.scoring import risk_limit, roadmap_checks, score_roadmap
from tests.test_strategist import RUN5, opp

BY = {o["name"]: o for o in RUN5}


def codes(findings):
    return sorted(f["code"] for f in findings)


def items(*names):
    return [BY[n] for n in names]


def test_risk_limit_follows_the_owners_tolerance():
    assert (risk_limit(0.0), risk_limit(0.5), risk_limit(1.0)) == (2, 5, 8)


def test_clean_roadmap_has_no_findings():
    assert roadmap_checks(items("Freight KB", "Spec-to-Quote", "Lender Pre-Screener"), 0.4) == []


def test_each_coded_check_fires():
    same_proc = [opp("A", 7, 3, 2, process="Quoting"), opp("B", 6, 3, 2, process="Quoting")]
    assert codes(roadmap_checks(same_proc, 0.4)) == ["duplicate_process"]
    assert roadmap_checks(same_proc, 0.4)[0]["item"] == "B"                       # the weaker one is named
    assert codes(roadmap_checks(items("Spec-to-Quote", "Freight KB"), 0.4)) == ["dependency_order"]
    risky = roadmap_checks(items("Warranty Triage", "Spec-to-Quote"), 0.2)        # limit 3.2, risk 4, pilot
    assert codes(risky) == ["risk_above_tolerance"] and risky[0]["penalty"] == round(0.03 * 0.8 * 2, 3)
    over = roadmap_checks(items("Spec-to-Quote", "Warranty Triage", "Dealer Onboarding"), 0.4, effort_budget=12)
    assert codes(over) == ["over_budget"] and over[0]["item"] == "Warranty Triage" and over[0]["penalty"] == 0.15
    assert codes(roadmap_checks(items("Spec-to-Quote"), 0.4, grounded={"Spec-to-Quote": False})) == ["ungrounded"]
    assert codes(roadmap_checks([opp("P", 7, 3, 2, placeholder=True)], 0.4)) == ["placeholder"]
    assert codes(roadmap_checks(items("Shortage Predictor", "Spec-to-Quote"), 0.4)) == ["pilot_effort"]
    assert codes(roadmap_checks(items("Spec-to-Quote", "Spec-to-Quote"), 0.4)) == ["duplicate"]


def test_rubric_can_only_nudge_the_coded_score():
    its = items("Spec-to-Quote", "Lender Pre-Screener")
    plain = score_roadmap(its, [])
    assert plain["score"] == plain["coded_score"] == round((0.48 + 0.33) / 2, 3)
    assert score_roadmap(its, [], 5)["score"] == round(plain["coded_score"] * 1.15, 3)
    assert score_roadmap(its, [], 1)["score"] == round(plain["coded_score"] * 0.85, 3)
    assert score_roadmap(its, [], 3)["score"] == plain["score"]
    assert score_roadmap(its, [{"penalty": 9}], 5)["score"] == 0.0               # never below zero


def state(roadmaps, **kw):
    return {"scored_opportunities": RUN5, "roadmaps": roadmaps, "profile": {"name": "Acme", "industry": "trailers"},
            "company_input": {"risk_tolerance": 0.4},
            "process_map": {"processes": [{"name": o["process"], "pain_points": [], "basis": "stated"} for o in RUN5]},
            "best_practices": {"practices": [{"practice": "Automate quote intake", "chunk_id": "order-to-delivery#1"}]},
            **kw}


def rm(rid, *names, **kw):
    return {"id": rid, "angle": rid, "opportunities": list(names), "score": 0.0, "rationale": "because", **kw}


TWO = [rm("quick_win", "Website assistant", "Spec-to-Quote", "Freight KB"),
       rm("highest_value", "Spec-to-Quote", "Warranty Triage", "Dealer Onboarding")]


def review(rid, f=4, s=4, fit=4, evidence=("Spec-to-Quote process",), objection="", weakest=None):
    return {"id": rid, "feasibility": f, "sequencing": s, "fit": fit, "evidence": list(evidence),
            "objection": objection, "weakest_item": weakest}


def test_rubric_with_real_evidence_is_kept_and_scores_come_from_code(scripted):
    seen = scripted({"critic": {"reviews": [
        review("quick_win", 5, 5, 5, evidence=["[order-to-delivery#1]"]),
        review("highest_value", 2, 3, 3, objection="Warranty triage is heavy.", weakest="warranty triage")]}})
    out = critic(state(TWO))
    q, h = out["roadmaps"]
    assert out["model_calls"] == 1 and q["rubric"]["evidence"] == ["order-to-delivery#1"] and q["rubric"]["avg"] == 5
    assert q["score"] == round(q["coded_score"] * 1.15, 3) and q["reviewed"] is True
    assert q["penalty"] == 0.05 and codes(q["findings"]) == ["dependency_order"]   # Freight KB placed last
    assert h["rubric"]["weakest_item"] == "Warranty Triage"
    assert "weakest_item" in codes(h["findings"]) and h["score"] < h["coded_score"]
    assert "Coded check findings" in seen["critic"][0] and "risk ratings above 4.4" in seen["critic"][0]


def test_review_without_valid_evidence_is_dropped(scripted):
    scripted({"critic": {"reviews": [review("quick_win", 5, 5, 5, evidence=["trust me"]),
                                     review("highest_value", "great", 3, 3)]}})
    out = critic(state(TWO))
    assert all(r["rubric"] is None and r["score"] == r["coded_score"] for r in out["roadmaps"])
    assert "2 review(s) dropped" in out["trace"][0]


def test_model_failure_leaves_coded_scores_and_logs_the_error(scripted):
    scripted({"critic": RuntimeError("down")})
    out = critic(state(TWO))
    assert out["call_log"][0]["error"] and "coded checks only" in out["trace"][0]
    assert out["roadmaps"][0]["score"] == out["roadmaps"][0]["coded_score"]


def test_reviewed_roadmaps_are_not_sent_to_the_model_again(scripted):
    seen = scripted({"critic": lambda p: {"reviews": [review(i) for i in re.findall(r"Roadmap id: (\S+)", p)]}})
    first = critic(state(TWO))
    again = critic(state(first["roadmaps"] + [rm("lowest_risk", "Freight KB", "Spec-to-Quote", "Lender Pre-Screener")]))
    assert again["model_calls"] == 1 and len(seen["critic"]) == 2
    assert "Roadmap id: quick_win" not in seen["critic"][1] and "Roadmap id: lowest_risk" in seen["critic"][1]
    assert critic(state(again["roadmaps"]))["model_calls"] == 0


def test_same_model_as_the_strategist_is_flagged(scripted, monkeypatch):
    scripted({"critic": {"reviews": [review("quick_win")]}})
    out = critic(state(TWO[:1]))
    assert out["flags"][0]["type"] == "critic_same_model" and "WARNING" in out["trace"][0]
    monkeypatch.setenv("LLM_CRITIC_MODEL", "some-other-model")
    out = critic(state(TWO[:1]))
    assert out["flags"] == [] and out["call_log"][0]["model"] == "some-other-model"


def test_call_cap_means_coded_checks_only(scripted):
    seen = scripted({"critic": {"reviews": [review("quick_win")]}})
    out = critic(state(TWO, model_calls=40))
    assert not seen and out["model_calls"] == 0 and "cap reached" in out["trace"][0]
