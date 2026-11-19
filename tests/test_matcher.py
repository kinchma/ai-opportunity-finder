from opportunity_finder.agents import common
from opportunity_finder.agents.matcher import matcher
from opportunity_finder.agents.process_mapper import process_mapper

STATE = {
    "profile": {"name": "Acme", "industry": "trailer manufacturing"},
    "company_input": {"risk_tolerance": 0.4, "description": "We build custom trailers."},
    "site_text": "Custom cargo trailers. Dealer network. Request a quote.",
    "process_map": {"processes": [
        {"name": "Quoting", "description": "d", "pain_points": ["slow"], "basis": "stated"},
        {"name": "Order status", "description": "d", "pain_points": [], "basis": "typical"}]},
    "best_practices": {"practices": [{"practice": "Automate quote intake", "chunk_id": "a#1"}]},
}


class Reply:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {"input_tokens": 100, "output_tokens": 50}


class FakeLLM:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def invoke(self, messages):
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return Reply(r)


def cand(name, process="Quoting", chunk=None, v=7, e=3, r=2, **kw):
    import json
    return {"name": name, "what_the_agent_does": "x", "process": process, "gap": "manual today",
            "supporting_chunk_id": chunk, "value": v, "effort": e, "risk": r, "enabler": False,
            "rating_reason": "because", **kw}


def reply(*cands):
    import json
    return json.dumps({"candidates": list(cands)})


def run_matcher(monkeypatch, llm):
    monkeypatch.setattr(common, "get_llm", lambda **kw: llm)
    return matcher(STATE)


def test_valid_candidates_are_scored_by_code(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(cand("Quote intake"), cand("Status bot", "Order status"),
                                                 cand("Practice only", process="Nope", chunk="a#1"))))
    opps = out["scored_opportunities"]
    assert [o["name"] for o in opps] == ["Quote intake", "Status bot", "Practice only"]
    assert opps[0]["score"] == round(max(7 - 0.5 * 3 - 0.6 * 2, 0) / 10, 3)
    assert opps[2]["process"] is None and opps[2]["supporting_chunk_id"] == "a#1"
    assert not any(o["placeholder"] for o in opps) and out["model_calls"] == 1


def test_ungrounded_duplicate_and_unrated_candidates_are_dropped(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(
        cand("Good one"), cand("good one"),                       # duplicate (case-insensitive)
        cand("Floating idea", process="Made up", chunk="zzz#9"),  # no valid process or practice
        cand("No ratings", v="lots"),                             # bad rating
        cand("Second", "Order status"), cand("Third", "Quoting"), cand("Fourth", "Quoting"))))
    names = [o["name"] for o in out["scored_opportunities"]]
    assert names == ["Good one", "Second", "Third", "Fourth"]
    assert "dropped" in out["trace"][0]


def test_ratings_are_clamped(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(cand("A", v=99, e=-4, r=3), cand("B"), cand("C"))))
    a = out["scored_opportunities"][0]
    assert (a["value"], a["effort"]) == (10, 1)


def test_too_few_valid_candidates_uses_flagged_placeholder(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(cand("Only one"))))
    opps = out["scored_opportunities"]
    assert len(opps) == 5 and all(o["placeholder"] for o in opps)
    assert "PLACEHOLDER" in out["trace"][0]


def test_llm_failure_falls_back_and_logs_error(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(RuntimeError("down")))
    assert out["call_log"][0]["error"] and out["scored_opportunities"][0]["placeholder"]


def test_process_mapper_cleans_the_list(monkeypatch):
    import json
    reply_ = json.dumps({"processes": [
        {"name": "Quoting", "description": "d", "pain_points": ["a", "b", "c", "d"], "basis": "stated"},
        {"name": "quoting", "description": "dup"},
        {"name": "Invoicing", "description": "d", "basis": "weird"}, {"name": ""}]})
    monkeypatch.setattr(common, "get_llm", lambda **kw: FakeLLM(reply_))
    out = process_mapper(STATE)
    procs = out["process_map"]["processes"]
    assert [p["name"] for p in procs] == ["Quoting", "Invoicing"]
    assert len(procs[0]["pain_points"]) == 3 and procs[1]["basis"] == "typical"
    assert "confirm with the owner" in out["process_map"]["note"]


def test_process_mapper_failure_gives_empty_map(monkeypatch):
    monkeypatch.setattr(common, "get_llm", lambda **kw: FakeLLM(RuntimeError("down")))
    out = process_mapper(STATE)
    assert out["process_map"]["processes"] == [] and out["call_log"][0]["error"]


def test_chunk_id_with_brackets_or_extra_text_counts_as_a_citation(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(
        cand("One", chunk="[a#1]"), cand("Two", "Order status", chunk=" 'A#1' "),
        cand("Three", chunk="[a#1] Automate quote intake"), cand("Four", chunk="a#10"))))
    cited = {o["name"]: o["supporting_chunk_id"] for o in out["scored_opportunities"]}
    assert cited == {"One": "a#1", "Two": "a#1", "Three": "a#1", "Four": None}


def test_no_citations_is_noted_and_keeps_a_reply_sample(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(
        cand("One", chunk="zzz#1"), cand("Two", "Order status"), cand("Three"))))
    assert "no candidate cites a practice" in out["trace"][0]
    assert "zzz#1" in out["call_log"][-1]["reply_sample"]


def test_no_note_or_sample_when_a_candidate_is_cited(monkeypatch):
    out = run_matcher(monkeypatch, FakeLLM(reply(
        cand("One", chunk="a#1"), cand("Two", "Order status"), cand("Three"))))
    assert "no candidate cites" not in out["trace"][0]
    assert "reply_sample" not in out["call_log"][-1]
