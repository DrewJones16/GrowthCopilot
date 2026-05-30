"""attention.py — three-tier attention architecture.

Tier 1 — Surfaced operational signals
    High attention cost. Shown in daily briefing.
    Requires: surface_score >= SURFACE_THRESHOLD
    AND: cluster passes all suppression checks

Tier 2 — Background tracked cognition
    Tracked in registry. Influences future escalation and causal reasoning.
    NOT shown in briefing. Shown in calibration console only.
    Requires: surface_score >= BACKGROUND_THRESHOLD

Tier 3 — Ephemeral noise
    Not persisted. Discarded immediately.
    Below BACKGROUND_THRESHOLD.

Surface score combines:
    confidence_score * confidence_weight
    urgency_score    * urgency_weight
    persistence      * persistence_weight
    detector_agree   * agreement_weight

This creates a single attention budget per run.
"""
from typing import Dict, List, Any, Tuple

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

SURFACE_THRESHOLD    = 32.0  # above this: shown in briefing
BACKGROUND_THRESHOLD = 18.0  # above this: tracked silently
# below BACKGROUND_THRESHOLD: ephemeral noise, discarded

# Max clusters surfaced per run (attention budget)
MAX_SURFACED_CLUSTERS = 2

# ---------------------------------------------------------------------------
# Surface score weights
# ---------------------------------------------------------------------------

CONFIDENCE_WEIGHT  = 0.35
URGENCY_WEIGHT     = 0.30
PERSISTENCE_WEIGHT = 0.20
AGREEMENT_WEIGHT   = 0.15

# Urgency scores
URGENCY_SCORES = {
    "immediate":  1.00,
    "this_week":  0.60,
    "monitor":    0.20,
}

# Persistence scores (days_active → score)
def _persistence_score(days: int) -> float:
    if days >= 14: return 1.00
    if days >= 7:  return 0.80
    if days >= 3:  return 0.55
    if days >= 1:  return 0.30
    return 0.10


def surface_score(cluster: Dict, decision: Dict) -> float:
    """Compute attention score for a cluster.

    Higher = more deserving of operator attention.
    """
    conf       = cluster.get("confidence", {})
    conf_score = conf.get("score", 50) / 100.0      # 0-1
    det_agree  = 1.0 if conf.get("detector_agreement") else 0.0

    urgency    = decision.get("urgency", "monitor")
    urg_score  = URGENCY_SCORES.get(urgency, 0.20)

    # Persistence: max days_active across insights
    insights   = cluster.get("insights", [])
    days_active = max(
        (getattr(ins, "trend", {}).get("days_active", 1) for ins in insights),
        default=1,
    )
    pers_score = _persistence_score(days_active)

    score = (
        conf_score  * CONFIDENCE_WEIGHT  * 100 +
        urg_score   * URGENCY_WEIGHT     * 100 +
        pers_score  * PERSISTENCE_WEIGHT * 100 +
        det_agree   * AGREEMENT_WEIGHT   * 100
    )
    return round(score, 1)


# ---------------------------------------------------------------------------
# Tier classification
# ---------------------------------------------------------------------------

def classify_clusters(
    clusters: List[Dict],
    decisions: List[Dict],
) -> Tuple[List[Dict], List[Dict]]:
    """Split clusters into surfaced (Tier 1) and background (Tier 2).

    Returns:
        surfaced    List[Dict]  — shown in briefing (with surface_score attached)
        background  List[Dict]  — tracked silently
    """
    scored = []
    for cluster, decision in zip(clusters, decisions):
        s = surface_score(cluster, decision)
        cluster["surface_score"] = s
        cluster["attention_tier"] = (
            "surfaced"   if s >= SURFACE_THRESHOLD else
            "background" if s >= BACKGROUND_THRESHOLD else
            "ephemeral"
        )
        scored.append((cluster, s))

    # Sort by surface score descending
    scored.sort(key=lambda x: x[1], reverse=True)

    surfaced   = []
    background = []

    for cluster, s in scored:
        tier = cluster["attention_tier"]
        if tier == "surfaced" and len(surfaced) < MAX_SURFACED_CLUSTERS:
            surfaced.append(cluster)
        elif tier in ("surfaced", "background"):
            # Demote to background if over budget or below threshold
            cluster["attention_tier"] = "background"
            background.append(cluster)
        # ephemeral: discard entirely

    return surfaced, background


def background_summary(background: List[Dict]) -> str:
    """One-line summary of background signals for calibration console."""
    if not background:
        return ""
    titles = [c["title"] for c in background]
    if len(titles) == 1:
        return f"1 background signal tracked: {titles[0]}"
    return f"{len(titles)} background signals tracked: {', '.join(titles)}"


def attention_report(surfaced: List[Dict], background: List[Dict]) -> Dict:
    """Summary dict for the calibration console."""
    return {
        "surfaced_count":     len(surfaced),
        "background_count":   len(background),
        "surfaced_titles":    [c["title"] for c in surfaced],
        "background_titles":  [c["title"] for c in background],
        "surface_scores":     {c["title"]: c.get("surface_score", 0)
                               for c in surfaced + background},
        "max_surface_score":  max((c.get("surface_score", 0)
                                   for c in surfaced + background), default=0),
    }