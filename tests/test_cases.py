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


def test_case_folder_is_named_after_the_company(tmp_path):
    assert cases.create_case("Acme Trailers, Inc.", SYNTH, tmp_path) == "acme-trailers-inc"
    assert cases.create_case("Acme Trailers, Inc.", SYNTH, tmp_path) == "acme-trailers-inc-2"


def test_documents_go_into_material_folders_and_runs_are_numbered(tmp_path):
    cid = cases.create_case("Acme", SYNTH, tmp_path)
    assert cases.add_document(cid, "sop.txt", b"Invoices arrive by email as PDFs.", tmp_path)["readable"]
    assert not cases.add_document(cid, "diagram.pdf", b"%PDF", tmp_path)["readable"]
    assert cases.add_document(cid, "ops call.md", b"Interview: we re-key orders.", tmp_path, folder="interviews")["file"] == "interviews/ops_call.md"
    with pytest.raises(ValueError):
        cases.add_document(cid, "x.md", b"x", tmp_path, folder="owner")          # not a material folder
    docs = cases.load_documents(cid, tmp_path)
    assert [d["name"] for d in docs] == ["documents/sop.txt", "interviews/ops_call.md"] and "Invoices" in docs[0]["text"]
    assert [d["source_type"] for d in docs] == ["owner_document", "sme_interview"]
    assert cases.authorized_folders(cid, tmp_path) == ["documents", "interviews"]   # uploading authorizes the folder
    assert cases.runs(cid, tmp_path) == [] and cases.load_result(cid, None, tmp_path) == {}
    assert cases.save_run(cid, {"process_map": {"processes": []}, "status": "a"}, "first", tmp_path) == "run-001"
    assert cases.save_run(cid, {"process_map": {"processes": [1]}, "status": "b"}, "second", tmp_path) == "run-002"
    assert cases.load_result(cid, None, tmp_path)["status"] == "b" and cases.load_result(cid, "run-001", tmp_path)["status"] == "a"
    assert cases.load(cid, "results/run-001/process_map.json", None, tmp_path)["run_note"] == "first"
    assert cases.load_case(cid, tmp_path)["latest_run"] == "run-002"
    with pytest.raises(ValueError):
        cases.run_dir(cid, "../../etc", tmp_path)


def test_unauthorized_folders_and_owner_files_never_reach_the_pipeline(tmp_path):
    cid = cases.create_case("Acme", SYNTH, tmp_path)
    root = cases.case_dir(cid, tmp_path)
    (root / "research").mkdir()
    (root / "research" / "market.md").write_text("# Market\n\nOutside research.", encoding="utf-8")
    (root / "documents").mkdir()
    (root / "documents" / ".hidden.md").write_text("hidden", encoding="utf-8")
    cases.save(cid, cases.PROFILE, {"name": "Acme", "secret_note": "OWNER ONLY"}, tmp_path)
    cases.save_run(cid, {"process_map": {}, "note": "EARLIER RUN"}, "x", tmp_path)
    assert cases.document_chunks(cid, tmp_path) == []                     # nothing authorized yet
    assert cases.material_summary(cid, tmp_path) == [{"folder": "research", "files": 1, "authorized": False}]
    cases.authorize_materials(cid, ["research"], tmp_path)
    chunks = cases.document_chunks(cid, tmp_path)
    assert [c["id"] for c in chunks] == ["doc:research/market.md#1"] and chunks[0]["source_type"] == "external_research"
    texts = "\n".join(c["text"] for c in chunks)
    assert "OWNER ONLY" not in texts and "EARLIER RUN" not in texts and "hidden" not in texts
    with pytest.raises(ValueError):
        cases.authorize_materials(cid, ["results"], tmp_path)
    assert [d["kind"] for d in cases.load(cid, cases.DECISIONS, [], tmp_path)] == ["materials_authorized"]


def test_local_website_resolves_to_the_case_folder(tmp_path):
    cid = cases.create_case("Acme", {"website": "local"}, tmp_path)
    assert cases.website_for(cid, {"website": "local"}, tmp_path).endswith(f"/{cid}/website")
    assert cases.website_for(cid, {"website": "https://acme.test"}, tmp_path) == "https://acme.test"
    assert cases.website_for(cid, {}, tmp_path) == ""                     # no site folder, no website
    (cases.case_dir(cid, tmp_path) / "website").mkdir()
    (cases.case_dir(cid, tmp_path) / "website" / "index.html").write_text("<html></html>", encoding="utf-8")
    assert cases.website_for(cid, {}, tmp_path).startswith("file://")


def test_a_saved_yes_no_authorization_from_before_nov_17_still_reads(tmp_path):
    cid = cases.create_case("Acme", SYNTH, tmp_path)
    cases.update_case(cid, tmp_path, materials_authorized=True)
    assert cases.authorized_folders(cid, tmp_path) == list(cases.MATERIAL_FOLDERS)


def test_stage_by_stage_resume_from_disk(tmp_path):
    """Each stage builds a brand-new graph, as a fresh Python process would."""
    cid = cases.create_case("Synthetic Trailers", SYNTH, tmp_path)
    profile = case_runner.discover(cid, tmp_path)
    assert profile["industry"] == "trailer manufacturing"
    assert cases.load_case(cid, tmp_path)["stage"] == "discovered"

    case_runner.confirm(cid, {"industry": "aluminum trailer manufacturing"}, tmp_path)
    assert cases.load(cid, cases.PROFILE, {}, tmp_path)["industry"] == "aluminum trailer manufacturing"

    cases.add_document(cid, "process.md", b"We quote by phone and invoice monthly.", tmp_path)
    result = case_runner.analyze(cid, tmp_path)
    assert result["status"] == "needs_owner_help"   # quiet fake model: placeholders only, so no pass
    assert "Needs the owner" in cases.load_case(cid, tmp_path)["status"]
    assert result["profile"]["industry"] == "aluminum trailer manufacturing"   # confirmed value carried over
    assert result["documents"][0]["name"] == "documents/process.md"
    assert cases.load_case(cid, tmp_path)["stage"] == "analyzed"
    assert cases.latest_run(cid, tmp_path) == "run-001"
    assert cases.load_result(cid, None, tmp_path)["final_recommendation"]
    assert cases.load(cid, "results/run-001/process_map.json", {}, tmp_path)["run"] == "run-001"
    assert list(cases.run_dir(cid, "run-001", tmp_path).glob(f"{cid}-*.json"))      # the call log
    assert cases.load(cid, cases.DISCOVERY, None, tmp_path) is not None
    kinds = [d["kind"] for d in cases.load(cid, cases.DECISIONS, [], tmp_path)]
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
