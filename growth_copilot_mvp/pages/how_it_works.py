"""pages/how_it_works.py — product explainer page."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st

st.set_page_config(page_title="GrowthCopilot — How It Works", page_icon=":bulb:", layout="centered")

st.title("How GrowthCopilot Works")
st.markdown(
    "<div style='color:#888;font-size:0.85rem;margin-bottom:1.5rem;'>"
    "An operational intelligence system for product and growth teams."
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# The core idea
# ---------------------------------------------------------------------------
st.markdown("## The core idea")
st.markdown(
    "<div style='padding:1rem;background:#f0f4ff;border-radius:8px;"
    "border-left:4px solid #1565c0;margin-bottom:1rem;'>"
    "<div style='font-size:0.95rem;color:#444;line-height:1.6;'>"
    "Most analytics tools tell you <strong>what happened</strong>.<br>"
    "GrowthCopilot tells you <strong>what to do about it</strong> — "
    "and explains the tradeoffs clearly enough that you can disagree."
    "</div></div>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Other analytics tools**")
    for line in [
        "TikTok conversion: -18%",
        "Install volume: +34%",
        "Onboarding complete: -12%",
        "D1 retention: -8%",
    ]:
        st.markdown(f"<div style='font-size:0.85rem;color:#888;padding:0.2rem 0;'>📊 {line}</div>",
                    unsafe_allow_html=True)

with col2:
    st.markdown("**GrowthCopilot**")
    st.markdown(
        "<div style='font-size:0.85rem;color:#444;background:#fafafa;"
        "border-left:3px solid #c62828;padding:0.6rem 0.8rem;border-radius:4px;'>"
        "🔴 <strong>TikTok activation failure</strong><br>"
        "<span style='color:#666;'>Worsening 7 days. Likely onboarding bug.</span><br>"
        "<span style='color:#c62828;font-size:0.8rem;'>→ Reduce spend + audit deploy</span>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# The 6-layer architecture
# ---------------------------------------------------------------------------
st.markdown("## The 6-layer architecture")
st.markdown(
    "<div style='font-size:0.85rem;color:#888;margin-bottom:0.8rem;'>"
    "Each layer builds on the previous. Most analytics systems stop at Layer 1."
    "</div>",
    unsafe_allow_html=True,
)

layers = [
    ("1", "Perception",  "#1565c0", "Detectors",
     "Three independent detectors watch for funnel drops, cohort divergence, and volume anomalies. "
     "Decorrelated thresholds so they don't always agree — disagreement is a feature, not a bug."),
    ("2", "Cognition",   "#1976d2", "Clustering + Memory",
     "Related signals are grouped into coherent situations. The system remembers each signal's "
     "full history: when it first appeared, how it escalated, whether it recurred, and how it resolved."),
    ("3", "Attention",   "#0288d1", "Surfacing + Suppression",
     "A three-tier architecture decides what reaches the briefing (Surfaced), what's tracked "
     "silently (Background), and what's discarded (Ephemeral). Attention is a finite resource."),
    ("4", "Decisioning", "#0097a7", "Consequence Modeling",
     "Every recommendation includes: expected value, blast radius, time sensitivity, cost of "
     "waiting, risk of inaction, and operator burden. The system explains tradeoffs, not just conclusions."),
    ("5", "Learning",    "#00897b", "Outcome Feedback",
     "Operators record whether alerts were real and recommendations were useful. Over time, "
     "detector weights become empirical, false positive patterns are recognized, and confidence calibrates."),
    ("6", "Trust",       "#2e7d32", "Adaptive Restraint",
     "Signals ignored repeatedly get their urgency downgraded. Chronic unresolved patterns lose "
     "escalation priority. The system becomes more cautious when history suggests caution."),
]

for num, name, color, subtitle, desc in layers:
    st.markdown(
        f"<div style='display:flex;gap:1rem;margin-bottom:0.8rem;align-items:flex-start;'>"
        f"<div style='min-width:2rem;height:2rem;background:{color};color:white;"
        f"border-radius:50%;display:flex;align-items:center;justify-content:center;"
        f"font-weight:700;font-size:0.9rem;flex-shrink:0;'>{num}</div>"
        f"<div>"
        f"<div style='font-weight:600;color:#333;'>{name} <span style='color:#888;"
        f"font-weight:400;font-size:0.85rem;'>— {subtitle}</span></div>"
        f"<div style='font-size:0.85rem;color:#555;margin-top:0.2rem;'>{desc}</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# What you see in the briefing
# ---------------------------------------------------------------------------
st.markdown("## What the daily briefing contains")

sections = [
    ("Operational posture",  "A one-line editorial summary of the day — Stable / Improving / Needs attention / All clear."),
    ("Signal header",        "Severity, confidence score, days active, trend direction, escalation history, recurrence count."),
    ("Narrative context",    "What changed since yesterday — direction shifts, confidence drift, escalation history."),
    ("Confidence breakdown", "Four-factor decomposition: sample size, effect size, baseline stability, signal novelty. Plus detector agreement bonus."),
    ("Why this surfaced",    "Surface score breakdown showing exactly why this signal reached the briefing vs staying in background."),
    ("Consequence model",    "Six dimensions: expected value, blast radius, time sensitivity, cost of waiting, risk of inaction, operator burden."),
    ("Trust notes",          "Orange warnings when the system's history suggests caution — ignored alerts, self-resolution patterns."),
    ("Quick feedback",       "3-question feedback widget: Was this real? Action taken? Recommendation useful? Feeds the learning loop."),
]

for title, desc in sections:
    st.markdown(
        f"<div style='padding:0.4rem 0;border-bottom:1px solid #f0f0f0;'>"
        f"<span style='font-weight:600;color:#333;'>{title}</span>"
        f"<span style='color:#666;font-size:0.85rem;'> — {desc}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# The 5 company archetypes
# ---------------------------------------------------------------------------
st.markdown("## Company archetypes")
st.markdown(
    "<div style='font-size:0.85rem;color:#888;margin-bottom:0.8rem;'>"
    "Switch archetypes in the sidebar to see how the same intelligence system "
    "produces completely different operational narratives."
    "</div>",
    unsafe_allow_html=True,
)

from growth_copilot_mvp.archetypes import ARCHETYPES
for key, arch in ARCHETYPES.items():
    st.markdown(
        f"<div style='padding:0.6rem 0.8rem;background:#fafafa;border-radius:6px;"
        f"margin-bottom:0.5rem;border-left:3px solid #1565c0;'>"
        f"<div style='font-weight:600;'>{arch['emoji']} {arch['name']}</div>"
        f"<div style='font-size:0.82rem;color:#555;margin-top:0.2rem;'>{arch['description']}</div>"
        f"<div style='font-size:0.78rem;color:#888;margin-top:0.2rem;'>"
        f"Key metric: {arch['key_metric']} &nbsp;·&nbsp; "
        f"~{arch['daily_installs']} installs/day &nbsp;·&nbsp; "
        f"Sources: {', '.join(arch['sources'])}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------------------------
# Scenario types
# ---------------------------------------------------------------------------
st.markdown("## Simulation scenarios")
st.markdown(
    "<div style='font-size:0.85rem;color:#888;margin-bottom:0.8rem;'>"
    "Each seed deterministically selects a scenario. Different archetypes have different "
    "scenario probabilities — mobile games see more regressions, SaaS sees more quiet days."
    "</div>",
    unsafe_allow_html=True,
)

scenarios = [
    ("A", "Full regression",     "Primary source hits a severe funnel drop. Both funnel and cohort detectors fire."),
    ("B", "Mild funnel drop",    "Moderate drop — funnel detector fires, cohort borderline. Realistic detector disagreement."),
    ("C", "DAU spike",           "Volume anomaly only, no funnel issue. Tests acquisition anomaly detector in isolation."),
    ("D", "Quiet day",           "No injection. System stays silent. Demonstrates restraint."),
    ("E", "Gradual recovery",    "Regression that improves day by day. Low confidence, recovering signals."),
    ("F", "False positive",      "Noisy baseline with no real signal. Stress-tests over-triggering."),
    ("G", "Seasonal decline",    "Volume drops gradually over 2 weeks. Tests slow-moving signal detection."),
    ("H", "Rollout regression",  "Bug introduced in phased rollout — worsens gradually, not overnight."),
    ("I", "Attribution shift",   "Organic traffic misattributed. Source divergence without a real product issue."),
    ("J", "Conflicting signals", "One source improves while another regresses. Tests causal reasoning under ambiguity."),
]

for code, name, desc in scenarios:
    st.markdown(
        f"<div style='display:flex;gap:0.8rem;margin-bottom:0.4rem;align-items:flex-start;'>"
        f"<div style='font-family:monospace;font-size:0.8rem;color:#888;min-width:1rem;'>{code}</div>"
        f"<div><strong style='font-size:0.85rem;'>{name}</strong>"
        f"<span style='color:#666;font-size:0.82rem;'> — {desc}</span></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    "<div style='padding:1.5rem 0 0.8rem;'>"
    "<div style='font-size:1.05rem;font-weight:700;letter-spacing:-0.025em;margin-bottom:0.35rem;'>"
    "Stay updated</div>"
    "<div style='font-size:0.82rem;opacity:0.45;line-height:1.6;max-width:440px;margin-bottom:1.1rem;'>"
    "We're building direct integrations, a daily email digest, and more. "
    "Leave your email and we'll let you know when new features ship."
    "</div></div>",
    unsafe_allow_html=True,
)
st.link_button(
    "Get notified about updates →",
    "https://form.typeform.com/to/r8s7hkGk",
)

st.markdown(
    "<div style='font-size:0.7rem;opacity:0.2;padding:1.2rem 0 2rem;text-align:center;'>"
    "GrowthCopilot · Operational intelligence for product and growth teams · "
    "Running on synthetic demo data</div>",
    unsafe_allow_html=True,
)