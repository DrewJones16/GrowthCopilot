"""synth_data.py — archetype-aware synthetic event generator.

Changes from previous version:
    - Accepts an archetype config dict so each company type produces
      different operational narratives
    - Scenario weights come from the archetype (e.g. mobile games have
      more regressions; SaaS has more quiet days)
    - Falls back to consumer_social defaults if no archetype provided
    - FUNNEL_STEPS exported dynamically from archetype
"""
import random
from datetime import date, timedelta
from typing import Dict, Any, List, Optional


# Default funnel steps (consumer social — backwards compatible)
FUNNEL_STEPS = [
    "install",
    "onboarding_start",
    "onboarding_complete",
    "first_action",
    "habit_action",
]


def _pick_scenario(seed: int, weights: Dict[str, float]) -> str:
    """Deterministically pick scenario using archetype-specific weights."""
    rng    = random.Random(seed + 9999)
    r      = rng.random()
    cumul  = 0.0
    # Map to single-letter codes for backwards compatibility
    letter_map = {
        "A_full_regression": "A",
        "B_mild_drop":       "B",
        "C_dau_spike":       "C",
        "D_quiet":           "D",
        "E_recovery":        "E",
        "F_false_positive":  "F",
    }
    for key, weight in weights.items():
        cumul += weight
        if r < cumul:
            return letter_map.get(key, "D")
    return "D"


def generate_events(
    days:           int = 90,
    daily_installs: int = 120,
    seed:           int = 42,
    archetype:      Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Generate synthetic events for the given archetype.

    If no archetype is provided, falls back to consumer_social defaults
    for backwards compatibility.
    """
    # Load archetype config
    if archetype is None:
        from growth_copilot_mvp.archetypes import get_archetype
        archetype = get_archetype("consumer_social")

    sources        = archetype.get("sources",        ["tiktok", "reddit", "organic", "google_ads"])
    source_weights = archetype.get("source_weights", [0.35, 0.20, 0.30, 0.15])
    base_rates     = archetype.get("base_rates", {
        "tiktok":     [0.88, 0.72, 0.45, 0.55],
        "reddit":     [0.93, 0.82, 0.62, 0.60],
        "organic":    [0.95, 0.85, 0.60, 0.58],
        "google_ads": [0.90, 0.75, 0.50, 0.55],
    })
    funnel_steps   = archetype.get("funnel_steps", FUNNEL_STEPS)
    scenario_wts   = archetype.get("scenario_weights", {
        "A_full_regression": 0.55,
        "B_mild_drop":       0.18,
        "C_dau_spike":       0.10,
        "D_quiet":           0.12,
        "E_recovery":        0.05,
    })
    injection      = archetype.get("injection", {
        "step_index":  2,
        "source":      sources[0],
        "severe_rate": 0.22,
        "mild_rate":   0.32,
        "spike_factor": 1.6,
    })

    inj_step     = injection.get("step_index",   2)
    inj_source   = injection.get("source",       sources[0])
    inj_severe   = injection.get("severe_rate",  0.22)
    inj_mild     = injection.get("mild_rate",    0.32)
    inj_spike    = injection.get("spike_factor", 1.6)

    scenario = _pick_scenario(seed, scenario_wts)
    random.seed(seed)
    today  = date.today()
    events = []

    injection_window = 7

    for d in range(days):
        day              = today - timedelta(days=days - 1 - d)
        weekend          = 0.85 if day.weekday() >= 5 else 1.0
        injection_active = d >= days - injection_window

        # Volume factor
        volume_factor = 1.0
        if scenario == "C" and injection_active and d >= days - 2:
            volume_factor = inj_spike
        elif scenario == "F" and injection_active:
            # False positive: noisy volume with no real signal
            volume_factor = random.uniform(0.85, 1.15)

        n_installs = int(daily_installs * weekend * volume_factor * random.uniform(0.92, 1.08))

        for _ in range(n_installs):
            source  = random.choices(sources, weights=source_weights)[0]
            user_id = f"u_{day.isoformat()}_{random.randint(1, 10_000_000)}"
            rates   = list(base_rates.get(source, base_rates[sources[0]]))

            if injection_active and source == inj_source:
                if scenario == "A":
                    rates[inj_step] = inj_severe
                elif scenario == "B":
                    rates[inj_step] = inj_mild
                elif scenario == "E":
                    # Gradual recovery toward baseline
                    days_into = d - (days - injection_window)
                    progress  = days_into / injection_window
                    baseline  = base_rates.get(source, base_rates[sources[0]])[inj_step]
                    recovered = inj_mild + (baseline - inj_mild) * progress
                    rates[inj_step] = round(recovered, 3)

            events.append({
                "user":   user_id,
                "event":  funnel_steps[0],   # install
                "source": source,
                "day":    day,
            })
            for step_idx in range(len(funnel_steps) - 1):
                if random.random() < rates[step_idx]:
                    events.append({
                        "user":   user_id,
                        "event":  funnel_steps[step_idx + 1],
                        "source": source,
                        "day":    day,
                    })
                else:
                    break

    return events