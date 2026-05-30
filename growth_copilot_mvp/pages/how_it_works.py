"""pages/how_it_works.py — product pitch page, not documentation."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st

st.set_page_config(
    page_title="GrowthCopilot — How It Works",
    page_icon="💡",
    layout="centered",
)

st.markdown("""
<style>

    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
    .stMarkdown, .stText, button, input, select, textarea, p, div, span {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 4rem !important; max-width: 720px !important; }
    h1 { font-size: 1.35rem !important; font-weight: 700 !important; letter-spacing: -0.02em; }
    h2 { font-size: 1.05rem !important; font-weight: 600 !important; letter-spacing: -0.01em; margin-top: 1.6rem !important; }
    h3 { font-size: 0.93rem !important; font-weight: 600 !important; }
    h4 { font-size: 0.85rem !important; font-weight: 600 !important; }
    hr { border: none !important; border-top: 1px solid rgba(128,128,128,0.1) !important; margin: 1.8rem 0 !important; }
    [data-testid="stExpander"] { border: 1px solid rgba(128,128,128,0.1) !important; border-radius: 10px !important; margin-bottom: 0.6rem !important; overflow: hidden !important; box-shadow: none !important; }
    [data-testid="stExpander"]:hover { border-color: rgba(128,128,128,0.18) !important; }
    .streamlit-expanderHeader { font-size: 0.78rem !important; font-weight: 500 !important; opacity: 0.6 !important; padding: 0.6rem 0.85rem !important; background: transparent !important; }
    .streamlit-expanderContent { padding: 0.2rem 0.85rem 0.85rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.65rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.07em; opacity: 0.4 !important; }
    [data-testid="stMetricValue"] { font-size: 1.25rem !important; font-weight: 600 !important; letter-spacing: -0.02em; }
    .stButton > button { font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; font-weight: 500 !important; border-radius: 8px !important; transition: all 0.15s ease !important; }
    .stButton > button[kind="primary"] { background-color: #1e293b !important; color: white !important; border: none !important; font-weight: 600 !important; }
    .stButton > button[kind="primary"]:hover { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,0.1) !important; }
    section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1.1rem !important; }
    [data-testid="stPageLink"] { border-radius: 6px !important; padding: 7px 9px !important; margin: 1px 0 !important; font-size: 0.83rem !important; }
    [data-testid="stPageLink"] p { font-size: 0.83rem !important; }
    .stRadio > div { gap: 0.2rem !important; }
    .stRadio label { font-size: 0.79rem !important; }
    .stSelectbox label { font-size: 0.72rem !important; opacity: 0.5 !important; }
    .stToggle label { font-size: 0.8rem !important; }
    .stCaption { font-size: 0.68rem !important; opacity: 0.38 !important; }
    @keyframes pulse-dot { 0%, 100% { box-shadow: 0 0 0 0 rgba(217,79,79,0.4); } 55% { box-shadow: 0 0 0 5px rgba(217,79,79,0); } }
    .dot-pulse { animation: pulse-dot 2.4s ease-in-out infinite; }
    [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
    [data-testid="stIconMaterial"] { display: none !important; }
    .streamlit-expanderHeader::after { content: "›"; float: right; opacity: 0.4; font-size: 1rem; }

    /* How It Works overrides */
    .block-container { max-width: 700px !important; padding-top: 3rem !important; }
    hr { border: none !important; border-top: 1px solid rgba(128,128,128,0.1) !important; margin: 2rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='padding:1rem 0 2.5rem;'>"
    "<div style='font-size:0.72rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.8rem;'>"
    "GrowthCopilot</div>"
    "<div style='font-size:2rem;font-weight:700;letter-spacing:-0.035em;"
    "line-height:1.2;margin-bottom:1rem;'>"
    "Watches your telemetry<br>like an experienced operator.</div>"
    "<div style='font-size:1rem;opacity:0.5;line-height:1.7;max-width:520px;'>"
    "Most analytics tools tell you what happened.<br>"
    "GrowthCopilot tells you what to do about it — and explains "
    "the tradeoffs clearly enough that you can disagree."
    "</div></div>",
    unsafe_allow_html=True,
)

st.markdown("<hr>", unsafe_allow_html=True)

# ── The contrast ──────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.65rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1.2rem;'>"
    "The difference</div>",
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    st.markdown(
        "<div style='padding:1rem 1.1rem;border-radius:8px;"
        "border:1px solid rgba(128,128,128,0.12);height:100%;'>"
        "<div style='font-size:0.65rem;font-weight:600;opacity:0.35;"
        "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.75rem;'>"
        "Other tools</div>"
        "<div style='font-size:0.85rem;opacity:0.45;line-height:2;font-family:ui-monospace,monospace;'>"
        "TikTok conversion: −18%<br>"
        "Install volume: +34%<br>"
        "Onboarding complete: −12%<br>"
        "D1 retention: −8%<br>"
        "DAU: −4%"
        "</div>"
        "<div style='font-size:0.75rem;opacity:0.3;margin-top:0.8rem;font-style:italic;'>"
        "You figure out the rest."
        "</div></div>",
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        "<div style='padding:1rem 1.1rem;border-radius:8px;"
        "border:1px solid rgba(128,128,128,0.15);height:100%;'>"
        "<div style='font-size:0.65rem;font-weight:600;opacity:0.35;"
        "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.75rem;'>"
        "GrowthCopilot</div>"
        "<div style='font-size:0.82rem;opacity:0.75;line-height:1.6;margin-bottom:0.6rem;'>"
        "Two independent detectors agree: TikTok activation quality is "
        "deteriorating at the funnel step, not install volume. Consistent "
        "with a creative or onboarding change."
        "</div>"
        "<div style='font-size:0.82rem;font-weight:600;opacity:0.85;"
        "padding:0.5rem 0.7rem;border-radius:6px;"
        "background:rgba(217,79,79,0.06);border:1px solid rgba(217,79,79,0.2);'>"
        "Reduce TikTok spend. Audit the onboarding_complete → first_action step."
        "</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ── How it thinks ─────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.65rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1.2rem;'>"
    "How it thinks</div>",
    unsafe_allow_html=True,
)

layers = [
    ("Detects",    "Three independent detectors watch for funnel drops, cohort divergence, and volume anomalies. They're deliberately decorrelated — disagreement between them is informative, not a bug."),
    ("Remembers",  "Every signal carries its full operational history: when it first appeared, how it escalated, whether it recurred, and how it resolved. The system knows if it's seen this before."),
    ("Prioritises","A three-tier attention system decides what reaches the briefing (surfaced), what's tracked silently (background), and what's discarded (noise). Not everything gets your attention."),
    ("Reasons",    "Every recommendation includes: expected value, blast radius, time sensitivity, cost of waiting, risk of inaction, operator burden. The system explains tradeoffs, not just conclusions."),
    ("Learns",     "Operators record whether signals were real and recommendations were useful. Over time, false positive patterns are recognised and confidence calibrates to actual outcomes."),
    ("Restrains",  "Signals ignored repeatedly get urgency downgraded. Chronic unresolved patterns lose escalation priority. The system becomes more cautious when history suggests caution."),
]

for i, (title, desc) in enumerate(layers):
    connector = "" if i == len(layers)-1 else (
        "<div style='width:1px;height:16px;background:rgba(128,128,128,0.15);"
        "margin-left:11px;'></div>"
    )
    st.markdown(
        f"<div style='display:flex;gap:1rem;align-items:flex-start;margin-bottom:0;'>"
        f"<div style='flex-shrink:0;padding-top:2px;'>"
        f"<div style='width:22px;height:22px;border-radius:50%;"
        f"border:1.5px solid rgba(128,128,128,0.25);"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-size:0.6rem;font-weight:700;opacity:0.5;'>{i+1}</div>"
        f"</div>"
        f"<div style='padding-bottom:0.9rem;'>"
        f"<div style='font-size:0.88rem;font-weight:600;margin-bottom:0.15rem;'>{title}</div>"
        f"<div style='font-size:0.8rem;opacity:0.5;line-height:1.55;'>{desc}</div>"
        f"</div></div>"
        f"{connector}",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ── The demo arc ──────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.65rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1.2rem;'>"
    "A 28-day operational story</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='font-size:0.82rem;opacity:0.45;margin-bottom:1.4rem;max-width:500px;'>"
    "Enable demo mode in the sidebar. Watch an escalation emerge, persist, and resolve. "
    "Each step shows a different capability of the system."
    "</div>",
    unsafe_allow_html=True,
)

arc_steps = [
    ("Day 1",  "All clear",              "The system is silent. No metric has crossed the confidence threshold."),
    ("Day 5",  "Something stirs",        "A single detector notices a mild signal. Confidence is low — the system watches, doesn't act."),
    ("Day 9",  "Two detectors agree",    "A second independent detector fires. Urgency rises from observe to act."),
    ("Day 14", "Escalation",             "Immediate action recommended. Spend reduction and funnel audit."),
    ("Day 16", "The system remembers",   "Prior occurrences surface. Resolution patterns, recurrence history, trust notes."),
    ("Day 19", "Recovery",               "Signal shifts direction. Intervention risk now exceeds inaction risk."),
    ("Day 23", "Stabilizing",            "De-escalating to monitor mode. Waiting for confirmation."),
    ("Day 28", "Resolution",             "Signal resolved. System returns to silence. Outcome logged."),
]

for day, label, desc in arc_steps:
    st.markdown(
        f"<div style='display:flex;gap:1rem;margin-bottom:0.55rem;align-items:baseline;'>"
        f"<div style='font-size:0.68rem;font-weight:600;opacity:0.3;min-width:44px;"
        f"font-family:ui-monospace,monospace;'>{day}</div>"
        f"<div>"
        f"<span style='font-size:0.82rem;font-weight:600;opacity:0.8;'>{label}</span>"
        f"<span style='font-size:0.79rem;opacity:0.4;'> — {desc}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ── What makes it different ───────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.65rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:1.2rem;'>"
    "What makes it different</div>",
    unsafe_allow_html=True,
)

differentiators = [
    ("It stays silent",      "Most alerting systems fire constantly. GrowthCopilot only surfaces what crosses a confidence threshold with sufficient evidence. Quiet days are a feature."),
    ("It explains tradeoffs","Every recommendation includes the cost of acting and the cost of waiting. You can read the reasoning and disagree — the system doesn't pretend certainty it doesn't have."),
    ("It has memory",        "The system knows if a signal has occurred before, how long it typically takes to resolve, and whether prior interventions worked. This changes recommendations."),
    ("It learns restraint",  "Signals that operators consistently ignore get deprioritised over time. The system adapts to what actually matters to each team."),
]

for title, desc in differentiators:
    st.markdown(
        f"<div style='margin-bottom:1rem;'>"
        f"<div style='font-size:0.85rem;font-weight:600;margin-bottom:0.2rem;'>{title}</div>"
        f"<div style='font-size:0.8rem;opacity:0.45;line-height:1.6;'>{desc}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown(
    "<div style='font-size:0.72rem;opacity:0.22;padding:0.5rem 0 2rem;'>"
    "GrowthCopilot · Operational intelligence for product and growth teams · "
    "Running on synthetic demo data</div>",
    unsafe_allow_html=True,
)