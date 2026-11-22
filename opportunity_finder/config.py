"""Tunable limits for the Supervisor and the coded checks. Values come from Checkpoints 4.1-6.1."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    max_review_rounds: int = 3          # Strategist/Critic loop cap
    keep_top_k: int = 3                 # roadmaps kept per round
    early_stop_margin: float = 0.10     # stop if best leads 2nd by >= 10%; below it = "close call"
    max_model_calls: int = 40           # hard cap on REAL model calls; then return best, partial
    max_verification_failures: int = 2  # then ask the owner for help
    roadmap_size: int = 3               # ideas per roadmap (pilot + up to two more)
    min_evidence_coverage: float = 0.60  # share of recommended ideas that must trace to a source
    rubric_weight: float = 0.15         # the Critic model can move the coded score by at most +/-15%
    deep_min_rounds: int = 3            # deep review (case setting): review rounds before an early stop is allowed


SETTINGS = Settings()
