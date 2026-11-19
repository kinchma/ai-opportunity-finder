"""Shared workflow state. The Supervisor owns this object."""
import operator
from typing import Annotated, TypedDict


class Roadmap(TypedDict, total=False):
    id: str
    angle: str            # highest_value | quick_win | lowest_risk | enabler | balanced
    opportunities: list   # up to 3 opportunity names, in order (pilot first)
    score: float          # set by the Critic: coded score nudged by the rubric
    rationale: str        # Strategist narrative; narrative_by says "model" or "code"
    findings: list        # Critic's coded checks and objection (what the Strategist revises)
    rubric: dict          # Critic model's 1-5 ratings with evidence, or None


class OpportunityState(TypedDict, total=False):
    # inputs and intake
    company_input: dict            # website / LinkedIn URL, risk tolerance, budget
    profile: dict
    site_text: str                 # trimmed website text, for later agents
    documents: list                # owner-provided documents [{name, text, source_type}] (text files, capped)
    document_chunks: list          # the same documents as citable chunks [{id, name, source_type, heading, text}]
    website_assessment: dict       # 1-10 website rating, chatbot finding, starter prompts
    intake_confirmed: bool
    # research results (written by agents, read by the next one)
    best_practices: dict
    process_map: dict
    gap_report: list
    scored_opportunities: list
    # review loop
    roadmaps: list
    review_round: int
    revision_exhausted: bool       # Strategist had nothing left to revise (Supervisor stops the loop)
    pruned_log: Annotated[list, operator.add]   # every pruned branch is logged
    # verification and outcome
    verified: bool
    verification_failures: int
    verification_report: dict      # per-idea evidence, coverage and the reasons for a failure
    failed_claims: list            # ideas the Verifier rejected; the Strategist leaves them out on a retry
    escalate_now: bool             # a failure a retry cannot fix (for example no practices at all)
    escalation: dict               # decision card shown to the owner
    flags: Annotated[list, operator.add]   # guardrail flags: injection, close_call, practices_empty ...
    final_recommendation: dict
    status: str                    # running | complete | partially_complete | needs_owner_help
    # counters / observability (reducers let parallel branches both write)
    model_calls: Annotated[int, operator.add]
    trace: Annotated[list, operator.add]
    call_log: Annotated[list, operator.add]   # one record per model call (see observability.py)
