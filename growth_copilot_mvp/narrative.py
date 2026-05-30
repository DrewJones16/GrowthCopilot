"""Presentation-layer narrative helpers.

Transforms CandidateInsight objects into founder-facing prose:
  - business_headline: business interpretation instead of metric comparison
  - confidence_narrative: confidence statement referencing the actual signals
    (sample size, MAD ratio, z-score, effect size)
  - ranking_explanation: plain English on why the ranker put this insight where
    it did, by inspecting the candidate's structured attributes

Reads only. No detector or ranker logic lives here. The ranker axis order is
mirrored as a description, not imported, to keep this file decoupled.
"""
from .schema import CandidateInsight


def _src(c: CandidateInsight) -> str:
    parts = c.id.split(":")
    return parts[1] if len(parts) >= 2 else "the affected segment"


# --- business headline -----------------------------------------------------

def business_headline(c: CandidateInsight) -> str:
    src = _src(c)
    rm = c.raw_metrics or {}
    if c.type == "funnel_drop":
        return (
            f"**{src} acquisition is converting through the funnel more slowly "
            f"than it has all month.** Users from this channel are stalling at "
            f"one specific step, and the size of the drop puts it well above "
            f"normal day-to-day noise — meaning a real change in user behavior "
            f"or in the product has occurred."
        )
    if c.type == "cohort_divergence":
        return (
            f"**{src} traffic isn't activating the way the rest of your users "
            f"do.** The gap is wide enough that the channel is likely "
            f"mismatched to your activation flow — either the audience differs "
            f"from what you expected, or the creative is bringing in users with "
            f"different intent than they find in the product."
        )
    if c.type == "anomaly":
        date = rm.get("date", "the flagged day")
        return (
            f"**Installs on {date} broke from their normal weekday pattern.** "
            f"Worth checking whether it was a real event (a campaign, press "
            f"hit, release, outage) or a tracking artifact before drawing any "
            f"business conclusion."
        )
    return c.summary


# --- confidence narrative --------------------------------------------------

def confidence_narrative(c: CandidateInsight) -> str:
    ci = c.confidence_inputs
    rm = c.raw_metrics or {}
    weak = []
    if ci.sample_size < 100:
        weak.append(f"the sample is small (n={ci.sample_size})")
    if ci.effect_size < 0.05:
        weak.append(f"the effect is small ({ci.effect_size})")
    if ci.baseline_stability != "stable":
        weak.append(f"the baseline was {ci.baseline_stability}")

    signals = [f"sample size n={ci.sample_size}"]
    if rm.get("mad_ratio") is not None:
        signals.append(f"observed change is {rm['mad_ratio']}x baseline MAD")
    if "z_score" in rm:
        signals.append(f"two-proportion z={rm['z_score']}")
    if "absolute_drop" in rm:
        signals.append(f"effect size {round(rm['absolute_drop'] * 100, 1)}pp")
    elif "gap" in rm:
        signals.append(f"effect size {round(rm['gap'] * 100, 1)}pp")
    signal_str = "; ".join(signals)

    if not weak:
        return (
            f"**High.** All three drivers — sample size, effect size, and "
            f"baseline stability — clear their thresholds. Signals: {signal_str}."
        )
    if len(weak) == 1:
        return (
            f"**Medium.** {weak[0].capitalize()}, but the other signals are "
            f"solid. Signals: {signal_str}."
        )
    return (
        f"**Low.** " + "; ".join(s.capitalize() for s in weak) + ". "
        f"Signals: {signal_str}."
    )


# --- ranking explanation ---------------------------------------------------

_RANK_AXES_DESC = (
    "impact tier first, then novelty (new beats ongoing), then baseline "
    "stability, then sample size, then alignment with the founder's focus"
)

_TIER_RANK = {"large": 3, "medium": 2, "small": 1, "unknown": 0}
_NOVELTY_RANK = {"new": 3, "ongoing_worsening": 2, "ongoing_improving": 1, "ongoing_unchanged": 0}
_BASELINE_RANK = {"stable": 2, "noisy": 1, "unknown": 0}


def ranking_explanation(c: CandidateInsight, ranked: list, position: int) -> str:
    n = len(ranked)
    tier = c.computed_impact_tier
    novelty = c.novelty_vs_prior
    stab = c.confidence_inputs.baseline_stability
    nsize = c.confidence_inputs.sample_size

    if position == 0:
        if n == 1:
            return (
                "This is the only insight today that cleared the noise and "
                "sample-size gates."
            )
        second = ranked[1]
        if tier != second.computed_impact_tier:
            reason = (
                f"Computed impact tier is **{tier}**, higher than the next "
                f"candidate (**{second.computed_impact_tier}**). Impact is the "
                f"ranker's top axis."
            )
        elif novelty != second.novelty_vs_prior:
            reason = (
                f"Same impact tier as the next candidate, but this one is "
                f"**{novelty}** vs **{second.novelty_vs_prior}** — newer "
                f"problems get priority."
            )
        elif stab != second.confidence_inputs.baseline_stability:
            reason = (
                f"Impact and novelty tie with the next candidate, but this "
                f"one sits on a **{stab}** baseline (next is "
                f"**{second.confidence_inputs.baseline_stability}**)."
            )
        elif nsize != second.confidence_inputs.sample_size:
            reason = (
                f"Higher-tier axes tied; sample size (**{nsize}** vs "
                f"**{second.confidence_inputs.sample_size}**) was the tiebreaker."
            )
        else:
            reason = "All ranked axes tied; this one happened to land first."
        return f"Ranked #1 of {n}. {reason} The ranker weighs {_RANK_AXES_DESC}."

    # Non-#1: walk axes in priority order; report the FIRST axis where this
    # candidate is strictly weaker than the top. That's the actual decider.
    top = ranked[0]
    if _TIER_RANK[tier] < _TIER_RANK[top.computed_impact_tier]:
        return (
            f"Ranked #{position + 1} of {n}. Lower computed impact tier "
            f"(**{tier}** vs **{top.computed_impact_tier}**). Impact is the "
            f"ranker's top axis."
        )
    if _NOVELTY_RANK[novelty] < _NOVELTY_RANK[top.novelty_vs_prior]:
        return (
            f"Ranked #{position + 1} of {n}. Same impact tier as the top "
            f"candidate, but weaker novelty (**{novelty}** vs "
            f"**{top.novelty_vs_prior}**)."
        )
    if _BASELINE_RANK[stab] < _BASELINE_RANK[top.confidence_inputs.baseline_stability]:
        return (
            f"Ranked #{position + 1} of {n}. Tied on impact and novelty with "
            f"the top candidate, but a **{stab}** baseline (top is "
            f"**{top.confidence_inputs.baseline_stability}**) pushed it down."
        )
    if nsize < top.confidence_inputs.sample_size:
        return (
            f"Ranked #{position + 1} of {n}. Tied with the top candidate on "
            f"every higher axis; smaller sample (**{nsize}** vs "
            f"**{top.confidence_inputs.sample_size}**) was the tiebreaker."
        )
    return (
        f"Ranked #{position + 1} of {n}. Tied on every ranked axis with the "
        f"top candidate; ordering came down to a final tiebreaker."
    )
