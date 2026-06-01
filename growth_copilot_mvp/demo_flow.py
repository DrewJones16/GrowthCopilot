"""demo_flow.py — curated 8-step demo arc.

Each seed is verified to produce the correct scenario type with the
updated archetype weights. The arc tells a complete operational story:

    Step 1: All clear      — system silent, nothing to act on
    Step 2: Emergence      — weak single-detector signal, wait-and-observe
    Step 3: Worsening      — multi-detector, urgency rises to 'act this week'
    Step 4: Escalated      — critical state, immediate action recommended
    Step 5: Memory         — system recalls prior occurrence, trust notes active
    Step 6: Recovery       — signal improving after intervention
    Step 7: Stabilizing    — de-escalating, moving toward resolution
    Step 8: Resolved       — primary resolved, system returns to quiet

Seeds verified against consumer_social archetype scenario weights.
"""
from typing import List, Tuple

DEMO_STEPS: List[Tuple[int, str, str]] = [
    (
        0,
        "Day 1 — All clear",
        "No signals above the attention threshold. System operating normally.",
    ),
    (
        5,
        "Day 5 — Something stirs",
        "Single detector fired on a mild funnel drop. Low confidence — wait and observe.",
    ),
    (
        7,
        "Day 9 — Worsening",
        "Two detectors now agree. Signal persisting and deteriorating. Urgency rises.",
    ),
    (
        8,
        "Day 14 — Escalated",
        "Critical escalation. Immediate spend reduction and funnel audit recommended.",
    ),
    (
        9,
        "Day 16 — Operational memory",
        "System recalls prior occurrences. Trust notes and recurrence pattern visible.",
    ),
    (
        74,
        "Day 19 — Signal recovering",
        "Signal shifting from worsening to recovering. Urgency downgraded.",
    ),
    (
        79,
        "Day 23 — Stabilizing",
        "Signal near baseline. System moves to monitor mode. Intervention may not be needed.",
    ),
    (
        57,
        "Day 28 — Resolved",
        "Primary signal resolved. System returns to quiet. Operational memory updated.",
    ),
]

DEMO_STEP_COUNT = len(DEMO_STEPS)


def get_demo_seed(step: int) -> int:
    step = max(0, min(step, DEMO_STEP_COUNT - 1))
    return DEMO_STEPS[step][0]


def get_demo_label(step: int) -> str:
    step = max(0, min(step, DEMO_STEP_COUNT - 1))
    return DEMO_STEPS[step][1]


def get_demo_description(step: int) -> str:
    step = max(0, min(step, DEMO_STEP_COUNT - 1))
    return DEMO_STEPS[step][2]


def render_demo_controls(sidebar_container) -> None:
    import streamlit as st

    with sidebar_container:
        st.markdown(
            "<div style='height:1px;background:rgba(128,128,128,0.15);"
            "margin:0.8rem 0;'></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='font-size:0.68rem;font-weight:600;opacity:0.45;"
            "text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;'>"
            "Demo flow</div>",
            unsafe_allow_html=True,
        )

        demo_mode = st.toggle(
            "Demo mode", key="demo_mode",
            value=st.session_state.get("demo_mode", False),
        )
        st.markdown(
            "<div style='font-size:0.68rem;opacity:0.4;line-height:1.4;"
            "margin-top:0.1rem;margin-bottom:0.2rem;'>"
            + ("Walk through a curated 28-day arc step by step."
               if demo_mode else
               "Enable to walk through a curated 28-day escalation arc.")
            + "</div>",
            unsafe_allow_html=True,
        )

        if demo_mode:
            step  = st.session_state.get("demo_step", 0)
            label = get_demo_label(step)
            desc  = get_demo_description(step)

            st.markdown(
                f"<div style='background:rgba(30,64,175,0.08);border-radius:6px;"
                f"border:1px solid rgba(30,64,175,0.15);"
                f"padding:0.5rem 0.7rem;margin:0.4rem 0;'>"
                f"<div style='font-size:0.75rem;font-weight:600;color:#3b82f6;'>"
                f"{label}</div>"
                f"<div style='font-size:0.72rem;opacity:0.6;margin-top:0.2rem;"
                f"line-height:1.4;'>{desc}</div>"
                f"<div style='font-size:0.65rem;opacity:0.35;margin-top:0.25rem;'>"
                f"Step {step+1} / {DEMO_STEP_COUNT}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            col_prev, col_next = st.columns(2)
            with col_prev:
                if st.button(
                    "← Back", key="demo_prev",
                    disabled=(step == 0),
                    use_container_width=True,
                ):
                    st.session_state["demo_step"] = max(0, step - 1)
                    st.session_state["seed"] = get_demo_seed(
                        st.session_state["demo_step"]
                    )
                    st.rerun()
            with col_next:
                if st.button(
                    "Next →", key="demo_next",
                    disabled=(step >= DEMO_STEP_COUNT - 1),
                    use_container_width=True,
                ):
                    st.session_state["demo_step"] = min(
                        DEMO_STEP_COUNT - 1, step + 1
                    )
                    st.session_state["seed"] = get_demo_seed(
                        st.session_state["demo_step"]
                    )
                    st.rerun()
