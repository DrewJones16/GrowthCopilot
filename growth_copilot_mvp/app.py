"""app.py - navigation entry point."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import streamlit as st

st.set_page_config(
    page_title="GrowthCopilot",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Global CSS applied to every page
st.markdown("""
<style>
    /* Hide broken icon text rendering */
    [data-testid="stIconMaterial"] { display: none !important; }
    /* Keep sidebar always expanded */
    section[data-testid="stSidebar"] { display: block !important; }
</style>
""", unsafe_allow_html=True)

_here  = os.path.dirname(os.path.abspath(__file__))
_pages = os.path.join(_here, "pages")

pg = st.navigation([
    st.Page(os.path.join(_pages, "how_it_works.py"),  title="How It Works"),
    st.Page(os.path.join(_pages, "briefing.py"),       title="Daily Briefing"),
    st.Page(os.path.join(_pages, "connect.py"),        title="Connect Your Data"),
    st.Page(os.path.join(_pages, "calibration.py"),    title="Calibration Console ↗"),
])
pg.run()
