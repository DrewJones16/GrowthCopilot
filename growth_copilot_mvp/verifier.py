"""Post-LLM verifier. Catches the failure mode where the model writes a
plausible-looking briefing with hallucinated numbers or unresolved citations.

Two checks:
  1. Every non-header line containing a number must carry a (source: ...) tag.
  2. Every (source: ...) tag must resolve to a real path in the briefing input.
"""
import re
from typing import Any


SOURCE_TAG_RE = re.compile(r"\(source:\s*([a-zA-Z0-9_\.\[\]]+)\)")
NUMERIC_RE = re.compile(r"(?<![\w_])(-?\d+(?:\.\d+)?%?)(?![\w_])")

EXEMPT_PREFIXES = ("Daily Growth Briefing", "Confidence", "Tier", "Open from")


def _resolve_path(data: dict, path: str) -> Any:
    parts = path.split(".")
    cur: Any = data
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def verify_briefing(briefing_text: str, briefing_input: dict) -> list[str]:
    issues = []
    for line in briefing_text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("-") and len(s) < 3:
            continue
        if any(s.startswith(e) for e in EXEMPT_PREFIXES):
            continue
        if NUMERIC_RE.search(line) and not SOURCE_TAG_RE.search(line):
            issues.append(f"Numeric claim without source tag: {s!r}")
    for m in SOURCE_TAG_RE.finditer(briefing_text):
        path = m.group(1)
        if _resolve_path(briefing_input, path) is None:
            issues.append(f"Unresolved source tag: {path}")
    return issues
