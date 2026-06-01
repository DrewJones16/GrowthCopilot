"""demo_loader.py — pre-loads synthetic outcome history for demo mode.

Run this once before showing the system to populate:
    - 30 days of signal history
    - realistic outcome mix (true positives, false positives, ignored alerts)
    - trust engine data so calibration console shows live metrics

Usage:
    python -m growth_copilot_mvp.demo_loader

This resets the registry and replaces it with a realistic 30-day history.
"""
import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from growth_copilot_mvp.signal_registry import (
    reset_registry, update_signal, record_outcome, increment_ignored,
)
from datetime import date, timedelta


def load_demo_history(seed: int = 42):
    print("Resetting registry and loading demo history...")
    reset_registry()
    rng   = random.Random(seed)
    today = date.today()

    # ---------------------------------------------------------------------------
    # Scenario 1: TikTok activation failure — 14-day worsening, then resolved
    # ---------------------------------------------------------------------------
    print("  Loading TikTok activation failure history...")
    for i in range(14):
        day       = today - timedelta(days=28 - i)
        direction = "worsening" if i < 10 else "stable"
        conf      = rng.randint(68, 82)
        rec = update_signal(
            cluster_title    = "TikTok activation failure",
            severity         = "CRITICAL",
            direction        = direction,
            confidence_score = conf,
            days_active      = i + 1,
        )

    # Record outcome: signal was real, team acted, resolved
    record_outcome(
        "TikTok activation failure",
        signal_real             = True,
        severity_accurate       = True,
        recommendation_followed = True,
        recommendation_useful   = True,
        action_taken            = "mitigated",
        issue_confirmed         = True,
        self_resolved           = False,
        time_to_resolution      = 14,
        business_impact         = "high",
        operator_feedback       = "Pausing TikTok spend confirmed — onboarding bug found in deploy from day -8.",
    )

    # Signal absent for 3 days → resolved
    from growth_copilot_mvp.signal_registry import check_resolutions
    for _ in range(3):
        check_resolutions([])

    # ---------------------------------------------------------------------------
    # Scenario 2: Acquisition anomaly — spike, monitored, self-resolved
    # ---------------------------------------------------------------------------
    print("  Loading Acquisition anomaly history...")
    for i in range(5):
        day  = today - timedelta(days=20 - i)
        conf = rng.randint(62, 78)
        update_signal(
            cluster_title    = "Acquisition anomaly",
            severity         = "WATCH",
            direction        = "recovering" if i >= 2 else "stable",
            confidence_score = conf,
            days_active      = i + 1,
        )

    # Ignored twice — team didn't act
    increment_ignored("Acquisition anomaly")
    increment_ignored("Acquisition anomaly")

    record_outcome(
        "Acquisition anomaly",
        signal_real             = True,
        severity_accurate       = False,
        recommendation_followed = False,
        recommendation_useful   = False,
        action_taken            = "none",
        issue_confirmed         = False,
        self_resolved           = True,
        time_to_resolution      = 5,
        business_impact         = "low",
        operator_feedback       = "Spike was organic — campaign launch coincidence. Self-resolved.",
    )
    check_resolutions([])

    # ---------------------------------------------------------------------------
    # Scenario 3: Onboarding regression — caught early, low confidence, dismissed
    # ---------------------------------------------------------------------------
    print("  Loading Onboarding conversion regression history...")
    for i in range(3):
        conf = rng.randint(42, 58)
        update_signal(
            cluster_title    = "Onboarding conversion regression",
            severity         = "WATCH",
            direction        = "stable",
            confidence_score = conf,
            days_active      = i + 1,
        )

    increment_ignored("Onboarding conversion regression")
    record_outcome(
        "Onboarding conversion regression",
        signal_real             = False,
        severity_accurate       = False,
        recommendation_followed = False,
        recommendation_useful   = False,
        action_taken            = "none",
        self_resolved           = True,
        business_impact         = "none",
        operator_feedback       = "False positive — noisy baseline week.",
    )
    check_resolutions([])

    # ---------------------------------------------------------------------------
    # Scenario 4: Second TikTok recurrence — recent, still active
    # ---------------------------------------------------------------------------
    print("  Loading TikTok recurrence (recent)...")
    for i in range(7):
        direction = "worsening" if i < 5 else "stable"
        conf      = rng.randint(65, 80)
        update_signal(
            cluster_title    = "TikTok activation failure",
            severity         = "CRITICAL",
            direction        = direction,
            confidence_score = conf,
            days_active      = i + 1,
        )

    print()
    print("Demo history loaded.")
    print("Registry now contains:")

    from growth_copilot_mvp.signal_registry import get_all_signals, outcome_summary
    sigs = get_all_signals()
    for sid, r in sigs.items():
        print(f"  {r['title']}: {r['status']} | strength={r.get('signal_strength',0):.0f} | ignored={r.get('ignored_count',0)}x | outcomes={1 if r.get('outcome',{}).get('recorded_at') else 0}")

    o = outcome_summary()
    print()
    print(f"Outcome summary:")
    print(f"  Total outcomes:       {o.get('total_outcomes', 0)}")
    print(f"  Signal real rate:     {(o.get('signal_real_rate') or 0)*100:.0f}%")
    print(f"  Rec. useful rate:     {(o.get('recommendation_useful_rate') or 0)*100:.0f}%")
    print(f"  False positive rate:  {(o.get('false_positive_rate') or 0)*100:.0f}%")
    print(f"  Self-resolution rate: {(o.get('self_resolution_rate') or 0)*100:.0f}%")


if __name__ == "__main__":
    load_demo_history()
    print()
    print("Run: py -m streamlit run growth_copilot_mvp/app.py")