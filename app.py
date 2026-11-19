"""Streamlit front end for the AI Opportunity Finder.

Run from the project folder (venv active):   streamlit run app.py
This file only CALLS the existing code (graph, llm settings, observability); it changes none of it.
Screens: 1 intake -> 2 confirm the Discovery guess -> 3 results.
"""
import uuid

import streamlit as st
from langgraph.types import Command

from opportunity_finder.graph import build_graph
from opportunity_finder.llm import llm_settings
from opportunity_finder.observability import summarize, write_run_log
from opportunity_finder.summaries import left_out_ideas, pruned_rows, website_check_view

AGENTS = ["discovery_profile", "discovery_research", "process_mapper", "matcher",
          "strategist", "critic", "planner"]
STEP_LABELS = {
    "owner_confirm": "Profile confirmed", "discovery_research": "Researched best practices",
    "process_mapper": "Mapped business processes", "matcher": "Proposed and scored ideas",
    "strategist": "Drafted roadmaps", "critic": "Scored roadmaps", "review_gate": "Reviewed and pruned",
    "planner": "Verified and planned", "escalate_to_owner": "Asked the owner for help",
}
STUB_AGENTS = {"strategist", "critic", "planner"}  # no model calls yet
CONFIDENCE_BADGE = {"high": "green", "medium": "orange", "low": "red"}

st.set_page_config(page_title="AI Opportunity Finder", page_icon=":material/travel_explore:", layout="wide")
ss = st.session_state
ss.setdefault("stage", "intake")


def start_over():
    for key in ("stage", "graph", "cfg", "profile", "result", "log_path"):
        ss.pop(key, None)


def badge(text: str, color: str) -> str:
    return f":{color}-badge[{text}]"


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. **Read** the business from its website  \n"
        "2. **Confirm** the industry guess  \n"
        "3. **Research** best practices and map processes  \n"
        "4. **Propose and score** AI agent ideas  \n"
        "5. **Review** roadmaps and recommend the best")
    st.divider()
    st.subheader("Models in use")
    rows = [{"agent": "supervisor", "model": "rule-based code", "runs": "no model"}]
    for a in AGENTS:
        s = llm_settings(agent=a)
        rows.append({"agent": a, "model": "no model yet" if a in STUB_AGENTS else s["model"],
                     "runs": "stub" if a in STUB_AGENTS else "hosted" if s["hosted"] else "local"})
    st.dataframe(rows, hide_index=True, width="stretch")
    st.caption("Models run locally by default. A hosted model is blocked unless you allow it in .env.")

st.title("AI Opportunity Finder")
st.caption("Find where AI agents can save a small business time and money.")

# ---------------------------------------------------------------- 1. intake
if ss.stage == "intake":
    with st.container(border=True):
        st.subheader("Tell us about the business")
        with st.form("intake", border=False):
            left, right = st.columns([3, 2], gap="large")
            site = left.text_input("Website URL", placeholder="example.com",
                                   help="Leave blank to use the synthetic demo company.")
            desc = left.text_area("Short description (optional)", height=100,
                                  help="Used if the site blocks automated reading or has little text.")
            risk = right.slider("Risk tolerance", 0.0, 1.0, 0.4,
                                help="Lower means risky ideas are penalized more.")
            budget = right.number_input("Budget in dollars (optional)", min_value=0, value=0, step=1000)
            linkedin = left.text_area("LinkedIn page text (optional, paste it yourself)", height=100,
                                      help="Copy the company's LinkedIn About text and paste it here. The tool never logs in to or scrapes LinkedIn.")
            go = st.form_submit_button("Find opportunities", type="primary")
    if go:
        company = {"risk_tolerance": risk}
        if budget:
            company["budget"] = budget
        if site.strip():
            company["website"] = site.strip()
            if desc.strip():
                company["description"] = desc.strip()
            if linkedin.strip():
                company["linkedin_text"] = linkedin.strip()
        else:
            company.update({"name": "Synthetic Trailers Inc", "industry": "trailer manufacturing", "size": "50"})
        ss.graph = build_graph()
        ss.cfg = {"configurable": {"thread_id": uuid.uuid4().hex}}
        with st.spinner("Reading the business..."):
            ss.graph.invoke({"company_input": company, "status": "running"}, ss.cfg)  # pauses at owner_confirm
        ss.profile = ss.graph.get_state(ss.cfg).values.get("profile", {})
        ss.stage = "confirm"
        st.rerun()

# --------------------------------------------------------------- 2. confirm
elif ss.stage == "confirm":
    p = ss.profile
    with st.container(border=True):
        st.subheader("Is this the right business?")
        st.markdown(f"**{p.get('name', 'unknown')}**  \n{p.get('website', '')}")
        c1, c2 = st.columns([3, 1], gap="large")
        industry = c1.text_input("Industry (edit if wrong)", value=p.get("industry", "unknown"))
        conf = p.get("confidence", "low")
        c2.markdown("Model confidence")
        c2.markdown(badge(conf, CONFIDENCE_BADGE.get(conf, "gray")))
        if p.get("evidence"):
            st.caption(f"Why: {p['evidence']}")
        if p.get("note"):
            st.warning(p["note"])
        go, back, _ = st.columns([1, 1, 4])
        if go.button("Continue", type="primary"):
            corrections = {"industry": industry.strip()} if industry.strip() != p.get("industry") else {}
            with st.status("Running the agents (a minute or so with a local model)...", expanded=True) as status:
                for update in ss.graph.stream(Command(resume={"corrections": corrections}), ss.cfg,
                                              stream_mode="updates"):
                    for node in update:
                        if node in STEP_LABELS:
                            st.write(f":material/check: {STEP_LABELS[node]}")
                status.update(label="Finished", state="complete", expanded=False)
            ss.result = ss.graph.get_state(ss.cfg).values
            ss.log_path = write_run_log(ss.result, "ui")
            ss.stage = "results"
            st.rerun()
        if back.button("Start over"):
            start_over()
            st.rerun()

# --------------------------------------------------------------- 3. results
else:
    r = ss.result
    rec = r["final_recommendation"]["roadmap"]
    opps = r["scored_opportunities"]
    by_name = {o["name"]: o for o in opps}

    if r.get("status") != "complete":
        st.warning(f"Status: {r.get('status')}")
    if any(o.get("placeholder") for o in opps):
        st.warning("The model gave too few valid ideas, so PLACEHOLDER opportunities were used. Treat this result as a demo.")

    with st.container(border=True):
        st.subheader("Recommended roadmap")
        if rec["opportunities"]:
            for col, name in zip(st.columns(len(rec["opportunities"]), gap="medium"), rec["opportunities"]):
                o = by_name.get(name, {})
                with col.container(border=True):
                    st.markdown(f"**{name}**")
                    st.caption(o.get("process") or "General")
                    st.markdown(f"Score **{o.get('score', '')}**")
        st.caption(f"Roadmap '{rec['id']}' ({rec['angle']}) scored {rec['score']} "
                   f"after {r.get('review_round')} review round(s).")

    s = summarize(r.get("call_log", []))
    m = st.columns(4)
    m[0].metric("Status", r.get("status", ""))
    m[1].metric("Review rounds", r.get("review_round"))
    m[2].metric("Model calls", s["calls"])
    m[3].metric("Seconds", s["seconds"])

    tab1, tab2, tab3, tab4, tabw, tab5 = st.tabs(
        ["Opportunities", "Processes", "Best practices", "Alternatives considered", "Website check", "Run details"])

    with tab1:
        ranked = sorted(opps, key=lambda o: -o["score"])
        st.bar_chart({"opportunity": [o["name"] for o in ranked], "score": [o["score"] for o in ranked]},
                     x="opportunity", y="score", color="#0F6E56")
        st.dataframe(
            [{"opportunity": o["name"], "score": o["score"], "process": o.get("process"),
              "value": o["value"], "effort": o["effort"], "risk": o["risk"],
              "practice": o.get("supporting_chunk_id"), "what it does": o.get("what_the_agent_does", ""),
              "why these ratings": o.get("rating_reason", "")} for o in ranked],
            hide_index=True, width="stretch")

    with tab2:
        pm = r.get("process_map", {})
        st.caption(pm.get("note", ""))
        for p in pm.get("processes", []):
            with st.container(border=True):
                st.markdown(f"**{p['name']}** {badge(p['basis'], 'green' if p['basis'] == 'stated' else 'gray')}")
                st.write(p["description"])
                for pain in p.get("pain_points", []):
                    st.markdown(f"- {pain}")

    with tab3:
        bp = r.get("best_practices", {})
        if bp.get("note"):
            st.warning(bp["note"])
        for pr in bp.get("practices", []):
            with st.container(border=True):
                st.markdown(f"**{pr['practice']}**")
                st.write(pr["why_it_matters"])
                st.caption(f"Source: {pr['source']}  ·  passage {pr['chunk_id']}")

    with tab4:
        st.subheader("Ideas not in the recommended roadmap")
        st.caption("Ideas that scored well enough to be proposed but are not in the recommended roadmap, and why.")
        left_out = left_out_ideas(opps, rec["opportunities"])
        if left_out:
            st.dataframe(left_out, hide_index=True, width="stretch")
        else:
            st.info("Every proposed idea is in the recommended roadmap.")
        st.subheader("Other roadmaps compared")
        st.caption("The Strategist drafts several candidate roadmaps (bundles of up to 3 ideas), each built around a different strategy. The Supervisor keeps the top scorers and drops the rest. These are the dropped ones.")
        st.dataframe(pruned_rows(r.get("pruned_log", [])) or [{"note": "nothing pruned"}],
                     hide_index=True, width="stretch")

    with tabw:
        wc = website_check_view(r.get("website_assessment"))
        if not wc:
            st.info("No website check: it needs a website address that could be read.")
        else:
            c1, c2 = st.columns([1, 3])
            c1.metric("Website rating", wc["headline"])
            (c2.success if wc["chatbot_status"] == "found" else c2.warning)(wc["chatbot"])
            st.dataframe(wc["rows"], hide_index=True, width="stretch")
            if wc["chatbot_status"] == "not_found":
                st.markdown("**Suggested starter choices for a website assistant:** " + " · ".join(wc["prompts"]))
                st.caption("It is also in the ranking as the 'Website AI assistant' idea.")
            for n in wc["notes"]:
                st.caption(n)

    with tab5:
        t = st.columns(3)
        t[0].metric("Input tokens", s["input_tokens"])
        t[1].metric("Output tokens", s["output_tokens"])
        t[2].metric("Errors", s["errors"])
        st.caption(f"{s['calls_without_usage']} call(s) reported no token usage (stubs, or a server that does not "
                   f"report it). Log saved to {ss.log_path}")
        st.json(s["calls_by_agent"])
        with st.expander("Step-by-step trace"):
            for line in r.get("trace", []):
                st.text(line)

    if st.button("Analyze another business"):
        start_over()
        st.rerun()
