"""NiceGUI front end for the AI Opportunity Finder.

Run from the project folder (venv active):   python app_nicegui.py     then open http://localhost:8080
Same pipeline wiring as app.py / app_v2.py (graph, llm settings, observability); only the UI layer differs.
Slow pipeline calls run in worker threads so the page stays responsive.
"""
import json
import uuid

from langgraph.types import Command
from nicegui import run, ui

from opportunity_finder.graph import build_graph
from opportunity_finder.llm import llm_settings
from opportunity_finder.observability import summarize, write_run_log
from opportunity_finder.summaries import left_out_ideas, pruned_rows, website_check_view

AGENTS = ["discovery_profile", "discovery_research", "process_mapper", "matcher",
          "strategist", "critic", "planner"]
STUB_AGENTS = {"strategist", "critic", "planner"}  # no model calls yet; update as you build them
RULE_BASED = ["supervisor"]                        # plain code, never calls a model
STEP_LABELS = {
    "owner_confirm": "Profile confirmed", "discovery_research": "Researched best practices",
    "process_mapper": "Mapped business processes", "matcher": "Proposed and scored ideas",
    "strategist": "Drafted roadmaps", "critic": "Scored roadmaps", "review_gate": "Reviewed and pruned",
    "planner": "Verified and planned", "escalate_to_owner": "Asked the owner for help",
}
FLOW = ["Describe", "Confirm", "Results"]
CONF_COLOR = {"high": "positive", "medium": "warning", "low": "negative"}

CSS = """
<style>
body { background:#F3F6F5; }
.hero { background:linear-gradient(135deg,#0B4F3F 0%,#0F6E56 55%,#1B8F73 100%); border-radius:18px; color:white; }
.step { padding:4px 14px; border-radius:999px; font-size:.8rem; font-weight:600;
        background:rgba(255,255,255,.14); color:rgba(255,255,255,.75); }
.step.on { background:white; color:#0B4F3F; } .step.done { background:rgba(255,255,255,.28); color:white; }
.sect { font-size:.75rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:#6B7A86; }
.card-soft { border:1px solid #E3E9E7; border-radius:14px; box-shadow:0 1px 3px rgba(31,41,51,.06); }
.rec { border-top:4px solid #0F6E56; }
.rank { width:28px; height:28px; border-radius:50%; background:#0F6E56; color:white; font-weight:700;
        display:flex; align-items:center; justify-content:center; font-size:.85rem; flex:none; }
.kpi-n { font-size:1.6rem; font-weight:700; color:#0B4F3F; line-height:1.1; }
.kpi-t { font-size:.72rem; color:#6B7A86; text-transform:uppercase; letter-spacing:.05em; }
</style>
"""


def pill(text, color="grey-6"):
    return ui.badge(str(text), color=color).props("rounded").classes("text-xs px-2 py-1")


def rating_pill(label, v, high_is_good):
    good = v >= 7 if high_is_good else v <= 3
    bad = v <= 3 if high_is_good else v >= 7
    return pill(f"{label} {v}/10", "positive" if good else "negative" if bad else "warning")


def score_bar(score):
    return ui.linear_progress(value=max(0, min(float(score), 1)), show_value=False, size="10px",
                              color="primary").props("rounded track-color=grey-3").classes("w-full")


def kpi(value, label):
    with ui.card().classes("card-soft flex-1 min-w-[150px] bg-[#EAF1EF]").props("flat"):
        ui.label(str(value)).classes("kpi-n")
        ui.label(label).classes("kpi-t")


@ui.page("/")
def index():
    ui.colors(primary="#0F6E56", secondary="#1B8F73", accent="#0B4F3F")
    ui.add_head_html(CSS)
    state = {"stage": "intake", "busy": "", "steps": [], "site": "", "desc": "", "linkedin": "", "risk": 0.4, "budget": 0,
             "industry": "", "graph": None, "cfg": None, "profile": {}, "result": None, "log_path": ""}

    # ------------------------------------------------------------ sidebar
    with ui.left_drawer(value=True, bordered=True).classes("bg-white").props("width=290"):
        ui.label("How it works").classes("sect mb-1")
        for line in ["Read the business from its website", "Confirm the industry guess",
                     "Research best practices, map processes", "Propose and score AI agent ideas",
                     "Review roadmaps and recommend the best"]:
            ui.label(f"•  {line}").classes("text-sm")
        ui.separator().classes("my-3")
        ui.label("Models in use").classes("sect mb-1")
        for a in RULE_BASED:
            with ui.row().classes("w-full items-center justify-between no-wrap border-b py-1"):
                with ui.column().classes("gap-0"):
                    ui.label(a.replace("_", " ").title()).classes("text-sm")
                    ui.label("rule-based code").classes("text-xs text-grey-6")
                pill("no model")
        for a in AGENTS:
            s = llm_settings(agent=a)
            with ui.row().classes("w-full items-center justify-between no-wrap border-b py-1"):
                with ui.column().classes("gap-0"):
                    ui.label(a.replace("_", " ").title()).classes("text-sm")
                    ui.label("no model yet" if a in STUB_AGENTS else s["model"]).classes("text-xs text-grey-6")
                if a in STUB_AGENTS:
                    pill("stub")
                else:
                    pill("hosted" if s["hosted"] else "local", "warning" if s["hosted"] else "positive")
        ui.label("Models run locally by default. A hosted model is blocked unless you allow it in .env."
                 ).classes("text-xs text-grey-6 mt-2")

    # ------------------------------------------------------------ actions
    def start_over():
        state.update(stage="intake", busy="", steps=[], profile={}, result=None, graph=None, cfg=None)
        screen.refresh()

    async def find():
        company = {"risk_tolerance": state["risk"]}
        if state["budget"]:
            company["budget"] = state["budget"]
        if state["site"].strip():
            company["website"] = state["site"].strip()
            if state["desc"].strip():
                company["description"] = state["desc"].strip()
            if state["linkedin"].strip():
                company["linkedin_text"] = state["linkedin"].strip()
        else:
            company.update({"name": "Synthetic Trailers Inc", "industry": "trailer manufacturing", "size": "50"})
        state["busy"] = "Reading the business..."
        screen.refresh()
        try:
            state["graph"] = build_graph()
            state["cfg"] = {"configurable": {"thread_id": uuid.uuid4().hex}}
            await run.io_bound(state["graph"].invoke, {"company_input": company, "status": "running"}, state["cfg"])
            state["profile"] = state["graph"].get_state(state["cfg"]).values.get("profile", {})
            state["industry"] = state["profile"].get("industry", "unknown")
            state["stage"] = "confirm"
        except Exception as exc:  # show the error instead of a blank page
            ui.notify(f"Run failed: {exc}", type="negative", multi_line=True)
        state["busy"] = ""
        screen.refresh()

    async def carry_on():
        p = state["profile"]
        industry = state["industry"].strip()
        corrections = {"industry": industry} if industry and industry != p.get("industry") else {}
        state["busy"] = "Running the agents (a minute or so with a local model)..."
        state["steps"] = []
        screen.refresh()
        try:
            it = state["graph"].stream(Command(resume={"corrections": corrections}), state["cfg"],
                                       stream_mode="updates")
            while True:
                update = await run.io_bound(next, it, None)
                if update is None:
                    break
                for node in update:
                    if node in STEP_LABELS:
                        state["steps"].append(STEP_LABELS[node])
                screen.refresh()
            state["result"] = state["graph"].get_state(state["cfg"]).values
            state["log_path"] = write_run_log(state["result"], "ui")
            state["stage"] = "results"
        except Exception as exc:
            ui.notify(f"Run failed: {exc}", type="negative", multi_line=True)
        state["busy"] = ""
        screen.refresh()

    # ------------------------------------------------------------ screens
    def hero():
        idx = {"intake": 0, "confirm": 1}.get(state["stage"], 2)
        with ui.column().classes("hero w-full p-7 gap-1"):
            ui.label("AI Opportunity Finder").classes("text-3xl font-bold")
            ui.label("Find where AI agents can save a small business time and money.").classes("opacity-85 mb-3")
            with ui.row().classes("gap-2"):
                for i, name in enumerate(FLOW):
                    cls = "on" if i == idx else "done" if i < idx else ""
                    ui.label(f"{i + 1}. {name}").classes(f"step {cls}")

    def busy_view():
        with ui.card().classes("card-soft w-full p-5"):
            with ui.row().classes("items-center gap-3"):
                ui.spinner(size="md")
                ui.label(state["busy"]).classes("text-base")
            for label in state["steps"]:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("check_circle", color="positive")
                    ui.label(label).classes("text-sm")

    def intake_view():
        with ui.card().classes("card-soft w-full p-5"):
            ui.label("Tell us about the business").classes("text-xl font-semibold")
            with ui.row().classes("w-full gap-8 no-wrap items-start"):
                with ui.column().classes("flex-[3] gap-2"):
                    ui.input("Website URL", placeholder="example.com").bind_value(state, "site").props(
                        "outlined dense").classes("w-full")
                    ui.label("Leave blank to use the synthetic demo company.").classes("text-xs text-grey-6")
                    ui.textarea("Short description (optional)",
                                placeholder="Used if the site blocks automated reading or has little text."
                                ).bind_value(state, "desc").props("outlined rows=3").classes("w-full")
                    ui.textarea("LinkedIn page text (optional, paste it yourself)",
                                placeholder="Copy the company's LinkedIn About text. The tool never logs in to or scrapes LinkedIn."
                                ).bind_value(state, "linkedin").props("outlined rows=3").classes("w-full")
                with ui.column().classes("flex-[2] gap-2"):
                    ui.label("Risk tolerance").classes("text-sm")
                    ui.slider(min=0, max=1, step=0.05).bind_value(state, "risk").props("label-always")
                    ui.label("Lower means risky ideas are penalized more.").classes("text-xs text-grey-6")
                    ui.number("Budget in dollars (optional)", min=0, step=1000).bind_value(state, "budget").props(
                        "outlined dense").classes("w-full")
            ui.button("Find opportunities", on_click=find).props("unelevated no-caps").classes("mt-2 px-5")

    def confirm_view():
        p = state["profile"]
        conf = p.get("confidence", "low")
        with ui.card().classes("card-soft w-full p-5"):
            ui.label(p.get("name", "unknown")).classes("text-xl font-semibold")
            ui.label(p.get("website", "")).classes("text-sm text-grey-6")
            with ui.row().classes("items-center gap-2 mt-2"):
                ui.label("Our best guess:").classes("text-sm")
                ui.label(p.get("industry", "unknown")).classes("font-bold")
                pill(f"{conf} confidence", CONF_COLOR.get(conf, "negative"))
            if p.get("evidence"):
                ui.label(f"Why: {p['evidence']}").classes("text-xs text-grey-6")
            if p.get("note"):
                ui.label(p["note"]).classes("text-sm bg-amber-1 text-amber-10 p-2 rounded")
            ui.input("Industry (edit if wrong)").bind_value(state, "industry").props("outlined dense").classes(
                "w-full mt-3")
            with ui.row().classes("gap-3 mt-2"):
                ui.button("Continue", on_click=carry_on).props("unelevated no-caps").classes("px-5")
                ui.button("Start over", on_click=start_over).props("flat no-caps")

    def results_view():
        r = state["result"]
        rec = r["final_recommendation"]["roadmap"]
        opps = r["scored_opportunities"]
        by_name = {o["name"]: o for o in opps}
        s = summarize(r.get("call_log", []))
        ranked = sorted(opps, key=lambda o: -o["score"])

        if r.get("status") != "complete":
            ui.label(f"Status: {r.get('status')}").classes("bg-amber-1 text-amber-10 p-2 rounded")
        if any(o.get("placeholder") for o in opps):
            ui.label("The model gave too few valid ideas, so PLACEHOLDER opportunities were used. "
                     "Treat this result as a demo.").classes("bg-amber-1 text-amber-10 p-2 rounded")

        ui.label("Recommended roadmap").classes("sect")
        with ui.row().classes("w-full gap-4 no-wrap"):
            for i, name in enumerate(rec["opportunities"], 1):
                o = by_name.get(name, {})
                with ui.card().classes("card-soft rec flex-1 gap-1"):
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        ui.label(str(i)).classes("rank")
                        ui.label(name).classes("font-semibold")
                    ui.label(o.get("process") or "General").classes("text-xs text-grey-6")
                    score_bar(o.get("score", 0))
                    ui.label(f"Score {o.get('score', '')}").classes("text-xs text-grey-6")
                    with ui.row().classes("gap-1"):
                        rating_pill("Value", o.get("value", 0), True)
                        rating_pill("Effort", o.get("effort", 0), False)
                        rating_pill("Risk", o.get("risk", 0), False)
        ui.label(f"Roadmap '{rec['id']}' ({rec['angle']}) scored {rec['score']} "
                 f"after {r.get('review_round')} review round(s).").classes("text-xs text-grey-6")

        with ui.row().classes("w-full gap-4"):
            kpi(r.get("status", ""), "Status")
            kpi(r.get("review_round"), "Review rounds")
            kpi(s["calls"], "Model calls")
            kpi(s["seconds"], "Seconds")

        with ui.tabs().classes("w-full justify-start") as tabs:
            t1, t2, t3, t4, tw, t5 = (ui.tab(n) for n in
                                  ["Opportunities", "Processes", "Best practices", "Alternatives considered", "Website check", "Run details"])
        with ui.tab_panels(tabs, value=t1).classes("w-full bg-transparent"):
            with ui.tab_panel(t1).classes("p-0 pt-3 gap-3"):
                ui.label("Ranking by score").classes("sect")
                with ui.card().classes("card-soft w-full gap-1"):
                    for o in ranked:
                        with ui.row().classes("w-full items-center no-wrap gap-3"):
                            ui.label(o["name"]).classes("w-1/3 text-sm")
                            with ui.element("div").classes("flex-1"):
                                score_bar(o["score"])
                            ui.label(str(o["score"])).classes("w-12 text-right font-bold text-sm")
                ui.label("Details").classes("sect mt-2")
                for o in ranked:
                    chunk = o.get("supporting_chunk_id")
                    with ui.card().classes("card-soft w-full gap-1"):
                        ui.label(o["name"]).classes("font-semibold")
                        ui.label(f"{o.get('process') or 'General'}{' · enabler' if o.get('enabler') else ''}"
                                 ).classes("text-xs text-grey-6")
                        with ui.row().classes("gap-1"):
                            rating_pill("Value", o["value"], True)
                            rating_pill("Effort", o["effort"], False)
                            rating_pill("Risk", o["risk"], False)
                            pill(f"Score {o['score']}")
                            pill(f"Practice {chunk}", "positive") if chunk else pill("No practice cited", "warning")
                        ui.label(o.get("what_the_agent_does", "")).classes("text-sm")
                        if o.get("rating_reason"):
                            ui.label(f"Why these ratings: {o['rating_reason']}").classes("text-xs text-grey-6")
            with ui.tab_panel(t2).classes("p-0 pt-3 gap-3"):
                pm = r.get("process_map", {})
                if pm.get("note"):
                    ui.label(pm["note"]).classes("text-xs text-grey-6")
                for p in pm.get("processes", []):
                    with ui.card().classes("card-soft w-full gap-1"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(p["name"]).classes("font-semibold")
                            pill(p["basis"], "positive" if p["basis"] == "stated" else "grey-6")
                        ui.label(p["description"]).classes("text-sm")
                        for pain in p.get("pain_points", []):
                            ui.label(f"•  {pain}").classes("text-sm")
            with ui.tab_panel(t3).classes("p-0 pt-3 gap-3"):
                bp = r.get("best_practices", {})
                if bp.get("note"):
                    ui.label(bp["note"]).classes("bg-amber-1 text-amber-10 p-2 rounded text-sm")
                for pr in bp.get("practices", []):
                    with ui.card().classes("card-soft w-full gap-1"):
                        ui.label(pr["practice"]).classes("font-semibold")
                        ui.label(pr["why_it_matters"]).classes("text-sm")
                        ui.label(f"Source: {pr['source']}  ·  passage {pr['chunk_id']}").classes(
                            "text-xs text-grey-6")
            with ui.tab_panel(t4).classes("p-0 pt-3 gap-3"):
                ui.label("Ideas not in the recommended roadmap").classes("sect")
                ui.label("Ideas that scored well enough to be proposed but are not in the recommended roadmap, and why.").classes("text-xs text-grey-6")
                left_out = left_out_ideas(opps, rec["opportunities"])
                if not left_out:
                    ui.label("Every proposed idea is in the recommended roadmap.").classes("text-sm")
                for row in left_out:
                    with ui.card().classes("card-soft w-full gap-1"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(row["name"]).classes("font-semibold")
                            pill(f"Score {row['score']}")
                        ui.label(row["process"]).classes("text-xs text-grey-6")
                        ui.label(row["reason"]).classes("text-sm")
                ui.label("Other roadmaps compared").classes("sect mt-3")
                ui.label("The Strategist drafts several candidate roadmaps (bundles of up to 3 ideas), each built around a different strategy. The Supervisor keeps the top scorers and drops the rest. These are the dropped ones.").classes("text-xs text-grey-6")
                pruned = pruned_rows(r.get("pruned_log", [])) or [{"note": "nothing pruned"}]
                cols = [{"name": k, "label": k, "field": k, "align": "left"} for k in pruned[0]]
                ui.table(columns=cols, rows=[{k: str(v) for k, v in row.items()} for row in pruned],
                         row_key=cols[0]["name"]).classes("w-full")
            with ui.tab_panel(tw).classes("p-0 pt-3 gap-3"):
                wc = website_check_view(r.get("website_assessment"))
                if not wc:
                    ui.label("No website check: it needs a website address that could be read.").classes("text-sm")
                else:
                    ui.label("Website rating").classes("sect")
                    with ui.row().classes("items-center gap-3"):
                        ui.label(wc["headline"]).classes("text-2xl font-semibold")
                        pill(wc["chatbot"], "positive" if wc["chatbot_status"] == "found" else "orange")
                    cols = [{"name": k, "label": k, "field": k, "align": "left"} for k in wc["rows"][0]]
                    ui.table(columns=cols, rows=[{k: str(v) for k, v in row.items()} for row in wc["rows"]],
                             row_key="Check").classes("w-full")
                    if wc["chatbot_status"] == "not_found":
                        ui.label("Suggested starter choices for a website assistant: " + " · ".join(wc["prompts"])).classes("text-sm")
                        ui.label("It is also in the ranking as the 'Website AI assistant' idea.").classes("text-xs text-grey-6")
                    for n in wc["notes"]:
                        ui.label(n).classes("text-xs text-grey-6")
            with ui.tab_panel(t5).classes("p-0 pt-3 gap-3"):
                with ui.row().classes("w-full gap-4"):
                    kpi(s["input_tokens"], "Input tokens")
                    kpi(s["output_tokens"], "Output tokens")
                    kpi(s["errors"], "Errors")
                ui.label(f"{s['calls_without_usage']} call(s) reported no token usage (stubs, or a server that "
                         f"does not report it). Log saved to {state['log_path']}").classes("text-xs text-grey-6")
                ui.code(json.dumps(s["calls_by_agent"], indent=2), language="json").classes("w-full")
                with ui.expansion("Step-by-step trace").classes("w-full card-soft bg-white"):
                    for line in r.get("trace", []):
                        ui.label(line).classes("text-xs font-mono")

        ui.button("Analyze another business", on_click=start_over).props("outline no-caps")

    @ui.refreshable
    def screen():
        with ui.column().classes("w-full max-w-[1180px] mx-auto gap-4"):
            hero()
            if state["busy"]:
                busy_view()
            elif state["stage"] == "intake":
                intake_view()
            elif state["stage"] == "confirm":
                confirm_view()
            else:
                results_view()

    with ui.column().classes("w-full"):
        screen()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="AI Opportunity Finder", port=8080, reload=False, show=True, favicon="🧭")
