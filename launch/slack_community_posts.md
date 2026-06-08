# GrowthCopilot — Slack Community Posts

> Replace `https://growthcopilot.streamlit.app` with your live link before posting.
> Post in each community's #tools, #feedback, or #show-and-tell channel.
> These are written to ask for feedback, not to pitch — that framing works far better in these communities.

---

## Lenny's Newsletter Slack
*Post in: #product-tools, #show-and-tell, or #growth*

Hey all — I built something I've been wanting for a while and would love honest feedback from this group specifically.

Background: I kept doing the same morning ritual — opening Mixpanel, checking a handful of numbers, deciding whether a funnel drop was real or noise. Eventually I got tired of doing that translation manually and built a system to do it.

**GrowthCopilot** produces a daily operational brief instead of a dashboard. One surfaced signal, a recommendation, and a consequence model (expected value, blast radius, cost of waiting). The goal is to answer "does this need a response today?" — not to replace your analytics stack, just to sit on top of it.

A few things that might be interesting or wrong:
- Three decorrelated detectors that don't share state (funnel drops, source divergence, volume anomalies)
- A "trust engine" that downgrades urgency when history suggests caution
- An explicit attention system that keeps quiet when evidence doesn't warrant action

Demo here (no signup, runs on synthetic data with a 28-day walkthrough): https://growthcopilot.streamlit.app

Specific things I'd love to know: Does the output format feel useful or just different? Is the morning ritual framing actually how you experience this problem?

---

## Reforge Alumni Slack
*Post in: #tools-and-resources or #product-growth*

Built something for this community's exact problem and would love a sanity check.

If you've ever done the morning dashboard crawl — checking whether a funnel drop is real, deciding whether to pause spend, trying to figure out if last night's deploy broke something — this is what I've been building to replace that ritual.

**GrowthCopilot**: a daily brief that surfaces the one thing that needs your attention, with a recommendation and a full consequence model (EV, blast radius, cost of waiting, operator burden). The architecture is fully deterministic — no LLM in the critical path, everything traceable to source data.

What I'd value most from this community is whether the consequence model framing is useful or just noise. Reforge trains people to think in loops and systems — curious whether the "blast radius + cost of waiting" breakdown adds anything to how you'd actually make the call.

Demo: https://growthcopilot.streamlit.app — there's a 28-day arc you can step through.

---

## Product Collective / Mind the Product Slack
*Post in: #tools or #feedback-wanted*

Made something and would genuinely love product people to tell me what's wrong with it.

**GrowthCopilot** is a daily operational briefing for product and growth teams — it watches your acquisition funnel, surfaces signals above a confidence threshold, and produces a recommendation with tradeoffs. It's meant to sit between your analytics tool and your morning Slack message saying "hey why did installs drop."

The bit I'm most uncertain about is whether the consequence model (expected value, blast radius, cost of waiting, risk of inaction) is actually useful for how PMs make decisions — or if it's just more information that gets ignored under pressure.

Demo (no signup, 28-day walkthrough built in): https://growthcopilot.streamlit.app

Anyone doing growth at a startup — would love 10 minutes of your honest reaction.

---

## Posting notes

- **Timing:** Post Tuesday–Thursday, late morning your timezone
- **Don't post all three the same day** — space them out by 2–3 days
- **Reply to every response the same day** — these communities remember who ghosts after asking for feedback
- **If someone says "I do this manually every morning"** — that's a warm lead. Ask if they'd be willing to do a 20-minute call
- **If someone asks for real data integration** — that's the strongest buy signal you can get. Note their name
