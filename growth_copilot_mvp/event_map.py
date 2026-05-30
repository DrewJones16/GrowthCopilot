"""event_map.py — translate app-specific event names to canonical funnel steps.

This is the ONLY file you need to edit when connecting a new data source.
The detector engine never sees raw event names — only canonical step names.

How to configure for your app:
    1. Find your funnel events in Firebase DebugView or BigQuery
    2. Map each canonical step to your actual event name
    3. Set SOURCE_PROPERTY to the user property or event param that identifies
       acquisition source (utm_source, media_source, campaign, etc.)

Canonical funnel steps (do not change these):
    install             — first time user opens the app
    onboarding_start    — user begins onboarding flow
    onboarding_complete — user completes onboarding
    first_action        — user takes first meaningful product action
    habit_action        — user takes a repeating value action

Example mappings for common app types:

    # Consumer mobile app
    EVENT_MAP = {
        "install":             "first_open",
        "onboarding_start":    "tutorial_begin",
        "onboarding_complete": "tutorial_complete",
        "first_action":        "content_view",
        "habit_action":        "session_start",
    }

    # SaaS / productivity tool
    EVENT_MAP = {
        "install":             "sign_up",
        "onboarding_start":    "onboarding_started",
        "onboarding_complete": "onboarding_completed",
        "first_action":        "project_created",
        "habit_action":        "project_opened",
    }

    # Marketplace / e-commerce
    EVENT_MAP = {
        "install":             "first_open",
        "onboarding_start":    "profile_setup_start",
        "onboarding_complete": "profile_setup_complete",
        "first_action":        "first_purchase",
        "habit_action":        "purchase",
    }
"""

# ---------------------------------------------------------------------------
# Your event map — edit these values to match your Firebase events
# ---------------------------------------------------------------------------

EVENT_MAP = {
    "install":             "first_open",        # ← replace with your event name
    "onboarding_start":    "onboarding_start",   # ← replace with your event name
    "onboarding_complete": "onboarding_complete",# ← replace with your event name
    "first_action":        "first_action",       # ← replace with your event name
    "habit_action":        "habit_action",       # ← replace with your event name
}

# User property or event parameter that identifies acquisition source
# Common values: "utm_source", "media_source", "campaign", "source"
SOURCE_PROPERTY = "utm_source"

# Acquisition sources to track as distinct cohorts
# Add any sources you actively manage (paid channels, organic, etc.)
TRACKED_SOURCES = [
    "tiktok",
    "google_ads",
    "organic",
    "reddit",
    # Add more as needed
]

# Default source label when source is unknown/missing
DEFAULT_SOURCE = "unknown"

# ---------------------------------------------------------------------------
# Reverse map (canonical → app event) — auto-generated, do not edit
# ---------------------------------------------------------------------------

REVERSE_MAP = {v: k for k, v in EVENT_MAP.items()}


def canonical(app_event_name: str) -> str:
    """Convert an app event name to its canonical funnel step name."""
    return REVERSE_MAP.get(app_event_name, app_event_name)


def app_event(canonical_name: str) -> str:
    """Convert a canonical funnel step name to the app's event name."""
    return EVENT_MAP.get(canonical_name, canonical_name)