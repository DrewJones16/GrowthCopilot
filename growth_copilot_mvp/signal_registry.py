"""signal_registry.py — persistent signal tracking with decay dynamics + outcome logging.

Phase 6 additions:
    - Richer outcome schema separating signal_real from recommendation_useful
    - ignored_count: tracks how many times operator didn't act on a signal
    - record_outcome() accepts the new schema
    - outcome_summary() returns empirical detector precision proxies
    - detector_precision_from_outcomes() derives per-detector true-positive rates
"""
import json
import os
from datetime import date
from typing import Dict, List, Optional


_HERE     = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_HERE, "data")
_REGISTRY = os.path.join(_DATA_DIR, "signal_registry.json")

_MAX_HISTORY   = 30
STABILIZE_DAYS = 3
ESCALATE_DAYS  = 5
ABSENCE_RUNS   = 2

STRENGTH_INITIAL  = 60.0
STRENGTH_FLOOR    = 25.0
STRENGTH_RESOLVE  = 10.0

DECAY_SEEN = {"worsening": 1.02, "stable": 0.96, "recovering": 0.90}
DECAY_ABSENT      = 0.70
REINFORCE_WEIGHT  = 0.30


def _today() -> str:
    return date.today().isoformat()


def _load() -> Dict:
    if not os.path.exists(_REGISTRY):
        return {}
    try:
        with open(_REGISTRY, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save(registry: Dict) -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_REGISTRY, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def _signal_id(title: str) -> str:
    return title.lower().replace(" ", "_").replace("/", "_")


def _trim(lst: List, n: int = _MAX_HISTORY) -> List:
    return lst[-n:] if len(lst) > n else lst


def _empty_outcome() -> Dict:
    """Richer outcome schema separating signal quality from recommendation quality."""
    return {
        # Signal quality
        "signal_real":           None,   # bool: was the underlying issue real?
        "severity_accurate":     None,   # bool: was the severity level right?
        "self_resolved":         None,   # bool: did it resolve without intervention?
        # Recommendation quality
        "recommendation_followed": None, # bool: did operator follow the recommendation?
        "recommendation_useful":   None, # bool: was it useful regardless?
        "action_taken":            None, # str: none / investigating / mitigated / resolved
        # Outcome
        "issue_confirmed":         None, # bool: was the root cause confirmed?
        "time_to_resolution":      None, # int: days from first_seen to resolved
        "business_impact":         None, # str: low / medium / high / none
        # Meta
        "operator_feedback":       "",   # free text
        "recorded_at":             None,
        "detector_type":           None, # which detector triggered this (set on record)
    }


def _decay_strength(current: float, direction: str, confidence: int) -> float:
    decay    = DECAY_SEEN.get(direction, 0.95)
    decayed  = current * decay
    reinforce = confidence * REINFORCE_WEIGHT
    return min(round(decayed + reinforce, 1), 100.0)


def _consecutive_direction(dir_history: List, direction: str) -> int:
    count = 0
    for _, d in reversed(dir_history):
        if d == direction: count += 1
        else: break
    return count


def _resolve_status(record: Dict, current_direction: str) -> str:
    dir_history = record.get("direction_history", [])
    prev_status = record.get("status", "active")
    consec_recovering = _consecutive_direction(dir_history, "recovering")
    consec_worsening  = _consecutive_direction(dir_history, "worsening")
    consec_stable     = _consecutive_direction(dir_history, "stable")
    if prev_status == "resolved": return "recurring"
    if consec_worsening >= 2: return "worsening"
    if consec_recovering >= 2: return "improving"
    if prev_status in ("worsening", "improving", "escalated") and consec_stable >= 2:
        return "stabilizing"
    if prev_status == "stabilizing" and consec_stable >= STABILIZE_DAYS:
        return "resolved"
    if prev_status == "improving" and consec_recovering >= STABILIZE_DAYS:
        return "resolved"
    if prev_status in ("worsening", "improving", "stabilizing", "escalated"):
        return prev_status
    return "active"


def _escalation_level(record: Dict, current_direction: str) -> int:
    dir_history      = record.get("direction_history", [])
    consec_worsening = _consecutive_direction(dir_history, "worsening")
    days             = record.get("days_active", 1)
    if consec_worsening >= ESCALATE_DAYS * 2 or days >= 14: return 2
    if consec_worsening >= ESCALATE_DAYS or days >= 7: return 1
    return 0


def _lifecycle_narrative(record: Dict) -> str:
    status    = record.get("status", "active")
    days      = record.get("days_active", 1)
    first     = record.get("first_seen", "")
    recur     = record.get("recurrence_count", 0)
    res_date  = record.get("resolution_date", "")
    dir_hist  = record.get("direction_history", [])
    consec_r  = _consecutive_direction(dir_hist, "recovering")
    consec_s  = _consecutive_direction(dir_hist, "stable")
    prev_escl = record.get("peak_escalation_level", 0)
    strength  = record.get("signal_strength", STRENGTH_INITIAL)

    if status == "resolved":
        note = f"Resolved {res_date}" if res_date else "Resolved"
        if prev_escl >= 1: note += " — was escalated"
        return note
    if not record.get("is_surfaced", True):
        return f"Fading — signal strength {strength:.0f}/100"
    if status == "recurring": return f"Recurring — seen {recur + 1}x total"
    if status == "improving":
        return f"Improving — returning toward baseline for {consec_r} day{'s' if consec_r != 1 else ''}"
    if status == "stabilizing":
        return f"Stabilizing — {consec_s} day{'s' if consec_s != 1 else ''} near baseline"
    if status == "worsening":
        d = _consecutive_direction(dir_hist, "worsening")
        return f"Worsening — {d} consecutive day{'s' if d != 1 else ''}"
    if status == "escalated": return f"Escalated — active {days} days"
    if record.get("is_new_today"): return "First detected today"
    return f"Active since {first}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def update_signal(
    cluster_title: str,
    severity: str,
    direction: str,
    confidence_score: int,
    days_active: int,
) -> Dict:
    registry = _load()
    sid      = _signal_id(cluster_title)
    today    = _today()

    if sid not in registry:
        strength = min(STRENGTH_INITIAL + confidence_score * REINFORCE_WEIGHT, 100.0)
        record = {
            "signal_id":             sid,
            "title":                 cluster_title,
            "first_seen":            today,
            "last_seen":             today,
            "days_active":           days_active,
            "absent_runs":           0,
            "severity_history":      [[today, severity]],
            "direction_history":     [[today, direction]],
            "confidence_history":    [[today, confidence_score]],
            "strength_history":      [[today, round(strength, 1)]],
            "signal_strength":       round(strength, 1),
            "is_surfaced":           strength >= STRENGTH_FLOOR,
            "status":                "new",
            "resolution_date":       None,
            "recurrence_count":      0,
            "ignored_count":         0,
            "escalation_level":      0,
            "peak_escalation_level": 0,
            "is_new_today":          True,
            "narrative":             "First detected today",
            "outcome":               _empty_outcome(),
            "outcome_history":       [],
        }
    else:
        record       = registry[sid]
        was_resolved = record.get("status") == "resolved"

        record["severity_history"]   = _trim(record.get("severity_history",   []) + [[today, severity]])
        record["direction_history"]  = _trim(record.get("direction_history",  []) + [[today, direction]])
        record["confidence_history"] = _trim(record.get("confidence_history", []) + [[today, confidence_score]])
        record["last_seen"]    = today
        record["days_active"]  = days_active
        record["absent_runs"]  = 0
        record["is_new_today"] = False

        current_strength = record.get("signal_strength", STRENGTH_INITIAL)
        new_strength     = _decay_strength(current_strength, direction, confidence_score)
        record["signal_strength"] = new_strength
        record["strength_history"] = _trim(
            record.get("strength_history", []) + [[today, round(new_strength, 1)]]
        )
        record["is_surfaced"] = new_strength >= STRENGTH_FLOOR

        if was_resolved:
            old_outcome = record.get("outcome", {})
            if old_outcome.get("recorded_at"):
                record.setdefault("outcome_history", []).append(old_outcome)
            record["recurrence_count"] = record.get("recurrence_count", 0) + 1
            record["resolution_date"]  = None
            record["outcome"]          = _empty_outcome()
            record["signal_strength"]  = STRENGTH_INITIAL

        if "outcome"         not in record: record["outcome"]         = _empty_outcome()
        if "outcome_history" not in record: record["outcome_history"] = []
        if "ignored_count"   not in record: record["ignored_count"]   = 0

    new_status = _resolve_status(record, direction)
    new_escl   = _escalation_level(record, direction)

    strength = record.get("signal_strength", STRENGTH_INITIAL)
    if strength <= STRENGTH_RESOLVE and new_status not in ("resolved", "recurring"):
        new_status = "resolved"
        record["resolution_date"] = today

    if new_status == "resolved" and record.get("outcome", {}).get("time_to_resolution") is None:
        try:
            d1 = date.fromisoformat(record.get("first_seen", today))
            d2 = date.fromisoformat(today)
            record["outcome"]["time_to_resolution"] = (d2 - d1).days
        except Exception:
            pass

    record["status"]                = new_status
    record["escalation_level"]      = new_escl
    record["peak_escalation_level"] = max(record.get("peak_escalation_level", 0), new_escl)
    record["narrative"]             = _lifecycle_narrative(record)

    registry[sid] = record
    _save(registry)
    return record


def record_outcome(
    cluster_title: str,
    signal_real:             Optional[bool] = None,
    severity_accurate:       Optional[bool] = None,
    self_resolved:           Optional[bool] = None,
    recommendation_followed: Optional[bool] = None,
    recommendation_useful:   Optional[bool] = None,
    action_taken:            Optional[str]  = None,
    issue_confirmed:         Optional[bool] = None,
    time_to_resolution:      Optional[int]  = None,
    business_impact:         Optional[str]  = None,
    operator_feedback:       str = "",
) -> Optional[Dict]:
    registry = _load()
    sid      = _signal_id(cluster_title)
    if sid not in registry:
        return None

    record  = registry[sid]
    outcome = record.setdefault("outcome", _empty_outcome())

    if signal_real             is not None: outcome["signal_real"]             = signal_real
    if severity_accurate       is not None: outcome["severity_accurate"]       = severity_accurate
    if self_resolved           is not None: outcome["self_resolved"]           = self_resolved
    if recommendation_followed is not None: outcome["recommendation_followed"] = recommendation_followed
    if recommendation_useful   is not None: outcome["recommendation_useful"]   = recommendation_useful
    if action_taken            is not None: outcome["action_taken"]            = action_taken
    if issue_confirmed         is not None: outcome["issue_confirmed"]         = issue_confirmed
    if time_to_resolution      is not None: outcome["time_to_resolution"]      = time_to_resolution
    if business_impact         is not None: outcome["business_impact"]         = business_impact
    if operator_feedback:                   outcome["operator_feedback"]       = operator_feedback

    outcome["recorded_at"] = _today()

    # Track ignored count (surfaced but no action taken)
    if recommendation_followed is False:
        record["ignored_count"] = record.get("ignored_count", 0) + 1

    registry[sid] = record
    _save(registry)
    return record


def outcome_summary() -> Dict:
    registry     = _load()
    all_outcomes = []
    for r in registry.values():
        o = r.get("outcome", {})
        if o.get("recorded_at"):
            all_outcomes.append(o)
        for h in r.get("outcome_history", []):
            if h.get("recorded_at"):
                all_outcomes.append(h)

    if not all_outcomes:
        return {"total_outcomes": 0}

    n             = len(all_outcomes)
    real          = sum(1 for o in all_outcomes if o.get("signal_real") is True)
    not_real      = sum(1 for o in all_outcomes if o.get("signal_real") is False)
    sev_accurate  = sum(1 for o in all_outcomes if o.get("severity_accurate") is True)
    self_res      = sum(1 for o in all_outcomes if o.get("self_resolved") is True)
    followed      = sum(1 for o in all_outcomes if o.get("recommendation_followed") is True)
    useful        = sum(1 for o in all_outcomes if o.get("recommendation_useful") is True)
    ignored       = sum(1 for o in all_outcomes if o.get("recommendation_followed") is False)
    confirmed     = sum(1 for o in all_outcomes if o.get("issue_confirmed") is True)
    resolutions   = [o["time_to_resolution"] for o in all_outcomes if o.get("time_to_resolution") is not None]
    avg_res_days  = round(sum(resolutions) / len(resolutions), 1) if resolutions else None
    impacts       = [o["business_impact"] for o in all_outcomes if o.get("business_impact")]
    actions       = [o["action_taken"] for o in all_outcomes if o.get("action_taken")]

    return {
        "total_outcomes":             n,
        "signal_real_rate":           round(real / n, 3) if n else None,
        "false_positive_rate":        round(not_real / n, 3) if n else None,
        "severity_accuracy_rate":     round(sev_accurate / n, 3) if n else None,
        "self_resolution_rate":       round(self_res / n, 3) if n else None,
        "recommendation_follow_rate": round(followed / n, 3) if n else None,
        "recommendation_useful_rate": round(useful / n, 3) if n else None,
        "ignored_rate":               round(ignored / n, 3) if n else None,
        "issue_confirmation_rate":    round(confirmed / n, 3) if n else None,
        "avg_time_to_resolution_days": avg_res_days,
        "business_impact_distribution": {i: impacts.count(i) for i in set(impacts)},
        "action_distribution":        {a: actions.count(a) for a in set(actions)},
    }


def detector_precision_from_outcomes() -> Dict:
    """Derive per-detector empirical precision from recorded outcomes.

    Returns {detector_type: {precision, n_samples}} for detectors
    with enough outcome data.
    """
    registry = _load()
    by_detector: Dict[str, List[bool]] = {}

    for r in registry.values():
        det = r.get("outcome", {}).get("detector_type")
        signal_real = r.get("outcome", {}).get("signal_real")
        if det and signal_real is not None:
            by_detector.setdefault(det, []).append(signal_real)
        for h in r.get("outcome_history", []):
            det = h.get("detector_type")
            signal_real = h.get("signal_real")
            if det and signal_real is not None:
                by_detector.setdefault(det, []).append(signal_real)

    result = {}
    for det, outcomes in by_detector.items():
        n = len(outcomes)
        result[det] = {
            "precision":   round(sum(outcomes) / n, 3) if n else None,
            "n_samples":   n,
            "min_for_reliable": 10,
            "reliable":    n >= 10,
        }
    return result


def increment_ignored(cluster_title: str) -> None:
    """Increment ignored count without recording a full outcome."""
    registry = _load()
    sid      = _signal_id(cluster_title)
    if sid in registry:
        registry[sid]["ignored_count"] = registry[sid].get("ignored_count", 0) + 1
        _save(registry)


def check_resolutions(active_signal_ids: List[str]) -> List[Dict]:
    registry = _load()
    today    = _today()
    resolved = []
    norm_ids = {_signal_id(t) for t in active_signal_ids}

    for sid, record in registry.items():
        if sid in norm_ids: continue
        if record.get("status") == "resolved": continue

        record["absent_runs"] = record.get("absent_runs", 0) + 1
        current_strength = record.get("signal_strength", STRENGTH_INITIAL)
        new_strength     = round(current_strength * DECAY_ABSENT, 1)
        record["signal_strength"] = new_strength
        record["is_surfaced"]     = new_strength >= STRENGTH_FLOOR

        if record["absent_runs"] >= ABSENCE_RUNS or new_strength <= STRENGTH_RESOLVE:
            record["status"]          = "resolved"
            record["resolution_date"] = today
            if record.get("outcome", {}).get("time_to_resolution") is None:
                try:
                    d1 = date.fromisoformat(record.get("first_seen", today))
                    d2 = date.fromisoformat(today)
                    record.setdefault("outcome", _empty_outcome())["time_to_resolution"] = (d2 - d1).days
                except Exception:
                    pass
            record["narrative"] = _lifecycle_narrative(record)
            resolved.append(record)

    _save(registry)
    return resolved


def get_signal(cluster_title: str) -> Optional[Dict]:
    return _load().get(_signal_id(cluster_title))

def get_all_signals() -> Dict:
    return _load()

def get_active_signals() -> List[Dict]:
    return [r for r in _load().values() if r.get("status") != "resolved"]

def get_resolved_signals() -> List[Dict]:
    return [r for r in _load().values() if r.get("status") == "resolved"]

def get_recently_resolved(n: int = 5) -> List[Dict]:
    resolved = get_resolved_signals()
    resolved.sort(key=lambda r: r.get("resolution_date", ""), reverse=True)
    return resolved[:n]

def get_recurring_signals() -> List[Dict]:
    return [r for r in _load().values() if r.get("recurrence_count", 0) > 0]

def reset_registry() -> None:
    if os.path.exists(_REGISTRY):
        os.remove(_REGISTRY)

def registry_summary() -> Dict:
    all_r    = _load()
    active   = [r for r in all_r.values() if r.get("status") != "resolved"]
    resolved = [r for r in all_r.values() if r.get("status") == "resolved"]
    surfaced = [r for r in active if r.get("is_surfaced", True)]
    return {
        "total_tracked": len(all_r),
        "active":        len(active),
        "surfaced":      len(surfaced),
        "fading":        len(active) - len(surfaced),
        "resolved":      len(resolved),
        "recurring":     sum(1 for r in all_r.values() if r.get("recurrence_count", 0) > 0),
        "escalated":     sum(1 for r in active if r.get("escalation_level", 0) >= 1),
        "improving":     sum(1 for r in active if r.get("status") == "improving"),
        "stabilizing":   sum(1 for r in active if r.get("status") == "stabilizing"),
        "with_outcomes": sum(1 for r in all_r.values() if r.get("outcome", {}).get("recorded_at")),
        "ignored_total": sum(r.get("ignored_count", 0) for r in all_r.values()),
    }