# GrowthCopilot — Product Hunt Launch Assets

> Launch Tuesday–Thursday. Have your email list ready to notify on launch morning.
> Ask for *feedback*, not upvotes — the algorithm penalizes solicitation.
> Aim for top 5 on the day, not necessarily #1. Comments and reviews matter more long-term.

---

## Tagline (under 60 chars)

```
A daily operational briefing instead of a dashboard
```

Alternative options:
```
Know what to act on. Not just what changed.
```
```
Your morning signal briefing — without the dashboard crawl
```

---

## Description (shown on listing page)

Most analytics tools tell you what happened. GrowthCopilot tells you what to do about it — and explains the tradeoffs clearly enough that you can disagree.

It watches your acquisition funnel for three types of signals (funnel drops, source divergence, DAU anomalies) and produces a single daily brief: the one thing that needs your attention, a recommendation with a full consequence model, and an explanation of why it surfaced today versus staying in background monitoring.

**What makes it different:**

→ **Operational, not informational.** Output is a brief, not a chart. One signal, one recommendation, one decision to make.

→ **Deterministic confidence scoring.** No LLMs on the critical path. Every confidence score traces back to sample size, effect size, baseline stability, and detector agreement. You can see exactly why the number is what it is.

→ **A trust engine, not just alerting.** Signals you ignore repeatedly get their urgency downgraded. Patterns that self-resolve lose escalation priority. The system gets more skeptical when history suggests skepticism.

→ **Consequence modeling.** Every recommendation includes expected value, blast radius, cost of waiting, risk of inaction, and operator burden. You see the tradeoffs, not just the conclusion.

**Try it now** at https://growthcopilot.streamlit.app — no signup required. Walk through the built-in 28-day demo arc (Day 1: all clear → Day 14: critical escalation → Day 28: resolved) to see the full system in context.

Currently works with CSV exports from Mixpanel and Amplitude. Direct API integrations coming.

---

## First comment (post immediately after launch — sets the tone)

Hey Product Hunt 👋

I built GrowthCopilot because I got tired of doing the same morning ritual: open Mixpanel, check four numbers, try to decide whether a funnel drop was real noise or something that needed a response today. That translation — from "here's what changed" to "here's what to do about it" — was always manual. I wanted to automate it.

A few things I'm genuinely uncertain about and would love your take on:

1. **The consequence model format** — does seeing "blast radius / cost of waiting / risk of inaction" alongside a recommendation actually change how you'd make the call, or is it information overload?

2. **The daily brief vs. dashboard framing** — is there a version of your team where this fits in? Or does "one signal per day" feel too constrained for how you actually work?

3. **The quiet days** — the system is explicitly designed to stay silent when evidence doesn't warrant action (Day 1 in the demo: "All clear. No signal crossed the confidence threshold."). Is that feature or annoyance?

Try it here: https://growthcopilot.streamlit.app

Would genuinely love brutal feedback — this is early and I'm still figuring out what's actually useful versus what just feels clever.

---

## Gallery / screenshot captions

**Image 1 — The day 14 escalated briefing (hero shot)**
Caption: "Critical signal surfaced with recommendation and full consequence model"

**Image 2 — Day 1 all clear**
Caption: "The system stays silent when evidence doesn't warrant action"

**Image 3 — Signal detail expander (evidence + surface score)**
Caption: "Every confidence score is traceable — no black box"

**Image 4 — The 28-day demo arc sidebar**
Caption: "Walk through a complete incident lifecycle step by step"

**Image 5 — How It Works page (6-layer architecture)**
Caption: "6 layers from raw data to recommendation"

---

## Topics / tags

- Product Analytics
- Growth
- Developer Tools
- SaaS
- Artificial Intelligence

---

## Launch day checklist

- [ ] Post on Tuesday, Wednesday, or Thursday (never Monday or weekend)
- [ ] Go live at 12:01am PST (Product Hunt day resets at midnight PST)
- [ ] Email your Typeform list at 8am — ask for feedback, mention it's live on PH
- [ ] Post Twitter/X thread at 9am on launch day with PH link added
- [ ] Pin first comment immediately after posting
- [ ] Reply to every comment within 30 minutes for first 3 hours
- [ ] Do NOT ask "please upvote" — ask "would love your feedback"
- [ ] Share in Slack communities same morning (different message, mention PH)
- [ ] Have someone post a supportive comment who has a PH history (higher weight)
- [ ] Check back at 6pm — respond to anything that slipped through
