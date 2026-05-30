"""archetypes.py — company archetypes for the simulation engine.

Each archetype defines:
    - funnel steps and their canonical names
    - baseline conversion rates by acquisition source
    - acquisition source mix
    - scenario probabilities (which signal types are likely)
    - detector sensitivities
    - display metadata (name, description, industry, key metrics)

Switching archetypes changes the entire operational narrative
without touching the detector engine.
"""
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# Archetype definitions
# ---------------------------------------------------------------------------

ARCHETYPES: Dict[str, Dict[str, Any]] = {

    # -----------------------------------------------------------------------
    "consumer_social": {
        "name":        "Consumer Social App",
        "emoji":       "📱",
        "description": "High-volume installs from paid social, narrow activation funnel, viral growth loops.",
        "industry":    "Consumer / Social",
        "key_metric":  "First post / first follow rate",

        "funnel_steps": [
            "install",
            "onboarding_start",
            "onboarding_complete",
            "first_action",    # first_post or first_follow
            "habit_action",    # daily_active
        ],

        "sources":        ["tiktok", "instagram", "organic", "referral"],
        "source_weights": [0.40,     0.25,        0.25,      0.10],

        "base_rates": {
            # per-step conversion rates (step i → step i+1)
            "tiktok":    [0.85, 0.70, 0.42, 0.50],
            "instagram": [0.88, 0.74, 0.48, 0.55],
            "organic":   [0.94, 0.82, 0.58, 0.65],
            "referral":  [0.96, 0.88, 0.68, 0.72],
        },

        "daily_installs": 180,

        # Scenario probabilities — what kinds of problems does this app face?
        "scenario_weights": {
            "A_full_regression":  0.34,   # TikTok quality drop
            "B_mild_drop":        0.18,   # mild funnel drop
            "C_dau_spike":        0.10,   # viral spike
            "D_quiet":            0.24,   # quiet day — restraint is a feature
            "E_recovery":         0.06,   # recovering
            "F_false_positive":   0.05,   # noisy baseline
            "G_seasonal":         0.02,
            "H_rollout":          0.01,
        },

        # Injected regression parameters
        "injection": {
            "step_index":    2,      # onboarding_complete → first_action
            "source":        "tiktok",
            "severe_rate":   0.18,   # Scenario A
            "mild_rate":     0.30,   # Scenario B
            "spike_factor":  1.8,    # Scenario C DAU spike
        },
    },

    # -----------------------------------------------------------------------
    "saas_productivity": {
        "name":        "SaaS Productivity Tool",
        "emoji":       "💼",
        "description": "Low-volume, high-intent signups. Deep onboarding. Activation tied to first project or workspace.",
        "industry":    "SaaS / B2B",
        "key_metric":  "Time to first project created",

        "funnel_steps": [
            "install",           # sign_up
            "onboarding_start",  # workspace_created
            "onboarding_complete", # first_integration
            "first_action",      # first_project_created
            "habit_action",      # daily_active_user
        ],

        "sources":        ["google_ads", "product_hunt", "organic", "referral"],
        "source_weights": [0.35,         0.15,           0.35,      0.15],

        "base_rates": {
            "google_ads":   [0.82, 0.75, 0.55, 0.60],
            "product_hunt": [0.90, 0.82, 0.65, 0.70],
            "organic":      [0.92, 0.84, 0.68, 0.72],
            "referral":     [0.95, 0.90, 0.78, 0.82],
        },

        "daily_installs": 55,   # lower volume, higher intent

        "scenario_weights": {
            "A_full_regression":  0.24,   # onboarding regression (deploy-caused)
            "B_mild_drop":        0.18,
            "C_dau_spike":        0.06,
            "D_quiet":            0.35,   # SaaS has many quiet stable days
            "E_recovery":         0.08,
            "F_false_positive":   0.06,
            "H_rollout":          0.03,
        },

        "injection": {
            "step_index":    2,      # first_integration → first_project
            "source":        "google_ads",
            "severe_rate":   0.25,
            "mild_rate":     0.38,
            "spike_factor":  2.5,   # product hunt spike is bigger
        },
    },

    # -----------------------------------------------------------------------
    "marketplace": {
        "name":        "Marketplace",
        "emoji":       "🛍️",
        "description": "Two-sided marketplace. Acquisition mix of buyers and sellers. First transaction is the key activation event.",
        "industry":    "Marketplace / E-commerce",
        "key_metric":  "First transaction rate",

        "funnel_steps": [
            "install",
            "onboarding_start",   # profile_created
            "onboarding_complete", # payment_method_added
            "first_action",        # first_purchase or first_listing
            "habit_action",        # repeat_transaction
        ],

        "sources":        ["google_ads", "meta", "organic", "email"],
        "source_weights": [0.30,         0.30,   0.25,      0.15],

        "base_rates": {
            "google_ads": [0.80, 0.68, 0.38, 0.45],
            "meta":       [0.78, 0.65, 0.35, 0.42],
            "organic":    [0.90, 0.78, 0.52, 0.58],
            "email":      [0.94, 0.82, 0.62, 0.68],
        },

        "daily_installs": 120,

        "scenario_weights": {
            "A_full_regression":  0.22,
            "B_mild_drop":        0.20,
            "C_dau_spike":        0.12,
            "D_quiet":            0.28,
            "E_recovery":         0.08,
            "F_false_positive":   0.07,
            "I_attribution":      0.03,
        },

        "injection": {
            "step_index":    2,      # payment_method → first purchase
            "source":        "meta",
            "severe_rate":   0.14,   # payment friction is severe
            "mild_rate":     0.25,
            "spike_factor":  2.2,
        },
    },

    # -----------------------------------------------------------------------
    "mobile_game": {
        "name":        "Mobile Game",
        "emoji":       "🎮",
        "description": "High install volume, fast churn. Day-1 retention is the critical metric. Viral loops from sharing.",
        "industry":    "Gaming / Entertainment",
        "key_metric":  "Day-1 retention rate",

        "funnel_steps": [
            "install",
            "onboarding_start",    # tutorial_start
            "onboarding_complete", # tutorial_complete
            "first_action",        # first_session_complete (day 1 return)
            "habit_action",        # day_7_return
        ],

        "sources":        ["tiktok", "youtube", "organic", "crosspromo"],
        "source_weights": [0.45,     0.20,      0.25,      0.10],

        "base_rates": {
            "tiktok":    [0.82, 0.68, 0.38, 0.28],   # lower retention — casual users
            "youtube":   [0.86, 0.75, 0.48, 0.38],
            "organic":   [0.90, 0.80, 0.55, 0.45],
            "crosspromo":[0.88, 0.76, 0.50, 0.40],
        },

        "daily_installs": 350,   # high volume

        "scenario_weights": {
            "A_full_regression":  0.38,   # tutorial regressions common after updates
            "B_mild_drop":        0.18,
            "C_dau_spike":        0.10,
            "D_quiet":            0.20,
            "E_recovery":         0.06,
            "F_false_positive":   0.05,
            "J_conflict":         0.03,
        },

        "injection": {
            "step_index":    2,      # tutorial_complete → day1_return
            "source":        "tiktok",
            "severe_rate":   0.15,
            "mild_rate":     0.28,
            "spike_factor":  2.0,
        },
    },

    # -----------------------------------------------------------------------
    "subscription_fitness": {
        "name":        "Subscription Fitness App",
        "emoji":       "💪",
        "description": "Premium subscription model. Low install volume, very high intent. Paywall conversion is the key event.",
        "industry":    "Health & Fitness / Subscription",
        "key_metric":  "Trial-to-paid conversion rate",

        "funnel_steps": [
            "install",
            "onboarding_start",    # goals_set
            "onboarding_complete", # trial_started
            "first_action",        # first_workout_completed
            "habit_action",        # subscription_renewed
        ],

        "sources":        ["instagram", "google_ads", "organic", "podcast"],
        "source_weights": [0.35,        0.25,         0.30,      0.10],

        "base_rates": {
            "instagram":  [0.80, 0.72, 0.45, 0.52],
            "google_ads": [0.84, 0.76, 0.50, 0.56],
            "organic":    [0.92, 0.86, 0.62, 0.70],
            "podcast":    [0.94, 0.88, 0.68, 0.75],
        },

        "daily_installs": 45,   # very low volume, very high intent

        "scenario_weights": {
            "A_full_regression":  0.22,
            "B_mild_drop":        0.16,
            "C_dau_spike":        0.08,
            "D_quiet":            0.36,   # low-volume app, many quiet days
            "E_recovery":         0.08,
            "F_false_positive":   0.07,
            "G_seasonal":         0.03,
        },

        "injection": {
            "step_index":    2,      # trial_started → first_workout
            "source":        "instagram",
            "severe_rate":   0.20,
            "mild_rate":     0.35,
            "spike_factor":  1.6,
        },
    },
}

DEFAULT_ARCHETYPE = "consumer_social"


def get_archetype(name: str) -> Dict[str, Any]:
    return ARCHETYPES.get(name, ARCHETYPES[DEFAULT_ARCHETYPE])


def archetype_names() -> List[str]:
    return list(ARCHETYPES.keys())


def archetype_display_options() -> List[str]:
    """Returns formatted display strings for the sidebar selector."""
    return [
        f"{v['emoji']} {v['name']}"
        for v in ARCHETYPES.values()
    ]


def archetype_from_display(display: str) -> str:
    """Convert display string back to archetype key."""
    for key, val in ARCHETYPES.items():
        if f"{val['emoji']} {val['name']}" == display:
            return key
    return DEFAULT_ARCHETYPE