"""Laurel Run synthetic case: offline discovery, the owner-confirmation gate, the materials
boundary, document citations and social-presence facts. All model calls are fakes.

The local fixture site lives in cases/Laurel_Run_Test_Case/website/site; tests that need it are
skipped when the folder is absent. The evaluator-only folder is never read by these tests; one
test proves the pipeline cannot receive it."""
import json
import os
from pathlib import Path

import pytest

from opportunity_finder import case_runner, cases
from opportunity_finder.agents import discovery, process_mapper
from opportunity_finder.agents.website import assess_website
from opportunity_finder.tools.web import fetch_site_text

CASE = Path(__file__).resolve().parents[1] / "cases" / "Laurel_Run_Test_Case"
SITE = CASE / "website" / "site"
MATERIAL = CASE / "01_analysis_agent_material"
needs_fixture = pytest.mark.skipif(not SITE.exists(), reason="Laurel Run fixture folder not present")


def profile_reply(industry="trailer manufacturing", conf="high"):
    return json.dumps({"name": "Laurel Run Trailer Works", "industry": industry, "confidence": conf,
                       "evidence": "The home page says 'Pennsylvania trailer manufacturing' and lists utility, "
                                   "enclosed cargo and equipment trailers built in Hollow Glen."})


WEBSITE_REPLY = json.dumps({"scores": {}, "prompts": ["Find a dealer", "Explore trailers", "Contact us"]})


# ----------------------------------------------------------------- website-only discovery
@needs_fixture
def test_local_site_is_read_offline_with_a_path_boundary():
    site = fetch_site_text(SITE.as_uri())
    assert site["error"] is None and site["local_fixture"] is True
    assert "trailer" in site["text"].lower() and site["url"].endswith("site/index.html")
    assert site["signals"]["social_links"]["linkedin"] == []           # not found on the page read
    # the route reads one page inside the named directory and nothing else
    outside = fetch_site_text((SITE / ".." / ".." / "case_manifest.json").as_uri())
    assert outside["error"] and "only a directory with index.html or an .html file" in outside["error"]
    assert fetch_site_text((SITE / "nope.html").as_uri())["error"] == "local site: page not found"


@needs_fixture
def test_discovery_uses_the_website_alone_and_names_its_evidence(tmp_path, scripted):
    seen = scripted({"discovery_profile": profile_reply(), "discovery_website": WEBSITE_REPLY})
    cid = cases.create_case("Laurel Run", {"website": SITE.as_uri(), "risk_tolerance": 0.4}, tmp_path)
    profile = case_runner.discover(cid, tmp_path)
    assert profile["industry"] == "trailer manufacturing" and profile["confidence"] == "high"
    assert "Pennsylvania trailer manufacturing" in profile["evidence"]
    assert profile["evidence_source"]["local_fixture"] and profile["evidence_source"]["page"].endswith("index.html")
    assert profile["confirmed_by_owner"] is False
    # the model saw the website text and nothing from the company package
    prompt = seen["discovery_profile"][0]
    assert "Hollow Glen" in prompt and "01_analysis_agent_material" not in prompt and "interview" not in prompt.lower()
    assert cases.load_case(cid, tmp_path)["stage"] == "discovered"


# ----------------------------------------------------------------- the confirmation gate
def seeded_case(tmp_path, scripted, website=None):
    scripted({"discovery_profile": profile_reply(), "discovery_website": WEBSITE_REPLY})
    cid = cases.create_case("Laurel Run", {"website": website or SITE.as_uri(), "risk_tolerance": 0.4}, tmp_path)
    case_runner.discover(cid, tmp_path)
    return cid


@needs_fixture
def test_analysis_is_refused_before_the_owner_confirms(tmp_path, scripted):
    cid = seeded_case(tmp_path, scripted)
    with pytest.raises(case_runner.ConfirmationRequired):
        case_runner.analyze(cid, tmp_path)
    ok, why = case_runner.confirmation_ok(cid, tmp_path)
    assert not ok and "not confirmed" in why


@needs_fixture
def test_a_hand_edited_stage_does_not_bypass_the_gate(tmp_path, scripted):
    cid = seeded_case(tmp_path, scripted)
    cases.set_stage(cid, "confirmed", tmp_path)          # someone edits case.json by hand
    with pytest.raises(case_runner.ConfirmationRequired):  # profile.json carries no owner confirmation
        case_runner.analyze(cid, tmp_path)


@needs_fixture
def test_reject_stops_the_case_until_a_renewed_acceptance(tmp_path, scripted):
    cid = seeded_case(tmp_path, scripted)
    case_runner.reject(cid, "wrong company", tmp_path)
    assert cases.load_case(cid, tmp_path)["stage"] == "rejected"
    with pytest.raises(case_runner.ConfirmationRequired, match="rejected"):
        case_runner.analyze(cid, tmp_path)
    profile = case_runner.confirm(cid, {"industry": "custom trailer manufacturing"}, tmp_path, note="checked by owner")
    assert profile["confirmed_by_owner"] and profile["industry"] == "custom trailer manufacturing"
    assert profile["owner_corrections"] == {"industry": "custom trailer manufacturing"}
    assert profile["confidence"] == "owner-confirmed" and profile["evidence"].startswith("Owner corrected")
    kinds = [d["kind"] for d in cases.load(cid, "decisions.json", [], tmp_path)]
    assert kinds == ["profile_rejected", "profile_confirmed"]
    assert case_runner.confirmation_ok(cid, tmp_path) == (True, "")


@needs_fixture
def test_rerunning_discovery_cancels_an_earlier_confirmation(tmp_path, scripted):
    cid = seeded_case(tmp_path, scripted)
    case_runner.confirm(cid, {}, tmp_path)
    case_runner.discover(cid, tmp_path)                   # fresh Discovery, fresh confirmation needed
    assert cases.load_case(cid, tmp_path)["stage"] == "discovered"
    with pytest.raises(case_runner.ConfirmationRequired):
        case_runner.analyze(cid, tmp_path)


# ----------------------------------------------------------------- the materials boundary
@needs_fixture
def test_sharing_copies_only_approved_material_and_refuses_the_evaluator_folder(tmp_path, scripted):
    cid = seeded_case(tmp_path, scripted)
    case_runner.confirm(cid, {}, tmp_path)
    out = cases.share_materials(cid, MATERIAL, ["processes", "interviews", "company"], tmp_path)
    assert len(out["copied"]) >= 20 and not out["refused"]
    files = cases.list_document_files(cid, tmp_path)
    assert all(f.split("/")[0] in ("processes", "interviews", "company") for f in files)
    assert not any("evaluator" in f.lower() or "expectations" in f.lower() for f in files)
    # the evaluator folder is refused as a root and as an item, even when named explicitly
    with pytest.raises(ValueError, match="evaluation or generation material"):
        cases.share_materials(cid, CASE / "02_evaluator_only_DO_NOT_SHARE", None, tmp_path)
    out2 = cases.share_materials(cid, CASE, ["02_evaluator_only_DO_NOT_SHARE", "case_manifest.json",
                                             "CLAUDE_DESKTOP_PROMPT.md", "01_analysis_agent_material/README.md"], tmp_path)
    reasons = {r["path"].split("/")[0]: r["reason"] for r in out2["refused"]}
    assert "02_evaluator_only_DO_NOT_SHARE" in reasons and "case_manifest.json" in reasons and "CLAUDE_DESKTOP_PROMPT.md" in reasons
    assert out2["copied"] == ["01_analysis_agent_material/README.md"]
    # what the pipeline can read is exactly what was copied
    chunks = cases.document_chunks(cid, tmp_path)
    assert chunks and all(c["id"].startswith("doc:") for c in chunks)
    assert {c["source_type"] for c in chunks} >= {"process_document", "sme_interview", "owner_document"}
    assert not any("DO_NOT_SHARE" in c["name"] or "EXPECTATIONS" in c["name"].upper() for c in chunks)


def test_sentinel_outside_the_shared_root_and_symlinks_are_refused(tmp_path):
    cid = cases.create_case("Boundary", {"name": "B", "industry": "x", "size": "5", "risk_tolerance": 0.5}, tmp_path)
    src = tmp_path / "share_root"
    (src / "processes").mkdir(parents=True)
    (src / "processes" / "quoting.md").write_text("# Quoting\n\nQuotes are typed by hand.", encoding="utf-8")
    secret = tmp_path / "SENTINEL_answer_key.md"            # outside the shared root
    secret.write_text("the expected answer is X", encoding="utf-8")
    (src / "hidden_secret.md").symlink_to(secret)            # a symlink that points outside
    (src / ".hidden.md").write_text("hidden", encoding="utf-8")
    out = cases.share_materials(cid, src, None, tmp_path)
    assert out["copied"] == ["processes/quoting.md"]
    assert {r["path"]: r["reason"] for r in out["refused"]} == {
        "hidden_secret.md": "symbolic link", ".hidden.md": "evaluation, hidden or generation material"}
    # traversal in an include list cannot reach the sentinel either
    out = cases.share_materials(cid, src, ["../SENTINEL_answer_key.md"], tmp_path)
    assert out["copied"] == [] and "outside the shared folder" in out["refused"][0]["reason"]
    texts = "\n".join(c["text"] for c in cases.document_chunks(cid, tmp_path))
    assert "expected answer" not in texts


# ----------------------------------------------------------------- document citations
@needs_fixture
def test_process_mapper_cites_the_shared_files_and_reports_gaps(tmp_path, scripted):
    cid = seeded_case(tmp_path, scripted)
    case_runner.confirm(cid, {}, tmp_path)
    cases.share_materials(cid, MATERIAL, ["processes", "interviews"], tmp_path)
    chunks = cases.document_chunks(cid, tmp_path)
    quoting = next(c["id"] for c in chunks if "08_quoting.md" in c["id"])
    interview = next(c["id"] for c in chunks if "08_quoting_interview.md" in c["id"])
    reply = {"processes": [
        {"name": "Quoting", "description": "Dealers request quotes", "pain_points": ["re-typing"],
         "basis": "stated", "sources": [f"[{quoting}]", interview]},
        {"name": "Invoicing", "description": "typical", "pain_points": [], "basis": "stated", "sources": ["doc:made-up.md#9"]}],
        "doc_vs_reality_gaps": [
            {"process": "Quoting", "document_says": "quotes go through the sales manager",
             "interview_says": "dealers often call the scheduler directly", "sources": [quoting, interview]},
            {"process": "Invoicing", "document_says": "x", "interview_says": "y", "sources": ["nope#1"]}]}
    seen = scripted({"process_mapper": reply})
    state = {"profile": {"name": "Laurel Run", "industry": "trailer manufacturing", "website": "file"},
             "company_input": {}, "site_text": "trailers", "document_chunks": chunks,
             "documents": cases.load_documents(cid, tmp_path)}
    out = process_mapper.process_mapper(state)
    pm = out["process_map"]
    q, inv = pm["processes"]
    assert q["sources"] == [quoting, interview] and q["basis"] == "stated"
    assert inv["sources"] == [] and inv["basis"] == "typical"          # an invented id earns no "stated"
    assert len(pm["doc_vs_reality_gaps"]) == 1 and pm["doc_vs_reality_gaps"][0]["sources"] == [quoting, interview]
    assert quoting in pm["sources_index"] and pm["sources_index"][interview]["source_type"] == "sme_interview"
    prompt = seen["process_mapper"][0]
    assert f"[{quoting}]" in prompt and "sme interview" in prompt and "DO_NOT_SHARE" not in prompt
    assert "1 with document citations" in out["trace"][0] and "1 document-vs-interview gap" in out["trace"][0]


# ----------------------------------------------------------------- social presence: facts only
@needs_fixture
def test_social_presence_reports_only_what_the_page_shows(scripted):
    scripted({"discovery_website": WEBSITE_REPLY})
    site = fetch_site_text(SITE.as_uri())
    assessment, _ = assess_website(site, {"name": "Laurel Run", "industry": "trailer manufacturing"})
    social = assessment["social_presence"]
    assert social["found_on_pages_read"] == {} and "linkedin" in social["not_found_on_pages_read"]
    assert social["owner_pasted_linkedin"] is False and social["basis"].startswith("code")
    text = json.dumps(assessment).lower()
    assert "@" not in text and "tiktok.com" not in text and "outage" not in text   # nothing invented


def test_another_company_with_a_linkedin_page_is_reported_as_such(scripted):
    """A second synthetic fixture: a page that links to LinkedIn and Facebook, plus pasted LinkedIn
    text. Proves 'no LinkedIn' is a per-case observation, not a global rule."""
    scripted({"discovery_website": WEBSITE_REPLY})
    html = ('<html><head><title>Brightline Bookkeeping</title></head><body><p>Monthly books for small firms.</p>'
            '<a href="https://www.linkedin.com/company/brightline-books">LinkedIn</a>'
            '<a href="https://facebook.com/brightlinebooks">Facebook</a></body></html>')
    from opportunity_finder.tools.web import extract_text
    from opportunity_finder.tools.site_signals import analyze_html
    site = {"url": "https://example.test", **extract_text(html), "signals": analyze_html(html, "https://example.test")}
    assessment, _ = assess_website(site, {"name": "Brightline", "industry": "bookkeeping"},
                                   linkedin_text="Brightline Bookkeeping | 11-50 employees | Accounting")
    social = assessment["social_presence"]
    assert set(social["found_on_pages_read"]) == {"linkedin", "facebook"}
    assert "instagram" in social["not_found_on_pages_read"] and social["owner_pasted_linkedin"] is True
