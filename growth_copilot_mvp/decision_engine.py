"""decision_engine.py — Layer 4: Decision consequence modeling.

New in this version:
    - consequence_model(): computes expected_value, blast_radius, time_sensitivity,
      operator_burden for every decision
    - wait_and_observe state: when evidence is insufficient, system says so explicitly
    - escalation_friction: chronic unresolved signals suppress urgency over time
    - recommendation_decay: repeated same recommendation weakens over time
    - Decision now includes a full consequence dict shown in UI
"""
from typing import Dict, List, Optional

URGENCY_DISPLAY = {
    "immediate":       "Act today",
    "this_week":       "Act this week",
    "monitor":         "Monitor",
    "wait_and_observe": "Wait and observe",
    "insufficient_evidence": "Insufficient evidence",
}
URGENCY_COLOR = {
    "immediate":            "#d32f2f",
    "this_week":            "#f57c00",
    "monitor":              "#388e3c",
    "wait_and_observe":     "#1565c0",
    "insufficient_evidence": "#757575",
}
HEDGE = {
    ("High",   "immediate"):  "",
    ("High",   "this_week"):  "",
    ("High",   "monitor"):    "",
    ("High",   "wait_and_observe"): "",
    ("Medium", "immediate"):  "Consider: ",
    ("Medium", "this_week"):  "Consider: ",
    ("Medium", "monitor"):    "",
    ("Medium", "wait_and_observe"): "",
    ("Low",    "immediate"):  "Low confidence — verify first: ",
    ("Low",    "this_week"):  "Low confidence — ",
    ("Low",    "monitor"):    "",
    ("Low",    "wait_and_observe"): "Insufficient evidence — ",
    ("Low",    "insufficient_evidence"): "",
}


def _get_trend(i) -> Dict:
    return getattr(i, "trend", {})


def _apply_hedge(action: str, conf_label: str, urgency: str) -> str:
    prefix = HEDGE.get((conf_label, urgency), "")
    if prefix:
        return prefix + action[0].lower() + action[1:]
    return action


def _get_direction(insights) -> str:
    dirs = {_get_trend(i).get("direction", "stable") for i in insights}
    if "worsening" in dirs:  return "worsening"
    if "recovering" in dirs: return "recovering"
    return "stable"


# ---------------------------------------------------------------------------
# Consequence modeling
# ---------------------------------------------------------------------------

def consequence_model(
    cluster: Dict,
    decision: Dict,
    causal_links: List[Dict],
) -> Dict:
    """Model the consequences of acting (or not acting) on this signal.

    Returns:
        expected_value      str   — expected upside of recommended action
        blast_radius        str   — who/what is affected if action is wrong
        time_sensitivity    str   — how much does delay cost?
        operator_burden     str   — low / medium / high (effort to execute)
        wait_cost           str   — cost of waiting 24-48h before acting
        inaction_risk       str   — what happens if we don't act at all?
        confidence_adjusted str   — plain-language confidence-adjusted framing
    """
    conf        = cluster.get("confidence", {})
    conf_label  = conf.get("label", "Medium")
    conf_score  = conf.get("score", 50)
    insights    = cluster.get("insights", [])
    title       = cluster.get("title", "").lower()
    urgency     = decision.get("urgency", "monitor")
    direction   = _get_direction(insights)
    days_active = max((_get_trend(i).get("days_active", 1) for i in insights), default=1)
    reversible  = decision.get("reversibility", "reversible") == "reversible"
    has_causal  = len(causal_links) > 0

    # Expected value of action
    if "tiktok" in title:
        if direction == "worsening" and days_active >= 5:
            expected_value = "Pausing spend stops compounding loss from low-quality installs. Audit identifies root cause within 1-2 days."
        elif direction == "recovering":
            expected_value = "Signal improving on its own — intervention may disrupt natural recovery. Value of waiting is high."
        else:
            expected_value = "Early intervention may prevent further funnel degradation. Upside moderate if onboarding bug is found."
    elif "onboarding" in title:
        expected_value = "Rollback or flag disable could restore conversion within hours if a recent deploy is the cause."
    elif "acquisition" in title:
        expected_value = "Investigation clarifies whether spike is signal or noise. Low upside if anomaly is one-time."
    else:
        expected_value = "Unknown — signal pattern is novel."

    # Blast radius (who is affected if action is wrong)
    # Use actual signal title for blast radius description
    src_label = title.replace(" failure","").replace(" regression","").replace(" anomaly","")                      .replace(" divergence","").strip().title() if title else "The affected channel"
    if "tiktok" in title or any(getattr(i,"detector","") == "funnel_drop" for i in insights):
        blast_radius = f"{src_label} spend reduction affects marketing budget and may temporarily reduce install volume."
    elif "onboarding" in title:
        blast_radius = "Rollback could revert recent product improvements alongside the regression."
    elif "acquisition" in title:
        blast_radius = "Campaign adjustments may reduce volume during investigation window."
    else:
        blast_radius = "Unknown scope — limit initial action to investigation only."

    # Time sensitivity
    if direction == "worsening" and days_active >= 7:
        time_sensitivity = "High — signal has been worsening for over a week. Each day of delay compounds activation losses."
    elif direction == "worsening" and days_active >= 3:
        time_sensitivity = "Moderate — signal is worsening but still early. 24-48h validation window is acceptable."
    elif direction == "recovering":
        time_sensitivity = "Low — signal is already improving. Delay is the lower-risk choice."
    elif days_active < 3:
        time_sensitivity = "Low — signal is too new to establish persistence. Observe for 2 more days."
    else:
        time_sensitivity = "Moderate — ongoing stable signal. Act within the week."

    # Operator burden
    cost = decision.get("intervention_cost", "low")
    if cost == "high":
        operator_burden = "High — requires engineering deployment or significant process change."
    elif cost == "medium":
        operator_burden = "Medium — requires cross-team coordination."
    else:
        operator_burden = "Low — investigation or spend adjustment can be done by one person."

    # Wait cost (cost of 24-48h delay)
    if urgency == "immediate" and direction == "worsening":
        wait_cost = "Each day of delay likely costs additional activation failures at current degradation rate."
    elif urgency == "monitor" or direction == "recovering":
        wait_cost = "Minimal — signal is either stabilising or already improving."
    else:
        wait_cost = "Low to moderate — 24-48h observation window unlikely to materially change outcome."

    # Inaction risk
    if direction == "worsening" and days_active >= 5:
        src_lbl = _source_from_title(title) if title else "Channel"
        inaction_risk = f"Continued regression erodes {src_lbl} ROI and may affect long-term cohort quality."
    elif direction == "recovering":
        inaction_risk = "Low — signal appears to be self-resolving. Monitoring is the appropriate posture."
    elif days_active < 3:
        inaction_risk = "Low — insufficient persistence to establish real impact."
    else:
        inaction_risk = "Moderate — unresolved signals can mask larger issues if left unmonitored."

    # Confidence-adjusted framing
    if direction == "recovering" and urgency in ("monitor", "wait_and_observe"):
        conf_frame = f"Signal improving ({conf_score}/100 confidence) — intervention risk likely exceeds inaction risk at this stage. Watch and confirm."
    elif conf_score >= 75:
        conf_frame = f"High confidence ({conf_score}/100) — evidence is strong enough to act on directly."
    elif conf_score >= 55:
        conf_frame = f"Medium confidence ({conf_score}/100) — evidence is suggestive but not conclusive. Validate before committing resources."
    else:
        conf_frame = f"Low confidence ({conf_score}/100) — evidence is weak. Prefer low-cost investigation over intervention."

    return {
        "expected_value":   expected_value,
        "blast_radius":     blast_radius,
        "time_sensitivity": time_sensitivity,
        "operator_burden":  operator_burden,
        "wait_cost":        wait_cost,
        "inaction_risk":    inaction_risk,
        "confidence_frame": conf_frame,
    }


# ---------------------------------------------------------------------------
# Escalation friction
# ---------------------------------------------------------------------------

def _escalation_friction(days_active: int, direction: str, conf_score: int) -> int:
    """Return urgency downgrade steps due to chronic unresolved signals.

    Long-running stable signals should generate less urgency over time —
    if nobody acted after 14 days, either it resolved itself or it's structural.
    """
    if direction == "worsening":
        return 0  # never suppress worsening signals
    if days_active >= 21 and direction == "stable":
        return 2  # downgrade two levels: immediate → monitor
    if days_active >= 14 and direction == "stable":
        return 1  # downgrade one level
    return 0


def _apply_friction(urgency: str, friction: int) -> str:
    order = ["immediate", "this_week", "monitor", "wait_and_observe"]
    if urgency not in order:
        return urgency
    idx = min(order.index(urgency) + friction, len(order) - 1)
    return order[idx]


# ---------------------------------------------------------------------------
# Urgency computation
# ---------------------------------------------------------------------------

def _compute_urgency(
    conf_score:         int,
    conf_label:         str,
    days_active:        int,
    direction:          str,
    base_urgency:       str,
    reversible:         bool = True,
    detector_agreement: bool = True,
) -> str:
    urgency = base_urgency

    # Insufficient evidence state
    if conf_score < 35 and days_active < 3:
        return "insufficient_evidence"

    # Low confidence rules
    if conf_label == "Low":
        urgency = "this_week" if days_active >= 7 else "wait_and_observe"

    # Recovering signals downgrade
    elif direction == "recovering":
        if urgency == "immediate":   urgency = "this_week"
        elif urgency == "this_week": urgency = "monitor"

    # Short-lived + uncertain
    elif days_active < 3 and conf_label != "High":
        urgency = "wait_and_observe"

    # Medium confidence caps immediate
    elif conf_label == "Medium" and urgency == "immediate":
        urgency = "this_week"

    # No detector agreement downgrades
    if not detector_agreement and urgency == "immediate":
        urgency = "this_week"

    # Irreversible + not High
    if not reversible and conf_label != "High" and urgency == "immediate":
        urgency = "this_week"

    # Escalation friction for chronic stable signals
    friction = _escalation_friction(days_active, direction, conf_score)
    urgency  = _apply_friction(urgency, friction)

    return urgency


# ---------------------------------------------------------------------------
# Decision builders
# ---------------------------------------------------------------------------

_BRAND_CAPS = {
    "tiktok": "TikTok", "google_ads": "Google Ads", "google ads": "Google Ads",
    "google": "Google", "facebook": "Facebook", "instagram": "Instagram",
    "reddit": "Reddit", "twitter": "Twitter", "snapchat": "Snapchat",
    "youtube": "YouTube", "linkedin": "LinkedIn", "organic": "Organic",
    "paid social": "Paid Social", "paid_social": "Paid Social",
}

def _source_from_title(title: str) -> str:
    """Extract source/channel name from signal title, preserving brand caps."""
    clean = title.lower()
    for suffix in [
        " activation failure", " activation regression", " activation drop",
        " funnel drop", " funnel regression", " cohort divergence",
        " cohort regression", " regression", " anomaly", " failure",
        " drop", " divergence", " signal", " activation",
    ]:
        clean = clean.replace(suffix, "")
    clean = clean.strip()
    return _BRAND_CAPS.get(clean, clean.title()) or "the affected channel"


def _decide_tiktok(insights, causal_links, confidence, title: str = "") -> Dict:
    conf_label  = confidence.get("label", "Medium")
    conf_score  = confidence.get("score", 50)
    det_agree   = confidence.get("detector_agreement", False)
    direction   = _get_direction(insights)
    days_active = max((_get_trend(i).get("days_active", 1) for i in insights), default=1)
    has_causal  = any(l["link_type"] == "funnel_drop_drives_completion_gap" for l in causal_links)

    src = _source_from_title(title) if title else "the affected channel"

    if direction == "worsening" and days_active >= 5:
        action       = f"Temporarily reduce {src} spend and audit the onboarding_complete to first_action step for changes shipped in the last 7 days."
        base_urgency = "immediate"
        rec_conf     = "medium-high"
    elif days_active >= 3:
        action       = f"Freeze onboarding changes for {src} cohorts and run a session recording review on the onboarding_complete to first_action step."
        base_urgency = "immediate"
        rec_conf     = "medium"
    else:
        action       = f"Observe {src} onboarding step conversion for 2 more days before escalating."
        base_urgency = "wait_and_observe"
        rec_conf     = "low-medium"

    urgency = _compute_urgency(conf_score, conf_label, days_active, direction,
                                base_urgency, reversible=True,
                                detector_agreement=det_agree)
    note = " The step-level drop is a likely contributor to the overall completion gap." if has_causal else ""

    return {
        "action":                  _apply_hedge(action, conf_label, urgency),
        "rationale":               f"{src} users are completing the activation step at a significantly lower rate than baseline for approximately {days_active} days.{note}",
        "urgency":                 urgency,
        "recommendation_confidence": rec_conf,
        "intervention_cost":       "low",
        "reversibility":           "reversible",
        "false_positive_risk":     f"If the drop is caused by a seasonal audience shift, pausing {src} spend may reduce volume unnecessarily. Recommend a 24hr hold before full pause.",
        "owner":                   "product + marketing",
        "blockers":                [f"Session recordings for {src} cohort", "Deploy history for onboarding changes in last 7 days"],
        "success_metric":          f"{src} onboarding_complete to first_action rate returns above baseline within 7 days",
    }


def _decide_onboarding(insights, causal_links, confidence) -> Dict:
    conf_label  = confidence.get("label", "Medium")
    conf_score  = confidence.get("score", 50)
    det_agree   = confidence.get("detector_agreement", False)
    direction   = _get_direction(insights)
    days_active = max((_get_trend(i).get("days_active", 1) for i in insights), default=1)
    base_urgency = "immediate" if direction == "worsening" else "this_week"
    urgency      = _compute_urgency(conf_score, conf_label, days_active, direction,
                                     base_urgency, reversible=True,
                                     detector_agreement=det_agree)
    return {
        "action":                  _apply_hedge("Review all onboarding flow changes deployed in the last 7 days. Consider rolling back the most recent change as a diagnostic step.", conf_label, urgency),
        "rationale":               "Onboarding conversion has dropped, likely linked to a recent code or config change.",
        "urgency":                 urgency,
        "recommendation_confidence": "medium",
        "intervention_cost":       "medium",
        "reversibility":           "reversible",
        "false_positive_risk":     "Rollback may revert unrelated improvements. Prefer feature-flag disable over full rollback where possible.",
        "owner":                   "engineering",
        "blockers":                ["Deploy history and feature flag audit"],
        "success_metric":          "Onboarding completion rate returns to baseline within 5 days",
    }


def _decide_acquisition(insights, causal_links, confidence) -> Dict:
    conf_label  = confidence.get("label", "Medium")
    conf_score  = confidence.get("score", 50)
    det_agree   = confidence.get("detector_agreement", False)
    has_funnel  = any(l["link_type"] == "dau_anomaly_upstream_of_funnel" for l in causal_links)
    direction   = _get_direction(insights)
    days_active = max((_get_trend(i).get("days_active", 1) for i in insights), default=1)

    if has_funnel:
        action       = "Review TikTok campaign targeting and creative quality — the install spike coincides with a funnel regression, which may suggest lower-intent traffic."
        base_urgency = "this_week"
        rec_conf     = "medium"
        fp           = "Install spike may be driven by organic virality. Verify channel breakdown before adjusting spend."
    elif direction == "recovering":
        action       = "Monitor install trend for 3 more days — anomaly appears to be normalising."
        base_urgency = "monitor"
        rec_conf     = "high"
        fp           = "Low — monitoring has minimal cost."
    else:
        action       = "Investigate acquisition channel mix for the anomaly date. Check for paid campaign spikes, viral content, or attribution issues."
        base_urgency = "this_week"
        rec_conf     = "low-medium"
        fp           = "Anomaly may be a one-time data artifact. Confirm with a second day of data before acting."

    urgency = _compute_urgency(conf_score, conf_label, days_active, direction,
                                base_urgency, reversible=True,
                                detector_agreement=det_agree)
    return {
        "action":                  _apply_hedge(action, conf_label, urgency),
        "rationale":               "Install volume deviated significantly from weekday-adjusted baseline.",
        "urgency":                 urgency,
        "recommendation_confidence": rec_conf,
        "intervention_cost":       "low",
        "reversibility":           "reversible",
        "false_positive_risk":     fp,
        "owner":                   "marketing",
        "blockers":                ["Campaign spend data and channel breakdown for anomaly date"],
        "success_metric":          "Install volume returns to weekday-adjusted baseline within 7 days",
    }


def _decide_generic(insights, causal_links, confidence) -> Dict:
    conf_label  = confidence.get("label", "Medium")
    conf_score  = confidence.get("score", 50)
    det_agree   = confidence.get("detector_agreement", False)
    direction   = _get_direction(insights)
    days_active = max((_get_trend(i).get("days_active", 1) for i in insights), default=1)
    urgency     = _compute_urgency(conf_score, conf_label, days_active, direction,
                                    "this_week", reversible=True,
                                    detector_agreement=det_agree)
    return {
        "action":                  "Investigate the flagged signals and compare against recent product and marketing changes.",
        "rationale":               "Multiple signals detected without a clear pattern match.",
        "urgency":                 urgency,
        "recommendation_confidence": "low",
        "intervention_cost":       "low",
        "reversibility":           "reversible",
        "false_positive_risk":     "Unknown — more context needed before acting.",
        "owner":                   "data",
        "blockers":                [],
        "success_metric":          "Signal drops below detection threshold within 14 days",
    }




# ---------------------------------------------------------------------------
# Editorial observation — one analyst sentence per situation
# ---------------------------------------------------------------------------

def editorial_observation(
    cluster: Dict,
    decision: Dict,
    causal_links: List[Dict],
    signal_record: Dict = None,
) -> str:
    """Generate one sharp, data-driven editorial observation.

    Fully generic — works on any signal from any data source.
    Reads actual metrics, source names, days, recurrence, and
    detector agreement from the cluster and signal record.
    Never hardcodes source names like "TikTok".
    """
    conf       = cluster.get("confidence", {})
    insights   = cluster.get("insights", [])
    title      = cluster.get("title", "")
    direction  = _get_direction(insights)
    days       = max((_get_trend(i).get("days_active", 1) for i in insights), default=1)
    urgency    = decision.get("urgency", "monitor")
    det_agree  = conf.get("detector_agreement", False)
    recur      = (signal_record or {}).get("recurrence_count", 0)
    peak_escl  = (signal_record or {}).get("peak_escalation_level", 0)
    ignored    = (signal_record or {}).get("ignored_count", 0)
    has_causal = len(causal_links) > 0
    conf_score = conf.get("score", 50)
    conf_label = conf.get("label", "Medium")

    # ── Extract real metric values from insights ──────────────────
    # Pull the primary insight's raw metrics for concrete numbers
    primary_ins = insights[0] if insights else None
    rm = getattr(primary_ins, "raw_metrics", {}) if primary_ins else {}

    # Source name — use real name from signal title if available
    # Title format is typically "Source activation failure" or "Source cohort divergence"
    title_words = title.replace(" failure","").replace(" regression","")                        .replace(" anomaly","").replace(" divergence","").strip()
    source_name = title_words if title_words else "the affected channel"

    # Concrete rate drop if available
    rate_context = ""
    if rm.get("current_rate") is not None and rm.get("baseline_rate") is not None:
        cur  = rm["current_rate"]  * 100
        base = rm["baseline_rate"] * 100
        drop = base - cur
        if drop > 0:
            rate_context = f"{drop:.1f} percentage point drop (currently {cur:.1f}% vs {base:.1f}% baseline)"
        else:
            gain = cur - base
            rate_context = f"{gain:.1f} percentage point improvement (currently {cur:.1f}% vs {base:.1f}% baseline)"
    elif rm.get("worst_rate") is not None and rm.get("others_rate") is not None:
        wr  = rm["worst_rate"]  * 100
        ors = rm["others_rate"] * 100
        gap = ors - wr
        rate_context = f"{gap:.1f}pp gap vs other sources ({wr:.1f}% vs {ors:.1f}%)"

    # ── Recurrence — highest credibility signal ───────────────────
    if recur >= 4 and direction == "worsening":
        return (f"This pattern has recurred {recur + 1} times. "
                f"Recurrence at this frequency suggests a systemic driver — "
                f"not a one-time incident.")

    if recur >= 2 and direction == "stable" and ignored >= 2:
        return ("Signal has appeared and resolved without intervention multiple times. "
                "Historical self-resolution rate is high — monitoring is the appropriate posture.")

    # ── Detector agreement — strong evidence signal ───────────────
    if det_agree and has_causal and direction == "worsening":
        if rate_context:
            return (f"Two independent detectors agree on a {rate_context}. "
                    f"Causal analysis points to the funnel step, not volume — "
                    f"consistent with a product or creative change.")
        return ("Two independent detectors agree. "
                "Causal analysis suggests a product-level issue rather than "
                "external noise.")

    if det_agree and direction == "worsening" and days >= 7:
        if rate_context:
            return (f"A {rate_context} has persisted for {days} days "
                    f"across two independent detectors. "
                    f"At this persistence level, the probability of a real regression "
                    f"substantially exceeds noise.")
        return (f"Signal confirmed across two detectors for {days} consecutive days. "
                f"Persistence at this level substantially exceeds baseline noise.")

    if det_agree and direction == "recovering":
        if peak_escl >= 1:
            return ("Both detectors are now showing recovery following the escalation. "
                    "The system recommends 3 more days of monitoring before declaring resolution.")
        return ("Multiple detectors agree the signal is improving. "
                "Intervention risk now exceeds inaction risk.")

    # ── Single detector — calibrate confidence ────────────────────
    if not det_agree and urgency == "immediate":
        return ("Single-detector escalation with high confidence. "
                "Independent confirmation is absent — treat as probable, not certain. "
                "A 24-hour hold before acting is reasonable.")

    if not det_agree and direction == "worsening" and days <= 2:
        return ("Signal is new and unconfirmed by a second detector. "
                "At this age, observe for 24-48 hours before acting — "
                "early signals have a higher false positive rate.")

    # ── Direction-specific observations ──────────────────────────
    if direction == "recovering" and peak_escl >= 1:
        if rate_context:
            return (f"Following the escalation, the signal is recovering: {rate_context}. "
                    f"If an intervention was applied, it appears to be working.")
        return ("The signal is recovering following the escalation. "
                "If an intervention was applied, it appears to be working.")

    if direction == "recovering" and urgency in ("monitor", "wait_and_observe"):
        return "Signal is self-correcting. The system recommends restraint — let the recovery complete."

    if direction == "stable" and days >= 14:
        return (f"Signal has been present for {days} days without worsening or resolving. "
                f"This duration suggests a structural baseline shift rather than an acute incident.")

    if direction == "stable" and days >= 7 and conf_score >= 65:
        return (f"Signal has persisted for {days} days at {conf_score}/100 confidence "
                f"without escalating. Monitoring is appropriate — the system will escalate "
                f"if direction changes.")

    # ── Causal context without detector agreement ─────────────────
    if has_causal and direction == "worsening" and not det_agree:
        if rate_context:
            return (f"A {rate_context} coincides with correlated signals across the funnel. "
                    f"The pattern suggests a shared root cause, though a single detector "
                    f"hasn't confirmed it independently.")
        return ("Correlated signals suggest a shared root cause. "
                "Single-detector confirmation only — treat as a hypothesis.")

    # ── Volume anomaly ────────────────────────────────────────────
    if rm.get("actual_installs") is not None:
        act = rm["actual_installs"]
        exp = rm.get("expected_installs", act)
        pct = abs(act - exp) / max(exp, 1) * 100
        if pct >= 20 and has_causal:
            return (f"Volume anomaly ({pct:.0f}% from expected) is coinciding with a funnel signal. "
                    f"This pattern is consistent with a traffic quality shift — "
                    f"not a platform outage.")
        if pct >= 20:
            return (f"Volume is {pct:.0f}% from expected. Without a correlated funnel signal, "
                    f"this is likely a measurement or attribution artifact.")

    # ── High confidence, clear urgency ───────────────────────────
    if conf_score >= 75 and urgency == "immediate":
        if rate_context:
            return (f"High confidence ({conf_score}/100) on a {rate_context}. "
                    f"The evidence threshold for action has been crossed.")
        return (f"High confidence ({conf_score}/100). "
                f"The evidence threshold for immediate action has been crossed.")

    if conf_score >= 70 and direction == "worsening" and days >= 5:
        return (f"Signal at {conf_score}/100 confidence, worsening over {days} days. "
                f"Evidence is sufficient to act — further observation increases cost, not certainty.")

    # ── Low confidence hedge ──────────────────────────────────────
    if conf_score < 50 and direction == "worsening":
        return (f"Signal confidence is {conf_score}/100. "
                f"Evidence exists but is not yet conclusive — "
                f"a 48-hour observation window is appropriate before committing resources.")

    return ""

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def make_decision(cluster: Dict, causal_links: List[Dict]) -> Dict:
    insights   = cluster.get("insights", [])
    title      = cluster.get("title", "").lower()
    confidence = cluster.get("confidence", {})

    # Route by signal type — check insight detector types, not source names
    # This makes decisioning work for any data source, not just synthetic
    insight_types = set()
    for ins in insights:
        det = getattr(ins, "detector", "")
        if det:
            insight_types.add(det)
        # Also check summary for signal type hints
        summary = getattr(ins, "summary", "").lower()
        if "funnel" in summary or "completion" in summary or "activation" in summary:
            insight_types.add("funnel_drop")
        if "install" in summary or "volume" in summary or "anomaly" in summary:
            insight_types.add("anomaly")
        if "cohort" in summary or "diverge" in summary or "source" in summary:
            insight_types.add("cohort_divergence")

    # Also check title for legacy synthetic data compatibility
    if "tiktok" in title or "funnel_drop" in insight_types:
        decision = _decide_tiktok(insights, causal_links, confidence, title=cluster.get("title",""))
    elif "onboarding" in title:
        decision = _decide_onboarding(insights, causal_links, confidence)
    elif "acquisition" in title or "installs" in title or "anomaly" in insight_types:
        decision = _decide_acquisition(insights, causal_links, confidence)
    else:
        decision = _decide_generic(insights, causal_links, confidence)

    # Attach consequence model
    decision["consequences"] = consequence_model(cluster, decision, causal_links)

    decision["urgency_display"] = URGENCY_DISPLAY.get(decision["urgency"], decision["urgency"])
    decision["urgency_color"]   = URGENCY_COLOR.get(decision["urgency"], "#555")
    return decision


def get_editorial_observation(cluster, decision, causal_links, signal_record=None):
    """Public wrapper — called from app.py after signal_record is available."""
    return editorial_observation(cluster, decision, causal_links, signal_record)