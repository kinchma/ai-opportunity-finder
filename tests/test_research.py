from opportunity_finder.agents import discovery
from opportunity_finder.tools import kb

DOC = """source: Test Source A
url: https://example.test/a
industries: trailer manufacturing, trailers
---
Quote intake from email is slow and error prone for trailer builders.

Order status questions from dealers repeat all day long.
"""
GENERAL = """source: Test General
url:
industries: *
---
Measure the current process before changing it so savings can be shown.
"""
OTHER = """source: Test Law
url:
industries: law firm, legal
---
Time capture drafts entries from calendar activity for the lawyer to approve.
"""


def make_kb(tmp_path):
    for folder, name, text in [("trailers", "a.md", DOC), ("general", "g.md", GENERAL), ("law", "l.md", OTHER)]:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / name).write_text(text, encoding="utf-8")
    (tmp_path / "README.md").write_text("ignored", encoding="utf-8")
    return tmp_path


def test_retrieve_prefers_matching_industry_and_adds_general(tmp_path):
    hits, note = kb.retrieve("trailer manufacturing", kb_dir=make_kb(tmp_path))
    sources = [h["source"] for h in hits]
    assert sources[0] == "Test Source A" and "Test General" in sources
    assert "Test Law" not in sources and note == ""


def test_unknown_industry_falls_back_to_general_with_note(tmp_path):
    hits, note = kb.retrieve("underwater basket weaving", kb_dir=make_kb(tmp_path))
    assert [h["source"] for h in hits] == ["Test General"]
    assert "no curated sources" in note


def test_starter_kb_covers_the_demo_industries():
    for industry in ("trailer manufacturing", "wholesale distribution", "law firm"):
        hits, note = kb.retrieve(industry)
        assert note == "" and any(not h["general"] for h in hits), industry


class Reply:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {"input_tokens": 50, "output_tokens": 20}


class FakeLLM:
    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def invoke(self, messages):
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return Reply(r)


def research(monkeypatch, tmp_path, llm, industry="trailer manufacturing"):
    monkeypatch.setenv("KB_DIR", str(make_kb(tmp_path)))
    monkeypatch.setattr(discovery, "get_llm", lambda **kw: llm)
    return discovery.discovery_research({"profile": {"industry": industry}})


def test_practices_keep_their_source(monkeypatch, tmp_path):
    out = research(monkeypatch, tmp_path, FakeLLM(
        '{"practices": [{"practice": "Automate quote intake", "why_it_matters": "slow", "chunk_id": "a#1"}]}'))
    bp = out["best_practices"]
    assert bp["practices"][0]["source"] == "Test Source A"
    assert bp["practices"][0]["url"] == "https://example.test/a"
    assert out["model_calls"] == 1 and out["call_log"][0]["input_tokens"] == 50


def test_practice_citing_unknown_chunk_is_dropped(monkeypatch, tmp_path):
    out = research(monkeypatch, tmp_path, FakeLLM(
        '{"practices": [{"practice": "Invented", "why_it_matters": "x", "chunk_id": "zzz#9"},'
        ' {"practice": "Real one", "why_it_matters": "y", "chunk_id": "a#1"}]}'))
    bp = out["best_practices"]
    assert [p["practice"] for p in bp["practices"]] == ["Real one"]
    assert "1 practice(s) dropped" in bp["note"]


def test_bad_json_retries_then_reports(monkeypatch, tmp_path):
    llm = FakeLLM("nope", "still nope")
    out = research(monkeypatch, tmp_path, llm)
    assert llm.calls == 2 and out["best_practices"]["practices"] == []
    assert "valid JSON" in out["best_practices"]["note"]


def test_llm_failure_keeps_sources_and_is_logged(monkeypatch, tmp_path):
    out = research(monkeypatch, tmp_path, FakeLLM(RuntimeError("down")))
    bp = out["best_practices"]
    assert bp["practices"] == [] and "Test Source A" in bp["sources"]
    assert out["call_log"][0]["error"] and "LLM call failed" in bp["note"]


def test_chunk_id_with_brackets_quotes_or_extra_text_still_matches(monkeypatch, tmp_path):
    out = research(monkeypatch, tmp_path, FakeLLM(
        '{"practices": ['
        '{"practice": "One", "why_it_matters": "x", "chunk_id": "[a#1]"},'
        '{"practice": "Two", "why_it_matters": "x", "chunk_id": " \\"A#1\\" "},'
        '{"practice": "Three", "why_it_matters": "x", "chunk_id": "[a#1] (Test Source A)"},'
        '{"practice": "Four", "why_it_matters": "x", "chunk_id": "a#10"}]}'))
    bp = out["best_practices"]
    assert [p["practice"] for p in bp["practices"]] == ["One", "Two", "Three"]
    assert all(p["chunk_id"] == "a#1" for p in bp["practices"])
    assert "1 practice(s) dropped" in bp["note"]


def test_all_practices_dropped_retries_and_keeps_raw_sample(monkeypatch, tmp_path):
    bad = '{"practices": [{"practice": "Nope", "why_it_matters": "x", "chunk_id": "zzz#9"}]}'
    good = '{"practices": [{"practice": "Real", "why_it_matters": "y", "chunk_id": "a#1"}]}'
    llm = FakeLLM(bad, good)
    out = research(monkeypatch, tmp_path, llm)
    bp = out["best_practices"]
    assert llm.calls == 2 and out["model_calls"] == 2
    assert [p["practice"] for p in bp["practices"]] == ["Real"]
    assert "zzz#9" in bp["raw_reply_sample"]


def test_no_usable_practices_is_stated_in_the_note(monkeypatch, tmp_path):
    bad = '{"practices": [{"practice": "Nope", "why_it_matters": "x", "chunk_id": "zzz#9"}]}'
    out = research(monkeypatch, tmp_path, FakeLLM(bad, bad))
    bp = out["best_practices"]
    assert bp["practices"] == [] and "No usable practices" in bp["note"]
    assert "zzz#9" in bp["raw_reply_sample"]
