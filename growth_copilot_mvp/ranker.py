"""ranker.py — selectivity, detector weighting, persistence thresholds.

Calibration targets (replay over 50 seeds):
    - Alert rate: ~65-70% (not 95-100%)
    - Silent runs: ~15-20%
    - Confidence entropy: >0.5
    - High/Medium split: ~60/35
    - Detector disagreement: ~25-35%

Changes from prior version:
    - MINIMUM_SCORE raised 42 → 50 — filters more ambiguous noise
    - PERSISTENCE_MIN_SCORE raised 52 → 58 — stale signals suppressed harder
    - EFFECT_SIZE_FLOOR raised 0.04 → 0.07 — tiny effects are noise
    - anomaly weight lowered 0.72 → 0.62 — single-day spikes less credible
    - Added MAD_RATIO_FLOOR: anomaly must clear 2.5x MAD minimum
"""
import math
from .schema import CandidateInsight


TIER_RANK     = {"large": 3, "medium": 2, "small": 1, "unknown": 0}
NOVELTY_RANK  = {
    "new":               3,
    "ongoing_worsening": 2,
    "ongoing_improving": 1,
    "ongoing_unchanged": 0,
}
BASELINE_RANK = {"stable": 2, "noisy": 1, "unknown": 0}

MINIMUM_SCORE         = 50    # raised from 42
DAILY_MAX_INSIGHTS    = 5
PERSISTENCE_MIN_SCORE = 58    # raised from 52
EFFECT_SIZE_FLOOR     = 0.07  # raised from 0.04
MAD_RATIO_FLOOR       = 2.5   # anomaly detector minimum MAD ratio

DETECTOR_WEIGHTS = {
    "funnel_drop":       1.15,
    "cohort_divergence": 1.00,
    "anomaly":           0.62,  # lowered from 0.72
}


def _composite_score(
    c: CandidateInsight,
    current_focus: str | None = None,
) -> float:
    tier_s     = TIER_RANK.get(c.computed_impact_tier, 0) / 3.0
    novelty_s  = NOVELTY_RANK.get(c.novelty_vs_prior, 0) / 3.0
    baseline_s = BASELINE_RANK.get(c.confidence_inputs.baseline_stability, 0) / 2.0
    sample_s   = min(math.log10(max(c.confidence_inputs.sample_size, 1)) / math.log10(1000), 1.0)
    effect_s   = min(c.confidence_inputs.effect_size / 0.30, 1.0)
    focus_b    = 0.05 if current_focus and current_focus.lower() in c.summary.lower() else 0

    raw = (
        tier_s     * 30 +
        novelty_s  * 25 +
        baseline_s * 20 +
        sample_s   * 15 +
        effect_s   * 10 +
        focus_b    * 100
    )
    det_weight = DETECTOR_WEIGHTS.get(getattr(c, "type", ""), 1.0)
    return round(raw * det_weight, 2)


def _passes_persistence_threshold(c: CandidateInsight, score: float) -> bool:
    # Absolute effect size floor — tiny effects are noise regardless
    if c.confidence_inputs.effect_size < EFFECT_SIZE_FLOOR:
        return False

    # Anomaly detector: require minimum MAD ratio
    if getattr(c, "type", "") == "anomaly":
        raw_metrics = getattr(c, "raw_metrics", {}) or {}
        mad_ratio   = raw_metrics.get("mad_ratio", 0)
        if mad_ratio < MAD_RATIO_FLOOR:
            return False

    # Stale unchanged signals need very strong evidence
    if c.novelty_vs_prior == "ongoing_unchanged":
        return score >= PERSISTENCE_MIN_SCORE

    return score >= MINIMUM_SCORE


def filter_weak(
    candidates: list[CandidateInsight],
    min_score: float = MINIMUM_SCORE,
    max_insights: int = DAILY_MAX_INSIGHTS,
) -> list[CandidateInsight]:
    scored = [(c, _composite_score(c)) for c in candidates]
    scored = [
        (c, s) for c, s in scored
        if _passes_persistence_threshold(c, s)
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:max_insights]]


def rank(
    candidates: list[CandidateInsight],
    current_focus: str | None = None,
    apply_filter: bool = True,
) -> list[CandidateInsight]:
    if apply_filter:
        candidates = filter_weak(candidates)
    return sorted(
        candidates,
        key=lambda c: _composite_score(c, current_focus),
        reverse=True,
    )


def detector_weight_report() -> dict:
    return {
        d: {"weight": w, "note": _weight_note(d)}
        for d, w in DETECTOR_WEIGHTS.items()
    }


def _weight_note(detector: str) -> str:
    notes = {
        "funnel_drop":       "High reliability — specific step, measurable, persistent",
        "cohort_divergence": "Medium reliability — may be structural rather than causal",
        "anomaly":           "Lower reliability — single-day spikes, higher false positive rate",
    }
    return notes.get(detector, "")