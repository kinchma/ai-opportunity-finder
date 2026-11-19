"""Case workspace: start a customer case, close the app, and resume it later.

Run:  streamlit run app_cases.py
Each customer is an isolated folder under cases/ (see opportunity_finder/cases.py). Every stage
saves to disk, so you can stop after Discovery, wait for documents, and pick the case up again.
"""
import streamlit as st

from opportunity_finder import case_runner, cases
from opportunity_finder.config import SETTINGS
from opportunity_finder.observability import summarize
from opportunity_finder.summaries import (evidence_rows, flag_rows, left_out_ideas, roadmap_rows,
                                          run_summary_rows, website_check_view)

st.set_page_config(page_title="AI Opportunity Finder: Cases", page_icon="🗂️", layout="wide")
ss = st.session_state
STEPS = [("new", "Discovery"), ("discovered", "Confirm profile"), ("confirmed", "Documents"), ("analyzed", "Recommendation")]


def tracker(stage: str):
    done = cases.STAGES.index(stage)
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
            site = st.text_input("Website URL (blank = synthetic demo company)")
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
profile = cases.load(meta["id"], "profile.json", {})
disc = cases.load(meta["id"], "discovery.json", {})
if stage in ("discovered", "confirmed", "analyzed") and profile:
    with st.container(border=True):
        st.markdown(f"**{profile.get('name', 'unknown')}**  ·  {profile.get('website', '')}")
        st.write(f"Industry: **{profile.get('industry', 'unknown')}** ({profile.get('confidence', 'n/a')} confidence)")
        if profile.get("evidence"):
            st.caption(profile["evidence"])
        if profile.get("note"):
            st.warning(profile["note"])
if stage == "discovered":
    fix = st.text_input("Industry (edit if wrong)", value=profile.get("industry", ""))
    if st.button("Confirm profile", type="primary"):
        corrections = {"industry": fix.strip()} if fix.strip() and fix.strip() != profile.get("industry") else {}
        case_runner.confirm(meta["id"], corrections)
        st.rerun()

# ------------------------------------------------------------------ stage 3: documents and analysis
if stage in ("confirmed", "analyzed"):
    st.markdown("#### Process documents from the owner")
    st.caption("Text files (.txt, .md, .csv, .json) are read by the Process Mapper. Other files are stored but not read yet. "
               "Documents can arrive weeks after Discovery; add them whenever they do.")
    ups = st.file_uploader("Add documents", accept_multiple_files=True, key=f"up-{meta['id']}-{len(cases.list_document_files(meta['id']))}")
    if ups:
        for f in ups:
            info = cases.add_document(meta["id"], f.name, f.getvalue())
            st.toast(f"Saved {info['file']}" + ("" if info["readable"] else " (stored, not read)"))
        st.rerun()
    files = cases.list_document_files(meta["id"])
    st.write("Documents on file: " + (", ".join(files) if files else "none yet"))
    label = "Run analysis" if stage == "confirmed" else "Re-run analysis with the current documents"
    if st.button(label, type="primary"):
        with st.spinner("Running the pipeline (this can take a few minutes with a local model)..."):
            case_runner.analyze(meta["id"])
        st.rerun()

# ------------------------------------------------------------------ stage 4: results
if stage == "analyzed":
    r = cases.load(meta["id"], "result.json", {})
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
            st.caption("Your choice is saved in decisions.json. Nothing below has been verified.")
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
    for col, (i, n) in zip(st.columns(max(len(names), 1)), enumerate(names, 1)):
        o = by_name.get(n, {})
        col.metric(f"{i}. {n}", o.get("score", ""), help=o.get("what_the_agent_does", ""))
        col.caption(f"Value {o.get('value')} · Effort {o.get('effort')} · Risk {o.get('risk')}")
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
        st.dataframe(roadmap_rows(r.get("roadmaps"), r.get("pruned_log")), hide_index=True, width="stretch")
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
        st.dataframe([{"opportunity": o["name"], "score": o["score"], "process": o.get("process"), "value": o["value"],
                       "effort": o["effort"], "risk": o["risk"], "what it does": o.get("what_the_agent_does", "")}
                      for o in sorted(opps, key=lambda o: -o["score"])], hide_index=True, width="stretch")
        left = left_out_ideas(opps, names)
        if left:
            st.caption("Left out of the roadmap:")
            st.dataframe(left, hide_index=True, width="stretch")
    with t2:
        versions = sorted(p.name for p in cases.case_dir(meta["id"]).glob("process_map.v*.json"))
        if versions:
            v = st.selectbox("Version", versions, index=len(versions) - 1)
            pm = cases.load(meta["id"], v, {})
            st.caption(f"{pm.get('version_note', '')} · {pm.get('note', '')}")
            for p in pm.get("processes", []):
                st.markdown(f"**{p['name']}** ({p['basis']}): {p['description']}")
                for pain in p.get("pain_points", []):
                    st.markdown(f"- {pain}")
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
        st.caption("Owner decisions and corrections are in decisions.json.")
