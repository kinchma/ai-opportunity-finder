"""Check that every model the pipeline is configured to use is available in LM Studio.

    python scripts/model_check.py

Lists the models the server reports (GET /v1/models), then, for each agent, the model it is set
to use (from .env) and whether the server has it. A missing id is the usual cause of a failed run
after switching models: copy the exact "API model identifier" from LM Studio into .env."""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opportunity_finder.llm import llm_settings  # noqa: E402
from opportunity_finder.tools.vectorstore import embed_settings  # noqa: E402

AGENTS = ["discovery_profile", "discovery_research", "process_mapper", "matcher", "strategist", "critic", "planner"]
servers: dict = {}
for agent in AGENTS:
    s = llm_settings(agent)
    servers.setdefault(s["base_url"], []).append((agent, s["model"]))
e = embed_settings()
if e["model"]:
    servers.setdefault(e["base_url"], []).append(("embeddings", e["model"]))

ok = True
for base, wanted in servers.items():
    try:
        with urllib.request.urlopen(base.rstrip("/") + "/models", timeout=5) as r:
            have = {m["id"] for m in json.load(r).get("data", [])}
    except Exception as exc:
        print(f"{base}: cannot reach the server ({exc})")
        ok = False
        continue
    print(f"{base}: {len(have)} model(s) available:\n  " + "\n  ".join(sorted(have)))
    for agent, model in wanted:
        found = model in have
        ok &= found
        print(f"  {'OK     ' if found else 'MISSING'} {agent:18} -> {model}")
print("\nAll configured models are available." if ok else
      "\nSomething is missing: copy the exact API model identifier from LM Studio into .env, then restart Streamlit.")
