# AI Opportunity Finder

A local multi-agent system that shows a small-business owner where AI agents could help most.
Capstone project for the Carnegie Mellon University Agentic AI program (Mark Kinch, November 2026).

## The problem and the user

Small and mid-sized business owners keep asking "What should I be doing with AI?" Answering it well
means researching the company, collecting industry best practices, reading process documents,
interviewing the people who do the work, finding the pain points and matching AI to them. Done by
hand that takes weeks per company, which most small businesses cannot pay for.

The user is the business owner (or a consultant working with them). The goal is a short,
evidence-backed roadmap of AI agents worth building, in order, where every recommendation cites the
company's own documents or a sourced best practice. Everything runs on local models, so company
documents never leave the machine.

## How it works

A LangGraph workflow with six LLM agents, a rule-based Supervisor in plain Python, and a
human approval step:

    1 Discovery (LLM + web fetch tool)     reads the website, builds a company profile, rates the site
    2 Owner confirms (human)               LangGraph interrupt: the owner corrects the profile and
                                           chooses which folders the agents may read
    Supervisor fan-out, in parallel:
      Discovery: industry research (LLM + shared RAG over sourced notes in kb_sources/)
      3 Process Mapper (LLM + company RAG) maps real processes and pain points, one process at a time,
                                           with each process document beside its interview passages
    Supervisor fan-in
    4 Matcher (LLM + code)                 proposes AI ideas and rates value, effort and risk;
                                           a scoring tool in code turns ratings into a ranked score
    5 Strategist (LLM + code)  <-> 6 Critic (LLM on a different model family + code)
                                           Tree of Thoughts over whole roadmaps: 4 angles (highest value,
                                           quick win, lowest risk, enabler), keep the top 3, revise up to
                                           3 rounds, stop early when one leads by 10%
    7 Verifier / Planner (code + LLM)      checks every citation; writes the plan, or after two failed
                                           checks hands the owner a decision card instead

Key design decisions:
- **The model judges, code does the math.** Scoring, ranking, pruning, stop rules and citation
  checks are code, so they are repeatable and tested.
- **Shared state, no messages.** Agents read and write one typed state object (`state.py`);
  reducers merge the two parallel branches.
- **Guardrails in code:** owner confirmation before any analysis, a prompt-injection filter on
  website and document text, cite-or-drop for every claim, the owner's risk limit, a 40-call cap,
  and a block on hosted models for any agent not explicitly allowed (`LLM_ALLOW_HOSTED`).
- **Memory:** shared graph state during a run; one folder per company between runs, so a case can
  pause for the owner and resume later. Each company gets its own vector store.
- **Observability:** every model call is logged per agent (model, seconds, input and output tokens,
  errors) and saved with the run, along with a decision trace and guardrail flags.

## Requirements

- Python 3.10 or newer
- [LM Studio](https://lmstudio.ai) with its local server running (port 1234) and three models
  loaded at the same time (context length in brackets):
  - Qwen3.6-35B-A3B, MLX 4-bit (32768): every agent except the Critic
  - Gemma 3 12B (16384): the Critic
  - nomic-embed-text v1.5 (2048): embeddings for retrieval
- Tested on a MacBook Pro M4 Pro with 48 GB of memory. A full analysis takes about 6 to 12 minutes.

## Setup

    git clone https://github.com/kinchma/ai-opportunity-finder.git
    cd ai-opportunity-finder
    python3 -m venv .venv
    source .venv/bin/activate          # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env               # then set the model ids exactly as LM Studio shows them
    python scripts/model_check.py      # confirms LM Studio serves every model .env asks for
    python -m pytest -q                # 152 tests on a fake LLM; no model server needed

## Usage

Start the app:

    streamlit run app_cases.py

1. Create a case with the company name, website, a short description and the owner's risk tolerance.
2. Discovery runs and shows a draft profile and a website check.
3. Add documents (process documents, interview transcripts, data exports) and confirm the profile.
   Nothing is read or analyzed before this step.
4. Run the analysis. The page shows the recommended roadmap first, the ideas that were left out and
   why, and how the business runs today. "Behind the recommendation" shows the agent timeline
   (every model call and code step, with time and tokens), the roadmaps compared, the evidence and
   the run log.

Every run is saved under `cases/<company>/results/run-NNN/`.

Command-line alternative (same steps and the same owner gate):

    python scripts/synthetic_case.py create "<company name>" --site <url> --risk 0.4
    python scripts/synthetic_case.py discover <case_id>
    python scripts/synthetic_case.py confirm <case_id>
    python scripts/synthetic_case.py authorize <case_id> --folders documents,interviews,data
    python scripts/synthetic_case.py analyze <case_id>
    python scripts/synthetic_case.py status <case_id>

## Evaluation

Synthetic companies with planted problems and answer keys test whether the agents find what a
good consultant would:

- `evaluation/synthetic/SYNTHETIC_CASE_PROMPT.md` generates a fictional company (website, process
  documents, interviews, data and an answer key). The companies and answer keys were generated with
  an LLM and reviewed by me.
- `scripts/unpack_case_bundle.py` turns the generator's output into a case folder and an answer key.
  Answer keys live in `evaluation/answer_keys/`, outside the cases, so the agents never see them.
- `evaluation/evaluate_case.py` scores a run against its answer key (industry, expected top picks,
  planted issues found, conflicts flagged, forbidden claims) and writes `evaluation.json` next to
  the run. It matches keywords, so it can overcount.

    python evaluation/evaluate_case.py <case_id> evaluation/answer_keys/<case>.json --run run-NNN

Main results (details in the final report): on Laurel Run Trailer Works, giving each company its
own retrieval roughly doubled the planted issues found (about 3.4 to 6.6 of 15 on average), and
moving the Critic to a different model family (Gemma) made the review decisive (close calls went
from 5 of 5 runs to 0 of 3). Limitations: the top 3 can change between runs, recall is still under
half, non-AI fixes and document-versus-interview conflicts are not yet detected, and the test set
is small.

## Sample cases

| Case | Type | What it shows |
|---|---|---|
| `laurel-run` | Synthetic trailer manufacturer, 15 planted issues | Evaluation with an answer key |
| `hvac-service-contractor` | Synthetic HVAC contractor (Larkmoor), answer key | A second industry; risk-tolerance sensitivity |
| `carmate-trailers`, `harleysville-ace-hardware`, `nyce-shirt-company` | Real companies, public website and LinkedIn text only | What happens with little documentation: the roadmap varies run to run |

No private, employer or customer information is used; real companies appear only through their
public websites.

## Repository layout

    app_cases.py                  Streamlit app (the only UI)
    opportunity_finder/
      graph.py                    LangGraph nodes and edges: interrupt, fan-out/fan-in, review loop
      supervisor.py               rule-based routing: review gate, stop rules, escalation (no LLM)
      state.py                    shared typed state with reducers for parallel branches
      agents/                     discovery, process_mapper, matcher, strategist, critic, planner
      tools/                      web fetch, injection guard, site signals, retrieval (BM25 + vectors,
                                  ChromaDB), scoring and roadmap checks, citation grounding
      llm.py                      per-agent model settings from .env, hosted-model guard, timeouts
      observability.py            per-call log: model, seconds, tokens, errors
      case_runner.py, cases.py    case folders, stages, save and resume
    kb_sources/                   sourced public-domain best-practice notes (SBA, IRS, NIST, NHTSA,
                                  EPA, ENERGY STAR, DOE); see kb_sources/SOURCES.md
    kb/                           older placeholder notes, kept for the tests
    cases/                        sample companies with every run's results
    evaluation/                   answer keys, evaluator, synthetic-company generator
    scripts/                      CLI harness, bundle unpacker, model check, RAG smoke test
    tests/                        152 tests that run on a fake LLM

## Built with

Python, LangGraph and LangChain (OpenAI-compatible client for LM Studio), ChromaDB, Streamlit,
python-dotenv and pytest. The workflow started from the course's Module 5 LangGraph sample, with
every agent built first as a hard-coded stub and then switched to a model one at a time. Claude Code
was used as a pair programmer; design decisions, testing and commits were mine.
