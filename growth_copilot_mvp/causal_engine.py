"""causal_engine.py — deterministic causal hypothesis generation.

Softened language throughout: no "confirms", "caused by", "explains the full gap".
Uses "likely contributor", "strongly suggests", "consistent with" instead.
"""
from typing import Any, Dict, List, Optional


LINK_SAME_SOURCE_MULTI_DETECTOR = "same_source_multi_detector"
LINK_FUNNEL_DRIVES_COMPLETION   = "funnel_drop_drives_completion_gap"
LINK_DAU_UPSTREAM               = "dau_anomaly_upstream_of_funnel"
LINK_STEP_CHAIN                 = "sequential_funnel_step_chain"


def _get_source(insight) -> Optional[str]:
    rm = getattr(insight, "raw_metrics", {})
    return rm.get("source") or rm.get("worst_source") or None


def _get_type(insight) -> str:
    return getattr(insight, "type", "")


def _get_step(insight) -> Optional[int]:
    return getattr(insight, "raw_metrics", {}).get("step_index")


def _find_same_source_links(insights: List[Any]) -> List[Dict]:
    by_source: Dict[str, List[Any]] = {}
    for ins in insights:
        src = _get_source(ins)
        if src:
            by_source.setdefault(src, []).append(ins)

    links = []
    for src, group in by_source.items():
        types = {_get_type(i) for i in group}
        if len(types) >= 2:
            type_list = sorted(types)
            links.append({
                "link_type": LINK_SAME_SOURCE_MULTI_DETECTOR,
                "source": src,
                "insight_ids": [i.id for i in group],
                "hypothesis": (
                    f"TikTok is showing correlated signals across "
                    f"{len(types)} independent detectors ({', '.join(type_list)}). "
                    f"This strongly suggests a single root cause rather than isolated noise, "
                    f"though a shared confounder cannot be ruled out."
                ),
                "strength": "strong" if len(types) >= 3 else "moderate",
            })
    return links


def _find_funnel_drives_completion(insights: List[Any]) -> List[Dict]:
    funnel_drops = {_get_source(i): i for i in insights if _get_type(i) == "funnel_drop"}
    divergences  = {_get_source(i): i for i in insights if _get_type(i) == "cohort_divergence"}

    links = []
    for src in set(funnel_drops) & set(divergences):
        fd = funnel_drops[src]
        cd = divergences[src]
        step = _get_step(fd)
        transition = fd.raw_metrics.get("transition", f"step {step}")
        gap_pp  = round(cd.raw_metrics.get("gap", 0) * 100, 1)
        drop_pp = round(fd.raw_metrics.get("absolute_drop", 0) * 100, 1)
        links.append({
            "link_type": LINK_FUNNEL_DRIVES_COMPLETION,
            "source": src,
            "insight_ids": [fd.id, cd.id],
            "hypothesis": (
                f"The {drop_pp}pp drop at '{transition}' for {src} users "
                f"is a likely contributor to the {gap_pp}pp overall completion gap. "
                f"The timing and magnitude are consistent with this step being the "
                f"primary driver, though other funnel stages have not been fully ruled out."
            ),
            "strength": "strong",
        })
    return links


def _find_dau_upstream(insights: List[Any]) -> List[Dict]:
    has_anomaly  = any(_get_type(i) == "anomaly" for i in insights)
    funnel_drops = [i for i in insights if _get_type(i) == "funnel_drop"]

    if not has_anomaly or not funnel_drops:
        return []

    links = []
    for fd in funnel_drops[:1]:
        src = _get_source(fd) or "unknown"
        links.append({
            "link_type": LINK_DAU_UPSTREAM,
            "source": src,
            "insight_ids": [fd.id] + [i.id for i in insights if _get_type(i) == "anomaly"],
            "hypothesis": (
                f"The install volume anomaly is occurring simultaneously with the "
                f"{src} funnel regression. This pattern is consistent with a campaign "
                f"quality shift — more installs from lower-intent users — "
                f"though a product-side cause has not been ruled out."
            ),
            "strength": "moderate",
        })
    return links


def _find_step_chains(insights: List[Any]) -> List[Dict]:
    by_source: Dict[str, List[Any]] = {}
    for ins in insights:
        if _get_type(ins) == "funnel_drop":
            src = _get_source(ins)
            if src:
                by_source.setdefault(src, []).append(ins)

    links = []
    for src, group in by_source.items():
        if len(group) < 2:
            continue
        steps = sorted([_get_step(i) for i in group if _get_step(i) is not None])
        consecutive = any(steps[i+1] - steps[i] == 1 for i in range(len(steps)-1))
        if consecutive:
            links.append({
                "link_type": LINK_STEP_CHAIN,
                "source": src,
                "insight_ids": [i.id for i in group],
                "hypothesis": (
                    f"{src.title()} users are showing drops at {len(steps)} consecutive "
                    f"funnel steps (steps {steps}). This is consistent with a "
                    f"systemic onboarding experience issue rather than a single "
                    f"step regression, though independent causes per step are possible."
                ),
                "strength": "strong",
            })
    return links


def find_causal_links(insights: List[Any]) -> List[Dict]:
    if not insights:
        return []

    links = []
    links.extend(_find_same_source_links(insights))
    links.extend(_find_funnel_drives_completion(insights))
    links.extend(_find_dau_upstream(insights))
    links.extend(_find_step_chains(insights))

    seen = set()
    deduped = []
    for link in links:
        key = frozenset(link["insight_ids"]) | {link["link_type"]}
        if key not in seen:
            seen.add(key)
            deduped.append(link)

    strength_rank = {"strong": 2, "moderate": 1, "weak": 0}
    deduped.sort(key=lambda l: strength_rank.get(l["strength"], 0), reverse=True)
    return deduped


def primary_hypothesis(links: List[Dict]) -> Optional[str]:
    if not links:
        return None
    return links[0]["hypothesis"]