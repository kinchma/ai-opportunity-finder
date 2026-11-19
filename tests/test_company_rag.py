"""Company RAG: one ChromaDB store per customer, per-process retrieval for the Process Mapper, and
customer isolation. Fake embeddings; no network, no LM Studio."""
import pytest

from opportunity_finder import case_runner, cases
from opportunity_finder.agents import planner, process_mapper
from opportunity_finder.tools import company_rag, vectorstore
from tests.test_vector_retrieval import REAL_EMBEDDER, FakeEmbeddings, embedder

pytest.importorskip("chromadb")
SYNTH = {"name": "X", "industry": "trailer manufacturing", "size": "20", "risk_tolerance": 0.4}

QUOTING = "# Quoting\n\nThe coordinator types the dealer request into the quote template.\n\n" + \
          "## Approval\n\n" + "The sales manager approves every quote before it is sent. " * 30 + \
          "\n\n## After acceptance\n\nOrders are entered a second time into the order register."
INTERVIEW = ("# Quoting interview\n\nI key the same order details twice, once in the quote and again in the "
             "register.\n\n## Weather\n\nThe shop gets cold in winter and we wear jackets.")
COUNTING = "# Inventory counting\n\nCora counts six selected categories every week on paper."
COUNT_INTERVIEW = "# Counting interview\n\nThe weekly count of axles happens on paper first, then Excel."


def make_case(tmp_path, name, files, folders=("documents", "interviews")):
    cid = cases.create_case(name, SYNTH, tmp_path)
    root = cases.case_dir(cid, tmp_path)
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text, encoding="utf-8")
    cases.authorize_materials(cid, list(folders), tmp_path)
    return cid


def laurel_like(tmp_path, name="Acme"):
    return make_case(tmp_path, name, {"documents/processes/08_quoting.md": QUOTING,
                                      "documents/processes/04_counting.md": COUNTING,
                                      "interviews/08_quoting_interview.md": INTERVIEW,
                                      "interviews/04_counting_interview.md": COUNT_INTERVIEW})


@pytest.fixture
def fake_vectors(monkeypatch):
    monkeypatch.setattr(vectorstore, "Embedder", lambda *a, **k: embedder(FakeEmbeddings()))


def test_each_company_has_its_own_store_and_cannot_see_another(tmp_path, fake_vectors):
    a = laurel_like(tmp_path, "Acme")
    b = make_case(tmp_path, "Bolt", {"interviews/b.md": "# B\n\nWe key the same order details twice into two systems."},
                  folders=("interviews",))
    for cid in (a, b):
        info = case_runner.refresh_index(cid, tmp_path)
        assert info["mode"] == "hybrid" and info["index_rebuilt"]
        assert (cases.case_dir(cid, tmp_path) / "index" / "index_info.json").exists()
    query = "key the same order details twice"
    for cid in (a, b):
        found = company_rag.Searcher(cases.case_dir(cid, tmp_path) / "index", cases.document_chunks(cid, tmp_path)).search(query, 5)
        assert found and all(c["id"] in {x["id"] for x in cases.document_chunks(cid, tmp_path)} for c in found)
    a_ids = {c["id"] for c in cases.document_chunks(a, tmp_path)}
    b_found = company_rag.Searcher(cases.case_dir(b, tmp_path) / "index", cases.document_chunks(b, tmp_path)).search(query, 10)
    assert not {c["id"] for c in b_found} & a_ids                      # Bolt's search never returns Acme's passages


def test_index_is_reused_and_rebuilt_only_when_material_changes(tmp_path, fake_vectors):
    cid = laurel_like(tmp_path)
    idx = cases.case_dir(cid, tmp_path) / "index"
    assert company_rag.index_status(idx, cases.document_chunks(cid, tmp_path))["exists"] is False
    assert case_runner.refresh_index(cid, tmp_path)["index_rebuilt"] is True
    assert case_runner.refresh_index(cid, tmp_path)["index_rebuilt"] is False
    st = company_rag.index_status(idx, cases.document_chunks(cid, tmp_path))
    assert st["up_to_date"] and st["passages"] == len(cases.document_chunks(cid, tmp_path))
    cases.add_document(cid, "new.md", b"# New\n\nA new interview.", tmp_path, folder="interviews")
    assert company_rag.index_status(idx, cases.document_chunks(cid, tmp_path))["up_to_date"] is False
    assert case_runner.refresh_index(cid, tmp_path)["index_rebuilt"] is True
    kinds = [d["kind"] for d in cases.load(cid, cases.DECISIONS, [], tmp_path)]
    assert kinds.count("company_index_built") == 2


def test_process_mapper_gets_each_process_document_in_full_plus_matching_interviews(tmp_path, fake_vectors, scripted):
    cid = laurel_like(tmp_path)
    chunks = cases.document_chunks(cid, tmp_path)
    built = case_runner.refresh_index(cid, tmp_path, chunks)
    seen = scripted({"process_mapper": {"processes": [], "doc_vs_reality_gaps": []}})
    out = process_mapper.process_mapper({"profile": {"name": "Acme"}, "company_input": {}, "site_text": "",
                                         "document_chunks": chunks, "company_index": str(cases.case_dir(cid, tmp_path) / "index"),
                                         "company_retrieval": built})
    prompt = seen["process_mapper"][0]
    assert "Orders are entered a second time" in prompt                  # a later section of the process document, in full
    quoting_block = prompt.split("=== documents/processes/08_quoting.md ===")[1].split("===")[0]
    assert "[doc:interviews/08_quoting_interview.md#1]" in quoting_block   # the matching interview, under its process
    assert "I key the same order details twice" in prompt                  # its text appears once (repeats are referenced)
    assert prompt.count("I key the same order details twice") == 1
    assert "passages retrieved because they match it" in prompt
    r = out["process_map"]["retrieval"]
    assert r["mode"] == "hybrid" and r["anchored_on"] == "process documents"
    per = {x["process"]: x["retrieved"] for x in r["per_process"]}
    assert list(per) == ["documents/processes/04_counting.md", "documents/processes/08_quoting.md"]
    assert per["documents/processes/08_quoting.md"][0] == "doc:interviews/08_quoting_interview.md#1"   # best match first
    assert per["documents/processes/04_counting.md"][0] == "doc:interviews/04_counting_interview.md#1"
    assert "(hybrid retrieval per process)" in out["trace"][0]


def test_without_process_documents_the_mapper_searches_common_processes(tmp_path, fake_vectors, scripted):
    cid = make_case(tmp_path, "NoDocs", {"interviews/ops.md": INTERVIEW}, folders=("interviews",))
    chunks = cases.document_chunks(cid, tmp_path)
    built = case_runner.refresh_index(cid, tmp_path, chunks)
    seen = scripted({"process_mapper": {"processes": []}})
    out = process_mapper.process_mapper({"profile": {}, "company_input": {}, "document_chunks": chunks,
                                         "company_index": str(cases.case_dir(cid, tmp_path) / "index"), "company_retrieval": built})
    assert out["process_map"]["retrieval"]["anchored_on"] == "common process searches"
    assert "=== search: order intake and quoting (no process document" in seen["process_mapper"][0]


def test_company_retrieval_off_brings_back_the_old_bundle(tmp_path, fake_vectors, scripted, monkeypatch):
    monkeypatch.setenv("COMPANY_RETRIEVAL", "off")
    cid = laurel_like(tmp_path)
    assert case_runner.refresh_index(cid, tmp_path)["mode"] == "off"
    seen = scripted({"process_mapper": {"processes": []}})
    out = process_mapper.process_mapper({"profile": {}, "company_input": {}, "document_chunks": cases.document_chunks(cid, tmp_path),
                                         "company_index": str(cases.case_dir(cid, tmp_path) / "index")})
    assert out["process_map"]["retrieval"]["mode"] == "off"
    assert "passages retrieved because they match it" not in seen["process_mapper"][0]
    assert not (cases.case_dir(cid, tmp_path) / "index").exists()


def test_without_vectors_the_search_is_keyword_only_but_still_per_process(tmp_path, scripted):
    cid = laurel_like(tmp_path)                                        # conftest: no embedding model configured
    chunks = cases.document_chunks(cid, tmp_path)
    built = case_runner.refresh_index(cid, tmp_path, chunks)
    assert built["mode"] == "keyword" and "no embedding model" in built["reason"]
    seen = scripted({"process_mapper": {"processes": []}})
    out = process_mapper.process_mapper({"profile": {}, "company_input": {}, "document_chunks": chunks,
                                         "company_index": str(cases.case_dir(cid, tmp_path) / "index"), "company_retrieval": built})
    assert out["process_map"]["retrieval"]["mode"] == "keyword"
    quoting_block = seen["process_mapper"][0].split("=== documents/processes/08_quoting.md ===")[1].split("===")[0]
    assert "I key the same order details twice" in quoting_block       # BM25 still matches "order"


def test_a_full_analysis_records_how_company_retrieval_ran(tmp_path, fake_vectors):
    cid = laurel_like(tmp_path)
    case_runner.discover(cid, tmp_path)
    case_runner.confirm(cid, {}, tmp_path)
    result = case_runner.analyze(cid, tmp_path)
    assert result["company_retrieval"]["mode"] == "hybrid" and result["process_map"]["retrieval"]["mode"] == "hybrid"
    assert (cases.case_dir(cid, tmp_path) / "index" / "index_info.json").exists()


def test_the_verifier_can_read_a_cited_company_passage(monkeypatch):
    chunk = {"id": "doc:interviews/q.md#1", "name": "interviews/q.md", "text": "We key orders twice.", "source_type": "sme_interview"}
    seen = {}

    def fake_ask(agent, msgs, validate):
        seen["prompt"] = msgs[1][1]
        return {"Order re-entry": {"supported": True, "quote": "We key orders twice", "reason": "ok"}}, [], ""
    monkeypatch.setattr(planner, "ask_json", fake_ask)
    status, _, _ = planner.check_citations({"document_chunks": [chunk]}, [({"name": "Order re-entry"}, chunk["id"])])
    assert status["Order re-entry"]["status"] == "confirmed" and "We key orders twice." in seen["prompt"]


def test_slow_local_agents_get_longer_timeouts(monkeypatch):
    from opportunity_finder import llm
    monkeypatch.delenv("LLM_TIMEOUT", raising=False)
    monkeypatch.delenv("LLM_PROCESS_MAPPER_TIMEOUT", raising=False)
    assert llm.timeout_for("process_mapper") == 900 and llm.timeout_for("discovery_research") == 600
    assert llm.timeout_for("critic") == 300 and llm.timeout_for(None) == 300
    monkeypatch.setenv("LLM_PROCESS_MAPPER_TIMEOUT", "1200")
    assert llm.timeout_for("process_mapper") == 1200
