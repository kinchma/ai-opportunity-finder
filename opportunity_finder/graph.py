"""LangGraph wiring for the AI Opportunity Finder.

START -> discovery_profile -> owner_confirm (human) -> [discovery_research || process_mapper]
      -> matcher -> strategist -> critic -> review_gate --(revise)--> strategist
                                                  \\--(finalize)--> planner
planner --(done)--> END | --(revise)--> strategist | --(escalate)--> escalate_to_owner -> END
(escalate_to_owner ends the run with status needs_owner_help and a decision card; it does not pause)
"""
import functools

from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .agents.critic import critic
from .agents.discovery import discovery_profile, discovery_research
from .agents.matcher import matcher
from .agents.planner import planner
from .agents.process_mapper import process_mapper
from .agents.strategist import strategist
from .state import OpportunityState
from .supervisor import after_verification, review_decision, review_gate


def owner_confirm(state: dict) -> dict:
    """Human in the loop: owner confirms or corrects the pre-filled profile."""
    answer = interrupt({"ask": "Confirm or correct this profile", "profile": state["profile"]})
    corrections = (answer or {}).get("corrections", {})
    return {"profile": {**state["profile"], **corrections}, "intake_confirmed": True,
            "trace": ["owner_confirm: intake confirmed"]}


def escalate_to_owner(state: dict) -> dict:
    """The Supervisor hands the decision to the owner: verification failed twice, or failed in a
    way a retry cannot fix. It ends the run with a short decision card (what is uncertain, and
    two or three clear choices) so the case can be saved and picked up later."""
    report = state.get("verification_report", {})
    draft = state.get("final_recommendation", {}).get("roadmap", {}).get("opportunities", [])
    failed = [c for c in state.get("call_log", []) if c.get("error")]
    if failed:  # the real cause is upstream: say so first, or the owner chases the wrong problem
        agents = ", ".join(dict.fromkeys(c["agent"] for c in failed))
        models = ", ".join(dict.fromkeys(c["model"] for c in failed))
        reason = (f"{len(failed)} model call(s) failed ({agents}; model {models}), so this run has little or "
                  "nothing from the model. Check that the model server is running and reachable, then re-run.")
    elif report.get("no_practices"):
        reason = "No best practices were found for this business, so the roadmap could not be checked."
    else:
        reason = f"The recommendation failed verification {state.get('verification_failures', 0)} time(s)."
    card = {
        "reason": reason,
        "what_is_uncertain": ([f"{c['agent']}: {c['error'][:120]}" for c in failed[:6]] if failed else [])
        + report.get("reasons", []),
        "draft_roadmap": draft,
        "choices": [
            {"id": "accept_draft", "label": "Use the draft as an unverified starting point"},
            {"id": "add_information", "label": "Add process documents or correct the profile, then re-run"},
            {"id": "stop", "label": "Stop here"},
        ],
    }
    return {"status": "needs_owner_help", "escalation": card,
            "trace": [f"escalate_to_owner: {card['reason']}"]}


def _reports_finish(name, fn):
    """Wrap a node so it announces its own finish on the "custom" stream the moment it returns.
    LangGraph's own end-of-task events wait for every parallel task in the step (3a and 3b), so the
    live panel uses this one instead. Display only: it never changes the node's result."""
    @functools.wraps(fn)
    def run(state):
        out = fn(state)
        try:
            get_stream_writer()({"node_end": name})
        except Exception:
            pass
        return out
    return run


def build_graph(checkpointer=None):
    g = StateGraph(OpportunityState)
    for name, fn in [
        ("discovery_profile", discovery_profile), ("owner_confirm", owner_confirm),
        ("discovery_research", discovery_research), ("process_mapper", process_mapper),
        ("matcher", matcher), ("strategist", strategist), ("critic", critic),
        ("review_gate", review_gate), ("planner", planner),
        ("escalate_to_owner", escalate_to_owner),
    ]:
        g.add_node(name, _reports_finish(name, fn))

    g.add_edge(START, "discovery_profile")
    g.add_edge("discovery_profile", "owner_confirm")
    # fan-out: research and process mapping run in parallel
    g.add_edge("owner_confirm", "discovery_research")
    g.add_edge("owner_confirm", "process_mapper")
    # fan-in: matcher waits for both
    g.add_edge(["discovery_research", "process_mapper"], "matcher")
    g.add_edge("matcher", "strategist")
    g.add_edge("strategist", "critic")
    g.add_edge("critic", "review_gate")
    g.add_conditional_edges("review_gate", review_decision,
                            {"revise": "strategist", "finalize": "planner"})
    g.add_conditional_edges("planner", after_verification,
                            {"done": END, "revise": "strategist", "escalate": "escalate_to_owner"})
    g.add_edge("escalate_to_owner", END)
    return g.compile(checkpointer=checkpointer or MemorySaver())
