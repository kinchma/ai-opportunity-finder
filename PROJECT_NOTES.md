# AI Opportunity Finder: project notes

Created 2026-11-11. Two parts: follow-ups to come back to, and research on search strategies.

---

## Part 1: Follow-ups

### Deadlines
- [ ] Checkpoint 6.1 (Safety Guardrails and Human Intervention Plan) due Mon Nov 16, 2026. Natural content: the owner-confirm step, the escalation after 2 failed verifications, the model-call cap with "partially complete" label, and the pruned-branch audit log.
- [ ] Final capstone 7.1 due date not posted yet as of Nov 8. Check the classroom once Module 7 appears.

### Code (current state: graph and Supervisor rules are real and tested; Discovery, Process Mapper and Matcher use LLMs; Strategist, Critic and Planner are still stubs)
- [ ] Replace stubs with real LLM calls, one at a time. Suggested order: Strategist, then Critic, then Matcher, Planner, Process Mapper, Discovery.
- [ ] Critic must run on a different model than the Strategist (design requirement).
- [x] (done: per-agent settings and hosted guard exist in llm.py) Make `llm.py` switch between OpenRouter and local servers using environment variables (base URL, model, key). Local options: LM Studio on the Windows PC (RTX 2080 Super, 8 GB VRAM: 7-8B models) and on the MacBook (M4, 48 GB: up to about 30-32B at 4-bit).
- [ ] Pruning currently keeps a hard top 3. The design says "prune with a margin rather than just the top candidate." Implement a margin rule (for example, also keep any roadmap within X% of the 3rd best) and unit test it.
- [ ] Log the lead margin in the trace so it is clear why the loop stopped early (the demo stopped after round 2; the reason was inferred, not printed).
- [ ] Decide where pruning and stop logic lives: the Supervisor or a separate decision-maker node (Checkpoint 4.1 had a Decision Maker; 5.1 folded it into the Supervisor).
- [ ] Optional: print `profile` and `best_practices` (Discovery output) in `main.py`.
- [ ] Add LangSmith tracing; record tokens, latency, and pruned branches.
- [ ] Add three RAG collections (industry research, company docs, interview transcripts), kept separate.
- [ ] Create a git repo and `.gitignore` (`.venv/`, `.env`, `__pycache__/`, `.pytest_cache/`).

### Test data and evaluation
- [ ] Build three synthetic companies modeled loosely on small businesses (overlapping roles, planted inefficiencies). A synthetic-company prompt already exists in the project docs.
- [ ] Test against cases where the owner already made a decision (from the 5.1 risk mitigation).
- [ ] Compare a local 8B model, a local ~30B model, and an OpenRouter model on the same runs; report the differences in the final report.

### Environment and policy
- [ ] Windows: use `py -m venv .venv`, then `.\.venv\Scripts\Activate.ps1`; inside the venv `python` works.
- [ ] Confirm the employer's policy before running local model servers or storing the project on the work MacBook. Keep all NetApp or customer information out of the project (course rule: public, synthetic, or anonymized data only).
- [ ] NUC (Ubuntu): consider only for an always-on vector store or long test runs, later.

---

## Part 2: Research: Tree of Thoughts, BFS, DFS, and beam search

### Tree of Thoughts in one paragraph
Tree of Thoughts (Yao et al., 2023) treats each intermediate reasoning step as a node. A model proposes several candidate next thoughts, an evaluator scores the states, and a search algorithm decides which branches to keep exploring. The paper uses breadth-first search (BFS) and depth-first search (DFS) as the search layer.

### BFS in ToT (the lab's approach)
- At each step, the model generates candidates from every kept state, the evaluator scores them, and only the top b states (the breadth limit) survive. After T steps the best remaining state gives the answer.
- Used for Game of 24 and Creative Writing, where trees are shallow (at most 3 steps) and b is small (5 or less).
- Game of 24 results with GPT-4 (success rate over 100 games): IO 7.3%, CoT 4.0%, CoT self-consistency 9.0%, ToT with b=1 45%, ToT with b=5 74%. Widening the beam helped a lot.
- Lab 4.1 settings: k=5 proposals per state, b=5 kept, T=3 steps.

### DFS in ToT
- Follows the most promising state first and goes deeper. It compares each state's score to a value threshold. If the score falls below it, the branch is pruned and the search backtracks to the parent to try an alternative.
- Used for Mini Crosswords, which needs up to 10 steps with pruning and backtracking.
- Better suited to deep problems where you can tell early that a path is dead; weaker when the evaluator is unreliable, because a wrong threshold decision kills a good branch for good (or wastes time on a bad one).

### Beam search
- A heuristic search that builds the tree level by level like BFS, but keeps only a fixed number of best candidates (the beam width) at each level and discards the rest. Beam width 1 is greedy search; an unlimited width is ordinary BFS.
- It is a greedy approximation: fast and cheap, but not guaranteed to find the best (or any) solution, because the right path can be cut at an early level.
- ToT's BFS with a breadth limit b is the same idea applied to reasoning states. That is why the lab's pruning and your Strategist/Critic loop both behave like beam search.

### Side-by-side

| | Full BFS | ToT BFS / beam search | DFS with threshold |
|---|---|---|---|
| What it keeps | Every state | Top b per level | One path at a time |
| Complete (finds a solution if one exists) | Yes | No | Only if the threshold never wrongly prunes |
| Cost | Grows very fast | Controlled by b | Low memory; cost depends on backtracking |
| Main risk | Too expensive | Good branch cut at an early level | Wrong threshold or evaluator |
| Best for | Tiny problems | Shallow trees with a useful evaluator | Deep trees with early dead-end signals |

### Evaluation methods the paper describes
- Value: the model scores each state alone (a number, or a category such as sure / maybe / impossible).
- Vote: the model compares several states together and picks the most promising.
- Either can be repeated and aggregated for reliability, at higher cost. Scores only need to be useful enough to guide search, not perfect.
- The Lab 4.1 evaluator uses value with categories, sampled 3 times and averaged, plus an exact solver check that can prune with no model call.

### Costs and limits noted in the paper
- ToT used far more compute than IO or CoT, often 5 to 100 times more generated tokens; about $0.74 per Game of 24 case with GPT-4.
- With GPT-3.5, Game of 24 dropped to 19%; the authors point to thought generation as the bottleneck. Relevant to running small local models.
- Deliberate search may not help on tasks the model already handles well.

### What this means for the capstone
- The Strategist/Critic review loop is a beam search: width 3 (keep top 3), at most 3 rounds, with an early stop when the best roadmap leads by 10%.
- The main risk is the same as in the lab: a good roadmap pruned by a weak score. Mitigations in the design: keep a margin, log every pruned branch, use a different model as Critic, and keep exact checks (scoring, budget, ROI) in code.
- A weaker generator (small local model) lowers the quality of the proposals themselves, so widening b will not fix it.
- DFS-style backtracking is not used today. Closest equivalents are the retry after a failed verification and the escalation to the owner after two failures. DFS would only make sense if roadmaps become deep multi-step sequences with clear early failure signals.

### Open questions
- What margin rule best protects good roadmaps without growing cost? Test on the synthetic companies.
- Is value scoring or voting more reliable for the Critic with a smaller model?
- Does a wider beam (b) or more proposals (k) buy more accuracy per dollar on this task?

### Sources
- Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (2023): https://arxiv.org/pdf/2305.10601
- Beam search overview (Wikipedia): https://en.wikipedia.org/wiki/Beam_search
- Beam search as breadth-first search with a width limit: https://muthu.co/beam-search
- Beam search explained with beam width: https://apphp.gitbook.io/artificial-intelligence-with-php/artificial-intelligence/problem-solving-in-ai/types-of-search-algorithms/informed-heuristic-search/beam-search
- Lab 4.1 transcript and notebook (project docs): Tree-of-Thought Agent Construction and Benchmarking

## Part 4: Lab 4.2, agent harnesses (Module 4)

Note: the Canvas and transcript title says "Tree of Thought Agent Benchmarking", but the lab content and slides (lab4_2_slides.pdf, 37 slides) are about agent harnesses. Benchmarking only comes up briefly in Q&A.

### What a harness is
- The harness is the loop around the model. The model is a stateless API. The harness owns the state: it builds the transcript (system prompt, tool specs, task, prior results), calls the model, catches any tool call in the reply, runs the tool, appends the result and repeats until a reply has no tool calls.
- The transcript is data (text). The harness is the code that runs the loop. `max_turns` is the fallback that stops runaway loops (8 in the lab).
- Six components: execution environment, permission gate, agent loop, system prompt, tool suite, context management.
- Tool failures come back as plain strings (for example `ERROR: x does not exist`) so the model can read them and adapt. An unregistered tool name may raise a KeyError in the lab code; a production harness should return an error string that lists the valid tools.

### Lab parts
- Part A: scripted model, 3 self-built tools (list_dir, read_file, write_file). Transcript grew from 2 to 9 entries.
- Part B: Claude Code (asks before each action), Codex CLI (acts in a sandbox, asks before leaving it), Antigravity (one shared harness core, CLI and IDE front ends), OpenCode (open source, MIT, many models).
- Part C: OpenCode driven from Python in headless mode with a free model. Built-in tools: read, write, edit, bash, grep, glob, plus MCP. The real model chose its own tools and order. Its manifest listed MANIFEST.txt itself; the scripted one did not (slide 24: ambiguous spec). JSON event stream: step_start, tool_use, text, step_finish (with token counts). Headless mode runs tools without approval, in a throwaway temp folder.
- Part D: one task through every installed harness with one runner.
- Design principles: small orthogonal tool suite, make every side effect observable ("you can't govern what you can't see"), build headless first, expand autonomy on purpose.

### Q&A takeaways (instructor: rumiq)
- LangGraph is a valid way to build a harness. ReAct is how the model reasons; the harness is the code that runs the actions safely in a loop.
- The SWE-agent paper (NeurIPS) found the harness/interface has a large effect on model performance. Design the harness with the model in mind. (Venue and year cited from memory; verify before citing.)
- Transcript growth: use RAG as a tool call, or summarize older context. It is a balancing act.
- If you do not build a formal harness for the capstone, say in the write-up that your system provides the same functions (readable trace per run, context budget, persistent checkpointer). Benchmarking is how you decide what to keep.

### Decision for the capstone
- Not using OpenCode or another coding harness in the product. The Opportunity Finder is a business-analysis pipeline, not a coding task, and a shell tool adds risk with no value.
- The LangGraph graph is the harness. Mapping: execution environment = local Python with Qwen; permission gate = owner-confirm interrupt and escalation; agent loop = Supervisor revise/finalize routing; system prompt = per-agent prompts; tool suite = scoring and coded checks; context management = pruning and call caps.
- Gaps to add: trace and token logging per model call, tool errors returned as text, a cap on context passed to each agent, persistent checkpointer (SQLite or Postgres) instead of MemorySaver.
- Production path to mention in the report: Langfuse (traces, self-hostable), LiteLLM (model routing and cost caps), vLLM or Ollama (local serving), Guardrails AI or NeMo Guardrails (guardrails). Alternatives to LangGraph: Claude Agent SDK, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework, CrewAI. Verify current details before citing.

### Follow-ups
- Check Checkpoint 4 and Module4_session_notes.md for any explicit harness requirement.
- OpenCode for building the capstone: not planned. A free or local small model (8 GB VRAM limits me to 7-8B) writes weaker code than the assistant I already use, setup costs time before the Nov 16 checkpoint, and the code itself is not sensitive (the sensitive part is company data, and test data is synthetic). Only reconsider for personal learning or a fully offline coding setup. The instructor only advised using some coding assistant that tracks tokens, events and statuses.

### Why OpenCode is in the course
- It was the lab's vehicle for showing a real harness: open source (MIT), scriptable in headless mode, needs no account or paid key, and offers free hosted models. That is why Parts C and D are built on it (the Part B slide has no account requirement for OpenCode).
- The goal is to see the harness loop and its JSON event stream on a real product, not to adopt OpenCode.
- The harness topic feeds the upcoming assignment, where students describe what they did about a harness. Instructor advice: it is fine to say the system provides the same functions as a harness.

## Part 5: Ideas to add

### After-hours call support agent
Idea: when the business is closed, an AI voice or phone agent still picks up the call.
- Orders: take the order details and record them for a person to review and approve. Someone calls the customer back the next business day. The agent never confirms or commits an order by itself.
- Support issues: log the issue and route it to the right department (for example warranty, parts, service).
- General inquiries: answer from a knowledge repository (trailer details, list pricing, office hours, and similar questions).
- Likely fits as a candidate opportunity the Matcher and Strategist can recommend (alongside Order status agent and Dealer Q&A bot). Relates to the curated knowledge base (`kb/`) approach already built for best practices.

Open questions to settle before building or recommending it:
- Voice vs text: the capstone agents are text-based. A phone channel needs speech-to-text, text-to-speech and telephony. Decide whether to demo it as a text simulation of a call.
- Keep a human approval step for orders, and a clear hand-off for anything the agent cannot answer.
- Source of truth for pricing and specs in the knowledge repository, and how it stays current.
- Privacy: call recordings and customer details. Local models fit the data-privacy goal.
- Record which questions the agent could not answer, to improve the knowledge repository.

### Website and LinkedIn analysis with a 1-10 rating
Idea: the LLM analyzes the company's website and LinkedIn presence, rates the website from 1 to 10, and adds both to the analysis shown to the owner.
- Where it fits: Discovery already fetches the site. Add a website assessment next to the industry guess and show it in the results (profile or its own tab).
- Rating: the LLM gathers evidence and sub-ratings (for example clarity of what the company does, how easy it is to contact or get a quote, product or service information, up-to-date content, and easy access to an AI assistant). The overall 1-10 is calculated in code from those sub-ratings with stated weights, not picked by the LLM. Show the sub-ratings and the reasons so the owner can challenge them.
- Limits to state in the UI: a text-only fetch cannot judge visual design or page speed, so the rating covers what can be read, and says so. Ratings from a small model tend to cluster, so test on several known sites before trusting the spread.
- LinkedIn: LinkedIn blocks automated reading (like the 403 seen on some sites) and restricts scraping in its terms. Plan to use text the owner pastes from the company page (About, services, size, recent posts) or a public page that loads without signing in. Do not log in or work around blocking. Company size and specialties from LinkedIn also fill the size field that Discovery does not extract yet.
- Guardrail: fetched pages are untrusted text. Treat them as data (ties to the 6.1 plan).

### Recommend an AI chatbot when the website lacks one
Idea: if the website has no easy-to-find AI chatbot, add that as a recommended opportunity.
- Detection: check the fetched page for chat widgets in code (common vendor scripts and chat buttons) and have the LLM confirm from the text. If none is found, say "none found on the pages read", since the fetch only reads part of the site.
- Recommendation: enters the Matcher as a candidate, scored by the same calculator as the other ideas, with the gap stated ("visitors have no instant way to ask a question or start a quote"). It also acts as an enabler for the after-hours support idea above.
- Starting prompts: the chatbot opens by offering choices customized to the business, for example get a quote, ask about products, check order status, get support, request a call back, find hours and locations. The choices come from the industry and the processes found by the Process Mapper, so a trailer maker gets "Get a trailer quote" and "Find a dealer" while a law office gets "Book a consultation".
- Human hand-off: anything the bot cannot answer, and every quote or order, goes to a person to approve, same as the after-hours agent.
- Answers come from a knowledge repository (the `kb/` approach), not from the model's memory.

Open questions:
- Which sub-ratings and weights to use for the website score, and how to check the score against my own ratings of test sites.
- Whether to show the website rating as a separate headline or only inside the profile.
- How to demo the chatbot suggestion (a mock-up of the opening menu is enough for the capstone).

### Status: website check and chatbot recommendation (built Nov 13)
- Built: `tools/site_signals.py` (page facts from the HTML, chat-widget signatures), `agents/website.py` (code calculates the 1-10 from 7 weighted sub-ratings; the model only rates clear offer, call to action and trust, and writes 3 starter prompts), Discovery stores `website_assessment`, Matcher adds a "Website AI assistant" idea (fixed code ratings value 6 / effort 3 / risk 3) when no chat widget is found, "Website check" tab in all three UIs, optional pasted-LinkedIn box (never scraped).
- Limits: text/source only (no visual design or speed), a widget that loads later can be missed (worded "not found on the pages read"), weights and the fixed assistant ratings are untuned first guesses. Not yet tried against a live site with LM Studio running.

### More SMB use cases: social media, customer support, hiring (added Nov 13)
These are three common small-business areas to add as knowledge-base notes, Process Mapper prompts and Matcher candidates. Each one follows the usual rule: the agent drafts or sorts, a person approves anything that leaves the business.

**Social media**
- Ideas: turn one source (a job photo, a new product, a customer review) into drafts for each platform; a monthly content calendar built from the business's seasons and offers; draft replies to comments and messages; a weekly summary of what got engagement.
- Guardrails: a human approves every post and every public reply; never invent testimonials, prices or claims; keep a short brand-voice note and a "never say" list in the KB; ask permission before using customer names or photos.
- Ratings guess: value medium, effort low, risk medium (a public mistake is visible). Quick-win angle.

**Customer support**
- Ideas: the website assistant already planned (starter choices: support, get a quote, request a call back); an inbox sorter that labels and drafts replies from an approved FAQ; after-hours handling (see the call support agent above); order or appointment status lookups.
- Guardrails: answer only from approved business info; hand off to a person for refunds, complaints, safety, legal or anything it is unsure about; log every conversation; tell visitors they are talking to an AI.
- Ratings guess: value high, effort low to medium, risk medium. Ties directly to the website check's chatbot finding.

**Hiring process**
- Ideas: draft job posts from a short brief; write structured screening questions and a scoring guide; schedule interviews; summarize interview notes against the same criteria; draft candidate status emails.
- Guardrails (highest risk of the three): the agent never ranks, rejects or filters candidates on its own; humans make every decision; avoid anything that infers age, gender, race, health or similar traits; keep to job-related criteria; check local rules on automated hiring tools before use (some places require notice or audits); keep candidate data out of hosted models unless the owner explicitly allows it.
- Ratings guess: value medium, effort medium, risk high. Likely lands in "alternatives considered" for a cautious owner, and that is the right answer to show with the reason.

**How to build it in this project**
- Add one KB note per area (practices with sources), each with the guardrails above, so the Matcher can cite them.
- Have the Process Mapper ask about each area during the interview step (who posts, who answers customers, how hiring works today).
- Add a risk flag in the scoring step for hiring ideas so they are never recommended without a human-review gate.

#### Decision (Nov 13): social media is hard-coded per demo customer, not automated
Detecting a business's social presence automatically is out of scope for the capstone. Instead each demo customer gets a small hand-written "social presence" record that the pipeline treats as owner-provided input, shown in the UI as "provided by the owner (demo data)". Example variety to cover:
- no LinkedIn, no other social accounts (the social media idea should score as a high-gap quick win)
- LinkedIn only, no Instagram (suggest an Instagram content agent, and keep LinkedIn posts)
- TikTok, Instagram and YouTube Shorts (suggest one repurposing agent that turns one clip into all three)
- Facebook only, posting rarely (suggest a simple scheduled-post drafter)
Suggested record per customer: platforms used, posting frequency, who posts today, and one line on what they post. The Process Mapper and Matcher read it like the pasted LinkedIn text, so no scraping or login is needed. The same approach can cover customer support and hiring (for example "answers calls himself, no after-hours", "hires 2 seasonal workers a year").

## Part 6: Presentation notes

### Build approach: script each agent first, then swap in the LLM
Talking point for the final video: I wrote every agent as a scripted stub (fixed, hard-coded output) before letting it call an LLM. The graph, state, Supervisor routing, human confirmation step and tests were built and working on the stubs first, so each LLM was added to an already-proven pipeline one agent at a time.

Why this was worth doing
- It separated two kinds of bugs: wiring problems (routing, state, the human-in-the-loop pause, review loop caps) versus model problems (bad JSON, weak ratings, made-up claims). With stubs, any failure was a wiring failure.
- Tests ran fast and offline with no model server. The test suite still uses a fake LLM that returns valid empty JSON, so no test needs LM Studio.
- Each swap was small and easy to check: replace one stub, compare the output to what the stub promised, and fall back if the model misbehaves.
- The scripted version doubles as the safety net: if the model is missing, blocked by the hosted-model guard, or returns bad JSON, the agent records a note and the run continues instead of crashing (for example the Matcher's flagged placeholder opportunities).
- It kept the "code does the math, the LLM does the judging" rule honest: scoring, the website rating and the final ranking stay in code, so the model never had to be trusted with them.

Current state to show on a slide (verify before presenting)
- LLM-backed: Discovery (profile, best-practice research, website check), Process Mapper, Matcher.
- Still scripted stubs: Strategist, Critic, Planner. The tree-of-thought control logic (top-3 pruning, round cap, early stop) runs in code on stub content. Say this plainly, and show the sidebar labels "stub" and "rule-based, no model".
- The UI marks each agent as model, rule-based code, or stub, so the audience can see the difference.

Demo idea: run the same business with the stubs and with the LLM agents side by side, then point to what changed (specific processes, practices with sources, ratings with reasons).

Lesson learned: scripting first made it obvious which parts needed a model at all. Several steps (Supervisor, scoring, validators) stayed plain code.

### Status: case folders and resume (built Nov 13)
- `cases/<id>/` holds one isolated customer case: case.json, discovery.json, profile.json, decisions.json, documents/, versioned process_map.vN.json, result.json, runs/. `case_runner.py` runs Discovery, owner confirmation and analysis as separate stages; the analysis re-enters the graph after `owner_confirm` using saved state, so closing Python and reopening it resumes where the case left off. `streamlit run app_cases.py` is the UI (pick a case, add documents, re-run analysis to get process map v2).
- Limits: stages resume between steps (a stage interrupted mid-run restarts); only text documents are read; no SME interview and no owner chat yet. The NiceGUI and older Streamlit apps do not use cases.
- Next: owner chat about the roadmaps (reads stored numbers, saves owner input to decisions.json, re-scores for a final recommendation).

### REMINDER: build the owner chat ("Talk to the roadmap") when the Strategist and Critic are real
Not started, on purpose (Nov 13). Build it once the Strategist and Critic use LLMs, so the roadmaps the owner talks about are real. Ask Claude to remind you at that point, or before the final video.
- Where: chat panel under the recommendation in `app_cases.py`, run by the Planner (Checkpoint 5: delivery and Q&A share one agent).
- Answers questions about cost, risk, value and effort from the stored result and the scoring code, not from model-generated numbers; says "I don't have that" when the case has no data.
- Owner can change budget, risk tolerance, excluded ideas and a preferred idea; each change is saved to `decisions.json`.
- After the chat, re-score with the owner's inputs through the same calculator and save a second recommendation that shows what changed and why.
- Guardrails: answers only from this case's data; the chat changes inputs, never scores.

### ReAct: what the checkpoints promised vs what the code does (Nov 13)
- Current code: no agent runs a ReAct loop. Each agent makes one model call, asks for JSON, validates it in code and moves on. Tools (scoring, retrieval, page fetch) are called by code at fixed points, not chosen by the model. That is a deliberate fit for a 7B local model and a fixed workflow.
- BUT the submitted checkpoints promise ReAct. Checkpoint 2.1 says Thought, Action and Observation repeat within each workflow stage (with the invoice example). The Checkpoint 4.1 table marks ReAct "Yes" for Discovery, Process Mapping, Matching, Prioritize/Plan and Verification, and "Maybe" for Scoring (fetch missing inputs). The final report must either implement some of this or say plainly what changed and why.
- Honest framing if not fully built: "fixed-workflow multi-agent pipeline; ReAct is used only where the next step cannot be known in advance (SME interview, verification, owner chat), with hard caps on rounds."
- Where ReAct earns its place, in suggested build order:
  1. Verifier/Planner: for each claim, check it against a source; if no evidence, search the knowledge base or ask the owner, then re-check. Small loop (cap 3 rounds), every tool result logged. Best first choice: it matches the 4.1 table and the "unsupported claims are flagged" promise.
  2. Process Mapper SME interview: reason about what is still unknown, ask one question, read the answer, repeat until gaps are filled.
  3. Owner chat (see reminder above): decide whether to look up stored scores, re-run the scoring with a changed budget, or retrieve a passage before answering.
- Loop rules: only a few allowed tools, hard round cap, count every model call toward the model-call cap, log each Thought/Action/Observation in `call_log`, validate tool arguments in code.

### REMINDER: when to implement ReAct
Do it AFTER the Strategist and Critic use LLMs, and BEFORE writing the final report and recording the video. Minimum to keep the checkpoints honest: build the Verifier loop (item 1). Items 2 and 3 are stretch goals. Ask Claude "is it time for ReAct?" at that point, and Claude will bring it up when the Strategist and Critic are finished.


---

## Part 7: Notes imported from the remote session (Nov 14)
Imported from the Claude Project "ideas inbox" after working remotely on the laptop. Items marked VERIFIED were checked against the code on the HP Omen on Nov 14; items marked NOT VERIFIED are ideas or outside facts to check before presenting.

### Code facts checked against the files (VERIFIED Nov 14)
- Graph wiring (`graph.py`): START -> discovery_profile -> owner_confirm (human interrupt) -> plain-edge fan-out to discovery_research and process_mapper -> list-edge fan-in to matcher -> strategist -> critic -> review_gate (conditional: revise or finalize) -> planner (conditional: done, revise, or escalate) -> escalate_to_owner -> END. Uses `add_edge` and `add_conditional_edges`, no `Send()`. The Supervisor is rule-based functions (`review_gate`, `review_decision`, `after_verification`), not an LLM node.
- Tools are plain Python functions that agents call directly (not LangGraph ToolNode, no @tool): `tools/kb.py` (BM25 `retrieve(industry, k_industry, k_general)`), `tools/scoring.py` (`score_opportunity`, `coded_roadmap_checks`), `tools/site_signals.py` (`analyze_html`), `tools/web.py` (`fetch_site_text`, `extract_text`, `normalize_url`). Not built: MCP, embeddings/vector DB, ReAct loop, LangSmith, any search or LinkedIn tool.
- No `make_agents` factory exists. Agents are separate modules in `agents/`. BUT `llm.py` already supports a different model per agent through `LLM_<AGENT>_MODEL`, `LLM_<AGENT>_BASE_URL` and `LLM_<AGENT>_API_KEY` (agent names: discovery_profile, discovery_research, process_mapper, matcher, strategist, critic, planner), with a per-agent hosted-model guard (`LLM_ALLOW_HOSTED`). So "Critic on a different model than the Strategist" needs only environment settings once those agents call a model.
- Strategist (31 lines), Critic (16) and Planner (18) are still stubs. WARNING: each stub still adds `model_calls: 1` and a `record_call(...)` entry (flagged `stub: true` in call_log). That inflates the model-call counter that feeds the cap of 40 and any cost or call-count claim. TODO: make stubs report 0 model calls, or exclude `stub: true` records when counting, before quoting model-call numbers in the presentation.
- `kb/` is already layered by industry: `general/smb-ai-adoption.md`, `distribution/order-and-inventory.md`, `professional-services/knowledge-and-admin.md`, `trailer-manufacturing/order-to-delivery.md` and `risk-and-rollout.md` (5 notes plus README). Each file has a header (source, url, industries) and `kb/README.md` says these are author-written placeholders, not published sources. `retrieve()` returns industry-specific chunks first, then general ones, and notes when an industry has no specific sources. So the "core library plus industry overlay" design below is partly built; the work left is replacing placeholder text with real, sourced notes.
- State audit against the slide rule ("a field goes in shared state only if 2+ agents read it, or you must audit or resume it"). `state.py` has about 20 fields, far more than the slide's 6. Fields only one agent touches: `gap_report` (matcher only); `intake_confirmed` (graph and case_runner, needed for resume); `documents` (process_mapper and cases.py, needed for persistence); `pruned_log` and `verified` (supervisor-side, needed for audit). Justify these as "audit or resume" fields, or remove `gap_report` if nothing needs it. Say this honestly if a slide shows the state rule.

### Presentation: why LangGraph + local models (not Claude Code agent .md files)
- Source: Module 5 live session (Nov 4), about 27:35-37:10 (the Claude Code agent-file version of the same squad); sovereignty at about 38:20.
- Line to use (polish in my own words): "I noticed how much simpler this would have been with Claude Code and agent .md files. I'm glad I built the LangGraph version, because my project may handle private company data and needs sovereignty. Local models also suit small businesses: no per-token cost, and an SMB's demand is low enough for one machine."
- Caveats to be ready for: the Claude Code agent files run on hosted models (data leaves the machine); small local models are weaker at reasoning and structured output (code does the math, the LLM only judges, Critic/Verifier check); "low demand" must be backed with measured run time and call counts (see the stub warning above); LangGraph adds explicit state, resume (case folders), a human interrupt and a non-LLM Supervisor.
- Rebuilding with OpenCode + Qwen 3.6 + agent .md files was considered and rejected: it would lose predictable control, saved state, deterministic tests and trace logs, and a week of time. Cheap alternative that keeps the benefit: load agent prompts from markdown files. Possible small experiment AFTER the capstone. NOT VERIFIED: whether OpenCode and similar harnesses read agent files and work well with local models; check their docs.
- The .md agent format is a Claude Code (harness) feature, not a model capability; local models can write such files but a harness must run them.

### Presentation: model decision process (professor, about 47:14-49:19)
- His four questions: must the data stay in-house? Is the license commercial-friendly (MIT/Apache)? What hardware? What is the job? Also: a different model per agent role is fine, but one strong model can do all roles if cost is not a concern. About 41:18: some open models are Chinese and organizations may restrict them. Slide (Nov 1): tiers Frontier / Workhorse MoE / One GPU or a laptop; green = MIT/Apache, amber = custom terms; "test on your own tasks."
- My answers: data in-house (yes, local only); consulting use means prefer green licenses and keep a non-Chinese option (Gemma 4, gpt-oss, Mistral); hardware = MacBook Pro M4 Pro 48 GB (about 32-36 GB usable for a model by default) and HP Omen RTX 2080 Super (8 GB VRAM); job differs per agent.
- Draft placement (TEST before claiming): Supervisor = no model; Discovery/Process Mapper/Matcher = lighter model; Strategist = larger local model (Qwen3.6-35B-A3B on the Mac); Critic = a different model family (for example Gemma 4); Verifier/Planner either.
- Status Nov 14: trying Qwen3.6-35B-A3B (lmstudio-community MLX 4-bit, roughly 20 GB; supports tools, vision, reasoning) in LM Studio on the Mac. Skip the "Uncensored" variant. Fallback: Gemma 4 31B 4-bit. The Mac is the work computer: check employer policy before putting customer data or model servers on it.
- Slide idea: "How I chose my models." Measure first: run one synthetic customer through two models and record quality and run time from `observability.py`.

### Presentation: agent count and communication
- Slide "Wiring the Squad" (Nov 4, about 10:13-11:31): same shape as my pipeline (fan-out to two parallel specialists, fan-in, review loop). Differences: my Supervisor is rule-based code (at about 38:11 a student described the same design and the professor said "that's actually supervisor"); plain edges plus a list-edge fan-in instead of `Send()`; owner_confirm before the fan-out; Strategist/Critic loop with a rule-based gate (max 3 rounds); verification and escalation branch after. TODO: side-by-side diagram of the slide and my pipeline.
- Slide "How many agents? Start with one, split only for a reason": split an agent only if it needs different tools or permissions, different knowledge, can run in parallel, or gives an independent check. Costs: calls, latency, tokens (Anthropic reported multi-agent research used about 15x the tokens of a chat). About 02:10: five agents at 95% each can drop to about 77% overall.
- Draft justification for my agents (CHECK before a slide): Discovery (tools, knowledge, parallel) justified; Process Mapper (knowledge, parallel) justified; Matcher is the weakest case (mostly code scoring plus LLM judgment, fan-in point); Strategist is like the slide's "writer" (ticks no box; separate so strategy and critique are distinct steps); Critic (independent check, different model) justified; Verifier/Planner (independent check) justified; Supervisor is code. Be honest that Strategist, Critic and Planner are stubs today.

### Presentation: ways to show tool use
- Options, cheapest first: (1) "tools used" table slide (tool, agent, what it does, code-decided or LLM-decided, data stays local); (2) a live trace panel in the app built from `observability.py` (agent, tool, short input/output, time, code step vs model call); (3) timeline of one run for the video; (4) per-agent tool map diagram; (5) evidence view per recommendation ("why we believe this"); (6) tests as proof (60 passing at last run). Preferred: 2 + 1 for the demo, 4 for the video. Only show tools that exist; label MCP and embedding RAG as planned.

### Knowledge base (RAG) plan, scaled down
- Pre-build a shared best-practice knowledge base rather than searching per company: no customer details in searches, cheap, repeatable, reviewed once. Layers: (1) core SMB process library by function (sales/quoting, invoicing/collections, support/follow-up, scheduling, hiring/onboarding, marketing, bookkeeping), (2) industry overlays only for the demo customers' industries, (3) AI use cases and risks per process (weight this most), (4) customer-specific documents and interview transcripts kept separate in a per-customer index (`cases/<id>/rag/`, later).
- Best practices are the baseline, not the answer; Discovery and the Process Mapper still learn the real process. Keep notes short (a paragraph or a few bullets) with source, URL, date and license. Existing BM25 is probably enough at this size; embeddings/ChromaDB later. Test the same customer with and without the industry overlay and show the result.
- Build timing: after the Strategist and Critic are real. Retrieved text is data, not instructions. Interview transcripts stay local. Possible legitimate MCP use: expose the RAG as a tool.
- Sources found Nov 14 (NOT VERIFIED licenses; confirm before saving content): SBA business guide (sba.gov/business-guide: finances, hiring, marketing and sales, AI for small business, cybersecurity); SCORE templates (score.org); OpenStax "Entrepreneurship" (CC BY 4.0 per the OpenStax page; one other listing said non-commercial, so confirm; check "Introduction to Business" separately); NIST Manufacturing Extension Partnership (lean, value stream mapping, 5S) and state MEP centers for the trailer overlay; NHTSA pages for trailer manufacturers; NIST AI Risk Management Framework for risks. Marketing-agency overlay: no verified free source yet. Do not copy copyrighted articles; write own summaries with links.

### Where Claude (hosted) fits
- Rule: public and generic information can go to Claude; customer-specific information stays local unless the customer opts in (matches rule 4 in CLAUDE.md and the per-agent `LLM_ALLOW_HOSTED` guard in `llm.py`).
- Safe uses: building the project; generating synthetic test customers with expected best picks; drafting knowledge-base notes from public sources (generic queries only); presentation and write-ups; offline evaluation on synthetic data (LLM judge, and a Claude-vs-local baseline comparison for cost and quality numbers).
- Discovery on a real customer: keep local. Hosted only in an optional, consent-based, off-by-default mode with public page text only; never owner notes, documents or interviews; never scrape LinkedIn. Middle path: use Claude ahead of time to build a better website checklist.
- Line for the deck: "Claude helped build the knowledge; local models handled the customer."

### Sample recommendation: quality inspection roadmap for a small trailer manufacturer
- Full draft saved as `SAMPLE_ROADMAP_trailer_quality_inspection.md` in this folder. Phases: baseline (no AI) -> digital inspection checklists with photos -> one defect log and dashboard (local model classifies free text; code counts) -> AI photo checks on simple items (human confirms) -> vision for weld/paint at one station (safety-critical: AI flags, a person decides) -> link defects to causes later. Ratings in it are placeholders. Use as a possible expected answer for a synthetic trailer-manufacturer test case and as material for the trailer overlay in the knowledge base. NHTSA facts (FMVSS items, certification label with GVWR/GAWR, VIN, self-certification) should be verified with NHTSA before presenting.

### Tooling and environment notes (Nov 14)
- Professor's lab: `agent-squad-lab.zip` from the Module 5 live session page (GitHub link `BaratiLab/agent-squad-lab` was not reachable from here). On the Mac: unzip, create a venv, `pip install -r requirements.txt` and also `pip install numpy` (the lab's tests failed without it), `cp .env.example .env`, set `LAB_MODEL=` to a local model (or `ollama:`), `python data/make_db.py`, `pytest -q`, `python run.py`. The default model is OpenAI, so run.py failed with a 401 until `.env` points at a local model.
- LM Studio vs Ollama on the Mac: chose LM Studio (already used by this project; MLX models are generally faster on Apple chips). Ollama if a headless service or the professor's exact `ollama:` setting is wanted. Do not load two big models at once.
- Git authentication: GitHub does not accept passwords for git; use `gh auth login` (browser), Git Credential Manager, a personal access token or an SSH key. Never paste tokens into chat or save them in project files.


---

## Part 8: Matcher model comparison, Qwen3.6-35B-A3B vs Qwen2.5 7B (Nov 14)
All numbers below are from the saved case folder `cases/carmate-trailers-20261114-175911/`: `result.qwen36_matcher.json` (Matcher on the Mac) and `result.json` (rerun with `.env.off`, Matcher on the 7B). VERIFIED from the files.

### Setup
- Same case (Carmate Trailers, synthetic demo), same saved profile and website text. Only the Matcher differed: Qwen3.6-35B-A3B MLX 4-bit via LM Studio on the MacBook Pro (192.168.1.97, over the home network) vs Qwen2.5 7B Instruct on the HP Omen. Discovery research and the Process Mapper used the 7B in both runs. `analyze()` reruns everything after owner_confirm, so the process map was regenerated; the two maps are nearly the same (same size and token counts, one late difference not inspected), a small confound.
- Matcher override lives in `.env` (LLM_MATCHER_BASE_URL / MODEL / API_KEY); renaming it to `.env.off` returns all agents to the Omen defaults.

### Results (one run per model)
| | Qwen3.6 (Mac) | Qwen2.5 7B (Omen) |
|---|---|---|
| Matcher time | 58 s | 8.8 s |
| Tokens out | about 4,975 | 591 |
| Ideas rated by the model | 6 | 5 |
| Score range | 0.18 - 0.49 | 0.17 - 0.38 |
| Std dev of scores | 0.126 | 0.08 |
| Risk ratings used | 1 to 4 | 3 or 4 |
| Ideas citing a KB note (supporting_chunk_id) | 6 of 6 | 0 of 5 |
| "Enabler" flagged | yes (Unstructured Order Data Cleaner) | no |
| Roadmaps | 3 distinct | 3 with the same top three ideas |
- Qwen3.6 top scores: Unstructured Order Data Cleaner 0.49, Warranty & Status Inquiry Bot 0.48, Custom Spec Extractor 0.42.
- 7B top scores: Order Status Assistant 0.38, Automated Quoting Agent 0.37, Customization Options Extractor 0.36.

### What it suggests (and what it does not)
- The bigger model used more of the rating range, grounded every idea in a KB note, and gave the Strategist distinct roadmaps to compare, at about 7x the Matcher time. A wider spread is not the same as better ratings; judge the top picks by hand.
- The missing citations from the 7B matter for rule 3 (cite or drop). TODO: check how the code treats an idea with no supporting_chunk_id.
- Limits: one run per model, one customer, 7B's own run-to-run variation unmeasured, no human-graded "correct" answer. Not a claim that Qwen3.6 is better in general.
- Next: rerun the 7B at least once more on the same case; add Process Mapper and Discovery on the Mac one at a time and time each; try the Gemma 4 31B fallback; add a second synthetic customer.

### Is this benchmarking?
- Not quite. It is a small pilot comparison of two models on one task (a task-specific evaluation). A benchmark would use a fixed test set (several synthetic customers with expected best picks), the same conditions every time, repeated runs, written metrics (agreement with expected picks, citation rate, validation failures, time, tokens), and a stated scoring method. Module 1 / Lab 1.1 (LLM comparisons and benchmarking) is the model for that. Say "pilot comparison" in the presentation and "benchmark" only after the larger test.

### Presentation: slide "How I chose my models" (add to Part 6 deck notes)
- Use the table above, labeled "one customer, one run each: a pilot, not a benchmark."
- Three talking points: (1) quality: wider spread, citations on every idea, distinct roadmaps; (2) cost: 58 s vs 8.8 s on the Matcher, local hardware only, no per-token fees; (3) design: because code does the math and the LLM only supplies ratings, a bigger model can be swapped into one agent through `.env`, no code change.
- Honest line: "I tested one agent on one customer; the 7B is faster, the 35B grounds its answers better. I would repeat this on more customers before generalizing."
- Ties to the sovereignty argument: both runs stayed on local machines (home network only).

### Part 8 addendum: run 3, all agents on Qwen3.6 (Nov 14, 6:12 pm run; VERIFIED from result.json)
- Setup: `.env` set the global LLM_BASE_URL / LLM_MODEL to the Mac, so discovery_research, process_mapper and matcher used Qwen3.6 (discovery_profile and the website check still show the 7B because Discovery was reused from the saved case). Same Carmate case, rerun with "Re-run analysis".
- Higher score = better. Formula in `tools/scoring.py`: (value - 0.5*effort - (1 - risk_tolerance)*risk) / 10. So 0.48 beats 0.28. Weights are marked TODO and untuned; absolute scores are not comparable between runs, only the ranking inside one run.
- Three runs on the Carmate case:
  | | Run 1: Matcher on Qwen3.6 | Run 2: all on 7B | Run 3: all on Qwen3.6 |
  |---|---|---|---|
  | Score range | 0.18-0.49 | 0.17-0.38 | 0.15-0.32 |
  | Std dev | 0.126 | 0.08 | 0.053 |
  | Winning roadmap | 0.463 | 0.37 | 0.29 (lowest_risk) |
  | Ideas citing a KB note | 6 of 6 | 0 of 5 | 0 of 8 |
  | Model time per agent | Matcher 58 s | Matcher 8.8 s | research 64 s, mapper 57 s, matcher 49 s |
- Run 3 was the worst on spread and on citations. Best so far: run 1 (7B for Discovery and the Process Mapper, Qwen3.6 only for the Matcher).
- Cause found in the file: `best_practices.note` says "6 practice(s) dropped: no valid source passage", so the Matcher got zero practices and none of its ideas cite a KB chunk. Run 2 (7B) shows the same zero citations; whether its practices were also dropped is not checked.
- Process Mapper on Qwen3.6 listed 7 processes (added Dealer Management, Dealer Financing Coordination, Warranty Claims), basis "stated", and dropped Order Intake, so the Matcher produced different ideas (Financing Application Router, Dealer Onboarding) and rated effort 3-8 and risk 2-5 (harder and riskier), which lowers every score.
- The run still shows `verified: True` with an empty practice list. TODO: check what the Verifier/Planner stub actually tests (Planner is a stub).

### Discovery research validation: code review (opportunity_finder/agents/discovery.py; Nov 14)
- Flow: `kb.retrieve(industry)` returns passages; the LLM must return JSON `{"practices": [{practice, why_it_matters, chunk_id}]}`; `_validate_practices` keeps an item only if `chunk_id` is exactly equal to a retrieved passage id (e.g. `risk-and-rollout#1`) and the text is non-empty and not a duplicate; everything else is counted as dropped.
- Likely cause of run 3 (NOT confirmed; the raw reply is not saved): the prompt says "copy its chunk_id exactly as shown in square brackets", and a model may copy the brackets or add spaces, quotes or the source name, so the exact-match check drops every item. A reasoning model may also have changed the format.
- Weak points in the code:
  1. The retry loop stops after the first reply that parses as JSON, even if ALL practices were dropped, so a bad id format never gets a second try.
  2. The check is exact string match: no stripping of brackets/whitespace, no case folding.
  3. The raw model reply is not stored, so a drop cannot be diagnosed afterward.
  4. An empty practice list is not treated as a failure; the Matcher just runs without grounding and the run is still marked verified.
- Possible small fixes (not applied; ask before changing code): normalize the id (strip [], whitespace, quotes, lowercase) before the lookup; retry once if every item was dropped; save the raw reply (or its first 500 characters) in the call record; add a test with bracketed and quoted ids; make an empty practice list visible in the UI and the run summary.
- Next test order: put `.env` back to Matcher-only on Qwen3.6, then add Discovery research alone on the Mac and check the practice count; then add the Process Mapper alone.

### Discovery research fixes APPLIED (Nov 14, evening)
- `agents/discovery.py`: new `_match_chunk_id` accepts ids with brackets, quotes, backticks, spaces, different capitals, or inside longer text (`[a#1] (Source)`), but not a different id (`a#10` does not match `a#1`). If every practice is dropped, the agent now retries once. When a reply is unusable or everything is dropped, `best_practices.raw_reply_sample` keeps the first 500 characters of the raw reply. An empty practice list adds "No usable practices: later agents run without knowledge-base grounding." to the note. Backup of the old file: `discovery.before_fix.bak` in the home folder.
- `tests/test_research.py`: 3 new tests (tolerant ids, retry plus raw sample, empty-list note). `tests/conftest.py`: tests now ignore the real `.env` (a global model override in `.env` had made `test_defaults_point_at_lm_studio` fail). Full suite: 63 passed.
- Not changed: the Verifier still marks a run verified with zero practices; the UI does not show the new note yet; Qwen3.6's real output has not been checked (rerun the Carmate case on all-Qwen3.6 and read `best_practices.note` and `raw_reply_sample` in `result.json`).

### Run 4 and Matcher fix (Nov 14, evening)
- Run 4 (all agents on Qwen3.6, after the Discovery fix; saved as `cases/carmate-.../result.run4_allqwen36_fixed.json`): research returned 6 practices (none dropped, no retry needed, so the tolerant id matching is the probable fix; not proven); score range 0.06-0.43, std dev 0.118, winning roadmap blend_1 0.34; but 0 of 7 ideas cited a practice, and blend_1 and blend_2 were identical (no enabler flagged). Model time about 220 s (research 71 s, mapper 69 s, matcher 80 s, about 6,800 matcher output tokens). Run 3's full file was overwritten (not backed up); its numbers are in the table above.
| | Run 1 (Matcher only, Qwen3.6) | Run 2 (all 7B) | Run 3 (all Qwen3.6, before fix) | Run 4 (all Qwen3.6, fixed) |
|---|---|---|---|---|
| Score range | 0.18-0.49 | 0.17-0.38 | 0.15-0.32 | 0.06-0.43 |
| Std dev | 0.126 | 0.08 | 0.053 | 0.118 |
| Winning roadmap | 0.463 | 0.37 | 0.29 | 0.34 |
| Ideas citing a KB note | 6 of 6 | 0 of 5 | 0 of 8 | 0 of 7 |
- Matcher fix APPLIED: `match_chunk_id` moved to `agents/common.py` and used by both Discovery research and the Matcher (the Matcher had the same exact-match check). `ask_json` has an optional `raw_out` list so a caller can keep a sample of the reply. If practices exist but no candidate cites one, the Matcher adds "no candidate cites a practice (N available)" to its trace and stores `reply_sample` (first 500 chars) in the last call-log record. Backup: `matcher.before_fix.bak` in the home folder. 3 new tests; suite: 66 passed.
- Still open: identical roadmaps (blend_1 = blend_2) mean the Strategist gets no real alternatives (design question for the Strategist/Critic work); Verifier still passes a run with zero practices; Qwen3.6 per-agent times add up to about 3-4 minutes per run.


---

## Part 9: Strategist, Critic, Verifier, counting and guardrails (Nov 14, evening session)
Built with fake LLMs only: my shell cannot reach LM Studio on either machine. Nothing in this part has run on a real model yet. Tests: 66 before, 110 after (`python -m pytest -q`, run in a Linux sandbox; confirm once on the Omen). Backup of the project before any change: `Agentic\ai-opportunity-finder_backup_2026-11-14_1900` (everything except `.venv`).

### What was wrong (found in the code, not the models)
- Identical roadmaps: the old Strategist appended the global top three as `blend_N` every revision round, so blend_1 and blend_2 matched by construction. The old Critic scored a roadmap as the plain average of its ideas, so that top-three set always won and the four angles could never beat it.
- Run 5 (all Qwen3.6, after the Matcher fix) was never written up: `result.json` is identical to `result.run5_allqwen36_matcherfix.json`; 5 of 7 ideas cite a practice (run 4: 0 of 7), so the tolerant id matching worked in the Matcher too. Only 5 of its 12 logged calls were real; 7 were stub records.
- The escalation path could not fire (the Planner always passed), and a retry would have regenerated the same four roadmaps.

### What was built
1. **Strategist** (`agents/strategist.py`): code picks and orders the ideas, the model writes the narrative (one call per round, all new roadmaps in one prompt). Round 0: highest value, quick win, lowest risk, and enabler-first (or "balanced" when no idea is flagged as an enabler). If an angle would repeat another roadmap's set of ideas it swaps in its next idea; with three or fewer ideas there is one roadmap and no comparison. Later rounds revise kept roadmaps from the Critic's findings (swap a too-risky, ungrounded, over-budget or same-process idea; move foundation work first; put the lowest-effort idea in the pilot slot). If nothing can be revised the Supervisor stops the loop, with no model call.
2. **Critic** (`agents/critic.py`, `tools/scoring.py`): coded checks with fixed penalties: duplicate idea 0.20, ungrounded or placeholder 0.10, foundation work out of order 0.05, effort over budget 0.05 per point (max 0.30), risk over the owner's limit 0.03 per point (doubled for the pilot), two ideas on one process 0.03, high-effort pilot 0.03. Risk limit = 2 + 6 x risk tolerance (4.4 at 0.4). Then one rubric call on a different model: feasibility, sequencing, fit (1-5 each) plus evidence that must be a listed process name or practice id; a review without valid evidence is dropped. Final score = (average idea score - penalties) x (1 + 0.15 x (rubric average - 3) / 2), so the model moves the score by at most 15%.
3. **Verifier/Planner** (`agents/planner.py`, `tools/grounding.py`): an idea is grounded if it names a process in the map, cites a practice Discovery kept, or came from the website check; placeholders never are. A "typical" process counts but is shown as an assumption. One model call asks whether each cited passage supports its idea and must quote it; code checks the quote is really in the passage (confirmed / unconfirmed / rejected; a rejected citation stops counting). Fail if a placeholder is recommended or under 60% of the recommended ideas are grounded. Rejected ideas go to `failed_claims` and the Strategist rebuilds without them. Two failures escalate; zero practices escalates on the first failure because a retry cannot fix it.
4. **Escalation**: `escalate_to_owner` no longer pauses the graph. It ends the run with `status: needs_owner_help` and a decision card (reason, what is uncertain, three choices: use the draft as unverified, add information and re-run, stop). The draft stays in `final_recommendation` marked `unverified_draft`. The owner's choice is saved in `decisions.json`.
5. **Honest counting**: stubs are gone, so nothing fakes a call. The no-website Discovery path also reports 0 calls. `summarize()` returns calls, tokens, seconds, errors and models per agent, and ignores `stub: true` records in old files. Strategist, Critic and Planner skip their model call once the cap of 40 is reached and say so in the trace.
6. **Guardrails from the 6.1 draft**: injection scan (`tools/guard.py`, 11 regex patterns) cuts instruction-like phrases out of website text, pasted LinkedIn text and owner documents before a model sees them, and flags each one; close-call flag when the best roadmap leads by under 10%, naming the ideas the two roadmaps differ in; `practices_empty` flag and escalation. The review gate now prints the lead margin in the trace.
7. **UI** (`app_cases.py` only): decision card with buttons, verified banner, narrative, close-call warning, guardrail flags, and three new tabs (Roadmaps compared, Evidence, Run log). New-case form has industry (for a case with no website) and an optional effort budget. Checked headless with Streamlit's AppTest on new results and on the two old saved cases.
8. **Tests**: `test_strategist.py`, `test_critic.py`, `test_planner.py`, `test_guard.py`, `test_end_to_end.py`, with a per-agent scripted fake model in `conftest.py`. Fixtures: `tests/fixtures/carmate.json` (replies from run 5) and `tests/fixtures/brightline.json` (synthetic 12-person bookkeeping firm, risk tolerance 0.2, effort budget 12, with a risk-9 "autonomous tax filer", an idea on a process that does not exist, and citations that can be rejected).

### Changed behavior to know about
- First real run (Nov 14, 7:26 pm, Carmate): ended `needs_owner_help`. Cause was not the new code: all four calls to the Mac (research, mapper, matcher, strategist) failed with `Request timed out` after about 42.6 s each, which is a connection that never opened, not a slow model. The Omen's 7B answered (profile, website check, Critic). The guardrails did their job (placeholders and zero practices were refused, not passed as verified) but the card blamed missing practices; it now leads with the failed model calls. Test added; suite 113. `result.json` in the Carmate folder is this failed run; run 5 is still in `result.run5_allqwen36_matcherfix.json`.
- First Omen test run (Nov 14, 7:23 pm): 109 of 110 passed. The one failure was `PermissionError [WinError 5]` in `cases.write_json` (`os.replace` refused while Windows still had the just-written `case.json` open; a timing flake, also possible in the real app). Fixed: `replace_with_retry` retries the swap up to 10 times with a short wait. Two tests added; suite is now 112.
- Three old tests were rewritten because they asserted the old stub behavior: a run with only placeholder ideas used to be "complete" and "verified"; it now ends as `needs_owner_help`.
- `.env` gained three lines: the Critic uses `qwen2.5-7b-instruct` at `http://localhost:1234/v1` (the Omen). Everything else stays on Qwen3.6 on the Mac (192.168.1.97). The Omen is 192.168.1.214, but the app runs on the Omen so localhost is used. Both models are Qwen family; the 6.1 draft says "different model family", so either load a non-Qwen model on the Omen and change `LLM_CRITIC_MODEL`, or change the draft's wording to "a different model".
- Expected real calls per run: Discovery 2, research 1, mapper 1, matcher 1, Strategist 1-3, Critic 1-3, Planner 1, so about 8-12. Rough time on Qwen3.6 at 50-80 s a call: 2-3 minutes more than run 5. The model timeout in `llm.py` is 120 s per call.

### Fake-model results (wiring only, not model quality)
- Carmate: four different roadmaps in round 1; highest_value wins at 0.383 over lowest_risk 0.376; verified 3 of 3; 6 calls; flagged as a close call (1.9%).
- Brightline: the risk-9 idea is never recommended at risk tolerance 0.2, 0.5 or 0.9, and the top roadmap is the same at all three. The agent picked the invoice follow-up where the pre-written picks expected the knowledge base (2 of 3 agree); the knowledge-base roadmap is the runner-up by 1.7%. Those expected picks were written by Claude as a stand-in: replace them with your own before using this as evaluation evidence.

### Run this on the Omen (in order)
1. LM Studio on the Omen: load `qwen2.5-7b-instruct`, start the server. LM Studio on the Mac: Qwen3.6 loaded, server on.
2. `python -m pytest -q` in the project `.venv`: expect 113 passed.
3. `streamlit run app_cases.py`, open the Carmate case, "Re-run analysis". Copy `result.json` to `result.run6_real_strategist_critic.json` afterwards.
4. Check in the app: (a) Roadmaps compared: four different idea sets, a rubric with evidence on each, "narrative by: model"; (b) Evidence: each idea grounded, citation checks mostly "confirmed"; (c) Run log: strategist and planner on qwen3.6, critic on qwen2.5-7b, no stub records, total calls about 8-12; (d) no "same model" flag.
5. New case with no website: name Brightline Bookkeeping, industry "bookkeeping and accounting firm", description from `tests/fixtures/brightline.json`, risk 0.2, effort budget 12. Run it through.
6. If something fails, the trace in the Run log tab says which agent and why ("rubric unavailable", "citation check unavailable", "narrative written by code"). Bring back `result.json`.

### Things likely to go wrong on real models
- Qwen3.6 is a reasoning model: a Strategist or Planner reply could pass 120 s and time out; the run still finishes with code narrative or id-only citation checks and says so.
- The 7B Critic may copy evidence loosely; reviews without a real process name or practice id are dropped and the score falls back to coded checks.
- Quotes that are paraphrased show as "unconfirmed" rather than "confirmed". That does not fail a run.
- Nearly every run will be flagged a close call, because the top roadmaps share two of three ideas. The 10% threshold may need tuning, or the flag can be limited to roadmaps that differ in the pilot.

### Still open
- Real-model runs of everything above; then update the Part 8 table with run 6.
- Checkpoint 6.1 draft: the injection scan, close-call flag, empty-practice escalation, decision card and separate Critic model can move from [Planned] to [Built] once step 3 above passes. Still [Planned]: low-confidence industry trigger, rank-flip test in the app, owner approval of the final roadmap, injection test set beyond the 9 unit-test attacks.
- Enablers only affect order, not score, so a foundation idea rarely wins on its own.
- Scoring weights are still untuned; change readiness, adoption, maintenance cost and consequence of failure (Checkpoint 1 feedback) are not scored.
- Margin-based pruning (keep anything within X% of third place) is not built; pruning is still a hard top 3.
- `gap_report` is still written only by the Matcher and read by nothing.
- The other three UIs show the old view. RAG, SME interview, owner chat, LangSmith: not started.
- Git repo and public GitHub link for the final submission.

### Decisions to mention in the presentation
- "Code does the math, the model judges" now holds end to end: the model cannot pick, reorder or score ideas, and its rubric is capped at 15%.
- The identical-roadmaps bug was a design bug, found by reading saved runs; a bigger model would not have fixed it.
- The Critic must cite evidence and the Verifier checks quotes in code, so a model's claim is never taken on trust.
- Escalation ends the run with a decision card instead of pausing, so a case can be closed and resumed weeks later.
- Stub calls were removed before quoting any cost numbers: run 5 was 5 real calls, not 12.
- The injection scan is a basic regex filter, stated as such; the prompts still treat page text as data.

### Moving to the Mac for travel (decided Nov 14, 7:50 pm)
- Run everything on the MacBook: all agents on localhost, Qwen3.6 plus a small second model for the Critic loaded together. Reason: the two-machine setup failed tonight on a network timeout, and hotel Wi-Fi usually blocks device-to-device traffic.
- Steps are in `MAC_SETUP.md`. Added `.env.mac` (template, no secrets), `streamlit` in `requirements.txt`, and a fuller `.gitignore` (`.env`, `.env.off`, `.venv/`, `runs/`, caches). Code moves through a private GitHub repo, which the final submission needs anyway (it must be public by then; decide about `cases/` first).
- The Mac's Claude desktop app must be signed in to the same Claude account as this Project (personal Gmail) to see the Project docs and chat history.


## Part 10: Mac runs and the Critic fix (Nov 16)
- Run 7 (Nov 16, 10:45 am, Carmate, everything on the Mac's LM Studio: Qwen3.6 for research/mapper/matcher/strategist/planner, Qwen2.5 7B for the Critic; saved as `result.run7_mac_all_local.json`): `complete`, `verified`, 3 rounds, 10 real calls, 419 s of model time (research 113 s and mapper 105 s, about double the Nov 14 two-machine runs: both models loaded on one Mac). Four distinct roadmaps in round 1; close-call flag fired (highest_value_r1 0.48 vs lowest_risk 0.463, 3.7%). Critic rubric: round 1 dropped all 4 reviews, rounds 2 and 3 kept 1 each; that one rubric (feasibility 4, sequencing 5, fit 4, evidence risk-and-rollout#1 and order-to-delivery#1, objection: Freight Damage Pre-Check too risky for a cautious owner) lifted highest_value_r1 from 0.437 to 0.48 and decided the winner. So the mechanism works; the 7B's hit rate was 1 of 11 reviews.
- Critic fix APPLIED (`agents/critic.py`, backup `critic.before_fix.bak` in the home folder): (1) ratings accept "4/5", "5 - strong", 4.0; (2) roadmap ids match case- and punctuation-insensitively; (3) evidence resolves from a process name, a practice id (tolerant), the practice's own sentence, an idea name (credited to the idea's process or practice), or a phrase containing a process name; (4) the trace now says why reviews were dropped (unknown id / bad ratings / no evidence) and the last Critic call-log record keeps a 500-character `reply_sample` whenever any review was dropped; (5) the system prompt shows an evidence example. Three new tests; suite 116 passed. Not yet run on a real model: rerun Carmate and compare the kept-review count with run 7 (1 of 11).
- Grader asks found in the Module folders (3.1, 4.1, 5.1 feedback) and the week plan are in the Project doc claude/capstone/final-week-plan-2026-11-16.md.

### Sourced knowledge-base notes (Nov 16, 11:45 am)
- New folder `kb_sources/` (13 notes, 37 chunks, all US-government public-domain sources: SBA Business Guide x8, IRS Pub 583, NIST AI RMF, NIST MEP lean and VSM, NHTSA manufacturers handbook) with `SOURCES.md` listing license, URL and gaps. Same header format as `kb/` plus license/accessed/note lines. Kept outside `kb/` so the app does not load them until copied in or `KB_DIR=kb_sources` is set. Verified: `kb.load_kb` parses them and `retrieve("trailer manufacturing")` returns 4 manufacturing/trailer chunks plus 2 general ones.
- The notes are summaries written from the pages on Nov 16 (the device shell cannot reach sba.gov or nist.gov, so text came through the fetch tool, which paraphrases). Check a figure against the source before quoting it in the final.
- OpenStax Entrepreneurship left out: the current edition is CC BY-NC-SA (commercial use needs permission); only the 2020 PDF is CC BY 4.0. SCORE is copyrighted (link only). Gaps: retail/hardware, distribution and marketing-agency overlays still have no sourced notes.
- Decision for the final: either replace the placeholder notes in `kb/` with these (and keep the placeholder files only where no source exists, labelled), or run with `KB_DIR=kb_sources` and say so. The citation rule then cites real documents.

## Part 11: Laurel Run synthetic test case integration (Nov 16, afternoon)
Built on the Mac with fake models only (128 tests pass; was 117). Not yet run on real models. Files changed: tools/web.py, tools/site_signals.py, agents/discovery.py, agents/website.py, agents/process_mapper.py, tools/grounding.py, cases.py, case_runner.py, state.py, summaries.py, app_cases.py; new scripts/synthetic_case.py, evaluation/evaluate_case.py, tests/test_synthetic_case_laurel_run.py.
- Offline discovery: `fetch_site_text` accepts `file:///path/to/site` (reads index.html, or a named .html file, inside that folder only; symlinks and traversal refused; `local_fixture: true` on the result). The profile now records `evidence_source` (page read, fields used, local fixture or not).
- Owner gate: `case_runner.confirm` (accept, with corrections kept as `owner_corrections` and `confidence: owner-confirmed`), `reject` (stage `rejected`), `confirmation_ok` (reads case.json, profile.json and decisions.json; the latest decision must be an acceptance), and `analyze` raises `ConfirmationRequired` otherwise. A hand-edited stage or a resumed case cannot bypass it. Re-running Discovery clears the confirmation.
- Materials boundary: `cases.share_materials(case_id, root, include)` is the only route for company material; it copies approved files into `documents/<subfolder>/...` and refuses evaluator/do-not-share/expectations/manifest/prompt paths, hidden files, symlinks and anything resolving outside the root; everything is logged in decisions.json. `case_runner.share` adds the confirmation gate. Agents read `documents/` only. Verified with a sentinel outside the root and a symlink pointing at it (both refused), and by checking the Process Mapper prompt contains no evaluator text.
- Process Mapper v2: builds its prompt from `document_chunks` (ids `doc:<file>#n`, source_type from the subfolder: process_document, sme_interview, data_sample, external_research, owner_document), within `MAPPER_DOC_CHARS` (default 16,000 chars: each file's first 700 chars plus the ids and headings of its other sections; process documents and interviews first). It must cite ids per process; invalid ids are dropped and a process with no valid source is "stated" only if the website names it. Also returns `doc_vs_reality_gaps` (document vs interview) with sources, and `sources_index` for the UI. `grounding.py` adds a `document` basis so the Evidence tab shows the file behind an idea.
- Social presence: `site_signals.social_links` lists links to LinkedIn, Facebook, Instagram, TikTok, YouTube, X found on the page; `assess_website` reports `social_presence` as found / not found on the pages read plus whether the owner pasted LinkedIn text; nothing is looked up elsewhere and the model is not asked about it. Tested on Laurel Run (nothing found) and on a fixture with LinkedIn and Facebook links plus pasted text (both reported).
- UI: Accept / Accept corrected / Reject buttons with name and industry edits and an owner note; evidence page shown; "Share a folder of company material" expander with refusals listed; Run analysis disabled with the reason until the gate is satisfied; process map shows sources and gaps.
- Harness: `scripts/synthetic_case.py create|discover|confirm|reject|share|analyze|status` reads the manifest only for paths (the manifest is never given to an agent). Evaluator: `evaluation/evaluate_case.py <case_id> <expectations.json>` compares a frozen result.json with a keyword answer key (industry, expected picks, planted issues, citation coverage, forbidden claims) and writes evaluations/<id>/report.json. I did NOT read `02_evaluator_only_DO_NOT_SHARE/`; its expectations must be transcribed into the JSON format by the evaluator after the first frozen run.
- Limits and risks: no per-process retrieval yet (the model sees the first chunk of each file and only ids for the rest, so a citation to a later section is checked by the Verifier's quote test and may come back "unconfirmed"); LM Studio context length must be above the prompt size (set 16k+ tokens when loading Qwen3.6) or the server truncates silently; the data CSVs are shown as header plus 12 rows; the `file://` path in case.json is machine-specific (create the case on the machine that runs it); the live manus.space site was private on Nov 16 and is not used.
- Run on the Mac (venv active, LM Studio with Qwen3.6 and the Critic model loaded, context length 16k+):
  1. `python -m pytest -q` (expect 128).
  2. `python scripts/synthetic_case.py create cases/Laurel_Run_Test_Case` then `discover <id>` (website only; prints the industry guess, confidence and evidence page), then `confirm <id>` (or `reject`, then `confirm --industry ...`), then `share <id> cases/Laurel_Run_Test_Case --only processes,interviews,company,data`, then `analyze <id>`. Or do the same in `streamlit run app_cases.py` (New case, website = the file:// URL printed by create).
  3. Freeze: copy `cases/<id>/result.json` to `result.run1_laurel.json`.
  4. Evaluate separately: write `02_evaluator_only_DO_NOT_SHARE/expectations.json` from CASE_EXPECTATIONS.md, then `python evaluation/evaluate_case.py <id> cases/Laurel_Run_Test_Case/02_evaluator_only_DO_NOT_SHARE/expectations.json`.
- Git: changes are staged but not committed (my shell has no git identity and cannot delete git's temp files). Commit from a terminal on the Mac. Before the repo goes public, keep `cases/` (real-company text and the evaluator folder) out of it.

### Score display: relative index and separate ratings (Nov 16, 3:45 pm)
- Laurel Run run 1 (all on the Mac, 10 calls, about 7 min): verified 3 of 3, every process cited a shared file, 3 of 3 citation checks confirmed, no gaps reported, no social links found on the page read. Winning roadmap highest_value_r1 scored 0.374; the question "why so low" is the formula, not the run: score = (value - 0.5 effort - (1 - tolerance) risk) / 10, so the best idea possible at tolerance 0.4 is 0.89 and a value-9 / effort-7 / risk-3 idea is 0.37.
- APPLIED: `scoring.EFFORT_WEIGHT` (0.5, named, still untuned), `best_possible_score(tolerance)` and `score_index(score, tolerance)` (0-100 as a share of the best possible; display only, never changes an order). `summaries.ranking_rows` shows rank, value, effort and risk as separate columns plus score and index; `score_scale_note` explains the scale. `app_cases.py`: the recommended ideas show index / 100 with Value, Effort and Risk as three small metrics; the Ranking tab uses ranking_rows; the Roadmaps compared table has an index column. 129 tests.
- Not changed: the weights. Retuning (for example EFFORT_WEIGHT 0.35) changes rankings, so do it with the low/medium/high sensitivity run on all three test cases, and report it as the 4.1 threshold test.

## Part 12: Handoff (Nov 16, 3:50 pm). Start here in a new session
State: Mac-only setup works end to end. 129 tests pass (`python -m pytest -q`). Git: all of today's work is STAGED but NOT COMMITTED (the assistant's shell has no git identity and cannot delete git temp files); commit from a Mac terminal first: `git -c user.name="Mark Kinch" -c user.email="<your email>" commit -m "Laurel Run harness, Critic fix, kb_sources, score index"`. Keep `cases/` out of the public repo (real-company website text in carmate/ace/mss cases, and the Laurel Run evaluator folder).

Done today (Nov 16): Checkpoint 6.1 submitted. Critic rubric fixed (Part 10; run 8 kept 9 of 11 reviews). certifi for HTTPS fetches. `kb_sources/` with 13 sourced public-domain notes (SBA, IRS, NIST, NHTSA) and SOURCES.md. Laurel Run synthetic case harness (Part 11): offline file:// discovery, enforced owner gate (accept / correct / reject), materials boundary (share_materials refuses evaluator material), Process Mapper citations and doc-vs-interview gaps, social presence from page links only, scripts/synthetic_case.py, evaluation/evaluate_case.py. Score index 0-100 and separate value/effort/risk display (above). Laurel Run run 1 completed and verified on real models.

Runs to keep: cases/carmate-.../result.run5_allqwen36_matcherfix.json, result.run7_mac_all_local.json, result.run8_critic_fix.json; cases/laurel-run-trailer-works-inc-20261116-145050/result.json (run 1; copy it to result.run1_laurel.json before re-running).

Next steps, in order (final capstone believed Mon Nov 23, unconfirmed; deliverables: public GitHub repo, 8-10 min video, optional 90 s pitch):
1. Commit. Confirm the final due date and Module 7 deliverables in the classroom.
2. Evaluate Laurel Run run 1 separately: write `cases/Laurel_Run_Test_Case/02_evaluator_only_DO_NOT_SHARE/expectations.json` from CASE_EXPECTATIONS.md (format in evaluation/evaluate_case.py), run `python evaluation/evaluate_case.py <case_id> <that file>`; record the result in the feedback tracker's evaluation log. Check whether planted document-vs-interview gaps were missed (run 1 reported none).
3. Per-process retrieval over the shared chunks (BM25, reuse tools/kb.py) so the Process Mapper and Verifier see the relevant sections, not only each file's first 700 chars. Then the with/without-retrieval comparison (3.1 grader ask).
4. Replace the placeholder `kb/` notes with `kb_sources/` (or run with KB_DIR=kb_sources); add overlays for the other demo industries if time.
5. Sensitivity run (low/medium/high risk and budget) on Carmate, Brightline and Laurel Run; decide EFFORT_WEIGHT; report the 60%/80% thresholds and the real call counts (4.1 grader ask). Your own expected picks per case, written before the runs.
6. Submission package: README with architecture and an honest built-vs-planned table, cases/ removed or anonymized, video, pitch.
Out of scope: live SME interview, owner Q&A chat, web search on the company name, MCP server, LangSmith, ChromaDB.

Known limits to state honestly: scores are a ranking index (weights untuned); the Critic's evidence bar was loosened for a 7B model (idea names count); no per-process retrieval yet; interviews are shared transcripts, not a live interview; the `file://` site path is machine-specific; the live manus.space site was private on Nov 16.

## Part 13: Run 1 evaluation, week plan decisions, and the new case layout (Nov 16 evening to Nov 17). Start here in a new session
Day-by-day plan for Nov 17-22 (1-3 hours a day while travelling): Project doc `claude/capstone/daily-plan-nov17-22.md`. Nov 16 work was committed (bf849a0) before the layout change below; the layout change is NOT committed yet.

### Laurel Run run 1 evaluated against the answer key
- Answer key transcribed to `evaluation/answer_keys/laurel-run.json` (from CASE_EXPECTATIONS.md and the evaluator-only key). The key names no "expected picks"; the three used (inventory, schedule, quote) were chosen from the largest AI-addressable issues and should be reviewed. Report: `cases/laurel-run/results/run-001/evaluation.json`.
- Evaluator: pass. Industry right; 3 of 3 recommended ideas grounded, all with a document citation; no invented social profiles or handles; social presence "not found on the pages read" for all six channels; no placeholders.
- Honest reading: expected picks really 2 of 3 (the "schedule" keyword matched the Delivery & Invoicing Coordinator's "auto-schedules"; the Production Schedule Sync Agent was ranked but not recommended). The plan leads with order-status lookups (I12, about $640/yr in the key, one of the smallest). About 5 of 15 planted issues surfaced (I02, I07 partly, I08, I09 partly, I12); missed I01, I03 (axle re-quote, the largest item at $21.6k gross), I04, I05, I06, I10, I11, I13, I14, I15. Several misses are non-AI fixes the Matcher cannot propose by design; I05, I06 and I13 are AI-addressable misses.
- Document-vs-interview gaps: none reported, probably correctly (the key plants none). The gap flag is still unexercised on a real run.
- Cause of the misses: the Process Mapper cited 10 of 132 passages, from 4 of the 10 process documents (it sees each file's first 700 characters). Not context truncation: Qwen3.6 was loaded at 262144 tokens. Best-practice citations are still the placeholder kb/ notes.

### Decisions (all recorded in the Project doc daily plan)
- RAG uses embeddings: course material teaches embeddings and vector stores (Module 6 RAG sessions, Labs 4.2 and 5.1, Module 5 agent-squad lab InMemoryVectorStore); BM25 is not mentioned anywhere in the course; Checkpoint 3.1 promised embeddings in a vector database. Model: LM Studio `text-embedding-nomic-embed-text-v1.5` (needs `search_document: ` / `search_query: ` prefixes; langchain-openai needs check_embedding_ctx_length=False).
- RAG design: one shared industry store (kb_sources/), one store per company in `cases/<id>/index/`, one `retrieve(query, scope, case_id, k, source_types)`; hybrid nomic + BM25 by reciprocal rank fusion, BM25-only fallback with a flag; Process Mapper gets each process document in full plus the top interview passages per process; Verifier looks citations up in the full company store; `COMPANY_RETRIEVAL=off` reproduces run 1 for the 3.1 comparison.
- Critic moves to a second model family: Gemma 3 12B Instruct (fallback Llama 3.1 8B), replacing Qwen2.5-7B; switch after Laurel Run run 2 so that comparison changes one variable. Only `LLM_CRITIC_MODEL` changes.
- Tools and MCP: an MCP server (`mcp` package) exposing read-only tools over the RAG stores, results and the scoring calculator; client = LM Studio with Qwen3.6, all local. This is the project's ReAct example (the pipeline itself is not ReAct). Owner chat is read-only plus what-if; "change the results" (propose, owner approves, partial re-run from the Strategist with LangGraph interrupt) is designed but not planned this week.
- Reasoning patterns, as built: Tree of Thoughts = Strategist 4 angles, Critic scores, review gate keeps top 3, up to 3 rounds, 10% early stop (beam search); verification retry loop with escalation after 2 failures; CoT only inside Qwen3.6's hidden think blocks, which agents/common.py strips (idea: log their length and one sample per agent).
- LM Studio settings: Qwen3.6 context 32768 (was 262144), Qwen2.5-7B 16384, nomic 2048; turn off Serve on Local Network while travelling.

### New case folder layout (APPLIED Nov 17, early am; 134 tests pass)
- `cases/<company>/`: `case.json` (now with `materials_authorized` as a list of folders and `latest_run`), `website/` (`"website": "local"` resolves to it at run time, so the case works on any machine), material folders `documents/` (subfolder `processes/` marks process documents), `interviews/`, `data/`, `research/`, then `owner/profile.json`, `owner/decisions.json`, `index/` (generated, git-ignored), `results/discovery.json`, `results/run-NNN/` (result.json, process_map.json, the run's call log, evaluation.json), `results/legacy/` (old process-map versions and unmatched call logs).
- Agents read only the website and authorized material folders (`cases._material_paths`): never owner/, results/, hidden files, symlinks or anything resolving outside the case. Authorization: `case_runner.authorize(case, folders)` (after owner confirmation), an upload (authorizes its folder), or `cases.share_materials` (import from elsewhere: interviews/ -> interviews, data/ -> data, research/ -> research, personas/ -> interviews/personas, everything else -> documents/; the root check now applies DENY_PATTERNS to the whole path, so `evaluation/answer_keys/...` is refused).
- Chunk ids are now relative to the case folder: `doc:documents/processes/08_quoting.md#1`, `doc:interviews/08_quoting_interview.md#3`. Old results keep their old ids.
- Case ids are named after the company (create_case: `acme-trailers-inc`, then `-2`), no timestamp.
- `case_runner.analyze` saves each analysis as the next `results/run-NNN` (cases.save_run; save_process_map removed). `evaluate_case.py <case> <answer key> [--run]` writes `results/run-NNN/evaluation.json`. `scripts/synthetic_case.py` gained `authorize`; `create` takes a company name and `--site local|<url>`. `app_cases.py`: material table with an Authorize control, upload target folder, run selector, process map per run.
- Migration (`scripts/migrate_case_layout_nov17.py`, kept for the record): moved, not copied. Carmate -> `cases/carmate-trailers` with runs 001 (Part 8 run 1, qwen36_matcher), 004, 005, 007, 008 (labels kept in each run_info.json; runs 2, 3, 6 were never saved). Ace -> `cases/harleysville-ace-hardware` run-001. MSS -> `cases/mss` (discovered only). Laurel Run -> `cases/laurel-run` run-001, materials authorized as in run 1 (documents = company + processes, interviews, data: the same 390 chunks), research copied in but not authorized, personas not copied. `cases/Laurel_Run_Test_Case` -> `evaluation/synthetic/laurel-run/` (prompts, manifest updated, site builder, pristine package; see WHERE_THINGS_MOVED.md) and `evaluation/answer_keys/laurel-run/` (evaluator notes). Exact duplicates removed (result.json = run8 / run1 copies, process_map.json = latest version), plus empty runs/ and evaluations/ folders.
- Runs to keep now: `cases/carmate-trailers/results/run-005`, `run-007`, `run-008`; `cases/laurel-run/results/run-001`.
- Next (Tuesday Nov 17): commit this; then embedding retrieval for the industry store (daily plan, Tue steps 6-8).

### Score index: min-max and plain-language bands (APPLIED Nov 17, 7:45 am; 134 tests pass)
- The 0-100 index was a share of the best possible score starting at 0, but scores run from -1.0 (value 1, effort 10, risk 10) to 0.89 (value 10, effort 1, risk 1) at tolerance 0.4, so mid-range ideas looked poor (Laurel Run run-002: 60, 49, 36). Now min-max: index = (score - worst) / (best - worst). Same ideas: 81, 76, 70. A straight rescale: no ranking changes; EFFORT_WEIGHT (the real lever) stays for the Thursday sensitivity run.
- `tools/scoring.py`: raw_score (unclamped), worst_possible_score, score_index (min-max), idea_index (from the three ratings, so ideas below the stored 0 floor still show low), INDEX_BANDS + index_band: 80+ Strong fit, 65-79 Good fit, 50-64 Possible, under 50 Weak fit. Roadmap index still uses the roadmap score (clamped at 0).
- UI: each recommended idea shows "81 / 100" with its band; the Ranking and Roadmaps tables gained a "fit" column; score_scale_note explains the scale and bands.
- Laurel Run run-002 (Nov 17 morning, no retrieval yet) recommended Invoice Matcher (I13), Dealer Status Inquiry (I12) and Quote Spec Extractor (I01/I09); run-001 led with Delivery & Invoicing. Two no-retrieval runs give a run-to-run variance baseline; the retrieval run on Wednesday will be run-003.

### Retrieval progression: keyword search to vector search (Nov 17)
Also in the Project doc `claude/capstone/retrieval-progression-keyword-to-vector.md`. Use it for the README "RAG design" section, the video's RAG segment and the 3.1 answer.

| Stage | When | Industry best practices | Company documents and interviews | Runs |
|---|---|---|---|---|
| 0. Keyword search over placeholder notes | Nov 13-15 | BM25 (`tools/kb.py`) over author-written placeholders in `kb/`; query = industry name; top 4 industry + 2 general; each practice cites a passage id | Not used (website text only) | Carmate runs 1-8, Ace |
| 1. Citable chunks, no retrieval | Nov 16-17 | Same as stage 0 | Files split into chunks with ids; the Process Mapper gets a fixed bundle (first 700 chars of each file plus section headings, at most 16,000 chars, same for every process); the Verifier checks quotes only against what it was shown | Laurel Run run-001, run-002 |
| 2. Vector search, industry scope | Tue Nov 17 | Sourced notes (`kb_sources/`) embedded with nomic-embed-text-v1.5 in LM Studio; hybrid vector + BM25 merged by reciprocal rank fusion; BM25 alone (flagged) if the embedding model is not loaded; query = industry + what the website says | Same as stage 1 | none planned |
| 3. Vector search, per company, per process | Wed Nov 18 | Same as stage 2 | One store per company (`cases/<id>/index/`) from authorized folders only; per process: the process document in full plus the top matching interview passages; the Verifier looks citations up in the whole store; `COMPANY_RETRIEVAL=off` reproduces stage 1 | Laurel Run run-003 |
| 4. Retrieval as a tool the model chooses (agentic RAG) | Thu Nov 19 | `search_industry_practices` MCP tool | `search_company_docs` MCP tool | Owner chat (ReAct) in LM Studio |

Why each step:
- Keyword search first: cheap, local, explainable (the words matched), good at exact terms ("packing slip", "axle"); misses paraphrase ("I type the order in again" does not match "re-keying").
- Stage 1 showed the gap: 10 of 132 passages cited, 4 of 10 process documents used, about 5 of 15 planted issues; month-end close, payroll and the axle re-quote never reached the model. Not context length (Qwen3.6 was at 262,144 tokens); the fixed bundle.
- Vectors add meaning (similar meanings sit close together), which is RAG as the course teaches it (Module 6 RAG and modular RAG; Labs 4.2 and 5.1; Module 5 lab in-memory vector store) and what Checkpoint 3.1 promised.
- Hybrid, not vectors alone: vectors can miss exact identifiers that keywords catch; reciprocal rank fusion merges by rank, no weights to tune; BM25 doubles as the fallback.
- Per company, per process: customers kept apart by design; deleting a case deletes its index; the process document beside matching interview passages puts "how it is supposed to run" next to "how it really runs" (the 5.1 document-vs-interview ask).
- Agentic RAG last: in the pipeline code decides what to retrieve; in the owner chat the model decides when and what to search (the ReAct example).

Design choices to state: all local (LM Studio); nomic task prefixes (`search_document: `, `search_query: `); in-memory vector store instead of ChromaDB (about 400 passages per company, no database server, no new dependency); passage ids kept at every stage so cite-or-drop and the Verifier work the same way.

Measured by: Laurel Run run-001 and run-002 (stage 1; also run-to-run variance) vs run-003 (stage 3) on the same 390 passages and models: process documents used, passages cited, planted issues surfaced, citation checks confirmed, document-vs-interview gaps, and whether the axle re-quote and month-end issues appear; scored by `evaluation/evaluate_case.py` against `evaluation/answer_keys/laurel-run.json`.

### Industry RAG on ChromaDB (APPLIED Nov 17, 1 pm; 143 tests pass)
- Decision (Nov 17, noon): ChromaDB instead of LangChain's in-memory store. Reasons: Checkpoint 3.1 named ChromaDB as the vector database; persistence and metadata filters come built in (needed for Wednesday's per-company, per-process search); a recognizable component; Mark has used it. Cost: a heavy dependency (about 87 packages incl. onnxruntime; checked to install on Python 3.14, macOS arm64, macOS 14+). Privacy: telemetry off and Chroma's default embedding model never used (we pass nomic vectors from LM Studio).
- `tools/vectorstore.py`: Embedder (LM Studio /v1/embeddings via langchain-openai OpenAIEmbeddings with check_embedding_ctx_length=False; nomic prefixes; hosted endpoints refused unless "embed" in LLM_ALLOW_HOSTED; per-call log), open_store (Chroma PersistentClient, cosine, fingerprint of passages + model in collection metadata; rebuilds only on change), vector_ranking, rrf (k=60).
- `tools/kb.py`: default folder is now kb_sources/; `retrieve_with_info(industry, ..., query_text, embedder)` returns (hits, note, info) with mode hybrid|keyword, reason, embed model, index_rebuilt, query, embedding calls; `retrieve()` keeps its old (hits, note) shape. Pools (industry-specific, general) are ranked separately as before; inside each pool the vector and BM25 rankings are fused.
- Discovery research: query = industry + profile evidence + owner description (300 chars); `best_practices.retrieval` holds the info; trace says "(hybrid retrieval)" or "(keyword retrieval)"; flag `retrieval_keyword_only` when an embedding model is configured but fails (not when none is configured).
- kb_sources/ gained the two placeholder overlays (professional-services, distribution) copied from kb/, listed in SOURCES.md as author-written.
- Settings: LLM_EMBED_MODEL=text-embedding-nomic-embed-text-v1.5 added to .env, .env.mac, .env.example; chromadb in requirements.txt; `.chroma/` git-ignored. Tests pin KB_DIR=kb and LLM_EMBED_MODEL="" (conftest), so they stay offline; tests/test_vector_retrieval.py (9 tests) uses a fake embedder and a real temporary Chroma.
- Smoke test on the Mac: `python scripts/rag_smoke_test.py` (expect mode: hybrid, index built the first time, NIST/NHTSA passages).

### Run-to-run variation (observed Nov 17; NOT fixed yet)
- Laurel Run runs 002-005 had identical company inputs and recommended four different plans: 002 Invoice Matcher / Dealer Status Inquiry / Quote Spec Extractor; 003 Inventory Reconciliation & Shortage Predictor / Pre-Shipment Inspection Checklist / Dealer Quote Extractor; 004 Warranty Policy Knowledge Base / Quote Configuration Assistant / Pre-Shipment Compliance Checker; 005 (first with the hybrid industry RAG) Inventory Reconciliation & PO Matcher / Delivery Status Sync / VIN-Linked Build Record. Evaluator (keyword matching): expected picks 2, 3, 1, 2 of 3; planted issues 3, 2, 3, 4 of 15. Run 005 also ended in a close call (2.8%).
- Mark wants each run to be consistent. Not changed yet; it must be measured and stated in the report (evaluation section): one run proves little; compare across several runs.
- Already in place: temperature 0 for every agent's JSON call (common.ask_json, Discovery), 0.3 only for the Strategist's narrative; retrieval is deterministic (same index, same query, same ranking); scoring and ranking are code.
- Likely causes, in order: (1) the Matcher invents new idea names and ratings each run, so the candidate pool itself changes; (2) the Process Mapper names and groups processes freely; (3) value/effort/risk are single model judgments, and small rating changes swing rankings when ideas are close (several within 0.05); (4) local inference is not bit-for-bit repeatable even at temperature 0 (no seed sent; Qwen3.6's hidden thinking varies in length and wording, and an early difference cascades through 10 chained calls).
- Candidate fixes (see the chat of Nov 17, 3:20 pm): seed + temperature 0 everywhere; processes anchored to the process documents (one per document, named by code); an idea catalog per process with model ratings tied to evidence the code can count (volumes, hours in the documents); self-consistency (run the Matcher 3 times, keep ideas that appear at least twice, median ratings); treat ideas within a margin as tied; measure stability (overlap of the recommended sets across 3-5 runs) and report it.

### Deadline (confirmed Nov 17)
Final capstone due Monday Nov 23, 11:29 AM EST (confirmed am). Deliverables per Module 7: final report (ten template sections), public GitHub repo, 8-10 minute video. Plan: submit Saturday Nov 21; Sunday buffer. Day-by-day plan: Project doc claude/capstone/daily-plan-nov17-22.md.

### Company RAG per customer (APPLIED Nov 17, 4:30 pm; 151 tests pass)
- `tools/company_rag.py`: build_index (Chroma store "company_docs" in cases/<id>/index/, passages = cases.document_chunks with source_type/name/heading metadata, fingerprint rebuild, index_info.json), index_status (up to date or not, without a model call), Searcher (hybrid nomic + BM25 by RRF with a Chroma `where` filter on source_type; BM25 only if vectors are unavailable), COMMON_PROCESSES, enabled() (COMPANY_RETRIEVAL).
- `case_runner.refresh_index(case)` runs at the start of analyze (logs `company_index_built` in owner/decisions.json when it rebuilds); the state gets `company_index` (path) and `company_retrieval` (mode, reason, passages, rebuilt). `scripts/synthetic_case.py index <case>` builds it on demand; `status` and the case app show passages, model, build time and whether it is up to date.
- Process Mapper v3: per process document, its full text, then the top 3 interview passages and the top 1 other company passage (documents/data) retrieved with that document's heading and first 600 characters as the query; a passage matching two processes is shown once and referenced the second time; without process documents it searches seven common SMB process queries. Budget MAPPER_RAG_CHARS=80000 (Laurel Run: about 72,000 characters, about 18,000-20,000 tokens, all 10 process documents, 97 passages; was 4 of 10 documents in runs 001-005). `process_map.retrieval` records mode, anchoring, per-process retrieved ids, anything skipped for space, embedding calls. Qwen3.6 must be loaded with a context of 49,152 or more for this prompt.
- Verifier: cited `doc:` ids are looked up in the state's document chunks, so a company passage can be quote-checked.
- Tests (tests/test_company_rag.py, 8): per-company stores and isolation (one company's search never returns another's passages), reuse and rebuild on change, the mapper prompt layout and per-process ranking, common-process searches, COMPANY_RETRIEVAL=off, keyword-only fallback, a full analysis, the Verifier lookup. The fake embedder now hashes words with crc32 (Python's hash() is randomized per process and made one test flaky).
- Next: Laurel Run run-006 (and run-007 for variation) with the Critic still on Qwen2.5; compare with runs 001-005.
