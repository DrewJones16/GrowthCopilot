# GrowthCopilot — Hacker News Show HN Post

> **Before posting:** Replace `https://growthcopilot.streamlit.app` with your live Streamlit link.
> Post Tuesday–Thursday between 8–11am US Eastern for best front-page chances.
> HN rewards honest, technically specific posts. Don't over-hype. Let the architecture do the work.

---

## Title

```
Show HN: GrowthCopilot – a daily operational briefing instead of a product analytics dashboard
```

---

## Body

I spent too many mornings doing the same thing: open Mixpanel, check four numbers, try to decide whether a 15% funnel drop was noise, a seasonal dip, or something that needed a response today.

The problem isn't lack of data — it's the translation layer between "here's what changed" and "here's what to do about it, and why." Most analytics tools stop at the first sentence.

GrowthCopilot is my attempt to build that layer. It watches your acquisition funnel and produces a daily brief: one prioritized signal, a recommendation, and a consequence model showing expected value, blast radius, cost of waiting, and risk of inaction. The goal is to answer the morning question — *is this real, and does it need a response today* — without requiring an analyst to dig.

A few things I tried to get right:

**No LLMs on the critical path.** All signal detection, confidence scoring, trend analysis, and urgency classification are deterministic functions. Every number in the "why this surfaced" breakdown traces back to source data. I wanted the system to be wrong in predictable ways, not confident-sounding-nonsense ways. There's a surface score breakdown in the UI that shows exactly why a signal reached the briefing versus staying in background monitoring.

**Three decorrelated detectors.** Funnel drops, source divergence, and volume anomalies are detected independently and combined. They intentionally don't share intermediate state — if two fire on the same day, that's a meaningful signal; if only one fires, the confidence score reflects that and adds a "single detector — treat with caution" warning. The goal was to produce fewer, higher-quality alerts than threshold-based monitoring.

**An attention system.** Not every signal reaches the briefing. There's a surface score (weighted combination of confidence, urgency, persistence, and detector agreement) with explicit tiers: Surfaced → Background → Ephemeral. Attention is treated as a finite resource. If too many signals fire simultaneously, lower-priority ones drop to background monitoring rather than flooding the output.

**Operational memory.** Signals accumulate a history: first seen, direction over time, escalation level, recurrence count, past outcomes. A recurring signal gets a different recommendation than a new one. Signals that have self-resolved three times before get lower urgency. The briefing shows trust notes — orange warnings when history suggests the system should be more skeptical than the current confidence score implies.

**A consequence model, not just a recommendation.** Every action recommendation includes: expected value, blast radius (cost if wrong), time sensitivity, cost of waiting, risk of inaction, and operator burden. I wanted to make the tradeoffs explicit enough that a PM could reasonably disagree with the recommendation and know what they're weighing.

Currently running on synthetic data — there are five company archetypes (consumer social, SaaS productivity, marketplace, mobile game, subscription fitness) that each produce different scenario distributions. Real data integration via CSV upload is live; direct Mixpanel/Amplitude API connectors are next.

There's a 28-day demo arc you can walk through step by step (Day 1: all clear → Day 14: critical escalation → Day 28: resolved) that shows how the full system behaves over a simulated incident lifecycle.

Demo: https://growthcopilot.streamlit.app

Happy to answer questions about the confidence scoring model, the attention/surface score architecture, the trust engine, or why I went deterministic rather than model-based for detection.

---

## Anticipated HN questions — prepare answers for these

**"Why not just use Amplitude/Mixpanel AI features?"**
Those tell you what changed. This tells you whether to act and what the cost of waiting is. Different jobs. Also: most AI analytics features require you to already know what question to ask. This surfaces questions you didn't know to ask.

**"This seems like it could produce a lot of false positives."**
That's why there's an attention system, a three-tier detector setup, and a trust engine. The system is explicitly designed to prefer silence over noise. The demo arc's Day 1 ("All clear") is a feature — most monitoring tools would have fired on that day.

**"The consequence model seems like it could be wrong."**
Yes, deliberately so in a legible way. It shows you the uncertainty, not a false precision. The goal is to give a PM a structured way to think through the decision, not to make the decision for them.

**"Will you open source it?"**
[Your answer here]

**"How does it handle multiple simultaneous signals?"**
Surface score ranking + the MAX_SURFACED_CLUSTERS cap. Lower-priority signals go to background monitoring and are summarized in a single line rather than getting a full briefing card. This is in the Calibration Console.

---

## Posting notes

- **Don't edit the title after posting** — HN penalizes edits in the first hour
- **Reply quickly** — being active in the comment thread in the first 2 hours strongly affects front-page ranking
- **Lead with technical honesty** — if someone finds a flaw, acknowledge it directly and explain your tradeoff
- **Don't cross-post the same day** — HN detects same-day cross-posting from Twitter and Reddit and it hurts ranking
- **The comment that lands best on HN:** a direct explanation of the one architectural decision you're least sure about — it signals intellectual honesty and invites constructive engagement
