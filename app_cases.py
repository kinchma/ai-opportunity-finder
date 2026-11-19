"""Case workspace: start a customer case, close the app, and resume it later.

Run:  streamlit run app_cases.py
Each customer is an isolated folder under cases/ (see opportunity_finder/cases.py). Every stage
saves to disk, so you can stop after Discovery, wait for documents, and pick the case up again.
"""
import streamlit as st

from opportunity_finder import case_runner, cases
from opportunity_finder.config import SETTINGS
from opportunity_finder.observability import summarize
from opportunity_finder.summaries import (evidence_rows, flag_rows, left_out_ideas, ranking_rows, roadmap_rows,
                                          run_summary_rows, score_scale_note, website_check_view)
from opportunity_finder.tools import company_rag
from opportunity_finder.tools.scoring import idea_index, index_band, score_index

st.set_page_config(page_title="AI Opportunity Finder: Cases", page_icon="🗂️", layout="wide")
ss = st.session_state
STEPS = [("new", "Discovery"), ("discovered", "Confirm profile"), ("confirmed", "Documents"), ("analyzed", "Recommendation")]


def tracker(stage: str):
    done = cases.tracker_index(stage)
    st.markdown("  →  ".join(
        f"**{'✅' if i < done or stage == 'analyzed' else '⏳' if i == done else '⬜'} {label}**" if i <= done
        else f"⬜ {label}" for i, (_, label) in enumerate(STEPS)))


# ------------------------------------------------------------------ sidebar: pick or create
with st.sidebar:
    st.header("Cases")
    st.caption(f"Folder: {cases.base_dir().resolve()}")
    existing = cases.list_cases()
    labels = {c["id"]: f"{c['name']} ({c['stage']})" for c in existing}
    if existing:
        ids = list(labels)
        pick = st.selectbox("Open a case", ids, format_func=labels.get,
                            index=ids.index(ss.case_id) if ss.get("case_id") in ids else 0)
        ss.case_id = pick
    else:
        ss.case_id = None
        st.info("No cases yet. Create one below.")
    with st.expander("New case", expanded=not existing):
        with st.form("new_case", border=False):
            name = st.text_input("Business name")
            site = st.text_input("Website URL (blank = synthetic demo company; local = the case's own website/ folder)")
            desc = st.text_area("Short description (optional)", height=80)
            linkedin = st.text_area("LinkedIn page text (optional, paste it yourself)", height=80)
            industry = st.text_input("Industry (only used when there is no website)", value="trailer manufacturing")
            risk = st.slider("Risk tolerance", 0.0, 1.0, 0.4)
            effort_budget = st.number_input("Effort budget in points (optional; 0 = no limit). Each idea is rated "
                                            "1-10 for effort; a roadmap's total should stay under this.",
                                            min_value=0, value=0, step=1)
            if st.form_submit_button("Create case", type="primary"):
                company = {"risk_tolerance": risk}
                if effort_budget:
                    company["effort_budget"] = effort_budget
                if desc.strip():
                    company["description"] = desc.strip()
                if site.strip():
                    company["website"] = site.strip()
                    if linkedin.strip():
                        company["linkedin_text"] = linkedin.strip()
                else:
                    company.update({"name": name.strip() or "Synthetic Trailers Inc",
                                    "industry": industry.strip() or "trailer manufacturing", "size": "50"})
                ss.case_id = cases.create_case(name.strip() or company.get("name", "case"), company)
                st.rerun()
    if ss.case_id:
        with st.expander("Delete this demo case"):
            sure = st.checkbox("Yes, delete this case folder permanently")
            if st.button("Delete case", disabled=not sure):
                cases.reset_case(ss.case_id)
                ss.case_id = None
                st.rerun()

st.title("AI Opportunity Finder: case workspace")
if not ss.get("case_id"):
    st.write("Create a case in the sidebar to begin. Cases are saved to disk, so you can close this app and resume later.")
    st.stop()

meta = cases.load_case(ss.case_id)
stage = meta["stage"]
st.subheader(meta["name"])
tracker(stage)
st.caption(f"{meta['status']}  ·  last updated {meta['updated']}  ·  folder: cases/{meta['id']}")

# ------------------------------------------------------------------ stage 1: discovery
if stage == "new":
    st.write("Discovery reads the website, guesses the industry, and rates the site. Results are saved to this case.")
    if st.button("Run Discovery", type="primary"):
        with st.spinner("Reading the business..."):
            case_runner.discover(meta["id"])
        st.rerun()

# ------------------------------------------------------------------ stage 2: confirm
profile = cases.load(meta["id"], cases.PROFILE, {})
disc = cases.load(meta["id"], cases.DISCOVERY, {})
if stage in ("discovered", "rejected", "confirmed", "analyzed") and profile:
    with st.container(border=True):
        st.markdown(f"**{profile.get('name', 'unknown')}**  ·  {profile.get('website', '')}")
        st.write(f"Industry: **{profile.get('industry', 'unknown')}** ({profile.get('confidence', 'n/a')} confidence)")
        if profile.get("evidence"):
            st.caption(profile["evidence"])
        src = profile.get("evidence_source") or {}
        if src.get("page"):
            st.caption(f"Evidence read from: {src['page']}" + (" (local fixture site, not a live website)" if src.get("local_fixture") else ""))
        if profile.get("note"):
            st.warning(profile["note"])
        if profile.get("confirmed_by_owner"):
            st.success("Confirmed by the owner" + (f" with corrections: {profile['owner_corrections']}" if profile.get("owner_corrections") else "."))
if stage == "rejected":
    st.error("The owner rejected this profile. Correct it and confirm to continue; nothing runs until then.")
if stage in ("discovered", "rejected"):
    st.caption("The owner decides here. Accept the profile as is, correct the industry or name and accept, "
               "or reject it. Nothing further runs until the owner accepts.")
    fix = st.text_input("Industry (edit if wrong)", value=profile.get("industry", ""))
    fix_name = st.text_input("Business name (edit if wrong)", value=profile.get("name", ""))
    note = st.text_input("Owner note (optional)")
    c1, c2 = st.columns(2)
    if c1.button("Accept profile" if stage == "discovered" else "Accept corrected profile", type="primary"):
        corrections = {}
        if fix.strip() and fix.strip() != profile.get("industry"):
            corrections["industry"] = fix.strip()
        if fix_name.strip() and fix_name.strip() != profile.get("name"):
            corrections["name"] = fix_name.strip()
        case_runner.confirm(meta["id"], corrections, note=note.strip())
        st.rerun()
    if stage == "discovered" and c2.button("Reject profile"):
        case_runner.reject(meta["id"], note.strip())
        st.rerun()

# ------------------------------------------------------------------ stage 3: documents and analysis
if stage in ("confirmed", "analyzed"):
    st.markdown("#### Company material from the owner")
    st.caption("Text files (.txt, .md, .csv, .json) are read by the Process Mapper. Other files are stored but not read yet. "
               "Material can arrive weeks after Discovery; add it whenever it does. The analysis reads only the "
               "folders the owner has authorized.")
    summary = cases.material_summary(meta["id"])
    if summary:
        st.dataframe(summary, hide_index=True)
        ist = company_rag.index_status(cases.case_dir(meta["id"]) / "index", cases.document_chunks(meta["id"]))
        st.caption("Company search index: " + (
            f"{ist['passages']} passages, {ist['embed_model']}, built {ist['built']}, "
            + ("up to date." if ist["up_to_date"] else "out of date (rebuilt when the analysis runs).")
            if ist["exists"] else "not built yet (built when the analysis runs)."))
    pending = [r["folder"] for r in summary if not r["authorized"]]
    if pending:
        pick = st.multiselect("Authorize these folders for the analysis", pending, default=[], key=f"auth-{meta['id']}")
        if pick and st.button("Authorize selected folders"):
            try:
                case_runner.authorize(meta["id"], pick)
                st.rerun()
            except (ValueError, case_runner.ConfirmationRequired) as exc:
                st.error(str(exc))
    target = st.selectbox("Upload into", list(cases.MATERIAL_FOLDERS), key=f"tgt-{meta['id']}",
                          help="documents: processes, policies, company info; interviews: SME transcripts; "
                               "data: CSV samples; research: outside material (context, not company facts)")
    ups = st.file_uploader("Add files", accept_multiple_files=True, key=f"up-{meta['id']}-{len(cases.list_document_files(meta['id']))}")
    if ups:
        for f in ups:
            info = cases.add_document(meta["id"], f.name, f.getvalue(), folder=target)
            st.toast(f"Saved {info['file']}" + ("" if info["readable"] else " (stored, not read)"))
        st.rerun()
    with st.expander("Import a folder of company material from this computer (owner authorization)"):
        st.caption("Copies the files the owner authorizes into this case: interviews/ to interviews, data/ to data, "
                   "research/ to research, everything else to documents (processes/ marks process documents). "
                   "Evaluation material, answer keys and generation prompts are refused even if selected.")
        src_dir = st.text_input("Folder path on this computer", key=f"share-{meta['id']}")
        include = st.text_input("Subfolders or files to include, comma-separated (blank = whole folder)", key=f"inc-{meta['id']}")
        if st.button("Share these files with the pipeline"):
            try:
                out = case_runner.share(meta["id"], src_dir.strip(),
                                            [x.strip() for x in include.split(",") if x.strip()] or None)
                st.success(f"Shared {len(out['copied'])} file(s)." + (f" Refused {len(out['refused'])}." if out["refused"] else ""))
                for r in out["refused"][:10]:
                    st.caption(f"refused {r['path']}: {r['reason']}")
            except (FileNotFoundError, ValueError, case_runner.ConfirmationRequired) as exc:
                st.error(str(exc))
    files = cases.list_document_files(meta["id"])
    st.write(f"Readable by the analysis ({len(files)}): " + (", ".join(files[:12]) + (" ..." if len(files) > 12 else "") if files else "none yet"))
    ok, why = case_runner.confirmation_ok(meta["id"])
    label = "Run analysis" if stage == "confirmed" else "Re-run analysis with the current documents"
    if not ok:
        st.error(f"Analysis is blocked: {why}")
    if st.button(label, type="primary", disabled=not ok):
        with st.spinner("Running the pipeline (this can take a few minutes with a local model)..."):
            try:
                case_runner.analyze(meta["id"])
            except case_runner.ConfirmationRequired as exc:
                st.error(f"Analysis refused: {exc}")
                st.stop()
        st.rerun()

# ------------------------------------------------------------------ stage 4: results
if stage == "analyzed":
    run_names = cases.runs(meta["id"])
    run = st.selectbox("Run", run_names, index=len(run_names) - 1, key=f"run-{meta['id']}") if len(run_names) > 1 else (run_names or [None])[0]
    r = cases.load_result(meta["id"], run)
    rec = r.get("final_recommendation", {}).get("roadmap", {})
    opps = r.get("scored_opportunities", [])
    by_name = {o["name"]: o for o in opps}
    st.divider()
    full = r.get("final_recommendation", {})
    esc = r.get("escalation")
    if r.get("status") == "needs_owner_help" and esc:
        with st.container(border=True):      # decision card: what is uncertain, and clear choices
            st.markdown("#### The system needs your decision")
            st.error(esc["reason"])
            for item in esc.get("what_is_uncertain", []):
                st.markdown(f"- {item}")
            for col, choice in zip(st.columns(len(esc["choices"])), esc["choices"]):
                if col.button(choice["label"], key=f"esc-{choice['id']}"):
                    case_runner.owner_decision(meta["id"], choice["id"])
                    st.rerun()
            st.caption("Your choice is saved in owner/decisions.json. Nothing below has been verified.")
    st.markdown("#### Recommended roadmap" + ("" if r.get("verified") else " (UNVERIFIED DRAFT)"))
    if r.get("status") not in ("complete", "needs_owner_help"):
        st.warning(f"Status: {r.get('status')}")
    if any(o.get("placeholder") for o in opps):
        st.warning("The model gave too few valid ideas, so PLACEHOLDER opportunities were used. Treat this as a demo.")
    ver = full.get("verification") or {}
    if r.get("verified") and ver:
        st.success(f"Verified: {ver.get('grounded')} of {len(ver.get('claims', []))} recommended ideas trace to a "
                   f"process, a cited best practice or the website check.")
    names = rec.get("opportunities", [])
    tol = meta.get("company_input", {}).get("risk_tolerance", 0.5)
    for col, (i, n) in zip(st.columns(max(len(names), 1)), enumerate(names, 1)):
        o = by_name.get(n, {})
        idx = idea_index(o, tol)
        col.metric(f"{i}. {n}", f"{idx} / 100",
                   help=f"raw score {o.get('score')}; 0 = worst idea possible, 100 = best. " + o.get("what_the_agent_does", ""))
        col.markdown(f"**{index_band(idx)}**")
        v, e, rk = col.columns(3)
        v.metric("Value", o.get("value"), help="1-10, model's judgment; higher is better")
        e.metric("Effort", o.get("effort"), help="1-10, model's judgment; lower is better")
        rk.metric("Risk", o.get("risk"), help="1-10, model's judgment; lower is better")
    if rec.get("score") is not None:
        r_idx = score_index(rec["score"], tol)
        st.caption(f"Roadmap index {r_idx} / 100, {index_band(r_idx).lower()} (raw {rec['score']}). " + score_scale_note(tol))
    if rec.get("rationale"):
        st.write(rec["rationale"])
        for label, key in (("Why this pilot", "pilot_reason"), ("Assumption to confirm", "assumption")):
            if rec.get(key):
                st.caption(f"{label}: {rec[key]}")
        st.caption("Narrative written by the " + ("Strategist model." if rec.get("narrative_by") == "model"
                                                 else "code fallback (the model was unavailable)."))
    if full.get("close_call"):
        st.warning("Close call: " + full.get("close_call_detail", "") + " Compare both before deciding.")
        ru = full.get("runner_up") or {}
        st.caption("Runner-up: " + " → ".join(ru.get("opportunities", [])))
    flags = flag_rows(r.get("flags"))
    if flags:
        with st.expander(f"Guardrail flags ({len(flags)})", expanded=any(f["flag"].startswith("Possible") for f in flags)):
            st.dataframe(flags, hide_index=True, width="stretch")
    tR, tE, tL = st.tabs(["Roadmaps compared", "Evidence", "Run log"])
    with tR:
        st.caption("Code builds and scores the roadmaps; the Critic model can move a score by at most "
                   f"{SETTINGS.rubric_weight:.0%}. Roadmaps from runs before Nov 14 have fewer columns.")
        st.dataframe(roadmap_rows(r.get("roadmaps"), r.get("pruned_log"), tol), hide_index=True, width="stretch")
    with tE:
        ev = evidence_rows(full)
        if ev:
            st.dataframe(ev, hide_index=True, width="stretch")
            if ver.get("note"):
                st.caption(ver["note"])
        else:
            st.info("No evidence report (this result was saved before the Verifier was built). Re-run the analysis.")
    with tL:
        summ = summarize(r.get("call_log", []))
        st.caption(f"Real model calls: {summ['calls']} of a cap of {SETTINGS.max_model_calls}"
                   + (f" ({summ['stub_records_ignored']} old stub records ignored)" if summ["stub_records_ignored"] else "")
                   + f" · review rounds: {r.get('review_round')}")
        st.dataframe(run_summary_rows(summ), hide_index=True, width="stretch")
        st.code("\n".join(r.get("trace", [])))
    t1, t2, t3, t4 = st.tabs(["Ranking", "Process map", "Website check", "Saved files"])
    with t1:
        st.caption(score_scale_note(tol))
        st.dataframe(ranking_rows(opps, tol), hide_index=True, width="stretch")
        left = left_out_ideas(opps, names)
        if left:
            st.caption("Left out of the roadmap:")
            st.dataframe(left, hide_index=True, width="stretch")
    with t2:
        pm = (cases.load(meta["id"], f"results/{run}/process_map.json", None) if run else None) or r.get("process_map") or {}
        if pm:
            st.caption(f"{run or ''} · {pm.get('run_note', '')} · {pm.get('note', '')}")
            idx = pm.get("sources_index", {})
            for p in pm.get("processes", []):
                st.markdown(f"**{p['name']}** ({p['basis']}): {p['description']}")
                for pain in p.get("pain_points", []):
                    st.markdown(f"- {pain}")
                if p.get("sources"):
                    st.caption("Sources: " + "; ".join(
                        f"{cid} ({idx.get(cid, {}).get('source_type', '').replace('_', ' ')}"
                        + (f", {idx[cid]['heading']}" if idx.get(cid, {}).get('heading') else "") + ")"
                        for cid in p["sources"]))
            gaps = pm.get("doc_vs_reality_gaps") or []
            if gaps:
                st.markdown("**Where a document and an interview disagree (owner to resolve):**")
                for g in gaps:
                    st.markdown(f"- **{g.get('process') or 'process'}**: document says *{g['document_says']}*; "
                                f"interview says *{g['interview_says']}* (sources: {', '.join(g['sources'])})")
    with t3:
        wc = website_check_view(disc.get("website_assessment"))
        if not wc:
            st.info("No website check for this case.")
        else:
            st.metric("Website rating", wc["headline"])
            st.write(wc["chatbot"])
            st.dataframe(wc["rows"], hide_index=True, width="stretch")
            for n in wc["notes"]:
                st.caption(n)
    with t4:
        root = cases.case_dir(meta["id"])
        st.code("\n".join(str(p.relative_to(root)) for p in sorted(root.rglob("*")) if p.is_file()))
        st.caption("Owner decisions and corrections are in owner/decisions.json; each run is in results/run-NNN/.")
