# GrowthCopilot — Twitter/X Launch Thread

> **Before posting:** Replace `https://growthcopilot.streamlit.app` and `[TYPEFORM_URL]` with your real links.
> Post Tuesday–Thursday morning for best reach. Space tweets 30–60 min apart if doing a slow-drip thread, or post all at once.

---

## Tweet 1 — Hook (lead tweet, makes or breaks the thread)

Every morning I was doing the same ritual:

Open Mixpanel. Check 4 numbers. Ask myself:
- Is that funnel drop real or just noise?
- Should I pause ad spend now or wait?
- Did something actually break?

I eventually got tired of answering the same questions manually and built a system to do it for me.

---

## Tweet 2 — The problem with dashboards

Most analytics tools tell you what happened:

📊 TikTok conversion: -18%
📊 Install volume: +34%
📊 Onboarding complete: -12%
📊 D1 retention: -8%

What they don't tell you: which number actually matters today. And what to do about it.

---

## Tweet 3 — The artifact (show the output)

GrowthCopilot produces a daily brief instead of a dashboard.

Instead of charts, you get:

🔴 **TikTok activation failure**
Worsening — day 7 of decline
Likely onboarding bug from recent deploy

→ Reduce spend immediately
→ Audit last 3 deploys before next campaign push

One signal. One recommendation. Traceable reasoning.

---

## Tweet 4 — What makes it different (the interesting mechanic)

Every recommendation includes a consequence model:

- Expected value of acting
- Blast radius if you're wrong
- Cost of waiting 24 hours
- Risk of inaction
- Operator burden

The system explains tradeoffs, not just conclusions.
You can disagree with it — and it tells you what to weigh.

---

## Tweet 5 — The trust engine (the part I'm most proud of)

It has a memory.

Signals you repeatedly ignore get their urgency downgraded.
Patterns that self-resolve without intervention lose escalation priority.
Recurring signals get flagged as recurring — the recommendation changes.

The system gets more cautious when history suggests caution.

No more alert fatigue from the same false positive firing every Monday.

---

## Tweet 6 — The demo arc (walk them through it)

There's a built-in 28-day demo arc:

Day 1 → All clear
Day 5 → Something stirs (single detector, low confidence)
Day 9 → Worsening (two detectors agree)
Day 14 → Critical escalation
Day 19 → Signal recovering
Day 23 → Stabilizing
Day 28 → Resolved

Walk it step by step and see how the system narrates a real incident from first signal to resolution.

---

## Tweet 7 — CTA

Built this for growth leads and PMs who are tired of translating dashboards into decisions.

Try the demo (no signup, runs on synthetic data): https://growthcopilot.streamlit.app

If it matches a real problem you have — or doesn't — I'd genuinely love to know: [TYPEFORM_URL]

---

## Optional reply tweet (pin as first reply for more context)

Technical notes for anyone curious:

- No LLMs on the critical path — all detection and scoring is deterministic arithmetic
- 3 decorrelated detectors (funnel drop, source divergence, DAU anomaly)
- Disagreement between detectors lowers the surface score and adds a caution warning
- Currently 5 company archetypes: consumer social, SaaS, marketplace, mobile game, fitness
- Real data integration (Mixpanel/Amplitude CSV) is live; API connectors are next

Ask me anything about the architecture.

---

## Posting notes

- **Best days:** Tuesday, Wednesday, Thursday
- **Best time:** 8–10am or 12–2pm in your target timezone (US EST for max reach)
- **Don't ask for retweets** — ask for feedback ("curious if this matches a real problem you have")
- **Reply to every comment** in the first 2 hours — algorithm rewards early engagement
- **Screenshot the Day 14 escalated briefing** and embed it in Tweet 3 if you can — visual anchor matters
