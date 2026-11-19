"""Hybrid retrieval (Chroma vectors + BM25) with a fake embedding model: no network, no LM Studio.
The fake maps a few words to shared "meaning" dimensions, so two texts with no word in common can
still be close, which is what real embeddings add over keyword search."""
import math
import re

import pytest

from opportunity_finder.agents import discovery
from opportunity_finder.tools import kb, vectorstore

chromadb = pytest.importorskip("chromadb")

CONCEPTS = {"duplicate": 0, "twice": 0, "same": 0, "again": 0, "entry": 1, "key": 1, "typed": 1,
            "status": 2, "phone": 2, "update": 2}


class FakeEmbeddings:
    def __init__(self, fail=False):
        self.seen, self.doc_calls, self.fail = [], 0, fail

    def _vec(self, text):
        v = [0.0] * 16
        for w in re.findall(r"[a-z]+", text.lower()):
            if w in ("search", "document", "query"):
                continue
            v[CONCEPTS.get(w, 3 + hash(w) % 13)] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def embed_documents(self, texts):
        if self.fail:
            raise ConnectionError("LM Studio is not running")
        self.doc_calls += 1
        self.seen += texts
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        if self.fail:
            raise ConnectionError("LM Studio is not running")
        self.seen.append(text)
        return self._vec(text)


REAL_EMBEDDER = vectorstore.Embedder


def embedder(fake=None):
    return REAL_EMBEDDER({"model": "fake-embed", "base_url": "http://localhost:1234/v1",
                                 "api_key": "x", "hosted_allowed": True}, client=fake or FakeEmbeddings())


def make_kb(tmp_path):
    notes = {
        "trailers/a.md": "source: Note A\nurl:\nindustries: trailer manufacturing\n---\nDealers phone for status updates all day long.\n",
        "trailers/b.md": "source: Note B\nurl:\nindustries: trailer manufacturing\n---\nClerks key the same details into the register twice.\n",
        "general/g.md": "source: General\nurl:\nindustries: *\n---\nMeasure the process before changing it.\n",
    }
    for rel, text in notes.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(text, encoding="utf-8")
    return tmp_path


def test_vectors_find_a_passage_that_shares_no_words_with_the_query(tmp_path):
    root = make_kb(tmp_path)
    kw, _, info_kw = kb.retrieve_with_info("trailer manufacturing", 1, 1, root, "duplicate data entry")
    assert info_kw["mode"] == "keyword" and kw[0]["source"] == "Note A"     # BM25: no word matches, file order
    hy, _, info = kb.retrieve_with_info("trailer manufacturing", 1, 1, root, "duplicate data entry", embedder())
    assert info["mode"] == "hybrid" and hy[0]["source"] == "Note B"         # vectors: same meaning
    assert info["embed_model"] == "fake-embed" and info["index_rebuilt"] is True
    assert hy[1]["source"] == "General"                                    # general guidance still added


def test_nomic_prefixes_are_added(tmp_path):
    fake = FakeEmbeddings()
    kb.retrieve_with_info("trailer manufacturing", kb_dir=make_kb(tmp_path), query_text="x", embedder=embedder(fake))
    assert all(t.startswith("search_document: ") for t in fake.seen[:-1])
    assert fake.seen[-1].startswith("search_query: ")


def test_the_index_is_built_once_and_rebuilt_when_a_note_changes(tmp_path):
    root = make_kb(tmp_path)
    fake = FakeEmbeddings()
    kb.retrieve_with_info("trailer manufacturing", kb_dir=root, embedder=embedder(fake))
    _, _, info = kb.retrieve_with_info("trailer manufacturing", kb_dir=root, embedder=embedder(fake))
    assert fake.doc_calls == 1 and info["index_rebuilt"] is False          # reused from disk
    assert (root / ".chroma").is_dir()
    (root / "trailers" / "a.md").write_text("source: Note A\nurl:\nindustries: trailer manufacturing\n---\nChanged text.\n",
                                            encoding="utf-8")
    _, _, info = kb.retrieve_with_info("trailer manufacturing", kb_dir=root, embedder=embedder(fake))
    assert fake.doc_calls == 2 and info["index_rebuilt"] is True


def test_embedding_failure_falls_back_to_keywords_and_is_flagged(tmp_path, monkeypatch):
    root = make_kb(tmp_path)
    hits, _, info = kb.retrieve_with_info("trailer manufacturing", kb_dir=root, embedder=embedder(FakeEmbeddings(fail=True)))
    assert info["mode"] == "keyword" and "LM Studio is not running" in info["reason"] and hits
    assert info["embedding_calls"] and info["embedding_calls"][0]["error"]
    # in the agent: a configured but failing embedding server raises a visible flag
    monkeypatch.setenv("KB_DIR", str(root))
    monkeypatch.setattr(vectorstore, "Embedder", lambda *a, **k: embedder(FakeEmbeddings(fail=True)))
    out = discovery.discovery_research({"profile": {"industry": "trailer manufacturing"}})
    assert out["best_practices"]["retrieval"]["mode"] == "keyword"
    assert [f["type"] for f in out["flags"]] == ["retrieval_keyword_only"]
    assert "(keyword retrieval)" in out["trace"][0]


def test_no_embedding_model_configured_means_keyword_search_without_a_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("KB_DIR", str(make_kb(tmp_path)))
    out = discovery.discovery_research({"profile": {"industry": "trailer manufacturing", "evidence": "builds trailers"}})
    bp = out["best_practices"]
    assert bp["retrieval"]["mode"] == "keyword" and "no embedding model configured" in bp["retrieval"]["reason"]
    assert out["flags"] == [] and "builds trailers" in bp["retrieval"]["query"]


def test_the_agent_uses_hybrid_retrieval_when_vectors_work(tmp_path, monkeypatch):
    monkeypatch.setenv("KB_DIR", str(make_kb(tmp_path)))
    monkeypatch.setattr(vectorstore, "Embedder", lambda *a, **k: embedder())
    out = discovery.discovery_research({"profile": {"industry": "trailer manufacturing",
                                                    "evidence": "clerks retype the same order twice"}})
    assert out["best_practices"]["retrieval"]["mode"] == "hybrid" and out["flags"] == []
    assert "(hybrid retrieval)" in out["trace"][0]


def test_a_hosted_embedding_server_is_refused(monkeypatch):
    monkeypatch.setenv("LLM_EMBED_MODEL", "some-embedder")
    monkeypatch.setenv("LLM_EMBED_BASE_URL", "https://api.example.com/v1")
    monkeypatch.delenv("LLM_ALLOW_HOSTED", raising=False)
    with pytest.raises(vectorstore.VectorsUnavailable, match="not local"):
        vectorstore.Embedder()
    monkeypatch.setenv("LLM_ALLOW_HOSTED", "embed")
    assert vectorstore.embed_settings()["hosted_allowed"] is True


def test_reciprocal_rank_fusion_rewards_agreement():
    assert vectorstore.rrf(["a", "b", "c"], ["b", "c", "a"])[0] == "b"
    assert vectorstore.rrf(["a"], []) == ["a"] and vectorstore.rrf() == []


def test_sourced_kb_covers_the_demo_industries(monkeypatch):
    monkeypatch.delenv("KB_DIR")                          # the app default: kb_sources/
    for industry in ("trailer manufacturing", "wholesale distribution", "bookkeeping and accounting firm"):
        hits, note = kb.retrieve(industry)
        assert note == "" and any(not h["general"] for h in hits), industry
    hits, _ = kb.retrieve("trailer manufacturing")
    assert {h["source"].split(":")[0] for h in hits} & {"NIST Manufacturing Extension Partnership", "NHTSA New Manufacturers Handbook"}
