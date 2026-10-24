"""Read requirements from line-separated text without changing their wording."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Requirement:
    """One requirement with its original text and one-based source line number."""

    text: str
    line_number: int


def parse_requirements(text: str) -> list[Requirement]:
    """Return one requirement per nonblank line, retaining source line numbers.

    Whitespace-only lines are skipped. Other lines keep their leading and
    trailing whitespace so later findings can refer to the original text.
    Line separators are excluded from the stored requirement text.
    """
    requirements = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            requirements.append(Requirement(text=line, line_number=line_number))
    return requirements
