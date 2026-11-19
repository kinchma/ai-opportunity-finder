"""Run the skeleton end to end.

    python -m opportunity_finder.main                 (asks for a website)
    python -m opportunity_finder.main example.com     (website on the command line)
"""
import json
import sys

from langgraph.types import Command

from .graph import build_graph
from .observability import summarize, write_run_log


def run(company_input: dict, corrections: dict | None = None, thread_id: str = "demo",
        ask_owner=None) -> dict:
    """Run the graph. It pauses at owner_confirm. If `ask_owner` is given it is called with
    the pre-filled profile and returns the owner's corrections; otherwise `corrections` is used."""
    graph = build_graph()
    cfg = {"configurable": {"thread_id": thread_id}}
    graph.invoke({"company_input": company_input, "status": "running"}, cfg)  # pauses at owner_confirm
    if ask_owner is not None:
        corrections = ask_owner(graph.get_state(cfg).values.get("profile", {}))
    return graph.invoke(Command(resume={"corrections": corrections or {}}), cfg)


def ask_owner_cli(profile: dict) -> dict:
    """Show the Discovery agent's guess and let the owner accept it or fix the industry."""
    print("\n--- Discovery agent's guess ---")
    for key in ("name", "website", "industry", "confidence", "evidence", "note"):
        if profile.get(key):
            print(f"  {key}: {profile[key]}")
    if not sys.stdin.isatty():
        return {}
    typed = input("Press Enter to accept, or type the correct industry: ").strip()
    return {"industry": typed} if typed else {}


if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else input(
        "Website to analyze (blank = synthetic demo company): ").strip()
    company = {"risk_tolerance": 0.4}
    if site:
        company["website"] = site
        if sys.stdin.isatty():
            desc = input("Optional one-line description of the business "
                         "(used if the site blocks us; Enter to skip): ").strip()
            if desc:
                company["description"] = desc
    else:
        company.update({"name": "Synthetic Trailers Inc", "industry": "trailer manufacturing", "size": "50"})

    result = run(company, ask_owner=ask_owner_cli)
    print("\nstatus:", result["status"])
    print("model calls:", result["model_calls"], "| rounds:", result["review_round"])
    print("verified:", result.get("verified"), "| flags:", json.dumps(result.get("flags", [])))
    if result.get("escalation"):
        print("ESCALATED TO OWNER:", json.dumps(result["escalation"], indent=2))
    print("recommendation:", json.dumps(result["final_recommendation"], indent=2))
    print("pruned branches:", json.dumps(result["pruned_log"], indent=2))
    print("trace:\n  " + "\n  ".join(result["trace"]))
    print("call summary:", json.dumps(summarize(result["call_log"]), indent=2))
    print("run log saved to:", write_run_log(result, "demo"))
    print("\nprocess map (", result["process_map"]["note"], "):")
    for p in result["process_map"]["processes"]:
        print(f"  - {p['name']} [{p['basis']}]: {p['description']}")
    print("\nscored opportunities:")
    for o in sorted(result["scored_opportunities"], key=lambda o: -o["score"]):
        tag = " (PLACEHOLDER)" if o.get("placeholder") else ""
        print(f"  {o['score']:.3f}  {o['name']}{tag}  value={o['value']} effort={o['effort']} risk={o['risk']}"
              f"  process={o.get('process')}  practice={o.get('supporting_chunk_id')}")
    print("profile:", json.dumps(result["profile"], indent=2))
    print("best practices:", json.dumps(result["best_practices"], indent=2))
