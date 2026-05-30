"""End-to-end demo. Run from the parent directory:

    python -m growth_copilot_mvp.run_demo
"""
import json
from .synth_data import generate_events
from .aggregations import funnel_step_table, daily_installs, source_funnel_completion
from .detectors import detect_funnel_drops, detect_source_divergence, detect_dau_anomaly
from .ranker import rank
from .briefing import assemble_briefing_input
from .verifier import verify_briefing


def section(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def run():
    section("STEP 1. Generate synthetic events")
    print("90 days, ~120 installs/day, 4 acquisition sources.")
    print("Injected: TikTok onboarding_complete -> first_action drop, last 7 days.")
    from growth_copilot_mvp.data_sources.firebase_reader import fetch_events

events = fetch_events()
    print(f"\n  events generated: {len(events):,}")

    section("STEP 2. Pre-aggregate into narrow tables")
    funnel = funnel_step_table(events)
    installs = daily_installs(events)
    source_completion = source_funnel_completion(events)
    print(f"  funnel rows (day, source, step):    {len(funnel):,}")
    print(f"  daily installs rows:                {len(installs):,}")
    print(f"  source-completion rows:             {len(source_completion):,}")
    app_dau = int(sum(installs.values()) / len(installs))
    print(f"  app DAU proxy:                      {app_dau}")

    section("STEP 3. Run detectors (deterministic, no LLM)")
    funnel_candidates, ff_funnel = detect_funnel_drops(funnel, app_dau)
    source_candidates, ff_source = detect_source_divergence(source_completion, app_dau)
    dau_candidates, ff_dau = detect_dau_anomaly(installs, app_dau)
    all_candidates = funnel_candidates + source_candidates + dau_candidates

    print(f"  funnel_drop candidates:        {len(funnel_candidates)}")
    print(f"  cohort_divergence candidates:  {len(source_candidates)}")
    print(f"  anomaly candidates:            {len(dau_candidates)}")
    print(f"  TOTAL after gates:             {len(all_candidates)}")
    print()
    for c in all_candidates:
        print(f"    [{c.computed_impact_tier:6s}] {c.summary}")
        print(f"             n={c.confidence_inputs.sample_size}, "
              f"effect={c.confidence_inputs.effect_size}, "
              f"baseline={c.confidence_inputs.baseline_stability}, "
              f"novelty={c.novelty_vs_prior}")

    section("STEP 4. Rank")
    ranked = rank(all_candidates, current_focus=None)
    for i, c in enumerate(ranked, 1):
        print(f"  #{i}  {c.id}")
        print(f"      tier={c.computed_impact_tier}, novelty={c.novelty_vs_prior}, "
              f"n={c.confidence_inputs.sample_size}")

    section("STEP 5. Assemble LLM input contract")
    app_context = {
        "category": "productivity",
        "stage": "early_growth",
        "current_focus": None,
        "dau": app_dau,
        "mau": int(app_dau * 4.5),
    }
    briefing_input = assemble_briefing_input(
        app_context=app_context,
        feature_frames=[ff_funnel, ff_source, ff_dau],
        ranked_candidates=ranked,
        prior_briefings=[],
        data_freshness_hours=6.0,
    )
    snippet = json.dumps(briefing_input, indent=2, default=str)
    print(snippet[:1600])
    print("\n  ... [briefing input continues, total " + str(len(snippet)) + " chars]")

    section("STEP 6. Verifier dry-run on a sample briefing")
    if not ranked:
        print("  Quiet day. Skipping verifier demo.")
        return briefing_input
    top = ranked[0]
    lines = ["# Daily Growth Briefing", "", "## Headline", top.summary + ".", "",
             "## What the data shows"]
    for field, value in top.evidence_values.items():
        if isinstance(value, float):
            disp = f"{value:.0%}" if value <= 1.0 else f"{value:.2f}"
        else:
            disp = str(value)
        label = field.split(".")[-1].replace("_", " ")
        lines.append(f"- {label}: {disp} (source: {field}).")
    lines += ["", "## Confidence",
              f"Derived from inputs: n={top.confidence_inputs.sample_size}, "
              f"effect_size={top.confidence_inputs.effect_size}, "
              f"baseline={top.confidence_inputs.baseline_stability}."]
    sample_briefing = "\n".join(lines)
    print(sample_briefing)
    issues = verify_briefing(sample_briefing, briefing_input)
    print(f"\n  Verifier issues: {len(issues)}")
    for i in issues:
        print(f"    ! {i}")

    section("STEP 7. Verifier catches a hallucination")
    bad_briefing = (
        "## Headline\n"
        "tiktok users dropped to 18% (source: feature_frame.funnel.tiktok.step_2.current_rate).\n"
        "This may reduce paid LTV by 12% (source: feature_frame.ltv.estimated_drop).\n"
        "Conversion fell 47% week-over-week.\n"
    )
    print(bad_briefing)
    issues = verify_briefing(bad_briefing, briefing_input)
    print(f"  Verifier issues: {len(issues)}")
    for i in issues:
        print(f"    ! {i}")

    return briefing_input


if __name__ == "__main__":
    run()
