"""narrative_memory.py — cross-signal pattern memory."""
from typing import Dict, List, Optional, Any
from datetime import date


def _days_between(d1: str, d2: str) -> Optional[int]:
    try:
        return abs((date.fromisoformat(d2) - date.fromisoformat(d1)).days)
    except Exception:
        return None


def get_narrative_hints(
    cluster: Dict[str, Any],
    signal_record: Optional[Dict[str, Any]],
    all_signals: Dict[str, Any],
) -> List[str]:
    if not signal_record:
        return []

    hints    = []
    today    = date.today().isoformat()
    recur    = signal_record.get("recurrence_count", 0)
    status   = signal_record.get("status", "active")
    days_act = signal_record.get("days_active", 1)
    hist     = signal_record.get("outcome_history", [])
    dir_hist = signal_record.get("direction_history", [])
    peak_e   = signal_record.get("peak_escalation_level", 0)
    ignored  = signal_record.get("ignored_count", 0)

    if recur >= 1:
        total_seen = recur + 1
        prior_durations     = [h["time_to_resolution"] for h in hist if h.get("time_to_resolution") is not None]
        prior_self_resolved = [h["self_resolved"] for h in hist if h.get("self_resolved") is not None]

        if prior_durations:
            avg_dur = round(sum(prior_durations) / len(prior_durations), 1)
            hints.append(
                f"Previously seen {total_seen} times — average resolution: {avg_dur:.0f} day{'s' if avg_dur != 1 else ''}."
            )
        else:
            hints.append(f"This signal has recurred {total_seen} times total.")

        if prior_self_resolved:
            sr_rate = sum(prior_self_resolved) / len(prior_self_resolved)
            if sr_rate >= 0.6:
                hints.append(f"In {int(sr_rate*100)}% of prior occurrences, the issue resolved without intervention.")
            elif sr_rate <= 0.3:
                hints.append(f"Prior occurrences typically required active intervention — self-resolution rate was {int(sr_rate*100)}%.")

    if peak_e >= 2 and status not in ("escalated", "worsening"):
        hints.append("Previously escalated to critical level — now de-escalating.")
    elif peak_e >= 1 and status == "new":
        hints.append("This signal type has escalated in a prior cycle.")

    if days_act >= 14 and status == "stabilizing":
        hints.append(f"Signal has been stable for {days_act} days without resolving — may be structural.")

    if len(dir_hist) >= 4:
        directions = [d for _, d in dir_hist[-6:]]
        reversals  = sum(1 for i in range(1, len(directions)) if directions[i] != directions[i-1])
        if reversals >= 3:
            hints.append("Signal direction has oscillated multiple times — may reflect measurement noise.")

    if ignored >= 3:
        hints.append(f"Operators have not acted on this signal {ignored} times. Urgency adjusted downward.")

    related = _find_related(cluster.get("title",""), signal_record, all_signals)
    if related:
        hints.append(related)

    return hints[:3]


def _find_related(title, record, all_signals):
    first_seen = record.get("first_seen", "")
    if not first_seen:
        return None
    co = []
    for sid, r in all_signals.items():
        if r.get("title","") == title:
            continue
        r_first = r.get("first_seen","")
        if not r_first:
            continue
        days = _days_between(first_seen, r_first)
        if days is not None and days <= 7:
            co.append(r.get("title", sid))
    if len(co) == 1:
        return f"Co-occurred with '{co[0]}' in a prior cycle — may share a root cause."
    elif len(co) >= 2:
        return f"Co-occurred with {len(co)} other signals in a prior cycle."
    return None


def render_narrative_memory(hints: List[str]) -> None:
    """Render narrative memory as compact indented text lines — no nodes or circles."""
    if not hints:
        return
    import streamlit as st
    lines_html = "".join(
        f"<div style='font-size:0.78rem;opacity:0.65;line-height:1.5;"
        f"padding:0.1rem 0 0.1rem 0.6rem;"
        f"border-left:1px solid rgba(128,128,128,0.2);"
        f"margin-bottom:0.18rem;'>{h}</div>"
        for h in hints
    )
    st.markdown(
        f"<div style='margin:0.1rem 0 0.6rem;'>"
        f"<div style='font-size:0.6rem;font-weight:600;opacity:0.48;"
        f"text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.28rem;'>"
        f"Operational memory</div>"
        f"{lines_html}</div>",
        unsafe_allow_html=True,
    )