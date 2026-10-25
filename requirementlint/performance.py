"""Conservative checks for missing time limits in common performance wording."""

import re

from .parser import Requirement
from .rules import Finding


_QUOTED_TEXT = re.compile(r'"[^"\r\n]*"|“[^”\r\n]*”')
_SPACE = r"[ \t]+"
_OBJECT_WORD = (
    r"(?:the|a|an|all|each|user|customer|dashboard|page|pages|screen|screens|"
    r"document|documents|file|files|image|images|report|reports|request|requests|"
    r"record|records|data|changes|application|service|results)"
)
_ACTION_FAST = re.compile(
    r"\b(?P<action>load(?:s|ing)?|respond(?:s|ing)?|process(?:es|ing)?|"
    r"sav(?:e|es|ing)|start(?:s|ing)?|render(?:s|ing)?)"
    + _SPACE
    + rf"(?:{_OBJECT_WORD}{_SPACE}){{0,4}}"
    + r"(?P<phrase>(?:very[ \t]+)?fast)\b"
    # A following noun can make Fast a label or adjective, rather than the
    # speed of the action: for example, "load the Fast preset".
    + r"(?=[ \t]*(?:$|[.,;:!?()\r\n—–-]|<=|≤|"
    r"\b(?:within|under|below|at|no|less|in|for|after|and|or|but|while|when|with|without)\b))",
    re.IGNORECASE,
)
_LATENCY_METRIC = r"(?:latenc(?:y|ies)|response[ \t]+times?)"
_LOW_FORM = r"(?:very[ \t]+)?low(?:er|est)?"
_LOW_METRIC = re.compile(
    rf"\b(?P<metric>{_LATENCY_METRIC})"
    r"(?:[ \t]+(?:should|must|shall|will))?"
    r"[ \t]+(?:be|remain|stay|is|are)[ \t]+"
    rf"(?P<phrase>{_LOW_FORM})\b",
    re.IGNORECASE,
)
_LOW_METRIC_PHRASE = re.compile(
    rf"\b(?P<phrase>{_LOW_FORM}[ \t]+"
    rf"(?P<metric>{_LATENCY_METRIC}))\b",
    re.IGNORECASE,
)
_TIME_LIMIT = (
    r"\d+(?:\.\d+)?[ \t]*"
    r"(?:milliseconds?|ms|seconds?|secs?|s|minutes?|mins?|min|"
    r"bytes?|B|KB|MB|GB|TB|kilobytes?|megabytes?|gigabytes?|terabytes?|"
    r"bps|Kbps|Mbps|Gbps|%|percent|percentage)"
    r"(?:[ \t]*(?:per[ \t]+(?:second|sec)|/s))?"
)
_ATTACHED_UPPER_BOUND = re.compile(
    r"[ \t]*(?:[,:—–-][ \t]*|\([ \t]*)?"
    r"(?:in[ \t]+)?"
    r"(?:within|under|below|at[ \t]+most|no[ \t]+more[ \t]+than|"
    r"less[ \t]+than|<=|≤)[ \t]*"
    + _TIME_LIMIT,
    re.IGNORECASE,
)
_COMPARATIVE_UPPER_BOUND = re.compile(r"[ \t]+than[ \t]+" + _TIME_LIMIT, re.IGNORECASE)


def _overlaps_quote(start: int, end: int, quoted_spans: list[tuple[int, int]]) -> bool:
    return any(start < quote_end and end > quote_start for quote_start, quote_end in quoted_spans)


def _has_attached_upper_bound(
    text: str, start: int, end: int, quoted_spans: list[tuple[int, int]]
) -> bool:
    """Accept only a nearby limit belonging to the matched performance phrase.

    An optional comma, colon, dash, opening parenthesis, or "in" is allowed.
    Crossing another action, metric, sentence, semicolon, or conjunction is
    deliberately unsupported, so unrelated deadlines do not hide a warning.
    """
    bound = _ATTACHED_UPPER_BOUND.match(text, end)
    # "Lower than 100 ms" supplies a bound; "lower than before" does not.
    # Keep the comparative form instead of normalizing it away.
    if bound is None and re.search(r"\blower\b", text[start:end], re.IGNORECASE):
        bound = _COMPARATIVE_UPPER_BOUND.match(text, end)
    return bound is not None and not _overlaps_quote(bound.start(), bound.end(), quoted_spans)


def check_performance_criteria(requirement: Requirement) -> list[Finding]:
    """Flag "fast" actions and low/lower/lowest latency without a local limit.

    This is a wording heuristic, not a semantic or completeness check. It
    recognizes a small set of actions, common objects, and adjacent upper
    time bounds. Distant/reordered bounds and externally defined targets
    remain for human review. A recognized time bound does not establish
    that its workload or test conditions are complete. Quoted prose is
    skipped in the same way as literal labels. Negation is not interpreted.
    """
    quoted_spans = [match.span() for match in _QUOTED_TEXT.finditer(requirement.text)]
    candidates = []
    for match in _ACTION_FAST.finditer(requirement.text):
        action = match.group("action").lower()
        if action.startswith("load"):
            metric = "loading time"
        elif action.startswith("respond"):
            metric = "response time"
        elif action.startswith("process"):
            metric = "processing time"
        elif action.startswith("sav"):
            metric = "save time"
        elif action.startswith("start"):
            metric = "startup time"
        else:
            metric = "rendering time"
        candidates.append((match.start("phrase"), match.end("phrase"), metric))
    for pattern in (_LOW_METRIC, _LOW_METRIC_PHRASE):
        for match in pattern.finditer(requirement.text):
            metric = "latency" if match.group("metric").lower().startswith("latenc") else "response time"
            candidates.append((match.start("phrase"), match.end("phrase"), metric))

    findings = []
    for start, end, metric in sorted(candidates):
        if _overlaps_quote(start, end, quoted_spans):
            continue
        if _has_attached_upper_bound(requirement.text, start, end, quoted_spans):
            continue
        phrase = requirement.text[start:end]
        findings.append(Finding(
            rule_id="RL003",
            category="missing-performance-criteria",
            line_number=requirement.line_number,
            start=start,
            end=end,
            phrase=phrase,
            explanation=f"'{phrase}' does not specify a measurable upper limit for {metric}.",
            suggestion=(
                f"Specify a maximum {metric} and the test conditions, such as workload, "
                "data size, and device or network setup."
            ),
        ))
    return findings
