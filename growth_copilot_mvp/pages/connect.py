"""pages/connect.py — guided data connection wizard."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import streamlit as st
import pandas as pd
from datetime import date

SHARED_CSS = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;1,14..32,400&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
    .stMarkdown, .stText, button, input, select, textarea, p, div, span {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .block-container { padding-top: 2.5rem !important; padding-bottom: 4rem !important; max-width: 680px !important; }
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; letter-spacing: -0.02em; }
    hr { border: none !important; border-top: 1px solid rgba(128,128,128,0.1) !important; margin: 1.5rem 0 !important; }
    .stButton > button { font-family: 'Inter', sans-serif !important; font-size: 0.82rem !important; border-radius: 8px !important; transition: all 0.15s; }
    .stButton > button[kind="primary"] { background-color: #1e293b !important; color: white !important; border: none !important; font-weight: 600 !important; }
    .stButton > button[kind="primary"]:hover { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,0.1) !important; }
    [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
    [data-testid="stIconMaterial"] { display: none !important; }
    [data-testid="stExpander"] { border: 1px solid rgba(128,128,128,0.1) !important; border-radius: 10px !important; }
    .streamlit-expanderHeader { font-size: 0.78rem !important; opacity: 0.6 !important; }
"""

st.set_page_config(page_title="GrowthCopilot — Connect", layout="centered")
st.markdown(f"<style>{SHARED_CSS}</style>", unsafe_allow_html=True)

# ── Tool configs ──────────────────────────────────────────────────────────
TOOLS = {
    "mixpanel": {
        "name":        "Mixpanel",
        "color":       "#7856FF",
        "col_user":    "distinct_id",
        "col_event":   "event",
        "col_source":  "utm_source",
        "col_ts":      "time",
        "steps": [
            ("Open Mixpanel", "Go to <strong>mixpanel.com</strong> and sign in."),
            ("Go to Events", "In the left sidebar, click <strong>Events</strong>."),
            ("Set your date range", "In the top right, set the date range to <strong>Last 90 days</strong>."),
            ("Export", "Click the <strong>Export</strong> button (top right) → <strong>Export to CSV</strong>."),
            ("Upload below", "Once downloaded, drag the CSV file into the upload box below."),
        ],
        "event_guesses": {
            "install":             ["first_open", "app_open", "install", "application_installed", "signed_up"],
            "onboarding_start":    ["onboarding_start", "onboarding_started", "tutorial_begin", "tutorial_start"],
            "onboarding_complete": ["onboarding_complete", "onboarding_completed", "tutorial_complete", "tutorial_end", "account_created"],
            "first_action":        ["first_action", "first_purchase", "project_created", "item_created", "content_view", "first_post"],
            "habit_action":        ["habit_action", "purchase", "session_start", "app_opened", "daily_active"],
        },
    },
    "amplitude": {
        "name":        "Amplitude",
        "color":       "#0066FF",
        "col_user":    "user_id",
        "col_event":   "event_type",
        "col_source":  "utm_source",
        "col_ts":      "event_time",
        "steps": [
            ("Open Amplitude", "Go to <strong>app.amplitude.com</strong> and sign in."),
            ("Go to Analytics", "In the left sidebar, click <strong>Analytics</strong> then <strong>Event Segmentation</strong>."),
            ("Select All Events", "In the event picker, select <strong>Any Event</strong> to include all events."),
            ("Set date range", "Set the date range to <strong>Last 90 days</strong>."),
            ("Export CSV", "Click the <strong>three dots</strong> menu (top right of chart) → <strong>Export CSV</strong>."),
            ("Upload below", "Once downloaded, drag the CSV file into the upload box below."),
        ],
        "event_guesses": {
            "install":             ["first_open", "install", "app_install", "user_created", "signed_up", "Register"],
            "onboarding_start":    ["onboarding_start", "Onboarding Started", "tutorial_begin", "start_onboarding"],
            "onboarding_complete": ["onboarding_complete", "Onboarding Completed", "tutorial_complete", "complete_onboarding"],
            "first_action":        ["first_action", "Purchase", "first_purchase", "Create Project", "first_post"],
            "habit_action":        ["habit_action", "Purchase", "Session Start", "App Open", "repeat_session"],
        },
    },
    "other": {
        "name":        "Other tool",
        "color":       "#64748b",
        "col_user":    None,
        "col_event":   None,
        "col_source":  None,
        "col_ts":      None,
        "steps": [
            ("Export from your tool", "Export a CSV of user events. Most analytics tools have an Export or Download button in their Events or Analytics section."),
            ("Required columns", "Your CSV needs: a <strong>user ID</strong>, an <strong>event name</strong>, an <strong>acquisition source</strong> (utm_source, channel, etc.), and a <strong>timestamp</strong>."),
            ("Column names", "Column names don't matter — you'll map them below after uploading."),
            ("Upload below", "Drag your CSV into the upload box below."),
        ],
        "event_guesses": {
            "install":             ["first_open", "install", "app_open", "signed_up", "user_created", "registered"],
            "onboarding_start":    ["onboarding_start", "tutorial_begin", "setup_start"],
            "onboarding_complete": ["onboarding_complete", "tutorial_complete", "setup_complete", "account_created"],
            "first_action":        ["first_action", "first_purchase", "project_created", "content_view"],
            "habit_action":        ["habit_action", "purchase", "session_start", "app_opened"],
        },
    },
}

CANON_LABELS = {
    "install":             "Install / First open",
    "onboarding_start":    "Onboarding started",
    "onboarding_complete": "Onboarding completed",
    "first_action":        "First key action",
    "habit_action":        "Repeat / habit action",
}

# ── Already connected banner ──────────────────────────────────────────────
if st.session_state.get("user_events"):
    n   = len(st.session_state["user_events"])
    src = st.session_state.get("user_data_source", "your data")
    st.markdown(
        f"<div style='padding:0.85rem 1rem;border-radius:8px;"
        f"border:1px solid rgba(22,163,74,0.25);background:rgba(22,163,74,0.05);"
        f"margin-bottom:1.4rem;display:flex;justify-content:space-between;align-items:center;'>"
        f"<div>"
        f"<div style='font-size:0.85rem;font-weight:600;color:#16a34a;'>Connected</div>"
        f"<div style='font-size:0.75rem;opacity:0.5;margin-top:0.1rem;'>"
        f"{src} · {n:,} events loaded · Daily Briefing is running on your data</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("Disconnect and use demo data"):
        for k in ["user_events", "user_data_source", "user_event_map", "connect_tool", "connect_step"]:
            st.session_state.pop(k, None)
        st.rerun()
    st.markdown("<hr>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='margin-bottom:1.8rem;'>"
    "<div style='font-size:1.35rem;font-weight:700;letter-spacing:-0.03em;'>"
    "Connect your data</div>"
    "<div style='font-size:0.85rem;opacity:0.42;margin-top:0.4rem;line-height:1.6;'>"
    "Takes about 3 minutes. GrowthCopilot will run the same intelligence on your real events."
    "</div></div>",
    unsafe_allow_html=True,
)

# ── Step 1: Pick your tool ────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.62rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem;'>"
    "Step 1 — What analytics tool do you use?</div>",
    unsafe_allow_html=True,
)

selected_tool = st.session_state.get("connect_tool")

# Clean single-row tool selector
c1, c2, c3 = st.columns(3)
with c1:
    _active = selected_tool == "mixpanel"
    if st.button(f"{'✓ ' if _active else ''}Mixpanel", key="tool_mixpanel",
                 use_container_width=True, type="primary" if _active else "secondary"):
        st.session_state["connect_tool"] = "mixpanel"
        st.rerun()
with c2:
    _active = selected_tool == "amplitude"
    if st.button(f"{'✓ ' if _active else ''}Amplitude", key="tool_amplitude",
                 use_container_width=True, type="primary" if _active else "secondary"):
        st.session_state["connect_tool"] = "amplitude"
        st.rerun()
with c3:
    _active = selected_tool == "other"
    if st.button(f"{'✓ ' if _active else ''}Other tool", key="tool_other",
                 use_container_width=True, type="primary" if _active else "secondary"):
        st.session_state["connect_tool"] = "other"
        st.rerun()

if not selected_tool:
    st.markdown(
        "<div style='font-size:0.78rem;opacity:0.38;margin-top:0.8rem;'>"
        "Select your analytics tool above to see export instructions.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

tool = TOOLS[selected_tool]

st.markdown("<hr>", unsafe_allow_html=True)

# ── Step 2: Export instructions ───────────────────────────────────────────
st.markdown(
    f"<div style='font-size:0.62rem;font-weight:600;opacity:0.35;"
    f"text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.8rem;'>"
    f"Step 2 — Export from {tool['name']}</div>",
    unsafe_allow_html=True,
)

for i, (title, desc) in enumerate(tool["steps"], 1):
    st.markdown(
        f"<div style='display:flex;gap:0.85rem;align-items:flex-start;"
        f"margin-bottom:0.7rem;'>"
        f"<div style='width:22px;height:22px;border-radius:50%;"
        f"background:{tool['color']};color:white;"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-size:0.65rem;font-weight:700;flex-shrink:0;margin-top:1px;'>{i}</div>"
        f"<div>"
        f"<div style='font-size:0.85rem;font-weight:600;margin-bottom:0.1rem;'>{title}</div>"
        f"<div style='font-size:0.8rem;opacity:0.52;line-height:1.55;'>{desc}</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ── Step 3: Upload ────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.62rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.6rem;'>"
    "Step 3 — Upload your CSV</div>",
    unsafe_allow_html=True,
)

uploaded = st.file_uploader(
    "Drop your CSV here",
    type=["csv"],
    label_visibility="collapsed",
)

if not uploaded:
    st.markdown(
        "<div style='font-size:0.75rem;opacity:0.32;margin-top:0.4rem;'>"
        "Your data stays in your browser session and is never stored or shared."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ── Parse file ────────────────────────────────────────────────────────────
try:
    df = pd.read_csv(uploaded)
except Exception as e:
    st.error(f"Could not read file: {e}")
    st.stop()

cols = list(df.columns)
n_rows = len(df)

st.markdown(
    f"<div style='font-size:0.78rem;opacity:0.4;margin:0.4rem 0 1rem;'>"
    f"Loaded {n_rows:,} rows · {len(cols)} columns</div>",
    unsafe_allow_html=True,
)

# ── Column mapping ────────────────────────────────────────────────────────
def best_col(candidates, cols, fallback=0):
    for cand in candidates:
        for col in cols:
            if cand.lower() in col.lower():
                return cols.index(col)
    return fallback

if tool["col_user"]:
    # Auto-detect for known tools
    idx_user   = best_col([tool["col_user"],   "user","id","pseudo","distinct"],  cols)
    idx_event  = best_col([tool["col_event"],  "event","name","type","action"],   cols)
    idx_source = best_col([tool["col_source"], "source","utm","channel","medium"], cols)
    idx_ts     = best_col([tool["col_ts"],     "time","date","stamp","created"],   cols)
else:
    idx_user   = best_col(["user","id","pseudo","distinct"], cols)
    idx_event  = best_col(["event","name","type","action"],  cols)
    idx_source = best_col(["source","utm","channel"],        cols)
    idx_ts     = best_col(["time","date","stamp","created"], cols)

# Only show column mapping for "other" or if auto-detect might be wrong
needs_mapping = selected_tool == "other"

if needs_mapping:
    st.markdown(
        "<div style='font-size:0.62rem;font-weight:600;opacity:0.35;"
        "text-transform:uppercase;letter-spacing:0.1em;margin:1rem 0 0.5rem;'>"
        "Match your columns</div>",
        unsafe_allow_html=True,
    )
    cc1, cc2, cc3, cc4 = st.columns(4)
    with cc1:
        st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.2rem;'>User ID</div>", unsafe_allow_html=True)
        col_user = st.selectbox("u", cols, index=idx_user, label_visibility="collapsed", key="col_user")
    with cc2:
        st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.2rem;'>Event name</div>", unsafe_allow_html=True)
        col_event = st.selectbox("e", cols, index=idx_event, label_visibility="collapsed", key="col_event")
    with cc3:
        st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.2rem;'>Source</div>", unsafe_allow_html=True)
        col_source = st.selectbox("s", cols, index=idx_source, label_visibility="collapsed", key="col_source")
    with cc4:
        st.markdown("<div style='font-size:0.6rem;font-weight:600;opacity:0.38;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.2rem;'>Timestamp</div>", unsafe_allow_html=True)
        col_ts = st.selectbox("t", cols, index=idx_ts, label_visibility="collapsed", key="col_ts")
else:
    col_user   = cols[idx_user]
    col_event  = cols[idx_event]
    col_source = cols[idx_source]
    col_ts     = cols[idx_ts]
    # Show a quiet confirmation
    st.markdown(
        f"<div style='font-size:0.75rem;opacity:0.35;margin-bottom:0.8rem;'>"
        f"Auto-detected: user={col_user} · event={col_event} · "
        f"source={col_source} · time={col_ts}</div>",
        unsafe_allow_html=True,
    )

# ── Event mapping ─────────────────────────────────────────────────────────
st.markdown(
    "<div style='font-size:0.62rem;font-weight:600;opacity:0.35;"
    "text-transform:uppercase;letter-spacing:0.1em;margin:1.2rem 0 0.4rem;'>"
    "Step 4 — Confirm your key events</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='font-size:0.78rem;opacity:0.38;margin-bottom:0.9rem;'>"
    "We've pre-filled these based on common event names. "
    "Just confirm or change if needed. Skip any you don't track."
    "</div>",
    unsafe_allow_html=True,
)

raw_events  = sorted(df[col_event].dropna().astype(str).unique().tolist())
event_opts  = ["— skip —"] + raw_events
guesses     = tool["event_guesses"]

event_map   = {}
for canon, label in CANON_LABELS.items():
    # Find best guess
    guess = "— skip —"
    for g in guesses.get(canon, []):
        for e in raw_events:
            if g.lower() == e.lower() or g.lower() in e.lower():
                guess = e
                break
        if guess != "— skip —":
            break

    idx_g = event_opts.index(guess) if guess in event_opts else 0

    ec1, ec2 = st.columns([1, 2])
    with ec1:
        st.markdown(
            f"<div style='font-size:0.8rem;font-weight:500;padding-top:0.55rem;'>"
            f"{label}</div>",
            unsafe_allow_html=True,
        )
    with ec2:
        chosen = st.selectbox(
            label, event_opts, index=idx_g,
            label_visibility="collapsed",
            key=f"ev_{canon}"
        )
    if chosen != "— skip —":
        event_map[chosen] = canon

# ── Connect button ────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:1.2rem;'></div>", unsafe_allow_html=True)

mapped = len(event_map)
if mapped == 0:
    st.markdown(
        "<div style='font-size:0.78rem;opacity:0.38;'>"
        "Map at least one event above to continue.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

st.markdown(
    f"<div style='font-size:0.75rem;opacity:0.38;margin-bottom:0.8rem;'>"
    f"{mapped} event{'s' if mapped != 1 else ''} mapped — ready to connect.</div>",
    unsafe_allow_html=True,
)

if st.button("Run analysis on my data", type="primary", use_container_width=True):
    events  = []
    skipped = 0

    for _, row in df.iterrows():
        try:
            raw_name = str(row[col_event])
            canon    = event_map.get(raw_name)
            if not canon:
                skipped += 1
                continue
            raw_ts = str(row[col_ts])
            if "T" in raw_ts:
                day = date.fromisoformat(raw_ts.split("T")[0])
            elif " " in raw_ts.strip():
                day = date.fromisoformat(raw_ts.strip().split(" ")[0])
            else:
                day = date.fromisoformat(raw_ts.strip()[:10])
            src = str(row.get(col_source, "unknown")).lower().strip() or "unknown"
            events.append({
                "user":   str(row[col_user]),
                "event":  canon,
                "source": src,
                "day":    day,
            })
        except Exception:
            skipped += 1
            continue

    if len(events) < 50:
        st.error(
            f"Only {len(events)} events were processed successfully "
            f"({skipped} skipped). "
            "Check that your event mapping matches the events in your file."
        )
    else:
        st.session_state["user_events"]      = events
        st.session_state["user_data_source"] = f"{tool['name']} · {uploaded.name}"
        st.session_state["user_event_map"]   = event_map
        st.success(
            f"Connected. {len(events):,} events loaded from {uploaded.name}. "
            "Head to Daily Briefing to see your analysis."
        )
        st.balloons()