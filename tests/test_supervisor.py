from opportunity_finder.config import Settings
from opportunity_finder.main import run
from opportunity_finder.supervisor import (after_verification, lead_margin,
                                           prune_roadmaps, review_decision, review_gate)


def rm(i, score):
    return {"id": i, "angle": i, "opportunities": [], "score": score}


def test_prune_keeps_top_k_and_logs():
    kept, log = prune_roadmaps([rm("a", .9), rm("b", .5), rm("c", .4), rm("d", .1)], 3)
    assert [r["id"] for r in kept] == ["a", "b", "c"]
    assert [e["id"] for e in log] == ["d"]


def test_lead_margin():
    assert abs(lead_margin([rm("a", 1.1), rm("b", 1.0)]) - 0.10) < 1e-9
    assert lead_margin([rm("a", 1.0)]) == float("inf")


def test_early_stop_on_margin():
    state = {"roadmaps": [rm("a", 1.2), rm("b", 1.0)], "review_round": 1, "model_calls": 5}
    assert review_decision(state) == "finalize"


def test_revise_when_close_and_rounds_left():
    state = {"roadmaps": [rm("a", 1.05), rm("b", 1.0)], "review_round": 1, "model_calls": 5}
    assert review_decision(state) == "revise"


def test_stops_at_round_cap():
    state = {"roadmaps": [rm("a", 1.01), rm("b", 1.0)], "review_round": 3, "model_calls": 5}
    assert review_decision(state) == "finalize"


def test_call_cap_marks_partial():
    s = Settings(max_model_calls=10)
    state = {"roadmaps": [rm("a", 1), rm("b", 1)], "model_calls": 10}
    assert review_gate(state, s)["status"] == "partially_complete"
    assert review_decision({**state, "review_round": 1}, s) == "finalize"


def test_verification_routing():
    assert after_verification({"verified": True}) == "done"
    assert after_verification({"verified": False, "verification_failures": 1}) == "revise"
    assert after_verification({"verified": False, "verification_failures": 2}) == "escalate"


def test_placeholder_run_is_escalated_not_passed():
    """No website and a model that returns nothing: only placeholder ideas and no practices.
    The old stub Planner marked this run verified; now the Supervisor hands it to the owner."""
    result = run({"name": "Test Co", "industry": "x", "risk_tolerance": 0.4}, thread_id="t1")
    assert result["status"] == "needs_owner_help" and result["verified"] is False
    assert result["intake_confirmed"] is True
    assert len(result["roadmaps"]) <= 3
    assert result["escalation"]["choices"] and result["escalation"]["what_is_uncertain"]
    assert result["final_recommendation"]["unverified_draft"] is True
