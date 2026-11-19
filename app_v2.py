"""Restyled Streamlit front end for the AI Opportunity Finder (v2).

Run from the project folder (venv active):   streamlit run app_v2.py
Same pipeline wiring as app.py (graph, llm settings, observability) -- only the look changes:
hero banner, step tracker, result cards, rating pills, score bars. app.py is left untouched.
"""
import html
import uuid

import streamlit as st
from langgraph.types import Command

from opportunity_finder.graph import build_graph
from opportunity_finder.llm import llm_settings
from opportunity_finder.observability import summarize, write_run_log
from opportunity_finder.summaries import left_out_ideas, pruned_rows, website_check_view

AGENTS = ["discovery_profile", "discovery_research", "process_mapper", "matcher",
          "strategist", "critic", "planner"]
STUB_AGENTS = {"strategist", "critic", "planner"}  # no model calls yet; update as you build them
RULE_BASED = ["supervisor"]  # plain code, never calls a model (it routes, prunes and decides when to stop)
STEP_LABELS = {
    "owner_confirm": "Profile confirmed", "discovery_research": "Researched best practices",
    "process_mapper": "Mapped business processes", "matcher": "Proposed and scored ideas",
    "strategist": "Drafted roadmaps", "critic": "Scored roadmaps", "review_gate": "Reviewed and pruned",
    "planner": "Verified and planned", "escalate_to_owner": "Asked the owner for help",
}
FLOW = ["Describe", "Confirm", "Results"]

st.set_page_config(page_title="AI Opportunity Finder", page_icon=":material/travel_explore:", layout="wide")

CSS = """
<style>
:root { --brand:#0F6E56; --brand-dark:#0B4F3F; --ink:#1F2933; --muted:#6B7A86; --line:#E3E9E7; --soft:#F3F6F5; }
#MainMenu, footer { visibility:hidden; }
.block-container { padding-top:1.6rem; max-width:1180px; }
h1,h2,h3 { color:var(--ink); letter-spacing:-0.01em; }

.hero { background:linear-gradient(135deg,#0B4F3F 0%,#0F6E56 55%,#1B8F73 100%); color:#fff; border-radius:18px;
        padding:28px 32px 22px 32px; margin-bottom:18px; box-shadow:0 6px 20px rgba(15,110,86,.18); }
.hero h1 { color:#fff; font-size:2rem; margin:0 0 4px 0; padding:0; }
.hero p { color:rgba(255,255,255,.85); margin:0 0 16px 0; font-size:1.02rem; }
.steps { display:flex; gap:10px; flex-wrap:wrap; }
.step { padding:5px 14px; border-radius:999px; font-size:.82rem; font-weight:600; background:rgba(255,255,255,.14); color:rgba(255,255,255,.75); }
.step.on { background:#fff; color:var(--brand-dark); }
.step.done { background:rgba(255,255,255,.28); color:#fff; }

.card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px 18px; margin-bottom:12px;
        box-shadow:0 1px 3px rgba(31,41,51,.05); }
.card h4 { margin:0 0 2px 0; font-size:1.02rem; color:var(--ink); }
.card .sub { color:var(--muted); font-size:.85rem; margin-bottom:8px; }
.card .body { color:var(--ink); font-size:.93rem; line-height:1.45; }
.card ul { margin:6px 0 0 18px; padding:0; color:var(--ink); font-size:.9rem; }
.card .meta { color:var(--muted); font-size:.8rem; margin-top:8px; }

.rec { border-top:4px solid var(--brand); }
.rank { display:inline-flex; align-items:center; justify-content:center; width:28px; height:28px; border-radius:50%;
        background:var(--brand); color:#fff; font-weight:700; font-size:.85rem; margin-right:8px; }
.rec h4 { display:flex; align-items:center; }

.pill { display:inline-block; padding:2px 10px; border-radius:999px; font-size:.76rem; font-weight:600; margin:2px 6px 2px 0; }
.good { background:#E3F4EC; color:#0B6B45; } .mid { background:#FFF1D6; color:#8A5A00; }
.bad { background:#FDE4E1; color:#A02C20; } .gray { background:#EDF0F2; color:#52616B; }

.bar { background:var(--soft); border-radius:999px; height:9px; overflow:hidden; margin:6px 0 2px 0; }
.bar > span { display:block; height:100%; border-radius:999px; background:linear-gradient(90deg,#1B8F73,#0F6E56); }
.barrow { display:flex; align-items:center; gap:12px; margin:7px 0; }
.barrow .lbl { width:34%; font-size:.88rem; color:var(--ink); }
.barrow .track { flex:1; }
.barrow .val { width:48px; text-align:right; font-weight:700; font-size:.88rem; color:var(--brand-dark); }

.kpi { background:var(--soft); border-radius:14px; padding:14px 16px; }
.kpi .n { font-size:1.6rem; font-weight:700; color:var(--brand-dark); line-height:1.1; }
.kpi .t { font-size:.78rem; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; margin-top:2px; }

.sect { font-size:.78rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); margin:6px 0 8px 2px; }
.mrow { display:flex; justify-content:space-between; align-items:center; padding:5px 0; border-bottom:1px solid var(--line); font-size:.85rem; }
.mrow .a { color:var(--ink); } .mrow .m { color:var(--muted); font-size:.74rem; }

.stTabs [data-baseweb="tab"] { font-weight:600; }
.stButton > button, .stFormSubmitButton > button { border-radius:10px; font-weight:600; padding:.45rem 1.2rem; }
[data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

ss = st.session_state
ss.setdefault("stage", "intake")


def start_over():
    for key in ("stage", "graph", "cfg", "profile", "result", "log_path"):
        ss.pop(key, None)


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def pill(text, kind="gray") -> str:
    return f'<span class="pill {kind}">{esc(text)}</span>'


def rating_pill(label, v, high_is_good) -> str:
    good = v >= 7 if high_is_good else v <= 3
    bad = v <= 3 if high_is_good else v >= 7
    return pill(f"{label} {v}/10", "good" if good else "bad" if bad else "mid")


def bar(frac) -> str:
    return f'<div class="bar"><span style="width:{max(0, min(frac, 1)) * 100:.0f}%"></span></div>'


def kpi(col, value, label):
    col.markdown(f'<div class="kpi"><div class="n">{esc(value)}</div><div class="t">{esc(label)}</div></div>',
                 unsafe_allow_html=True)


def hero(stage_idx: int):
    steps = "".join(
        f'<span class="step {"on" if i == stage_idx else "done" if i < stage_idx else ""}">{i + 1}. {s}</span>'
        for i, s in enumerate(FLOW))
    st.markdown(
        '<div class="hero"><h1>AI Opportunity Finder</h1>'
        '<p>Find where AI agents can save a small business time and money.</p>'
        f'<div class="steps">{steps}</div></div>', unsafe_allow_html=True)


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown('<div class="sect">How it works</div>', unsafe_allow_html=True)
    st.markdown(
        "1. **Read** the business from its website  \n"
        "2. **Confirm** the industry guess  \n"
        "3. **Research** best practices, map processes  \n"
        "4. **Propose and score** AI agent ideas  \n"
        "5. **Review** roadmaps and recommend the best")
    st.divider()
    st.markdown('<div class="sect">Models in use</div>', unsafe_allow_html=True)
    rows = []
    for a in RULE_BASED:
        rows.append(f'<div class="mrow"><div><div class="a">{esc(a.replace("_", " ").title())}</div>'
                    f'<div class="m">rule-based code</div></div>{pill("no model", "gray")}</div>')
    for a in AGENTS:
        s = llm_settings(agent=a)
        if a in STUB_AGENTS:
            tag, model = pill("stub", "gray"), "no model yet"
        else:
            tag, model = pill("hosted" if s["hosted"] else "local", "mid" if s["hosted"] else "good"), s["model"]
        rows.append(f'<div class="mrow"><div><div class="a">{esc(a.replace("_", " ").title())}</div>'
                    f'<div class="m">{esc(model)}</div></div>{tag}</div>')
    st.markdown("".join(rows), unsafe_allow_html=True)
    st.caption("Models run locally by default. A hosted model is blocked unless you allow it in .env.")

stage_idx = {"intake": 0, "confirm": 1}.get(ss.stage, 2)
hero(stage_idx)

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
    conf = p.get("confidence", "low")
    st.markdown(
        f'<div class="card"><h4>{esc(p.get("name", "unknown"))}</h4>'
        f'<div class="sub">{esc(p.get("website", ""))}</div>'
        f'<div class="body">Our best guess: <b>{esc(p.get("industry", "unknown"))}</b> '
        f'{pill(conf + " confidence", {"high": "good", "medium": "mid"}.get(conf, "bad"))}</div>'
        + (f'<div class="meta">Why: {esc(p["evidence"])}</div>' if p.get("evidence") else "") + "</div>",
        unsafe_allow_html=True)
    if p.get("note"):
        st.warning(p["note"])
    with st.container(border=True):
        industry = st.text_input("Industry (edit if wrong)", value=p.get("industry", "unknown"))
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
    s = summarize(r.get("call_log", []))

    if r.get("status") != "complete":
        st.warning(f"Status: {r.get('status')}")
    if any(o.get("placeholder") for o in opps):
        st.warning("The model gave too few valid ideas, so PLACEHOLDER opportunities were used. "
                   "Treat this result as a demo.")

    st.markdown('<div class="sect">Recommended roadmap</div>', unsafe_allow_html=True)
    names = rec["opportunities"]
    if names:
        for col, (i, name) in zip(st.columns(len(names), gap="medium"), enumerate(names, 1)):
            o = by_name.get(name, {})
            col.markdown(
                f'<div class="card rec"><h4><span class="rank">{i}</span>{esc(name)}</h4>'
                f'<div class="sub">{esc(o.get("process") or "General")}</div>'
                f'{bar(o.get("score", 0))}'
                f'<div class="meta">Score {esc(o.get("score", ""))}</div>'
                f'<div style="margin-top:6px">{rating_pill("Value", o.get("value", 0), True)}'
                f'{rating_pill("Effort", o.get("effort", 0), False)}'
                f'{rating_pill("Risk", o.get("risk", 0), False)}</div></div>', unsafe_allow_html=True)
    st.caption(f"Roadmap '{rec['id']}' ({rec['angle']}) scored {rec['score']} "
               f"after {r.get('review_round')} review round(s).")

    k = st.columns(4)
    kpi(k[0], r.get("status", ""), "Status")
    kpi(k[1], r.get("review_round"), "Review rounds")
    kpi(k[2], s["calls"], "Model calls")
    kpi(k[3], s["seconds"], "Seconds")
    st.write("")

    tab1, tab2, tab3, tab4, tabw, tab5 = st.tabs(
        ["Opportunities", "Processes", "Best practices", "Alternatives considered", "Website check", "Run details"])

    with tab1:
        ranked = sorted(opps, key=lambda o: -o["score"])
        st.markdown('<div class="sect">Ranking by score</div>', unsafe_allow_html=True)
        st.markdown("".join(
            f'<div class="barrow"><div class="lbl">{esc(o["name"])}</div>'
            f'<div class="track">{bar(o["score"])}</div><div class="val">{o["score"]}</div></div>'
            for o in ranked), unsafe_allow_html=True)
        st.write("")
        st.markdown('<div class="sect">Details</div>', unsafe_allow_html=True)
        for o in ranked:
            chunk = o.get("supporting_chunk_id")
            st.markdown(
                f'<div class="card"><h4>{esc(o["name"])}</h4>'
                f'<div class="sub">{esc(o.get("process") or "General")}'
                f'{" · enabler" if o.get("enabler") else ""}</div>'
                f'<div>{rating_pill("Value", o["value"], True)}{rating_pill("Effort", o["effort"], False)}'
                f'{rating_pill("Risk", o["risk"], False)}{pill("Score " + str(o["score"]))}'
                f'{pill("Practice " + str(chunk), "good") if chunk else pill("No practice cited", "mid")}</div>'
                f'<div class="body" style="margin-top:8px">{esc(o.get("what_the_agent_does", ""))}</div>'
                + (f'<div class="meta">Why these ratings: {esc(o["rating_reason"])}</div>'
                   if o.get("rating_reason") else "") + "</div>", unsafe_allow_html=True)
        with st.expander("Full table"):
            st.dataframe(
                [{"opportunity": o["name"], "score": o["score"], "process": o.get("process"),
                  "value": o["value"], "effort": o["effort"], "risk": o["risk"],
                  "practice": o.get("supporting_chunk_id")} for o in ranked],
                hide_index=True, width="stretch")

    with tab2:
        pm = r.get("process_map", {})
        if pm.get("note"):
            st.caption(pm["note"])
        for p in pm.get("processes", []):
            pains = "".join(f"<li>{esc(x)}</li>" for x in p.get("pain_points", []))
            st.markdown(
                f'<div class="card"><h4>{esc(p["name"])} '
                f'{pill(p["basis"], "good" if p["basis"] == "stated" else "gray")}</h4>'
                f'<div class="body">{esc(p["description"])}</div>'
                + (f"<ul>{pains}</ul>" if pains else "") + "</div>", unsafe_allow_html=True)

    with tab3:
        bp = r.get("best_practices", {})
        if bp.get("note"):
            st.warning(bp["note"])
        for pr in bp.get("practices", []):
            st.markdown(
                f'<div class="card"><h4>{esc(pr["practice"])}</h4>'
                f'<div class="body">{esc(pr["why_it_matters"])}</div>'
                f'<div class="meta">Source: {esc(pr["source"])} · passage {esc(pr["chunk_id"])}</div></div>',
                unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="sect">Ideas not in the recommended roadmap</div>', unsafe_allow_html=True)
        st.caption("Ideas that scored well enough to be proposed but are not in the recommended roadmap, and why.")
        left_out = left_out_ideas(opps, rec["opportunities"])
        if not left_out:
            st.info("Every proposed idea is in the recommended roadmap.")
        for row in left_out:
            st.markdown(
                f'<div class="card"><h4>{esc(row["name"])} {pill("Score " + str(row["score"]))}</h4>'
                f'<div class="sub">{esc(row["process"])}</div>'
                f'<div class="body">{esc(row["reason"])}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="sect" style="margin-top:14px">Other roadmaps compared</div>',
                    unsafe_allow_html=True)
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
        kpi(t[0], s["input_tokens"], "Input tokens")
        kpi(t[1], s["output_tokens"], "Output tokens")
        kpi(t[2], s["errors"], "Errors")
        st.caption(f"{s['calls_without_usage']} call(s) reported no token usage (stubs, or a server that does not "
                   f"report it). Log saved to {ss.log_path}")
        st.json(s["calls_by_agent"])
        with st.expander("Step-by-step trace"):
            for line in r.get("trace", []):
                st.text(line)

    if st.button("Analyze another business"):
        start_over()
        st.rerun()
