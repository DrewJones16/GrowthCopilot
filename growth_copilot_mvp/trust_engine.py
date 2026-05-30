"""trust_engine.py — Layer 6: Trust & Adaptation.

Computes trust-adjusted urgency and surface scores based on operational history.

Three mechanisms:
    1. Trust decay from ignored alerts
       - Signals ignored N times get urgency downgraded
       - Creates adaptive humility without manual tuning

    2. Recommendation accountability
       - Tracks whether past recommendations for this signal type worked
       - Low-value recommendation history softens future action language

    3. Empirical detector weight adjustment
       - When outcome data exists, replaces heuristic weights
       - Transparent, auditable, reversible

All adjustments are:
    - inspectable (every adjustment has a reason string)
    - bounded (max downgrade is 2 levels, never suppresses High+persistent)
    - logged (trust_adjustments returned for display)
"""
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Trust decay thresholds
# ---------------------------------------------------------------------------

IGNORE_DECAY_THRESHOLD   = 2   # ignored this many times → downgrade urgency once
IGNORE_SUPPRESS_THRESHOLD = 5  # ignored this many times → downgrade urgency twice

# Minimum outcome samples before empirical weights take effect
MIN_EMPIRICAL_SAMPLES = 5

# How much a low recommendation-useful rate softens action language
REC_USEFUL_FLOOR = 0.40   # below this → add hedge language


def compute_trust_adjustments(
    cluster: Dict,
    decision: Dict,
    signal_record: Optional[Dict],
    outcome_summary: Dict,
    detector_precision: Dict,
) -> Tuple[Dict, List[str]]:
    """Apply trust-based adjustments to a decision.

    Returns:
        adjusted_decision   Dict    — decision with trust adjustments applied
        adjustments         List[str] — human-readable list of adjustments made
    """
    import copy
    decision    = copy.deepcopy(decision)
    adjustments = []
    conf        = cluster.get("confidence", {})
    conf_label  = conf.get("label", "Medium")
    conf_score  = conf.get("score", 50)

    if signal_record is None:
        return decision, adjustments

    ignored_count = signal_record.get("ignored_count", 0)
    status        = signal_record.get("status", "active")
    days_active   = signal_record.get("days_active", 1)

    # -----------------------------------------------------------------------
    # 1. Trust decay from ignored alerts
    # -----------------------------------------------------------------------

    if ignored_count >= IGNORE_SUPPRESS_THRESHOLD:
        # Two-level downgrade — operators consistently don't act
        old_urgency = decision["urgency"]
        decision["urgency"] = _downgrade_urgency(decision["urgency"], 2)
        if decision["urgency"] != old_urgency:
            adjustments.append(
                f"Urgency downgraded from {old_urgency} → {decision['urgency']}: "
                f"signal ignored {ignored_count} times without action."
            )

    elif ignored_count >= IGNORE_DECAY_THRESHOLD:
        # One-level downgrade
        old_urgency = decision["urgency"]
        decision["urgency"] = _downgrade_urgency(decision["urgency"], 1)
        if decision["urgency"] != old_urgency:
            adjustments.append(
                f"Urgency downgraded from {old_urgency} → {decision['urgency']}: "
                f"signal seen {ignored_count} times without operator action."
            )

    # -----------------------------------------------------------------------
    # 2. Recommendation accountability
    # -----------------------------------------------------------------------

    rec_useful_rate = outcome_summary.get("recommendation_useful_rate")
    total_outcomes  = outcome_summary.get("total_outcomes", 0)

    if total_outcomes >= MIN_EMPIRICAL_SAMPLES and rec_useful_rate is not None:
        if rec_useful_rate < REC_USEFUL_FLOOR:
            # Soften action language — recommendations historically not useful
            old_action = decision.get("action", "")
            if not decision["action"].startswith("Low historical value"):
                decision["action"] = (
                    f"[Low historical recommendation value — {rec_useful_rate*100:.0f}% useful] "
                    + decision["action"]
                )
                adjustments.append(
                    f"Action prefixed with low-value warning: recommendation useful rate "
                    f"is {rec_useful_rate*100:.0f}% across {total_outcomes} outcomes."
                )

    # -----------------------------------------------------------------------
    # 3. Empirical detector weight signal
    # -----------------------------------------------------------------------

    # Which detector types are in this cluster?
    insights         = cluster.get("insights", [])
    detector_types   = {getattr(ins, "type", "") for ins in insights}
    low_prec_detectors = []

    for det in detector_types:
        info = detector_precision.get(det, {})
        if info.get("reliable") and info.get("precision") is not None:
            if info["precision"] < 0.60:
                low_prec_detectors.append(det)

    if low_prec_detectors and decision["urgency"] == "immediate":
        decision["urgency"] = "this_week"
        adjustments.append(
            f"Urgency capped at this_week: detector(s) {', '.join(low_prec_detectors)} "
            f"have empirical precision < 60%."
        )

    # -----------------------------------------------------------------------
    # 4. Chronic unresolved stable signals
    # -----------------------------------------------------------------------

    if days_active >= 21 and status == "stabilizing":
        if decision["urgency"] in ("immediate", "this_week"):
            old = decision["urgency"]
            decision["urgency"] = "monitor"
            adjustments.append(
                f"Urgency downgraded to monitor: signal stable for {days_active} days "
                f"without resolution. Chronic unresolved signals get lower priority."
            )

    # Update display values
    from growth_copilot_mvp.decision_engine import URGENCY_DISPLAY, URGENCY_COLOR
    decision["urgency_display"] = URGENCY_DISPLAY.get(decision["urgency"], decision["urgency"])
    decision["urgency_color"]   = URGENCY_COLOR.get(decision["urgency"], "#555")

    return decision, adjustments


def _downgrade_urgency(urgency: str, steps: int = 1) -> str:
    order = ["immediate", "this_week", "monitor", "wait_and_observe"]
    if urgency not in order:
        return urgency
    idx = min(order.index(urgency) + steps, len(order) - 1)
    return order[idx]


def trust_summary(signal_record: Optional[Dict], outcome_summary: Dict) -> Dict:
    """Return a trust summary dict for display in the briefing."""
    if signal_record is None:
        return {}

    ignored       = signal_record.get("ignored_count", 0)
    total         = outcome_summary.get("total_outcomes", 0)
    real_rate     = outcome_summary.get("signal_real_rate")
    useful_rate   = outcome_summary.get("recommendation_useful_rate")
    self_res_rate = outcome_summary.get("self_resolution_rate")

    trust_level = "establishing"
    if total >= 10:
        if (real_rate or 0) >= 0.75 and (useful_rate or 0) >= 0.60:
            trust_level = "high"
        elif (real_rate or 0) >= 0.50:
            trust_level = "moderate"
        else:
            trust_level = "low"

    notes = []
    if ignored >= IGNORE_SUPPRESS_THRESHOLD:
        notes.append(f"Frequently ignored ({ignored}x) — urgency suppressed")
    elif ignored >= IGNORE_DECAY_THRESHOLD:
        notes.append(f"Ignored {ignored}x — urgency downgraded once")
    if self_res_rate is not None and self_res_rate >= 0.60:
        notes.append(f"Self-resolves {self_res_rate*100:.0f}% of the time — intervention may not be needed")
    if useful_rate is not None and total >= MIN_EMPIRICAL_SAMPLES and useful_rate < REC_USEFUL_FLOOR:
        notes.append(f"Recommendation historically low value ({useful_rate*100:.0f}% useful)")

    return {
        "trust_level":    trust_level,
        "ignored_count":  ignored,
        "total_outcomes": total,
        "real_rate":      real_rate,
        "useful_rate":    useful_rate,
        "notes":          notes,
    }