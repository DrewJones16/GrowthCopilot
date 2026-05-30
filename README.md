# GrowthCopilot

**Watches your product telemetry like an experienced operator.**

Most analytics tools tell you what happened. GrowthCopilot tells you what to do about it — and explains the tradeoffs clearly enough that you can disagree.

[**Live demo →**](https://growthcopilot.streamlit.app)

---

## What it does

GrowthCopilot runs a continuous intelligence layer on your product events:

- **Detects** meaningful changes across funnel conversion, cohort divergence, and volume anomalies — using three independent detectors that are deliberately decorrelated
- **Remembers** every signal's full history: when it first appeared, how it escalated, whether it recurred, and how it resolved
- **Prioritises** what actually needs your attention — most days it stays silent
- **Recommends** specific actions with explicit tradeoffs: expected value, blast radius, cost of waiting, risk of inaction
- **Learns** from feedback — signals you consistently ignore get deprioritised over time

---

## Demo

Enable **Follow the story** in the sidebar to walk through a choreographed 28-day operational narrative:

| Day | What happens |
|-----|-------------|
| 1   | All clear — system silent |
| 5   | Weak signal detected — single detector, low confidence |
| 9   | Two independent detectors agree — urgency rises |
| 14  | Critical escalation — immediate action recommended |
| 16  | System surfaces operational memory from prior occurrences |
| 19  | Signal recovering — intervention appears to be working |
| 23  | Stabilizing — system moves to monitor mode |
| 28  | Resolved — system returns to silence |

---

## Connect your data

Upload a CSV export from Mixpanel, Amplitude, or any analytics tool via **Connect Your Data** in the sidebar. The system auto-detects columns and event names and runs the full intelligence pipeline on your real events.

**Required fields:** user ID, event name, acquisition source, timestamp

---

## Run locally

```bash
git clone https://github.com/yourusername/growthcopilot
cd growthcopilot
pip install -r requirements.txt
streamlit run growth_copilot_mvp/app.py
```

---

## Architecture

Six layers, each building on the previous:

1. **Perception** — three independent detectors (funnel drop, cohort divergence, volume anomaly)
2. **Cognition** — signal clustering and cross-signal pattern recognition
3. **Attention** — three-tier surfacing system (surface / background / ephemeral)
4. **Decisioning** — consequence modeling across six dimensions
5. **Learning** — outcome feedback loop that calibrates detector weights over time
6. **Trust** — adaptive restraint based on operator response history

---

Built with Python + Streamlit. Running on synthetic demo data.
