import pytest

from opportunity_finder import case_runner, cases
from opportunity_finder.agents import discovery

SYNTH = {"name": "Synthetic Trailers Inc", "industry": "trailer manufacturing", "size": "50", "risk_tolerance": 0.4}


def test_create_list_and_resume_metadata(tmp_path):
    cid = cases.create_case("Acme Trailers", SYNTH, tmp_path)
    assert cases.load_case(cid, tmp_path)["stage"] == "new"
    cases.set_stage(cid, "discovered", tmp_path)
    assert [c["id"] for c in cases.list_cases(tmp_path)] == [cid]
    assert cases.list_cases(tmp_path / "nothing") == []


def test_bad_case_id_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        cases.case_dir("../escape", tmp_path)


def test_documents_and_process_map_versions(tmp_path):
    cid = cases.create_case("Acme", SYNTH, tmp_path)
    assert cases.add_document(cid, "sop.txt", b"Invoices arrive by email as PDFs.", tmp_path)["readable"]
    assert not cases.add_document(cid, "diagram.pdf", b"%PDF", tmp_path)["readable"]
    docs = cases.load_documents(cid, tmp_path)
    assert [d["name"] for d in docs] == ["sop.txt"] and "Invoices" in docs[0]["text"]
    assert cases.save_process_map(cid, {"processes": []}, "v1 note", tmp_path) == 1
    assert cases.save_process_map(cid, {"processes": [1]}, "v2 note", tmp_path) == 2
    assert cases.load(cid, "process_map.json", None, tmp_path)["version"] == 2
    assert cases.load(cid, "process_map.v1.json", None, tmp_path)["version_note"] == "v1 note"


def test_stage_by_stage_resume_from_disk(tmp_path):
    """Each stage builds a brand-new graph, as a fresh Python process would."""
    cid = cases.create_case("Synthetic Trailers", SYNTH, tmp_path)
    profile = case_runner.discover(cid, tmp_path)
    assert profile["industry"] == "trailer manufacturing"
    assert cases.load_case(cid, tmp_path)["stage"] == "discovered"

    case_runner.confirm(cid, {"industry": "aluminum trailer manufacturing"}, tmp_path)
    assert cases.load(cid, "profile.json", {}, tmp_path)["industry"] == "aluminum trailer manufacturing"

    cases.add_document(cid, "process.md", b"We quote by phone and invoice monthly.", tmp_path)
    result = case_runner.analyze(cid, tmp_path)
    assert result["status"] == "needs_owner_help"   # quiet fake model: placeholders only, so no pass
    assert "Needs the owner" in cases.load_case(cid, tmp_path)["status"]
    assert result["profile"]["industry"] == "aluminum trailer manufacturing"   # confirmed value carried over
    assert result["documents"][0]["name"] == "process.md"
    assert cases.load_case(cid, tmp_path)["stage"] == "analyzed"
    assert cases.load(cid, "result.json", {}, tmp_path)["final_recommendation"]
    assert cases.load(cid, "process_map.json", {}, tmp_path)["version"] == 1
    assert list((cases.case_dir(cid, tmp_path) / "runs").glob("*.json"))
    kinds = [d["kind"] for d in cases.load(cid, "decisions.json", [], tmp_path)]
    assert kinds == ["profile_confirmed", "document_added"]


def test_documents_reach_the_process_mapper_prompt(monkeypatch):
    from opportunity_finder.agents import process_mapper
    seen = {}
    monkeypatch.setattr(process_mapper, "ask_json", lambda agent, msgs, v: (seen.update(m=msgs[1][1]) or [], [], ""))
    out = process_mapper.process_mapper({"profile": {}, "documents": [{"name": "sop.txt", "text": "We invoice monthly."}]})
    assert "We invoice monthly." in seen["m"] and "1 owner document" in out["process_map"]["note"]


def test_reset_removes_the_case(tmp_path):
    cid = cases.create_case("Acme", SYNTH, tmp_path)
    cases.reset_case(cid, tmp_path)
    assert cases.list_cases(tmp_path) == []


def test_write_retries_when_windows_briefly_locks_the_file(tmp_path, monkeypatch):
    """Antivirus or the indexer can hold a just-written file for a moment; the save must not fail."""
    real, calls = cases.os.replace, []

    def flaky(src, dst):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError(5, "Access is denied")
        return real(src, dst)
    monkeypatch.setattr(cases.os, "replace", flaky)
    monkeypatch.setattr(cases.time, "sleep", lambda s: None)
    cases.write_json(tmp_path / "case.json", {"ok": True})
    assert cases.read_json(tmp_path / "case.json") == {"ok": True} and len(calls) == 3


def test_write_gives_up_if_the_file_stays_locked(tmp_path, monkeypatch):
    def locked(src, dst):
        raise PermissionError(5, "Access is denied")
    monkeypatch.setattr(cases.os, "replace", locked)
    monkeypatch.setattr(cases.time, "sleep", lambda s: None)
    with pytest.raises(PermissionError):
        cases.write_json(tmp_path / "case.json", {"ok": True})
