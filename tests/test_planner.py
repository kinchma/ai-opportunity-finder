"""Verifier/Planner: code decides pass or fail; the model only checks citations, and code checks its quote."""
import re

from opportunity_finder.agents.planner import planner, quote_in_passage
from opportunity_finder.supervisor import after_verification, review_decision
from opportunity_finder.tools import kb
from tests.test_strategist import opp

PASSAGE = kb.get_passages(["order-to-delivery#1"])["order-to-delivery#1"]["text"]
QUOTE = " ".join(PASSAGE.split()[:8])

OPPS = [opp("Quote intake", 8, 4, 2, process="Quoting", supporting_chunk_id="order-to-delivery#1"),
        opp("Status bot", 7, 3, 2, process="Order status"),
        opp("Typical only", 6, 3, 2, process="Scheduling"),
        opp("Floating A", 9, 2, 1, process="Not in the map"),
        opp("Floating B", 9, 2, 1, process=None),
        opp("Cited only", 7, 3, 2, process=None, supporting_chunk_id="order-to-delivery#1")]


def state(*names, practices=True, second=None, **kw):
    roadmaps = [{"id": "best", "angle": "balanced", "opportunities": list(names), "score": 0.5}]
    if second:
        roadmaps.append({"id": "second", "angle": "quick_win", "opportunities": ["Status bot"], "score": second})
    return {"scored_opportunities": OPPS, "roadmaps": roadmaps, "status": "running",
            "process_map": {"processes": [{"name": "Quoting", "basis": "stated"}, {"name": "Order status", "basis": "stated"},
                                          {"name": "Scheduling", "basis": "typical"}]},
            "best_practices": {"practices": [{"practice": "Automate quote intake", "chunk_id": "order-to-delivery#1",
                                              "source": "note"}] if practices else []}, **kw}


def checker(supported=True, quote=QUOTE):
    return lambda p: {"checks": [{"name": n, "supported": supported, "quote": quote, "reason": "r"}
                                 for n in re.findall(r"Idea: (.+)", p)]}


def test_quote_must_really_be_in_the_passage():
    assert quote_in_passage(QUOTE.upper() + "!!", PASSAGE)
    assert not quote_in_passage("Trailers are best sold with free ponies", PASSAGE)
    assert not quote_in_passage("Quote and", PASSAGE)          # too short to count


def test_grounded_roadmap_passes_and_shows_its_evidence(scripted):
    scripted({"planner": checker()})
    out = planner(state("Quote intake", "Status bot", "Typical only", second=0.3))
    rec = out["final_recommendation"]
    assert out["verified"] is True and out["status"] == "complete" and out["model_calls"] == 1
    claims = {c["idea"]: c for c in rec["verification"]["claims"]}
    assert claims["Quote intake"]["citation"] == {"status": "confirmed", "detail": QUOTE}
    assert {b["type"] for b in claims["Quote intake"]["basis"]} == {"practice", "process"}
    assert claims["Typical only"]["assumption"] is True and claims["Status bot"]["assumption"] is False
    assert rec["verification"]["coverage"] == 1.0 and rec["runner_up"]["id"] == "second"
    assert rec["close_call"] is False and out["flags"] == []


def test_made_up_quote_leaves_the_citation_unconfirmed_but_the_id_still_counts(scripted):
    scripted({"planner": checker(quote="completely invented words that are not there")})
    out = planner(state("Quote intake"))
    c = out["final_recommendation"]["verification"]["claims"][0]
    assert c["citation"]["status"] == "unconfirmed" and c["grounded"] and out["verified"]


def test_citation_the_model_rejects_no_longer_counts(scripted):
    scripted({"planner": checker(supported=False)})
    out = planner(state("Cited only", "Floating B", "Status bot"))
    report = out["verification_report"]
    assert out["verified"] is False and report["coverage"] == 0.33
    assert sorted(report["rejected"]) == ["Cited only", "Floating B"] == out["failed_claims"]
    assert out["verification_failures"] == 1 and out["review_round"] == 0 and out["escalate_now"] is False
    assert out["final_recommendation"]["unverified_draft"] is True
    assert after_verification({**out}) == "revise"


def test_one_ungrounded_idea_in_three_still_passes_but_is_reported(scripted):
    scripted({"planner": checker()})
    out = planner(state("Quote intake", "Status bot", "Floating A"))
    assert out["verified"] and out["verification_report"]["coverage"] == 0.67
    assert out["verification_report"]["rejected"] == ["Floating A"]


def test_placeholder_ideas_fail_verification():
    ph = [{**o, "placeholder": True} for o in OPPS[:2]]
    out = planner({**state("Quote intake", "Status bot"), "scored_opportunities": ph, "verification_failures": 1})
    assert out["verified"] is False and out["verification_failures"] == 2
    assert "placeholder" in out["trace"][0] and after_verification(out) == "escalate"


def test_no_practices_goes_straight_to_the_owner():
    out = planner(state("Status bot", "Typical only", practices=False))
    assert out["verified"] is False and out["escalate_now"] is True
    assert out["flags"] == [{"type": "practices_empty", "detail": "Discovery returned no usable best practices"}]
    assert after_verification(out) == "escalate"               # on the first failure, not the second


def test_close_call_is_flagged_with_the_runner_up(scripted):
    scripted({"planner": checker()})
    out = planner(state("Quote intake", "Status bot", second=0.47))
    rec = out["final_recommendation"]
    assert rec["close_call"] is True and rec["lead_margin"] == round((0.5 - 0.47) / 0.47, 3)
    assert out["flags"][0]["type"] == "close_call" and "CLOSE CALL" in out["trace"][0] and out["verified"]


def test_no_roadmap_at_all_fails_cleanly():
    out = planner({**state(), "roadmaps": []})
    assert out["verified"] is False and out["final_recommendation"]["agents_to_build"] == []


def test_supervisor_rules_for_the_new_paths():
    assert after_verification({"verified": False, "status": "partially_complete"}) == "escalate"
    close = [{"score": 1.01}, {"score": 1.0}]
    assert review_decision({"roadmaps": close, "review_round": 1, "revision_exhausted": True}) == "finalize"
    assert review_decision({"roadmaps": close, "review_round": 1}) == "revise"
    assert review_decision({"roadmaps": [], "review_round": 1}) == "finalize"


def test_call_cap_checks_citations_by_id_only(scripted):
    seen = scripted({"planner": checker()})
    out = planner(state("Quote intake", model_calls=40))
    assert not seen and out["model_calls"] == 0 and out["verified"] and "cap reached" in out["trace"][0]
