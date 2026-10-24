"""Explainable checks for potentially vague requirement wording."""

from dataclasses import dataclass
import re

from .parser import Requirement


@dataclass(frozen=True)
class Finding:
    """A warning located in a requirement's original text.

    start and end are zero-based character offsets within the source line;
    end is exclusive, so requirement.text[start:end] equals phrase.
    """

    rule_id: str
    category: str
    line_number: int
    start: int
    end: int
    phrase: str
    explanation: str
    suggestion: str


_GUIDANCE = {
    "quickly": (
        "The required speed is not measurable from 'quickly' alone.",
        "Specify a time limit and the conditions under which it will be tested.",
    ),
    "user-friendly": (
        "Different users may interpret 'user-friendly' differently.",
        "Specify the user task and observable criteria for completing it successfully.",
    ),
    "efficiently": (
        "The word 'efficiently' does not identify a metric or target.",
        "Specify a relevant metric, such as processing time or resource usage, and its target and test conditions.",
    ),
}

_VAGUE_WORDING = re.compile(r"\b(?:quickly|user-friendly|efficiently)\b", re.IGNORECASE)
_QUOTED_TEXT = re.compile(r'"[^"\r\n]*"|“[^”\r\n]*”')


def check_vague_wording(requirement: Requirement) -> list[Finding]:
    """Flag supported phrases outside paired straight or curly double quotes.

    Quoted spans are treated as literal text, such as UI labels. This is a
    heuristic: it also skips quoted prose and does not infer sentence meaning.
    """
    quoted_spans = [match.span() for match in _QUOTED_TEXT.finditer(requirement.text)]
    findings = []
    for match in _VAGUE_WORDING.finditer(requirement.text):
        if any(start <= match.start() and match.end() <= end for start, end in quoted_spans):
            continue
        explanation, suggestion = _GUIDANCE[match.group().lower()]
        findings.append(
            Finding(
                rule_id="RL001",
                category="vague-wording",
                line_number=requirement.line_number,
                start=match.start(),
                end=match.end(),
                phrase=match.group(),
                explanation=explanation,
                suggestion=suggestion,
            )
        )
    return findings
