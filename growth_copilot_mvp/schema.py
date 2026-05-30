"""Data structures shared across the pipeline.

A CandidateInsight is the unit of currency between the deterministic detectors
and the LLM narration layer. Every numeric field cited by the LLM must trace
back to evidence_values via an evidence_fields path.
"""
from dataclasses import dataclass, field, asdict
from typing import Literal, Any


Significance = Literal["significant", "noisy", "insufficient_data"]
ImpactTier = Literal["small", "medium", "large", "unknown"]
BaselineStability = Literal["stable", "noisy", "unknown"]
Novelty = Literal["new", "ongoing_unchanged", "ongoing_worsening", "ongoing_improving"]


@dataclass
class ConfidenceInputs:
    sample_size: int
    effect_size: float
    baseline_stability: BaselineStability
    is_seasonal: bool


@dataclass
class CandidateInsight:
    id: str
    type: str
    summary: str
    evidence_fields: list[str]
    computed_impact_tier: ImpactTier
    confidence_inputs: ConfidenceInputs
    novelty_vs_prior: Novelty
    supports_causal_claim: bool
    evidence_values: dict[str, Any] = field(default_factory=dict)
    # Standardized fields consumed by the UI, LLM prompt, and verifier.
    # All have safe defaults so detectors that don't set them still produce
    # valid objects.
    evidence: list[str] = field(default_factory=list)
    detection_reason: str = ""
    raw_metrics: dict[str, Any] = field(default_factory=dict)

    def to_brief_dict(self) -> dict:
        d = asdict(self)
        d.pop("evidence_values", None)
        return d
