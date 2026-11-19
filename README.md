# AI Opportunity Finder (capstone implementation)

LangGraph implementation of the Checkpoint 5.1 design: a rule-based Supervisor plus six agents, all on local models.
Current status is in `CLAUDE.md`; design notes and run results are in `PROJECT_NOTES.md` (Part 9 is the latest).

## Run

    pip install -r requirements.txt
    python -m pytest -q
    python -m opportunity_finder.main

## Layout

- `opportunity_finder/graph.py`: nodes and edges (fan-out/fan-in, review loop, human steps)
- `opportunity_finder/supervisor.py`: pure-Python routing rules (no LLM): prune top 3, 3-round cap,
  10% early stop, model-call cap with "partially complete", escalate after 2 verification failures
- `opportunity_finder/state.py`: shared state; `config.py`: limits
- `opportunity_finder/agents/`: discovery, process_mapper, matcher, strategist, critic, planner
- `opportunity_finder/tools/scoring.py`: coded scoring and checks (exact math stays out of the LLM)
- `opportunity_finder/llm.py`: LLM factory, defaults to local LM Studio (settings in `.env`, see `.env.example`)

## Next steps

1. Replace stub agents with LLM calls (use a different model for the Critic).
2. Add the three RAG collections (industry research, company docs, interview transcripts).
3. Add LangSmith tracing; log tokens, latency and pruned branches.
4. Build the three synthetic test companies and compare against decisions the owner already made.
