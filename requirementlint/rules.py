"""Explainable checks for potentially vague requirement wording."""

from dataclasses import dataclass
import re
from typing import TYPE_CHECKING

from .parser import Requirement

if TYPE_CHECKING:
    from .preprocessing import Token


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
    "seamlessly": (
        "'Seamlessly' does not identify the user-visible behavior or acceptance threshold.",
        "Describe the specific workflow, expected result, and the conditions that demonstrate success.",
    ),
    "robust": (
        "'Robust' is subjective unless paired with concrete safety, reliability, or failure-handling criteria.",
        "State the operating conditions, failure modes, and acceptable performance under those conditions.",
    ),
    "highly reliable": (
        "'Highly reliable' does not state a measurable availability or failure threshold.",
        "Specify the reliability target, such as uptime or error rate, and the conditions under which it is measured.",
    ),
    "state-of-the-art": (
        "'State-of-the-art' is promotional rather than testable and does not define a measurable outcome.",
        "Replace it with a measurable target, such as a latency, throughput, accuracy, or availability threshold.",
    ),
}

_VAGUE_WORDING = re.compile(
    r"\b(?:quickly|user-friendly|efficiently|seamlessly|robust|highly[ \t]+reliable|state-of-the-art)\b",
    re.IGNORECASE,
)
_QUOTED_TEXT = re.compile(r'"[^"\r\n]*"|“[^”\r\n]*”')
_IMPRECISE_QUANTITIES = {"many", "several", "few"}
_IMPRECISE_QUANTITY_PHRASES = re.compile(
    r"\b(?:large[ \t]+(?:volume|volumes)|high[ \t]+(?:capacity|capacities)|significant[ \t]+(?:amount|amounts))\b",
    re.IGNORECASE,
)


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


def check_imprecise_quantity(
    requirement: Requirement, tokens: list["Token"]
) -> list[Finding]:
    """Flag unspecified quantities using tokens from the supplied requirement.

    The caller passes tokenize_requirement(requirement) so the app can reuse
    the same tokens for analysis and display. This is a lexical heuristic;
    it does not infer grammatical roles or resolve quantities from context.
    """
    quoted_spans = [match.span() for match in _QUOTED_TEXT.finditer(requirement.text)]
    findings = []
    for token in tokens:
        if token.text.lower() not in _IMPRECISE_QUANTITIES:
            continue
        if any(start <= token.start and token.end <= end for start, end in quoted_spans):
            continue
        findings.append(
            Finding(
                rule_id="RL002",
                category="imprecise-quantity",
                line_number=requirement.line_number,
                start=token.start,
                end=token.end,
                phrase=token.text,
                explanation=f"'{token.text}' does not specify an exact quantity or range.",
                suggestion=(
                    "Specify a count, minimum, maximum, or range and the conditions "
                    "it applies to. For user capacity, state whether users are concurrent."
                ),
            )
        )
    return findings


def check_imprecise_quantity_phrases(requirement: Requirement) -> list[Finding]:
    """Flag vague multi-word quantity phrases such as 'large volume' or 'high capacity'.

    This complements the single-word quantity rule by catching short, common
    phrase patterns that leave the size or capacity unclear without specifying a
    measurable threshold.
    """
    quoted_spans = [match.span() for match in _QUOTED_TEXT.finditer(requirement.text)]
    findings = []
    for match in _IMPRECISE_QUANTITY_PHRASES.finditer(requirement.text):
        if any(start <= match.start() and match.end() <= end for start, end in quoted_spans):
            continue
        phrase = match.group(0)
        findings.append(
            Finding(
                rule_id="RL004",
                category="imprecise-quantity-phrase",
                line_number=requirement.line_number,
                start=match.start(),
                end=match.end(),
                phrase=phrase,
                explanation=f"'{phrase}' does not specify a measurable quantity, capacity, or limit.",
                suggestion=(
                    "State the exact capacity, throughput, or volume target and the conditions "
                    "under which it is measured, such as concurrent users, dataset size, or time window."
                ),
            )
        )
    return findings
