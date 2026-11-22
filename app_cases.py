"""AI Opportunity Finder: the case workspace (Streamlit UI).

Run:  streamlit run app_cases.py
One design system (palette, type scale, components), a dark case header with a progress stepper,
headline KPI tiles, styled section headers and callouts, and a developer section for the agent internals.
Owner-first layout: the recommendation comes right after a compact company summary; Discovery and
the company material fold into sections below it. "Behind the recommendation" holds the agent
timeline (every model call, code step, tokens and time), the roadmaps compared, the evidence and the run log.
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
from opportunity_finder.tools.scoring import idea_index, index_band, risk_limit, score_index

st.set_page_config(page_title="AI Opportunity Finder", page_icon="🔎", layout="wide")
ss = st.session_state
STEPS = [("new", "Discovery"), ("discovered", "Confirm profile"), ("confirmed", "Documents"), ("analyzed", "Recommendation")]


# ------------------------------------------------------------------ v2 look: vertical roadmap cards
import html as _html
import re as _rx

RM_CSS = (
    "<style>"
    ".rm-head{display:grid;grid-template-columns:1fr 88px 88px 88px 128px;gap:8px;align-items:end;padding:0 22px 8px;"
    "color:#5B6770;font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700}"
    ".rm-head .c{text-align:center}"
    ".rm-card{border:1px solid #DDE3E1;border-radius:16px;padding:18px 22px;margin:0 0 14px;background:#FFFFFF;"
    "box-shadow:0 1px 3px rgba(16,24,40,.05)}"
    ".rm-card.pilot{border:1px solid #EFD3A1;border-left:7px solid #E8A33D;background:#FFFBF3;padding:24px 22px}"
    ".rm-top{display:grid;grid-template-columns:1fr 88px 88px 88px 128px;gap:8px;align-items:center}"
    ".rm-title{display:flex;align-items:center;gap:14px;min-width:0}"
    ".rm-rank{flex:none;width:36px;height:36px;border-radius:50%;background:#0F6E56;color:#FFFFFF;font-weight:700;"
    "display:flex;align-items:center;justify-content:center;font-size:1rem}"
    ".pilot .rm-rank{background:#E8A33D;color:#13212E;width:44px;height:44px;font-size:1.2rem}"
    ".rm-name{font-size:1.12rem;font-weight:700;color:#13212E;line-height:1.25}"
    ".pilot .rm-name{font-size:1.4rem}"
    ".rm-tag{display:inline-block;margin-left:10px;font-size:.68rem;font-weight:700;letter-spacing:.08em;padding:3px 9px;"
    "border-radius:999px;background:#13212E;color:#F6DDB0;vertical-align:middle}"
    ".rm-tag.next{background:#E3ECEA;color:#0B5040}"
    ".rm-proc{color:#5B6770;font-size:.84rem;margin-top:3px}"
    ".rm-stat{text-align:center}"
    ".rm-num{font-size:1.55rem;font-weight:700;color:#13212E;line-height:1}"
    ".pilot .rm-num{font-size:1.8rem}"
    ".rm-bar{height:6px;border-radius:3px;background:#E6EBEA;margin:7px 12px 0;overflow:hidden}"
    ".rm-bar span{display:block;height:100%;border-radius:3px}"
    ".rm-fit{text-align:center}"
    ".rm-badge{display:inline-block;padding:4px 11px;border-radius:999px;font-weight:700;font-size:.8rem}"
    ".rm-idx{font-size:.78rem;color:#5B6770;margin-top:5px}"
    ".rm-body{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px}"
    ".rm-sec{background:#F3F6F5;border-radius:12px;padding:12px 14px}"
    ".pilot .rm-sec{background:#FBF0DC}"
    ".rm-sec.wide{grid-column:1 / -1;background:#13212E}"
    ".rm-sec.wide .rm-lbl{color:#E8A33D}.rm-sec.wide .rm-txt{color:#F3EFE6}"
    ".rm-lbl{font-size:.7rem;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:#0F6E56;margin-bottom:5px}"
    ".rm-txt{font-size:.94rem;color:#1F2933;line-height:1.5}"
    ".pilot .rm-txt{font-size:1rem}"
    ".rm-foot{margin-top:12px;font-size:.8rem;color:#5B6770;line-height:1.45}"
    ".rm-ok{color:#0F6E56;font-weight:700}.rm-warn{color:#A8620F;font-weight:700}"
    ".rm-why{border:1px solid #DDE3E1;border-radius:14px;padding:16px 20px;background:#F7F9F8;margin:4px 0 8px}"
    ".rm-why .rm-txt{font-size:.98rem}"
    "</style>"
)


def _e(x) -> str:
    return _html.escape(str(x if x is not None else ""))


def _band_colors(band: str) -> tuple:
    if band.startswith("Strong"):
        return "#0F6E56", "#FFFFFF"
    if band.startswith("Good"):
        return "#D6EDE5", "#0B5040"
    if band.startswith("Possible"):
        return "#FBE8C4", "#7A4B0A"
    return "#E9E9E6", "#444441"


def _evidence_line(claim: dict | None) -> str:
    if not claim:
        return "Evidence: not checked by the Verifier in this run."
    docs = sum(1 for b in claim.get("basis", []) if b.get("type") == "document")
    procs = [b for b in claim.get("basis", []) if b.get("type") == "process"]
    pracs = [b for b in claim.get("basis", []) if b.get("type") == "practice"]
    bits = []
    if procs:
        p = procs[0]
        bits.append(f"process “{_e(p['id'])}” ({'stated in company material' if p.get('stated') else 'typical for the industry: confirm'})")
    if docs:
        bits.append(f"{docs} company passage{'s' if docs != 1 else ''}")
    if pracs:
        bits.append(f"{len(pracs)} best practice{'s' if len(pracs) != 1 else ''}")
    g = '<span class="rm-ok">Grounded</span>' if claim.get("grounded") else '<span class="rm-warn">Not grounded</span>'
    cite = claim.get("citation")
    c = f" · Practice citation {_e(cite.get('status'))}: {_e(cite.get('detail'))}" if cite else ""
    a = ' · <span class="rm-warn">Assumption: owner must confirm</span>' if claim.get("assumption") else ""
    return f"{g}: " + ("; ".join(bits) or _e(claim.get("note", ""))) + c + a


def roadmap_cards(names: list, by_name: dict, tol: float, rec: dict, claims: list) -> str:
    claim_by = {c.get("idea"): c for c in claims or []}
    rub = rec.get("rubric") or {}
    out = [RM_CSS, '<div class="rm-head"><div>Recommended roadmap</div><div class="c">Value ↑</div>'
                   '<div class="c">Effort ↓</div><div class="c">Risk ↓</div><div class="c">Fit index</div></div>']
    for i, n in enumerate(names, 1):
        o = by_name.get(n, {})
        idx = idea_index(o, tol)
        band = index_band(idx)
        bg, fg = _band_colors(band)
        pilot = i == 1
        tag = '<span class="rm-tag">PILOT</span>' if pilot else f'<span class="rm-tag next">STEP {i}</span>'
        stats = "".join(
            f'<div class="rm-stat"><div class="rm-num">{_e(o.get(k))}</div><div class="rm-bar">'
            f'<span style="width:{int(o.get(k) or 0) * 10}%;background:{col}"></span></div></div>'
            for k, col in (("value", "#0F6E56"), ("effort", "#E8A33D"), ("risk", "#D85A30")))
        top = (f'<div class="rm-top"><div class="rm-title"><div class="rm-rank">{i}</div><div>'
               f'<div class="rm-name">{_e(n)}{tag}</div><div class="rm-proc">Process: {_e(o.get("process") or "not tied to one process")}</div>'
               f'</div></div>{stats}<div class="rm-fit"><span class="rm-badge" style="background:{bg};color:{fg}">{_e(band)}</span>'
               f'<div class="rm-idx">{idx} / 100 · raw {_e(o.get("score"))}</div></div></div>')
        secs = [("Problem identified", o.get("gap")),
                ("What the AI agent will do", o.get("what_the_agent_does")),
                ("How it makes things better", o.get("rating_reason"))]
        body = "".join(f'<div class="rm-sec"><div class="rm-lbl">{lbl}</div><div class="rm-txt">{_e(txt) or "Not stated in this run."}</div></div>'
                       for lbl, txt in secs)
        if pilot and rec.get("pilot_reason"):
            body += (f'<div class="rm-sec wide"><div class="rm-lbl">Why this pilot</div>'
                     f'<div class="rm-txt">{_e(rec["pilot_reason"])}</div></div>')
        if rub.get("weakest_item") == n and rub.get("objection"):
            body += (f'<div class="rm-sec" style="grid-column:1 / -1;background:#FFF1E8"><div class="rm-lbl" style="color:#993C1D">'
                     f'Critic’s concern</div><div class="rm-txt">{_e(rub["objection"])}</div></div>')
        foot = f'<div class="rm-foot">{_evidence_line(claim_by.get(n))}</div>'
        out.append(f'<div class="rm-card{" pilot" if pilot else ""}">{top}<div class="rm-body">{body}</div>{foot}</div>')
    return "".join(out)


def strategy_box(rec: dict) -> str:
    rub = rec.get("rubric") or {}
    critic = ""
    if rub.get("avg") is not None:
        critic = (f'<div class="rm-foot">Critic review ({_e(rub.get("model"))}): feasibility {_e(rub.get("feasibility"))}, '
                  f'sequencing {_e(rub.get("sequencing"))}, fit {_e(rub.get("fit"))} out of 5.</div>')
    return (f'<div class="rm-why"><div class="rm-lbl">Why this roadmap, in this order</div>'
            f'<div class="rm-txt">{_e(rec.get("rationale"))}</div>{critic}</div>')



# ================================================================== design system
# One palette, one type scale, one set of components, used everywhere on the page.
INK, TEAL, TEAL_D, TEAL_50, AMBER, AMBER_50, PAPER, LINE, MUTED = (
    "#13212E", "#0F6E56", "#0B5040", "#E3ECEA", "#E8A33D", "#FFF7E8", "#F6F5F1", "#E2E6E4", "#5B6770")

DESIGN_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root{--ink:#13212E;--teal:#0F6E56;--teal-d:#0B5040;--teal-50:#E3ECEA;--amber:#E8A33D;--amber-50:#FFF7E8;
      --paper:#F6F5F1;--line:#E2E6E4;--muted:#5B6770;--card:#FFFFFF;--shadow:0 1px 2px rgba(16,24,40,.05),0 1px 8px rgba(16,24,40,.04)}
html,body,.stApp,button,input,textarea,select{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif}
.stMarkdown,[data-testid="stMarkdownContainer"],.stMarkdown p,.stMarkdown li,[data-testid="stCaptionContainer"],
[data-testid="stWidgetLabel"] p,.stApp td,.stApp th,.stApp label{font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif!important}
.stAppDeployButton,[data-testid="stAppDeployButton"]{display:none!important}
.stApp{background:var(--paper)}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.1rem;padding-bottom:4rem;max-width:1320px}
h1,h2,h3,h4,.pro-display{font-family:'Space Grotesk','Inter',sans-serif!important;color:var(--ink);letter-spacing:-.01em}
.stMarkdown p{color:#1F2933}
/* sidebar */
section[data-testid="stSidebar"]{background:#FFFFFF;border-right:1px solid var(--line)}
section[data-testid="stSidebar"] .block-container{padding-top:1rem}
/* buttons */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{border-radius:10px;font-weight:600;
  border:1px solid var(--line);padding:.48rem 1rem;transition:all .15s ease;box-shadow:none}
.stButton>button:hover{border-color:var(--teal);color:var(--teal)}
button[data-testid="stBaseButton-primary"],button[data-testid="stBaseButton-primaryFormSubmit"],
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"]{background:var(--teal);border-color:var(--teal);color:#fff}
button[data-testid="stBaseButton-primary"]:hover,.stButton>button[kind="primary"]:hover{background:var(--teal-d);border-color:var(--teal-d);color:#fff}
/* expanders as cards */
div[data-testid="stExpander"]{border:1px solid var(--line);border-radius:14px;background:var(--card);box-shadow:var(--shadow);overflow:hidden}
div[data-testid="stExpander"] details{border:none}
div[data-testid="stExpander"] summary{font-weight:600;color:var(--ink);padding-top:.7rem;padding-bottom:.7rem}
div[data-testid="stExpander"] summary:hover{color:var(--teal)}
/* tabs as a segmented control */
.stTabs [role="tablist"]{gap:4px;background:#ECEFED;padding:5px;border-radius:12px;width:fit-content;max-width:100%;flex-wrap:wrap;border-bottom:none!important;box-shadow:none}
.stTabs [data-testid="stTab"]{border-radius:9px;padding:7px 16px!important;height:auto;font-weight:600;color:var(--muted);background:transparent;border:none!important}
.stTabs [data-testid="stTab"] p{font-size:.92rem;font-weight:600}
.stTabs [data-testid="stTab"][aria-selected="true"],.stTabs [data-testid="stTab"][data-selected]{background:#FFFFFF;color:var(--ink);box-shadow:0 1px 3px rgba(16,24,40,.12)}
.stTabs [data-testid="stTab"]::after,.stTabs [role="tablist"]::after,.stTabs [role="tablist"]>span{display:none!important}
.stTabs [data-testid="stTab"]:hover{color:var(--ink)}
.stTabs [role="tabpanel"]{padding-top:1rem}
.stTabs [data-baseweb="tab-list"]{gap:4px;background:#ECEFED;padding:5px;border-radius:12px;width:fit-content;max-width:100%;flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{border-radius:9px;padding:7px 16px;height:auto;font-weight:600;color:var(--muted);background:transparent}
.stTabs [data-baseweb="tab"] p{font-size:.92rem}
.stTabs [aria-selected="true"]{background:#FFFFFF;color:var(--ink);box-shadow:0 1px 3px rgba(16,24,40,.12)}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.stTabs [data-baseweb="tab-panel"]{padding-top:1rem}
/* bordered containers, tables, code */
div[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px;background:var(--card);border-color:var(--line)}
div[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:12px;overflow:hidden}
div[data-testid="stCodeBlock"] pre,.stCode pre{border-radius:12px}
div[data-testid="stMetric"]{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 18px}
div[data-testid="stAlert"]{border-radius:12px}
.stSelectbox label,.stTextInput label,.stTextArea label,.stSlider label,.stNumberInput label,.stMultiSelect label{font-weight:600;color:var(--ink)}
/* roadmap cards get the display face */
.rm-name,.rm-num{font-family:'Space Grotesk','Inter',sans-serif}
/* ---------- pro components ---------- */
.pro-bar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 18px}
.pro-brand{display:flex;align-items:center;gap:12px}
.pro-logo{width:40px;height:40px;border-radius:11px;background:var(--ink);display:flex;align-items:center;justify-content:center}
.pro-name{font-family:'Space Grotesk','Inter',sans-serif;font-weight:700;font-size:1.25rem;color:var(--ink);line-height:1.1}
.pro-tag{font-size:.8rem;color:var(--muted)}
.pro-pills{display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end}
.pro-pill{display:inline-flex;align-items:center;gap:6px;font-size:.76rem;font-weight:600;padding:5px 11px;border-radius:999px;
  background:#FFFFFF;border:1px solid var(--line);color:var(--ink);white-space:nowrap}
.pro-dot{width:7px;height:7px;border-radius:50%;background:var(--teal);display:inline-block}
.pro-hero{background:var(--ink);border-radius:20px;padding:26px 30px;color:#F3EFE6;box-shadow:0 10px 30px rgba(19,33,46,.18);margin-bottom:14px}
.pro-hero-top{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;flex-wrap:wrap}
.pro-eyebrow{font-size:.72rem;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:var(--amber)}
.pro-hero h1.pro-title{font-family:'Space Grotesk','Inter',sans-serif;font-size:2.15rem;line-height:1.1;margin:6px 0 8px;color:#FFFFFF;padding:0}
.pro-sub{font-size:.95rem;color:#B9C6CF}
.pro-sub a{color:#F6DDB0;text-decoration:none}
.pro-chips{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap}
.pro-chip{font-size:.78rem;font-weight:600;padding:5px 11px;border-radius:999px;background:rgba(255,255,255,.08);
  border:1px solid rgba(255,255,255,.14);color:#E7ECEF}
.pro-chip.ok{background:rgba(15,110,86,.28);border-color:rgba(120,200,170,.45);color:#C9F0DF}
.pro-chip.warn{background:rgba(232,163,61,.18);border-color:rgba(232,163,61,.5);color:#F6DDB0}
.pro-steps{display:flex;align-items:center;gap:0;min-width:360px}
.pro-step{display:flex;flex-direction:column;align-items:center;gap:6px;width:92px;text-align:center}
.pro-step .c{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;
  font-size:.82rem;border:2px solid rgba(255,255,255,.25);color:#B9C6CF}
.pro-step.done .c{background:var(--teal);border-color:var(--teal);color:#fff}
.pro-step.now .c{background:var(--amber);border-color:var(--amber);color:var(--ink);box-shadow:0 0 0 5px rgba(232,163,61,.22)}
.pro-step .l{font-size:.72rem;color:#B9C6CF;line-height:1.2}
.pro-step.done .l,.pro-step.now .l{color:#FFFFFF;font-weight:600}
.pro-line{flex:1;height:2px;background:rgba(255,255,255,.18);margin-top:-22px;min-width:14px}
.pro-line.done{background:var(--teal)}
.pro-kpis{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin:0 0 18px}
.pro-kpi{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:14px 16px;box-shadow:var(--shadow)}
.pro-kpi .k{font-size:.68rem;font-weight:700;letter-spacing:.07em;text-transform:uppercase;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pro-kpi .v{font-family:'Space Grotesk','Inter',sans-serif;font-size:1.7rem;font-weight:700;color:var(--ink);line-height:1.1;margin-top:6px}
.pro-kpi .v small{font-size:.9rem;color:var(--muted);font-weight:600}
.pro-kpi .s{font-size:.78rem;color:var(--muted);margin-top:4px;line-height:1.3}
.pro-kpi.hi{background:var(--amber-50);border-color:#EFD3A1}
.pro-kpi.hi .v{color:#8A5208}
@media (max-width:1100px){.pro-kpis{grid-template-columns:repeat(3,minmax(0,1fr))}}
.pro-sec{margin:30px 0 14px}
.pro-sec .pro-eyebrow{color:var(--teal)}
.pro-sec h2{font-family:'Space Grotesk','Inter',sans-serif;font-size:1.65rem;margin:4px 0 4px;padding:0;color:var(--ink)}
.pro-sec .d{color:var(--muted);font-size:.95rem;max-width:900px}
.pro-sec.dev{background:var(--ink);border-radius:18px;padding:20px 24px;margin-top:38px}
.pro-sec.dev .pro-eyebrow{color:var(--amber)}
.pro-sec.dev h2{color:#FFFFFF}
.pro-sec.dev .d{color:#B9C6CF}
.pro-lead{font-size:1.06rem;color:#1F2933;margin-top:6px}
.pro-lead b{color:var(--ink)}
.pro-call{border-radius:14px;padding:12px 16px;margin:8px 0;font-size:.93rem;line-height:1.5;display:flex;gap:12px;align-items:flex-start;border:1px solid}
.pro-call .i{flex:none;width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:.78rem;margin-top:1px}
.pro-call.ok{background:#F0F8F4;border-color:#CBE5DA;color:#0B3F32}.pro-call.ok .i{background:var(--teal);color:#fff}
.pro-call.warn{background:var(--amber-50);border-color:#EFD3A1;color:#5A3A08}.pro-call.warn .i{background:var(--amber);color:var(--ink)}
.pro-call.bad{background:#FCEFEC;border-color:#F0C9BE;color:#6E2414}.pro-call.bad .i{background:#B4281E;color:#fff}
.pro-call.info{background:#F1F5F9;border-color:#D8E1E8;color:#1F2933}.pro-call.info .i{background:var(--ink);color:#F6DDB0}
.pro-empty{background:var(--card);border:1px dashed #C9D1CE;border-radius:20px;padding:44px 36px;text-align:center;margin-top:10px}
.pro-empty h2{font-family:'Space Grotesk','Inter',sans-serif;margin:8px 0 6px}
.pro-empty p{color:var(--muted);max-width:620px;margin:0 auto}
.pro-flow{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:22px}
.pro-flow span{background:#F3F6F5;border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:.82rem;font-weight:600;color:var(--ink)}
.pro-side-brand{display:flex;align-items:center;gap:10px;margin:0 0 6px}
.pro-side-brand .pro-logo{width:32px;height:32px;border-radius:9px}
.pro-side-brand b{font-family:'Space Grotesk','Inter',sans-serif;font-size:1.02rem;color:var(--ink)}
/* live analysis panel */
@keyframes lvspin{to{transform:rotate(360deg)}}
@keyframes lvpulse{0%,100%{opacity:1}50%{opacity:.55}}
.lv{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:var(--shadow);padding:18px 20px;margin:8px 0 14px}
.lv-head{display:flex;justify-content:space-between;align-items:baseline;gap:12px;margin-bottom:10px}
.lv-title{font-family:'Space Grotesk','Inter',sans-serif;font-weight:700;font-size:1.15rem;color:var(--ink)}
.lv-meta{font-size:.8rem;color:var(--muted)}
.lv-row{display:grid;grid-template-columns:34px 1fr 130px 170px;align-items:center;gap:10px;padding:9px 6px;border-top:1px solid #F0F2F1;border-radius:10px}
.lv-row.run{background:#FFF9EE;animation:lvpulse 1.6s ease-in-out infinite}
.lv-ic{width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700}
.lv-ic.wait{border:2px solid #D3D9D7}
.lv-ic.run{border:3px solid #F3E2C0;border-top-color:var(--amber);animation:lvspin .8s linear infinite}
.lv-ic.done{background:var(--teal);color:#fff}
.lv-name{font-weight:600;color:var(--ink);font-size:.93rem}
.lv-name small{display:block;font-weight:400;color:var(--muted);font-size:.76rem}
.lv-kind{font-size:.74rem;font-weight:600;color:var(--muted)}
.lv-stat{font-size:.8rem;color:var(--ink);text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.lv-stat.run{color:#8A5208;font-weight:600}
.lv-x{display:inline-block;margin-left:6px;font-size:.68rem;font-weight:700;padding:1px 7px;border-radius:999px;background:#13212E;color:#F6DDB0}
</style>"""

LOGO_SVG = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-label="logo">'
            '<circle cx="11" cy="11" r="6.5" stroke="#F6DDB0" stroke-width="2.2"/>'
            '<path d="M16 16l4.5 4.5" stroke="#E8A33D" stroke-width="2.4" stroke-linecap="round"/>'
            '<circle cx="11" cy="11" r="2.2" fill="#E8A33D"/></svg>')


def tol_word(t: float) -> str:
    return "cautious" if t < 0.35 else "balanced" if t < 0.65 else "comfortable with risk"


LIVE_STEPS = [
    ("company_index", "Setup: Company search index", "Builds or refreshes this company's vector store", "code + embeddings"),
    ("discovery_research", "3a Discovery: Industry research", "Best practices from the shared knowledge base", "LLM + RAG"),
    ("process_mapper", "3b Process Mapper", "Maps processes and pain points from company material", "LLM + RAG"),
    ("matcher", "4 Matcher", "Proposes and rates AI ideas; code scores them", "LLM + code"),
    ("strategist", "5 Strategist", "Builds and revises roadmaps (Tree of Thoughts)", "LLM + code"),
    ("critic", "6 Critic", "Reviews each roadmap on a different model", "LLM + code"),
    ("review_gate", "Review gate", "Keeps the top 3; revise or stop", "code"),
    ("planner", "7 Verifier / Planner", "Checks every citation, writes the plan", "code + LLM"),
    ("escalate_to_owner", "Decision card", "Hands the decision to the owner", "code"),
]


def _live_html(state: dict, t_start: float, done_all: bool = False) -> str:
    import time as _t
    now = _t.time()
    rows = []
    for key, name, desc, kind in LIVE_STEPS:
        s_ = state.get(key, {})
        stt = s_.get("st", "wait")
        if key == "escalate_to_owner" and stt == "wait":
            continue
        icon = {"wait": "", "run": "", "done": "✓"}[stt]
        rounds = f'<span class="lv-x">×{s_["n"]}</span>' if s_.get("n", 0) > 1 else ""
        if stt == "run":
            stat = f'running since {_t.strftime("%H:%M:%S", _t.localtime(s_["t0"]))}'
        elif stt == "done":
            stat = f'{s_["secs"]:.0f} s' if s_["secs"] >= 1 else "under 1 s"
        else:
            stat = "waiting"
        rows.append(f'<div class="lv-row {stt}"><div class="lv-ic {stt}">{icon}</div>'
                    f'<div class="lv-name">{_e(name)}{rounds}<small>{_e(desc)}</small></div>'
                    f'<div class="lv-kind">{_e(kind)}</div><div class="lv-stat {stt}">{stat}</div></div>')
    running = [n for k, n, _, _ in LIVE_STEPS if state.get(k, {}).get("st") == "run"]
    title = "Analysis complete" if done_all else ("Running: " + " and ".join(running) if running else "Starting the analysis")
    meta_ = f"{(now - t_start) / 60:.1f} min elapsed · updates as each step starts and finishes"
    return (f'<div class="lv"><div class="lv-head"><div class="lv-title">{_e(title)}</div>'
            f'<div class="lv-meta">{meta_}</div></div>{"".join(rows)}</div>')


def live_analyze(case_id: str):
    """Run the analysis with a live panel: one row per agent, a spinner on whichever is running now
    (two at once during the parallel step), a tick and the time when each finishes, and a round
    counter when the Strategist and Critic loop."""
    import time as _t
    box = st.empty()
    state: dict = {}
    t_start = _t.time()

    def on_event(kind: str, node: str):
        s_ = state.setdefault(node, {"st": "wait", "n": 0, "t0": None, "secs": 0.0})
        if kind == "start":
            s_.update(st="run", t0=_t.time())
            s_["n"] += 1
        else:
            s_["secs"] += _t.time() - (s_["t0"] or _t.time())
            s_["st"] = "done"
        box.markdown(_live_html(state, t_start), unsafe_allow_html=True)

    box.markdown(_live_html(state, t_start), unsafe_allow_html=True)
    case_runner.analyze(case_id, on_event=on_event)
    box.markdown(_live_html(state, t_start, done_all=True), unsafe_allow_html=True)


def pro_css():
    st.markdown(DESIGN_CSS, unsafe_allow_html=True)


def _models_in_use() -> list:
    """Model ids from .env, for the header pills (display only; never fails the page)."""
    try:
        from opportunity_finder.llm import llm_settings
        main, critic = llm_settings()["model"], llm_settings(agent="critic")["model"]
        return list(dict.fromkeys(m for m in (main, critic) if m))
    except Exception:
        return []


def _run_models(case_id) -> list:
    """Models the latest run of this case actually called (from its call log)."""
    try:
        runs_ = cases.runs(case_id)
        log = cases.load_result(case_id, runs_[-1]).get("call_log", []) if runs_ else []
        return list(dict.fromkeys(c.get("model") for c in log if c.get("model") and not c.get("stub")))
    except Exception:
        return []


def pro_app_bar():
    models = (_run_models(ss.get("case_id")) if ss.get("case_id") else []) or _models_in_use()
    pills = ('<span class="pro-pill"><span class="pro-dot"></span>Runs locally · private</span>'
             + "".join(f'<span class="pro-pill">{_e(m)}</span>' for m in models))
    st.markdown(
        f'<div class="pro-bar"><div class="pro-brand"><div class="pro-logo">{LOGO_SVG}</div><div>'
        f'<div class="pro-name">AI Opportunity Finder</div>'
        f'<div class="pro-tag">Where AI can actually help a small business · a local multi-agent system</div></div></div>'
        f'<div class="pro-pills">{pills}</div></div>', unsafe_allow_html=True)


def pro_steps_html(stage: str) -> str:
    done = cases.tracker_index(stage)
    parts = []
    for i, (_, label) in enumerate(STEPS):
        state = "done" if (i < done or stage == "analyzed") else "now" if i == done else ""
        mark = "✓" if state == "done" else str(i + 1)
        if i:
            parts.append(f'<div class="pro-line{" done" if i <= done or stage == "analyzed" else ""}"></div>')
        parts.append(f'<div class="pro-step {state}"><div class="c">{mark}</div><div class="l">{_e(label)}</div></div>')
    return '<div class="pro-steps">' + "".join(parts) + "</div>"


def pro_hero(meta: dict, profile: dict, stage: str):
    tol_ = meta.get("company_input", {}).get("risk_tolerance", 0.5)
    site = profile.get("website") or meta.get("company_input", {}).get("website") or ""
    site_html = (f'<a href="{_e(site)}" target="_blank">{_e(site.replace("https://", "").replace("http://", "").rstrip("/"))}</a>'
                 if site.startswith("http") else "local test website" if site.startswith("file:") else _e(site))
    industry = profile.get("industry") or meta.get("company_input", {}).get("industry") or "industry not set yet"
    industry = industry[:1].upper() + industry[1:]
    updated = str(meta.get("updated", "")).replace("T", " ")[:16]
    chips = []
    if profile:
        chips.append('<span class="pro-chip ok">✓ Profile confirmed by owner</span>' if profile.get("confirmed_by_owner")
                     else '<span class="pro-chip warn">Profile awaiting owner</span>')
    chips.append(f'<span class="pro-chip">Risk tolerance {tol_:g} · {tol_word(tol_)}</span>')
    if meta.get("company_input", {}).get("deep_review"):
        chips.append('<span class="pro-chip warn">Deep review on</span>')
    for m in cases.material_summary(meta["id"]):
        chips.append(f'<span class="pro-chip{" ok" if m["authorized"] else ""}">{_e(m["folder"]).capitalize()} · '
                     f'{m["files"]} file{"s" if m["files"] != 1 else ""}{"" if m["authorized"] else " · not shared"}</span>')
    sub = " · ".join(x for x in (_e(industry), site_html, f"updated {_e(updated)}" if updated else "") if x)
    st.markdown(
        f'<div class="pro-hero"><div class="pro-hero-top"><div><div class="pro-eyebrow">Case · {_e(str(meta.get("status", stage)).rstrip("."))}</div>'
        f'<h1 class="pro-title">{_e(meta["name"])}</h1><div class="pro-sub">{sub}</div>'
        f'<div class="pro-chips">{"".join(chips)}</div></div>{pro_steps_html(stage)}</div></div>',
        unsafe_allow_html=True)


def pro_section(eyebrow: str, title: str, desc: str = "", dev: bool = False, extra: str = ""):
    st.markdown(f'<div class="pro-sec{" dev" if dev else ""}"><div class="pro-eyebrow">{_e(eyebrow)}</div>'
                f'<h2>{_e(title)}</h2>' + (f'<div class="d">{desc}</div>' if desc else "") + extra + '</div>',
                unsafe_allow_html=True)


def pro_callout(kind: str, text_html: str):
    icon = {"ok": "✓", "warn": "!", "bad": "!", "info": "i"}.get(kind, "i")
    st.markdown(f'<div class="pro-call {kind}"><div class="i">{icon}</div><div>{text_html}</div></div>',
                unsafe_allow_html=True)


def pro_kpis(r: dict, names: list, by_name: dict, tol: float, ver: dict):
    """Six headline numbers for the run: the owner's view first, the system's view last."""
    pm = r.get("process_map") or {}
    summ = summarize(r.get("call_log", []))
    top = by_name.get(names[0], {}) if names else {}
    t_idx = idea_index(top, tol) if top else None
    claims = ver.get("claims", [])
    tok = (summ["input_tokens"] or 0) + (summ["output_tokens"] or 0)
    tiles = [
        ("hi", "Pilot fit", f'{t_idx if t_idx is not None else "–"}<small> / 100</small>',
         (index_band(t_idx) + " · " + _e(names[0])) if names else "no recommendation"),
        ("", "Ideas considered", str(len(r.get("scored_opportunities", []))), f"{len(names)} chosen for the roadmap"),
        ("", "Processes", str(len(pm.get("processes", []))), "mapped from company material"),
        ("", "Grounded", f'{ver.get("grounded", "–")}<small> / {len(claims) or "–"}</small>',
         "verified" if r.get("verified") else "not verified"),
        ("", "Model time", f'{(summ["seconds"] or 0) / 60:.1f}<small> min</small>', f'{summ["calls"]} model calls'),
        ("", "Tokens", f"{tok / 1000:.1f}<small>k</small>" if tok else "–",
         f'{summ["input_tokens"]:,} in · {summ["output_tokens"]:,} out' if tok else "not reported"),
    ]
    st.markdown('<div class="pro-kpis">' + "".join(
        f'<div class="pro-kpi {c}"><div class="k">{k}</div><div class="v">{v}</div><div class="s">{s}</div></div>'
        for c, k, v, s in tiles) + "</div>", unsafe_allow_html=True)


def left_out_v2(opps: list, names: list, rec: dict, tol: float) -> list:
    """Ideas left out of the roadmap, each with one distinct main reason plus the numbers behind it."""
    import re as _re
    picked = [o for o in opps if o["name"] in set(names)]
    if not picked:
        return []
    low = min(picked, key=lambda o: o["score"])
    low_idx = idea_index(low, tol)
    limit = risk_limit(tol)
    swapped = {}
    for c in rec.get("changes") or []:
        m = _re.match(r"replaced (.+?) with (.+?) \((.+)\)", c)
        if m:
            swapped[m.group(1)] = (m.group(2), m.group(3))
    owner = {}
    for o in sorted(picked, key=lambda o: -o["score"]):
        owner.setdefault(o.get("process"), o)
    rows = []
    for o in sorted((o for o in opps if o["name"] not in set(names)), key=lambda o: -o["score"]):
        v, e, rk = o.get("value", 0), o.get("effort", 0), o.get("risk", 0)
        same = owner.get(o.get("process")) if o.get("process") else None
        if o["name"] in swapped:
            main = f"Swapped out for {swapped[o['name']][0]}: {swapped[o['name']][1]}"
        elif rk > limit:
            main = f"Risk {rk} is over your limit of {limit:g} (risk tolerance {tol:g})"
        elif o["name"] == "Website AI assistant" and not o.get("process"):
            main = "Website quick win with fixed ratings, not company evidence"
        elif same and same["score"] >= o["score"]:
            main = f"Same process as {same['name']}, which scored higher"
        elif e >= 7:
            main = f"Too much effort for this round ({e}/10)"
        else:
            drags = {"lower value": low.get("value", 0) - v,
                     "more effort": 0.5 * (e - low.get("effort", 0)),
                     "more risk": (1 - tol) * (rk - low.get("risk", 0))}
            what, amt = max(drags.items(), key=lambda kv: kv[1])
            if amt > 0:
                ref = {"lower value": f"value {v} vs {low.get('value')}", "more effort": f"effort {e} vs {low.get('effort')}",
                       "more risk": f"risk {rk} vs {low.get('risk')}"}[what]
                main = f"Held back mostly by {what} than {low['name']} ({ref})"
            else:
                main = f"Level with the picks; the roadmap holds at most {len(picked)} ideas"
        idx = idea_index(o, tol)
        gap = low_idx - idx
        rows.append({"idea": o["name"], "fit": f"{idx} / 100", "V / E / R": f"{v} / {e} / {rk}",
                     "main reason": main,
                     "vs. lowest pick": f"{gap} points below {low['name']} ({low_idx})" + (" · close call" if 0 <= gap <= 5 else "")
                     if gap > 0 else f"level with {low['name']} ({low_idx})"})
    return rows


FLAG_HELP = {
    "Possible hidden instruction removed from fetched text": (
        "#B4281E", "Text that read like an instruction to an AI was cut from a fetched page or document before any model "
        "saw it. Look at the source if this keeps appearing."),
    "Close call between the top two roadmaps": (
        "#A8620F", "The winning roadmap leads by under 10%, so a small change in ratings could flip the order. "
        "Read the runner-up too, or re-run to see whether the pick holds."),
    "No best practices found": (
        "#A8620F", "No industry best practices matched, so ideas rest only on company material. Confirm the industry "
        "or add industry notes to kb_sources."),
    "Critic ran on the same model as the Strategist": (
        "#5B6770", "The judge shares the writer's habits, so its review is less independent. Set a different model "
        "family for the Critic in .env."),
    "Vector search unavailable: best practices found by keyword search only": (
        "#5B6770", "The embedding model was not loaded, so retrieval used keywords only and can miss paraphrases. "
        "Load nomic-embed-text in LM Studio and re-run."),
}


def flags_html(rows: list) -> str:
    out = ["<style>.fl{border:1px solid #DDE3E1;border-left:6px solid var(--c);border-radius:12px;padding:12px 16px;"
           "margin:0 0 10px;background:#FFFFFF}.fl-t{font-weight:700;color:#13212E;font-size:.98rem}"
           ".fl-w{color:#5B6770;font-size:.82rem;margin-left:6px;font-weight:400}"
           ".fl-d{margin-top:6px;font-size:.92rem;color:#1F2933;line-height:1.5;white-space:normal;overflow-wrap:anywhere}"
           ".fl-h{margin-top:6px;font-size:.84rem;color:#5B6770;line-height:1.45}</style>"]
    for f in rows:
        col, help_ = FLAG_HELP.get(f["flag"], ("#5B6770", ""))
        where = f'<span class="fl-w">· {_e(f["where"])}</span>' if f.get("where") else ""
        out.append(f'<div class="fl" style="--c:{col}"><div class="fl-t">{_e(f["flag"])}{where}</div>'
                   f'<div class="fl-d">{_e(f.get("detail"))}</div>'
                   + (f'<div class="fl-h">What it means: {_e(help_)}</div>' if help_ else "") + "</div>")
    return "".join(out)


TBL_CSS = (
    "<style>.tw{overflow-x:auto;border:1px solid #DDE3E1;border-radius:12px;margin:4px 0 14px}"
    ".tw table{border-collapse:collapse;width:100%;font-size:.86rem;color:#1F2933}"
    ".tw th{position:sticky;top:0;background:#F3F6F5;color:#13212E;text-align:left;font-weight:700;font-size:.74rem;"
    "letter-spacing:.05em;text-transform:uppercase;padding:9px 10px;border-bottom:1px solid #DDE3E1;white-space:nowrap}"
    ".tw td{padding:9px 10px;border-bottom:1px solid #EEF1F0;vertical-align:top;line-height:1.45;"
    "white-space:normal;overflow-wrap:anywhere}"
    ".tw tr:nth-child(even) td{background:#FAFBFB}.tw tr:last-child td{border-bottom:none}"
    ".tw td.n{text-align:center;white-space:nowrap;font-variant-numeric:tabular-nums}"
    ".tw td.b{font-weight:600;color:#13212E}"
    ".tw .bd{display:inline-block;padding:2px 9px;border-radius:999px;font-weight:700;font-size:.76rem;white-space:nowrap}"
    "</style>"
)


def wrap_table(rows: list, widths: dict | None = None, bold: tuple = (), badge: tuple = ("fit",)) -> str:
    """Rows of dicts as an HTML table that wraps long text instead of cutting it off."""
    if not rows:
        return ""
    cols = list(dict.fromkeys(k for r in rows for k in r))
    widths = widths or {}
    head = "".join(f'<th style="min-width:{widths[c]}px">{_e(c)}</th>' if c in widths else f"<th>{_e(c)}</th>" for c in cols)
    body = []
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c, "")
            if c in badge and v:
                bg, fg = _band_colors(str(v))
                cells.append(f'<td class="n"><span class="bd" style="background:{bg};color:{fg}">{_e(v)}</span></td>')
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(f'<td class="n">{_e(v)}</td>')
            else:
                cells.append(f'<td{" class=b" if c in bold else ""}>{_e(v)}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return TBL_CSS + f'<div class="tw"><table><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


TBL2_CSS = (
    "<style>.tw2{border:1px solid #DDE3E1;border-radius:12px;margin:4px 0 14px;overflow:hidden}"
    ".tw2 table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:.86rem;color:#1F2933}"
    ".tw2 th{background:#F3F6F5;color:#13212E;text-align:left;font-weight:700;font-size:.72rem;letter-spacing:.05em;"
    "text-transform:uppercase;padding:9px 10px;border-bottom:1px solid #DDE3E1}"
    ".tw2 td{padding:10px;border-bottom:1px solid #EEF1F0;vertical-align:top;line-height:1.45;overflow-wrap:break-word}"
    ".tw2 tr:nth-child(even) td{background:#FAFBFB}.tw2 tr:last-child td{border-bottom:none}"
    ".tw2 .c{text-align:center;font-variant-numeric:tabular-nums}"
    ".tw2 .nm{font-weight:700;color:#13212E}.tw2 .sub{color:#5B6770;font-size:.8rem;margin-top:2px}"
    ".tw2 .desc{color:#1F2933;font-size:.84rem;margin-top:5px}"
    ".tw2 .big{font-size:1.05rem;font-weight:700;color:#13212E}"
    ".tw2 .bd{display:inline-block;padding:2px 9px;border-radius:999px;font-weight:700;font-size:.74rem;white-space:nowrap;margin-top:4px}"
    ".tw2 .tg{display:inline-block;padding:1px 7px;border-radius:999px;font-size:.7rem;font-weight:700;background:#E3ECEA;color:#0B5040;margin-left:6px}"
    ".tw2 .k{color:#5B6770;font-size:.78rem}"
    "</style>"
)


def _badge(band) -> str:
    if not band:
        return ""
    bg, fg = _band_colors(str(band))
    return f'<span class="bd" style="background:{bg};color:{fg}">{_e(band)}</span>'


def ranking_html(rows: list) -> str:
    """Every idea, best first. The description sits under the name so nothing runs off the right edge."""
    if not rows:
        return ""
    head = ('<tr><th style="width:5%" class="c">#</th><th style="width:47%">Opportunity, process and what it does</th>'
            '<th style="width:8%" class="c">Value</th><th style="width:8%" class="c">Effort</th><th style="width:8%" class="c">Risk</th>'
            '<th style="width:14%" class="c">Score · index · fit</th><th style="width:10%">Rated by</th></tr>')
    body = []
    for r in rows:
        tag = '<span class="tg">ENABLER</span>' if r.get("enabler") else ""
        body.append(
            f'<tr><td class="c big">{_e(r.get("rank"))}</td>'
            f'<td><div class="nm">{_e(r.get("opportunity"))}{tag}</div>'
            f'<div class="sub">Process: {_e(r.get("process") or "general / website")}</div>'
            f'<div class="desc">{_e(r.get("what it does"))}</div></td>'
            f'<td class="c big">{_e(r.get("value (1-10)"))}</td><td class="c big">{_e(r.get("effort (1-10)"))}</td>'
            f'<td class="c big">{_e(r.get("risk (1-10)"))}</td>'
            f'<td class="c"><div class="big">{_e(r.get("index (0-100)"))}</div><div class="k">raw {_e(r.get("score"))}</div>'
            f'{_badge(r.get("fit"))}</td><td>{_e(r.get("rated by"))}</td></tr>')
    return TBL2_CSS + f'<div class="tw2"><table><thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>'


def roadmaps_html(rows: list) -> str:
    """Every roadmap compared, best first, with related columns grouped so the table fits the page."""
    if not rows:
        return ""
    head = ('<tr><th style="width:15%">Roadmap</th><th style="width:25%">Ideas (in order)</th>'
            '<th style="width:14%" class="c">Score · index · fit</th><th style="width:22%">Critic review (1-5)</th>'
            '<th style="width:24%">Findings, revisions, status</th></tr>')
    body = []
    for r in rows:
        ideas = _e(r.get("ideas (in order)") or "(pruned before ideas were kept)").replace(" → ", "<br>→ ")
        parts = ""
        if r.get("idea average") is not None:
            parts = f'<div class="k">ideas avg {_e(r.get("idea average"))} − penalties {_e(r.get("penalties"))}</div>'
        critic = ""
        if r.get("critic rubric (1-5)"):
            critic = f'<div>{_e(r.get("critic rubric (1-5)"))}</div>'
            if r.get("critic evidence"):
                critic += f'<div class="k" style="margin-top:4px">Evidence: {_e(r.get("critic evidence"))}</div>'
        notes = []
        if r.get("findings"):
            notes.append(f'<div><span class="k">Findings:</span> {_e(r["findings"])}</div>')
        if r.get("revised"):
            notes.append(f'<div><span class="k">Revised:</span> {_e(r["revised"])}</div>')
        if r.get("narrative by"):
            notes.append(f'<div><span class="k">Narrative by:</span> {_e(r["narrative by"])}</div>')
        notes.append(f'<div><span class="k">Status:</span> <b>{_e(r.get("status"))}</b></div>')
        body.append(
            f'<tr><td><div class="nm">{_e(r.get("roadmap"))}</div><div class="sub">{_e(r.get("strategy"))}</div></td>'
            f'<td>{ideas}</td>'
            f'<td class="c"><div class="big">{_e(r.get("index (0-100)"))}</div><div class="k">raw {_e(r.get("score"))}</div>'
            f'{_badge(r.get("fit"))}{parts}</td><td>{critic}</td><td>{"".join(notes)}</td></tr>')
    return TBL2_CSS + f'<div class="tw2"><table><thead>{head}</thead><tbody>{"".join(body)}</tbody></table></div>'


AGENT_ROWS = [("discovery_profile", "1 Discovery · profile"), ("discovery_website", "1 Discovery · website check"),
              ("discovery_research", "3a Discovery · industry research"), ("process_mapper", "3b Process Mapper (company RAG)"),
              ("matcher", "4 Matcher"), ("strategist", "5 Strategist"), ("critic", "6 Critic"),
              ("planner", "7 Verifier / Planner")]
DISCOVERY_AGENTS = ("discovery_profile", "discovery_website")


def _model_color(model: str) -> tuple:
    m = (model or "").lower()
    if "gemma" in m:
        return "#E8A33D", "#13212E"
    if "qwen2.5" in m or "7b" in m:
        return "#7F77DD", "#FFFFFF"
    return "#0F6E56", "#FFFFFF"


def _tl_row(label: str, sub: str, inner: str, shade: str, track_h: int) -> str:
    return (f'<div style="display:flex;align-items:center;border-top:1px solid #F0F2F1">'
            f'<div title="{_e(sub)}" style="width:260px;flex:none;font-size:.84rem;font-weight:600;color:#13212E;'
            f'padding-right:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{_e(label)}</div>'
            f'<div style="position:relative;flex:1;height:{track_h}px;background:#F4F2EC">{shade}{inner}</div></div>')


def _code_points(result: dict, ana: list) -> list:
    """(number, time, short label) for the code steps between model calls, in pipeline order."""
    by = lambda a: [c for c in ana if c["agent"] == a]
    pts = []
    first = min(c["start"] for c in ana)
    pts.append(("A", first, "Supervisor fans out: research and Process Mapper start together"))
    if by("matcher"):
        pts.append(("B", by("matcher")[0]["start"], "Fan-in: the Matcher waits for both branches"))
        pts.append(("C", by("matcher")[0]["end"], "Scoring tool: code turns the ratings into scores and ranks the ideas"))
    gates = [t for t in result.get("trace") or [] if t.startswith("review_gate")]
    crit = by("critic")
    for i, g in enumerate(gates):
        t = crit[min(i, len(crit) - 1)]["end"] if crit else (by("strategist") or ana)[-1]["end"]
        pts.append(("DEFGH"[i], t, f"Review gate {i + 1} (Tree of Thoughts): " + g.split(":", 1)[-1].strip()))
    if by("planner"):
        pts.append(("DEFGH"[len(gates)], by("planner")[0]["end"], "Verifier code checks every citation; pass, retry or escalate"))
    return pts


def _code_marks(result: dict, ana: list, xpos, width) -> str:
    pts = _code_points(result, ana)
    gap, right = 2.4, 98.6                     # min spacing between dots and the last position that still fits
    xs = []
    for _, t, _ in pts:                        # left to right: keep dots apart
        x = xpos(t)
        xs.append(max(x, xs[-1] + gap) if xs else x)
    for i in range(len(xs) - 1, -1, -1):       # right to left: keep the last dots inside the track
        xs[i] = min(xs[i], right if i == len(xs) - 1 else xs[i + 1] - gap)
    out = []
    for (n, t, lab), x in zip(pts, xs):
        out.append(f'<div class="tl-x tl-{n}" title="{_e(lab)}" style="position:absolute;left:calc({x:.2f}% - 10px);top:3px;width:20px;height:20px;'
                   f'border-radius:50%;background:#13212E;color:#F6DDB0;font-size:.7rem;font-weight:700;display:flex;'
                   f'align-items:center;justify-content:center">{n}</div>')
    return "".join(out)


CONCEPT_COLORS = {"LLM": ("#E3ECEA", "#0B5040"), "Code": ("#E9E9E6", "#2C2C2A"), "Tool use": ("#E6F1FB", "#0C447C"),
                  "Guardrail": ("#FCEBEB", "#791F1F"), "Human-in-the-loop": ("#13212E", "#F6DDB0"),
                  "Coordination": ("#EEEDFE", "#3C3489"), "RAG": ("#E1F5EE", "#085041"),
                  "Chain of thought": ("#FAEEDA", "#633806"), "Tree of Thoughts": ("#FAEEDA", "#633806"),
                  "Critic on a different model": ("#FBEAF0", "#72243E"), "Verification": ("#FCEBEB", "#791F1F"),
                  "Memory": ("#EEEDFE", "#3C3489"), "Observability": ("#E6F1FB", "#0C447C")}


def _tags(*names) -> str:
    return "".join(f'<span style="display:inline-block;margin:0 6px 4px 0;padding:2px 9px;border-radius:999px;font-size:.72rem;'
                   f'font-weight:700;background:{CONCEPT_COLORS.get(n, ("#EEE", "#333"))[0]};'
                   f'color:{CONCEPT_COLORS.get(n, ("#EEE", "#333"))[1]}">{_e(n)}</span>' for n in names)


def agent_story_html(result: dict, run: str | None, meta: dict) -> str:
    """Step by step: what each agent and code step did in this run, tagged with the course concept it shows."""
    tr = {}
    for t in result.get("trace") or []:
        k, _, v = t.partition(":")
        tr.setdefault(k.strip(), []).append(v.strip())
    calls = [c for c in result.get("call_log") or [] if not c.get("stub")]
    models = {c["agent"]: c.get("model") for c in calls}
    pm = result.get("process_map") or {}
    pret = pm.get("retrieval") or {}
    bp = result.get("best_practices") or {}
    bret = bp.get("retrieval") or {}
    ver = (result.get("final_recommendation") or {}).get("verification") or {}
    cites = [c.get("citation", {}).get("status") for c in ver.get("claims", []) if c.get("citation")]
    cite_txt = ", ".join(f"{cites.count(s)} {s}" for s in ("confirmed", "unconfirmed", "rejected") if cites.count(s))
    inj = sum(1 for f in result.get("flags") or [] if f.get("type") == "injection")
    shared = ", ".join(meta.get("materials_authorized") or []) or "no folders"
    tol = (result.get("company_input") or meta.get("company_input", {})).get("risk_tolerance", 0.5)
    gates = tr.get("review_gate", [])
    strat = tr.get("strategist", [])
    pruned = ", ".join(f"{p.get('id')} ({p.get('reason')})" for p in result.get("pruned_log") or []) or "none"
    close = any(f.get("type") == "close_call" for f in result.get("flags") or [])
    rows = [
        ("1", "Discovery", ("LLM", "Tool use", "Guardrail"),
         f"Fetched the website with a page-fetch tool and ran the injection filter before the model read it "
         f"({inj} phrase{'s' if inj != 1 else ''} removed). {'; '.join(tr.get('discovery_profile', []))}."),
        ("2", "Owner confirms", ("Human-in-the-loop",),
         f"The LangGraph graph paused at an interrupt until the owner accepted the profile. Folders the owner shared: {shared}."),
        ("A", "Supervisor fans out", ("Coordination", "Code"),
         "Plain Python routing started industry research and the Process Mapper as parallel branches of the graph."),
        ("3a", "Discovery: Industry research", ("RAG", "LLM"),
         f"Hybrid search ({bret.get('mode', 'n/a')}: {bret.get('embed_model') or 'keywords'} vectors plus BM25, merged by rank "
         f"fusion) over sourced industry notes. {'; '.join(tr.get('discovery_research', []))}."),
        ("3b", "Process Mapper", ("RAG", "Chain of thought", "LLM"),
         f"Searched this company's own index ({pret.get('passages_in_index', '?')} passages, {pret.get('embedding_calls', '?')} "
         f"searches), one process at a time, so each process document sat beside its interview passages. "
         f"{'; '.join(tr.get('process_mapper', []))}. Qwen3.6 reasons step by step before it answers."),
        ("4 · B C", "Matcher, with fan-in and the scoring tool", ("Coordination", "LLM", "Code"),
         f"The Matcher waited for both branches. {'; '.join(tr.get('matcher', [])).rstrip('.')}. The model only rated value, effort and "
         f"risk; code computed (value − 0.5 × effort − {1 - tol:.1f} × risk) / 10 and did the ranking."),
        ("5–6", "Strategist and Critic", ("Tree of Thoughts", "Critic on a different model", "Code"),
         f"Branched into roadmaps from four angles (highest value, quick win, lowest risk, enabler); "
         f"{'; then '.join(strat)}. Code applied the hard checks and kept the top 3 (pruned: {pruned}). The Critic "
         f"({models.get('critic', 'n/a')}) scored each with a rubric and cited evidence; its score moves a roadmap by at most 15%."),
    ]
    for i, g in enumerate(gates, 1):
        rows.append(("DEFGH"[i - 1], f"Review gate {i}", ("Tree of Thoughts", "Code"),
                     f"{g}. The loop stops early once one roadmap leads by 10% or more, and never runs past 3 rounds."))
    rows += [
        ("7 · " + "DEFGH"[len(gates)], "Verifier / Planner", ("Verification", "Guardrail", "LLM", "Code"),
         f"{'; '.join(tr.get('planner', []))}. Practice citations: {cite_txt or 'none checked'}. Code confirms each quote is "
         f"really in its passage; after 2 failed checks the run would stop with a decision card for a person."
         + (" Close call flagged for the owner." if close else "")),
        ("", "Memory and logging", ("Memory", "Observability"),
         f"Saved as results/{run or 'run'} in this company's own folder: the full state, the process map and "
         f"{len(calls)} logged model calls with model, seconds and tokens (the timeline above). The case can be resumed or re-run later."),
    ]
    keymap = {"1": ["discovery_profile", "discovery_website"], "2": ["owner"], "3a": ["discovery_research"],
              "3b": ["process_mapper"], "4": ["matcher"], "5": ["strategist"], "6": ["critic"], "7": ["planner"]}
    css = [".aof-steps{max-height:max(280px,calc(100vh - 600px));overflow-y:auto;scroll-behavior:smooth}",
           ".aof-step{transition:background .15s}.aof-step:hover{background:#EEF4FF}",
           ".tl-x{transition:box-shadow .15s,transform .15s}"]
    for i, (n, *_r) in enumerate(rows):
        keys = [k for tok in _rx.split(r"[^0-9A-Za-z]+", n) if tok for k in keymap.get(tok, [tok])]
        if keys:
            sel = ",".join(f".aofw:has(.st-{i}:hover) .tl-{k}" for k in keys)
            css.append(sel + "{box-shadow:0 0 0 2px #FFFFFF,0 0 0 5px #2563EB;transform:scale(1.06);z-index:3}")
    out = ["<style>" + "".join(css) + "</style>",
           '<div style="margin-top:14px;border:1px solid #DDE3E1;border-radius:14px;background:#FFFFFF;overflow:hidden">',
           '<div style="padding:14px 18px 6px;font-weight:700;font-size:1.05rem;color:#13212E">What happened at each step, '
           'and the course concept it shows<div style="font-weight:400;font-size:.8rem;color:#5B6770">Numbers are agents; '
           'letters match the code dots on the timeline. Scroll this box; hover a step to light it up on the timeline.'
           '</div></div><div class="aof-steps">']
    for i, (n, title, tags, txt) in enumerate(rows):
        detail = _step_calls(result, [k for tok in _rx.split(r"[^0-9A-Za-z]+", n) if tok for k in keymap.get(tok, [])])
        badge = (f'<div style="flex:none;min-width:34px;height:26px;padding:0 6px;border-radius:13px;background:#13212E;'
                 f'color:#F6DDB0;font-size:.74rem;font-weight:700;display:flex;align-items:center;justify-content:center">{_e(n)}</div>'
                 if n else '<div style="flex:none;min-width:34px"></div>')
        out.append(f'<div class="aof-step st-{i}" style="display:flex;gap:14px;padding:10px 18px;border-top:1px solid #F0F2F1">{badge}'
                   f'<div style="flex:1"><div style="font-weight:700;color:#13212E;font-size:.92rem;margin-bottom:3px">{_e(title)}</div>'
                   f'{detail}'
                   f'<div>{_tags(*tags)}</div><div style="font-size:.86rem;color:#1F2933;line-height:1.5">{_e(txt)}</div></div></div>')
    out.append('</div></div>')
    return "".join(out)


AGENT_NAMES = {"discovery_profile": "Discovery profile", "discovery_website": "Website check",
               "discovery_research": "Industry research", "process_mapper": "Process Mapper", "matcher": "Matcher",
               "strategist": "Strategist", "critic": "Critic", "planner": "Verifier / Planner"}


def _step_calls(result: dict, keys: list) -> str:
    """Small grey lines under a step's title: calls, model, seconds and tokens per agent (or the owner pause)."""
    from datetime import datetime, timedelta
    calls = [c for c in result.get("call_log") or [] if not c.get("stub") and c.get("seconds") is not None]
    lines = []
    for k in keys:
        if k == "owner":
            try:
                spans = [(datetime.fromisoformat(c["ts"]) - timedelta(seconds=float(c["seconds"])), datetime.fromisoformat(c["ts"]), c["agent"])
                         for c in calls if c.get("ts")]
                d_end = max(e for _, e, a in spans if a in DISCOVERY_AGENTS)
                a_start = min(s0 for s0, _, a in spans if a not in DISCOVERY_AGENTS)
                hrs = (a_start - d_end).total_seconds() / 3600
                lines.append(f"paused {hrs:.1f} h for the owner, then approved" if hrs >= 1
                             else f"paused {hrs * 60:.0f} min for the owner, then approved")
            except (ValueError, KeyError):
                pass
            continue
        mine = [c for c in calls if c["agent"] == k]
        if not mine:
            continue
        name = AGENT_NAMES.get(k, k) + ": " if len(keys) > 1 else ""
        lines.append(f"{name}{len(mine)} call{'s' if len(mine) != 1 else ''} · {mine[0].get('model')} · {_tok_line(mine)}")
    if not lines:
        return ""
    return ('<div style="font-size:.76rem;color:#5B6770;margin:0 0 4px;line-height:1.45">'
            + "<br>".join(_e(l) for l in lines) + "</div>")


def _tok_n(c: dict, key: str):
    v = c.get(key)
    return int(v) if isinstance(v, (int, float)) else None


def _tok_line(mine: list) -> str:
    """Seconds and tokens for one agent's calls, for the row label. Blank counts are left out, not shown as 0."""
    secs = sum(float(c["seconds"]) for c in mine)
    ins = [_tok_n(c, "input_tokens") for c in mine]
    outs = [_tok_n(c, "output_tokens") for c in mine]
    if any(v is None for v in ins + outs):
        return f"{secs:.0f} s · tokens not reported"
    return f"{secs:.0f} s · {sum(ins):,} in / {sum(outs):,} out tokens"


def _tok_total(calls: list) -> str:
    ins = [_tok_n(c, "input_tokens") for c in calls]
    outs = [_tok_n(c, "output_tokens") for c in calls]
    known = [(i, o) for i, o in zip(ins, outs) if i is not None and o is not None]
    if not known:
        return ""
    miss = len(calls) - len(known)
    tail = f" ({miss} call{'s' if miss != 1 else ''} without counts)" if miss else ""
    return (f" · {sum(i for i, _ in known):,} input + {sum(o for _, o in known):,} output tokens"
            f" = {sum(i + o for i, o in known):,} total{tail}")


def agent_timeline_html(result: dict) -> str:
    """Each model call drawn when it ran and for how long, one row per agent. Built from the run's call log."""
    from datetime import datetime, timedelta
    calls = []
    for c in result.get("call_log") or []:
        if c.get("stub") or not c.get("ts") or c.get("seconds") is None:
            continue
        end = datetime.fromisoformat(c["ts"])
        calls.append({**c, "end": end, "start": end - timedelta(seconds=float(c["seconds"]))})
    if not calls:
        return '<div style="color:#5B6770">No timed model calls in this run (it was saved before timing was recorded).</div>'
    disc = [c for c in calls if c["agent"] in DISCOVERY_AGENTS]
    ana = [c for c in calls if c["agent"] not in DISCOVERY_AGENTS] or calls
    if ana is calls:
        disc = []
    a0, a1 = min(c["start"] for c in ana), max(c["end"] for c in ana)
    a_span = max((a1 - a0).total_seconds(), 1)
    if disc:
        d0, d1 = min(c["start"] for c in disc), max(c["end"] for c in disc)
        d_span = max((d1 - d0).total_seconds(), 1)
        d_w = max(10.0, min(22.0, 100 * d_span / (d_span + a_span)))
        gap_w = 6.0
    else:
        d0, d_span, d_w, gap_w = a0, 1, 0.0, 0.0
    pause = ""
    a_w = 100.0 - d_w - gap_w

    def xpos(t):
        if disc and t < a0:
            return d_w * (t - d0).total_seconds() / d_span
        return d_w + gap_w + a_w * (t - a0).total_seconds() / a_span

    def width(c):
        span, w = (d_span, d_w) if c in disc else (a_span, a_w)
        return max(0.6, w * float(c["seconds"]) / span)

    known = [a for a, _ in AGENT_ROWS]
    rows = AGENT_ROWS + [(a, a) for a in dict.fromkeys(c["agent"] for c in calls) if a not in known]
    track_h = 26
    out = ['<div style="border:1px solid #DDE3E1;border-radius:14px;padding:16px 18px;background:#FFFFFF">']
    # axis labels
    axis = ['<div style="position:relative;height:20px;margin-left:260px;font-size:.72rem;color:#5B6770">']
    if disc:
        axis.append(f'<div style="position:absolute;left:0;width:{d_w}%">Discovery</div>')
        pause_h = (a0 - d1).total_seconds() / 3600
        pause = f"{pause_h:.1f} h" if pause_h >= 1 else f"{(a0 - d1).total_seconds() / 60:.0f} min"
    step = 60 if a_span <= 900 else 120
    t = 0
    while t <= a_span:
        x = d_w + gap_w + a_w * t / a_span
        axis.append(f'<div style="position:absolute;left:{x}%;white-space:nowrap;transform:translateX({"0" if t == 0 else "-50%"})">'
                    f'{"analysis start" if t == 0 else f"+{t // 60} min"}</div>')
        t += step
    axis.append('</div>')
    out += axis
    for agent, label in rows:
        mine = [c for c in calls if c["agent"] == agent]
        if not mine and agent not in known[:2] and agent not in [c["agent"] for c in calls]:
            continue
        bars = []
        for c in mine:
            bg, fg = _model_color(c.get("model"))
            err = c.get("error")
            border = "2px solid #B4281E" if err else "none"
            tip = (f"{c.get('model')} · {float(c['seconds']):.0f} s · in {c.get('input_tokens') or '?'} / "
                   f"out {c.get('output_tokens') or '?'} tokens" + (f" · ERROR: {err}" if err else ""))
            lab = f"{float(c['seconds']):.0f}s" if width(c) > 3.5 else ""
            left_ = min(xpos(c["start"]), 99.0)
            bars.append(f'<div class="tl-x tl-{agent}" title="{_e(tip)}" style="position:absolute;left:{left_:.2f}%;width:{max(0.6, min(width(c), 100 - left_)):.2f}%;'
                        f'top:3px;height:{track_h - 6}px;background:{bg};color:{fg};border:{border};border-radius:6px;'
                        f'font-size:.72rem;font-weight:700;display:flex;align-items:center;justify-content:center;'
                        f'overflow:hidden;white-space:nowrap">{lab}</div>')
        shade = (f'<div style="position:absolute;left:{d_w}%;width:{gap_w}%;top:0;bottom:0;'
                 'background:repeating-linear-gradient(45deg,#F3F6F5,#F3F6F5 4px,#FFFFFF 4px,#FFFFFF 8px)"></div>') if disc else ""
        out.append(f'<div style="display:flex;align-items:center;border-top:1px solid #F0F2F1">'
                   f'<div style="width:260px;flex:none;font-size:.84rem;font-weight:600;color:#13212E;padding-right:10px;'
                   f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{_e(label)}</div>'
                   f'<div style="position:relative;flex:1;height:{track_h}px;background:#FAFBFB">{shade}{"".join(bars)}</div></div>')
        if agent == "discovery_website" and disc:
            pill = (f'<div class="tl-x tl-owner" title="The graph paused here until the owner accepted the profile (LangGraph interrupt)" '
                    f'style="position:absolute;left:{d_w + 0.3:.2f}%;width:{gap_w - 0.6:.2f}%;top:3px;height:{track_h - 6}px;'
                    f'border:2px solid #13212E;border-radius:6px;background:#FFFFFF;font-size:.66rem;font-weight:700;'
                    f'display:flex;align-items:center;justify-content:center;color:#13212E">OK</div>')
            out.append(_tl_row("2 Owner confirms (human)", f"paused {pause}, then approved", pill, shade, track_h))
    out.append(_tl_row("Supervisor + code (no LLM)", "routing, scoring, checks", _code_marks(result, ana, xpos, width),
                       "", track_h))
    # summary
    total = sum(float(c["seconds"]) for c in calls)
    par = ""
    r3a = [c for c in ana if c["agent"] == "discovery_research"]
    r3b = [c for c in ana if c["agent"] == "process_mapper"]
    if r3a and r3b:
        ov = (min(r3a[0]["end"], r3b[0]["end"]) - max(r3a[0]["start"], r3b[0]["start"])).total_seconds()
        if ov > 0:
            par = f" · Research and Process Mapper ran in parallel for {ov:.0f} s"
    close = any(f.get("type") == "close_call" for f in result.get("flags") or [])
    stop = "lead under 10% (close call flagged)" if close else "a roadmap led by 10% or more"
    models = dict.fromkeys(c.get("model") for c in calls)
    legend = "".join(f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:16px">'
                     f'<span style="width:14px;height:14px;border-radius:3px;background:{_model_color(m)[0]}"></span>{_e(m)}</span>'
                     for m in models)
    out.append(f'<div style="margin-top:12px;font-size:.84rem;color:#1F2933">{legend}</div>')
    out.append(f'<div style="margin-top:8px;font-size:.84rem;color:#1F2933"><b>{len(calls)} model calls</b> · '
               f'{total / 60:.1f} min of model time{_tok_total(calls)} · analysis took {a_span / 60:.1f} min end to end{par} · '
               f'review rounds: {_e(result.get("review_round"))}, ended with {stop}</div>')
    out.append('<div style="margin-top:6px;font-size:.78rem;color:#5B6770">Each bar is one model call, placed when it ran; '
               'overlapping bars ran at the same time. Hover a bar or a lettered dot for details. Lettered dots are code steps '
               '(Supervisor routing, scoring, review gates, citation checks): they take milliseconds, so they are drawn where '
               'they happened, not to scale. The hatched gap is the pause for the owner, also not to scale.</div></div>')
    return "".join(out)


def tracker(stage: str):
    done = cases.tracker_index(stage)
    st.markdown("  →  ".join(
        f"**{'✅' if i < done or stage == 'analyzed' else '⏳' if i == done else '⬜'} {label}**" if i <= done
        else f"⬜ {label}" for i, (_, label) in enumerate(STEPS)))


# ------------------------------------------------------------------ sidebar: pick or create
pro_css()
with st.sidebar:
    st.markdown(f'<div class="pro-side-brand"><div class="pro-logo">{LOGO_SVG}</div><b>Opportunity Finder</b></div>',
                unsafe_allow_html=True)
    st.markdown("#### Cases")
    st.caption(f"Saved in {cases.base_dir().resolve()}")
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
            industry = st.text_input("Industry (only used when there is no website)", value="", placeholder="e.g. HVAC contractor")
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
                    company.update({"name": name.strip() or "Unnamed company",
                                    "industry": industry.strip() or "unknown", "size": "unknown"})
                ss.case_id = cases.create_case(name.strip() or company.get("name", "case"), company)
                st.rerun()
    if ss.case_id:
        with st.expander("Delete this demo case"):
            sure = st.checkbox("Yes, delete this case folder permanently")
            if st.button("Delete case", disabled=not sure):
                cases.reset_case(ss.case_id)
                ss.case_id = None
                st.rerun()

pro_app_bar()
if not ss.get("case_id"):
    st.markdown(
        '<div class="pro-empty"><div class="pro-eyebrow" style="color:#0F6E56">Get started</div>'
        '<h2>Find where AI can help a business</h2>'
        '<p>Create a case in the sidebar with the company’s website and the owner’s risk tolerance. '
        'Cases are saved to disk, so you can stop at any step and pick the case up later.</p>'
        '<div class="pro-flow"><span>1 · Discovery reads the website</span><span>2 · Owner confirms</span>'
        '<span>3 · Agents map the business</span><span>4 · Ranked AI roadmap</span></div></div>',
        unsafe_allow_html=True)
    st.stop()

meta = cases.load_case(ss.case_id)
stage = meta["stage"]
_hero_profile = cases.load(meta["id"], cases.PROFILE, {})
pro_hero(meta, _hero_profile, stage)
st.caption(f"Case folder: cases/{meta['id']}")

# ------------------------------------------------------------------ stage 1: discovery
if stage == "new":
    pro_section("Step 1 · Discovery", "Read the business",
                "Discovery reads the website, guesses the industry and rates the site. Results are saved to this case, "
                "and nothing else runs until the owner confirms the profile.")
    if st.button("Run Discovery", type="primary"):
        with st.spinner("Reading the business..."):
            case_runner.discover(meta["id"])
        st.rerun()

# ------------------------------------------------------------------ stage 2: confirm
profile = cases.load(meta["id"], cases.PROFILE, {})
disc = cases.load(meta["id"], cases.DISCOVERY, {})


def run_button(label: str, ok: bool, key: str, **kw):
    """The button only asks for a run; the run itself happens in run_pending(), at full page width,
    so the live progress panel is never squeezed into the button's column."""
    if st.button(label, type="primary", disabled=not ok, key=key, **kw):
        ss["pending_run"] = meta["id"]
        st.rerun()


def run_pending():
    if ss.get("pending_run") != meta["id"]:
        return
    ss.pop("pending_run", None)
    try:
        live_analyze(meta["id"])
    except case_runner.ConfirmationRequired as exc:
        st.error(f"Analysis refused: {exc}")
        st.stop()
    st.rerun()


def profile_card():
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


def material_section(key: str):
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
    if not ok:
        st.error(f"Analysis is blocked: {why}")
    run_button("Run analysis" if stage == "confirmed" else "Re-run analysis with the current documents", ok, key)


def owner_overview():
    """Compact company summary and the re-run button, so the recommendation sits near the top."""
    return _control_row()


def _unused_summary_box():
    tol_ = meta.get("company_input", {}).get("risk_tolerance", 0.5)
    summary = cases.material_summary(meta["id"])
    chips = "".join(
        f'<span style="display:inline-block;margin:4px 8px 0 0;padding:4px 11px;border-radius:999px;font-size:.82rem;'
        f'font-weight:600;background:{"#E3ECEA" if m["authorized"] else "#F1EFE8"};color:{"#0B5040" if m["authorized"] else "#5F5E5A"}">'
        f'{_e(m["folder"]).capitalize()}: {m["files"]} file{"s" if m["files"] != 1 else ""}'
        f'{" · shared" if m["authorized"] else " · not shared"}</span>'
        for m in summary)
    _none = '<span style="color:#5B6770">No company material shared yet.</span>'
    confirmed = '<span style="color:#0F6E56;font-weight:700">Confirmed by the owner</span>' if profile.get("confirmed_by_owner") \
        else '<span style="color:#A8620F;font-weight:700">Not confirmed</span>'
    st.markdown(
        '<div style="border:1px solid #DDE3E1;border-radius:14px;padding:14px 18px;background:#FFFFFF">'
        f'<div style="font-size:.95rem;color:#1F2933"><b>{_e(profile.get("industry", "unknown")).capitalize()}</b>'
        f' &nbsp;·&nbsp; {_e(profile.get("website", ""))} &nbsp;·&nbsp; {confirmed}'
        f' &nbsp;·&nbsp; Risk tolerance {tol_:g} ({tol_word(tol_)})</div>'
        f'<div>{chips or _none}</div></div>',
        unsafe_allow_html=True)


def _control_row():
    ok, why = case_runner.confirmation_ok(meta["id"])
    ci = meta.get("company_input", {})
    cur = float(ci.get("risk_tolerance", 0.5))
    with st.container(border=True):
        b_col, sel_col, r_col, go_col = st.columns([1, 1.1, 1.6, 1.1], vertical_alignment="bottom")
        with b_col:
            run_button("Re-run analysis", ok, "rerun-top", width="stretch")
        new_tol = r_col.slider("Owner risk tolerance", 0.0, 1.0, cur, 0.05, key=f"tol-{meta['id']}",
                               help="0 = very cautious, 1 = comfortable with risk. The highest risk rating the owner "
                                    "accepts is 2 + 6 x tolerance. Re-running at a new value saves it to this case.")
        cur_deep = bool(ci.get("deep_review"))
        new_deep = st.toggle("Deep review: the Critic’s objections drive revisions, at least 2 rounds",
                             value=cur_deep, key=f"deep-{meta['id']}",
                             help="Off (default): the Strategist revises only for a concrete problem (risk over the "
                                  "owner's limit, over budget, ungrounded, a low Critic score) and the loop stops early "
                                  "when one roadmap leads by 10%. On: every idea the Critic names as weakest is sent "
                                  "back for a swap, and the loop runs at least 2 rounds (3 at most).")
        changed = abs(new_tol - cur) > 1e-9 or new_deep != cur_deep
        if go_col.button("Re-run with these settings" if changed else "Re-run with settings", type="primary",
                         disabled=not (ok and changed), key=f"tolrun-{meta['id']}", width="stretch"):
            cases.update_case(meta["id"], company_input={**ci, "risk_tolerance": round(new_tol, 2),
                                                         "deep_review": new_deep})
            ss["pending_run"] = meta["id"]
            st.rerun()
        st.caption((f"Now {cur:g} ({tol_word(cur)}): ideas rated above {risk_limit(cur):g} risk count against a roadmap. "
                    + (f"At {new_tol:g} ({tol_word(new_tol)}) the limit becomes {risk_limit(new_tol):g}; a lower limit "
                       "makes the Strategist and Critic revise more." if changed else
                       "Move the slider to try a different owner, then re-run.")) if ok else f"Re-run blocked: {why}")
    return sel_col


if stage in ("discovered", "rejected", "confirmed") and profile:
    pro_section("Step 2 · Owner review" if stage != "confirmed" else "Profile", "What Discovery found",
                "The owner checks this before any company material is read.")
    profile_card()
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

if stage == "confirmed":
    pro_section("Step 3 · Company material", "Share documents and run the analysis",
                "Process documents, interview transcripts and data exports make the answer specific to this business.")
    material_section("run-first")
    run_pending()
_run_col = None
if stage == "analyzed":
    _run_col = owner_overview()
    run_pending()

# ------------------------------------------------------------------ stage 4: results
if stage == "analyzed":
    run_names = cases.runs(meta["id"])
    run = (_run_col or st).selectbox("Showing analysis", run_names, index=len(run_names) - 1, key=f"run-{meta['id']}") if len(run_names) > 1 else (run_names or [None])[0]
    r = cases.load_result(meta["id"], run)
    rec = r.get("final_recommendation", {}).get("roadmap", {})
    opps = r.get("scored_opportunities", [])
    by_name = {o["name"]: o for o in opps}
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
    _plan = rec.get("opportunities", [])
    ver = full.get("verification") or {}
    names = rec.get("opportunities", [])
    tol = (r.get("company_input") or meta.get("company_input", {})).get("risk_tolerance", 0.5)
    _cur_tol = meta.get("company_input", {}).get("risk_tolerance", 0.5)
    if run and abs(float(tol) - float(_cur_tol)) > 1e-9:
        pro_callout("info", f"This analysis ({_e(run)}) ran at risk tolerance <b>{tol:g}</b>; the case is now set to "
                            f"<b>{_cur_tol:g}</b>. Scores below use {tol:g}, the value this run used.")
    pro_kpis(r, names, by_name, tol, ver)
    _lead = ('<div class="pro-lead">Start with <b>' + _e(_plan[0]) + '</b>'
             + "".join(f", then <b>{_e(x)}</b>" for x in _plan[1:]) + '.</div>') if _plan else ""
    pro_section("Recommendation", "Your recommended AI roadmap" + ("" if r.get("verified") else " (unverified draft)"),
                extra=_lead)
    if r.get("status") not in ("complete", "needs_owner_help"):
        pro_callout("warn", f"Status: <b>{_e(r.get('status'))}</b>")
    if any(o.get("placeholder") for o in opps):
        pro_callout("warn", "The model gave too few valid ideas, so PLACEHOLDER opportunities were used. Treat this as a demo.")
    if r.get("verified") and ver:
        pro_callout("ok", f"<b>Verified.</b> {ver.get('grounded')} of {len(ver.get('claims', []))} recommended ideas trace to a "
                          f"process, a cited best practice or the website check.")
    st.markdown(roadmap_cards(names, by_name, tol, rec, ver.get("claims", [])), unsafe_allow_html=True)
    if rec.get("score") is not None:
        r_idx = score_index(rec["score"], tol)
        st.caption(f"Roadmap index {r_idx} / 100, {index_band(r_idx).lower()} (raw {rec['score']}). " + score_scale_note(tol))
    if rec.get("rationale"):
        st.markdown(strategy_box(rec), unsafe_allow_html=True)
        if rec.get("assumption"):
            st.caption(f"Assumption to confirm: {rec['assumption']}")
        st.caption("Narrative written by the " + ("Strategist model." if rec.get("narrative_by") == "model"
                                                 else "code fallback (the model was unavailable)."))
    if full.get("close_call"):
        ru = full.get("runner_up") or {}
        pro_callout("warn", "<b>Close call.</b> " + _e(full.get("close_call_detail", "")) + " Compare both before deciding."
                    + (f'<br><span style="opacity:.85">Runner-up: {_e(" → ".join(ru.get("opportunities", [])))}</span>'
                       if ru.get("opportunities") else ""))
    flags = flag_rows(r.get("flags"))
    if flags:
        with st.expander(f"Checks and warnings ({len(flags)})", expanded=any(f["flag"].startswith("Possible") for f in flags)):
            st.markdown(flags_html(flags), unsafe_allow_html=True)
    _owner_box = st.container()
    with _owner_box:
        pro_section("Explore", "Everything the agents considered",
                    "Every idea and how it scored, how the business runs today, the website check and the case files.")
    pro_section("For developers", "Behind the recommendation",
                "How the agents decided: every model call and code step with time and tokens, the Tree-of-Thoughts "
                "roadmaps compared, the evidence behind each idea and the full run log.", dev=True)
    _tech = st.container()
    tT, tR, tE, tL = _tech.tabs(["Agent timeline", "Roadmaps compared", "Evidence", "Run log"])
    with tT:
        st.markdown('<div class="aofw">' + agent_timeline_html(r) + agent_story_html(r, run, meta) + '</div>',
                    unsafe_allow_html=True)
    with tR:
        st.caption("Code builds and scores the roadmaps; the Critic model can move a score by at most "
                   f"{SETTINGS.rubric_weight:.0%}. Roadmaps from runs before Nov 14 have fewer columns.")
        st.markdown(roadmaps_html(roadmap_rows(r.get("roadmaps"), r.get("pruned_log"), tol)), unsafe_allow_html=True)
    with tE:
        ev = evidence_rows(full)
        if ev:
            st.markdown(wrap_table(ev, bold=("idea",), badge=(), widths={"idea": 180, "evidence": 320, "citation check": 320}), unsafe_allow_html=True)
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
    t1, t2, t3, t4 = _owner_box.tabs(["All ideas considered", "How your business runs today", "Your website", "Case files"])
    with t1:
        st.caption(score_scale_note(tol))
        st.markdown(ranking_html(ranking_rows(opps, tol)), unsafe_allow_html=True)
        left = left_out_v2(opps, names, rec, tol)
        if left:
            st.markdown(
                '<div style="margin:28px 0 0;border-top:3px solid #E8A33D;padding-top:18px"></div>'
                '<div style="background:#FFF7E8;border:1px solid #EFD3A1;border-left:7px solid #E8A33D;border-radius:14px;'
                'padding:16px 20px 6px">'
                '<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">'
                '<span style="font-size:1.25rem;font-weight:700;color:#13212E">Left out of the roadmap</span>'
                f'<span style="background:#13212E;color:#F6DDB0;font-weight:700;font-size:.75rem;letter-spacing:.06em;'
                f'padding:3px 10px;border-radius:999px">{len(left)} IDEA{"S" if len(left) != 1 else ""} NOT CHOSEN</span></div>'
                '<div style="color:#5B6770;font-size:.9rem;margin:6px 0 12px">Ideas the system considered but did not '
                'recommend: value / effort / risk, the main reason each one missed, and how far it fell below the lowest '
                'pick.</div>'
                + wrap_table(left, bold=("idea",), badge=(), widths={"idea": 190, "main reason": 300, "vs. lowest pick": 220})
                + '</div>', unsafe_allow_html=True)
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

# ------------------------------------------------------------------ details, folded below the recommendation
if stage == "analyzed":
    pro_section("Company", "Company details", "The Discovery profile and the company material behind this case.")
    with st.expander("Company profile from Discovery"):
        profile_card()
    with st.expander("Company material: add files, share folders, re-run"):
        material_section("rerun-bottom")
