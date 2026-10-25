"""Tools for analyzing natural-language software requirements."""

from .parser import Requirement, parse_requirements
from .rules import (
    Finding,
    check_imprecise_quantity,
    check_imprecise_quantity_phrases,
    check_vague_wording,
)
from .performance import check_performance_criteria

__all__ = [
    "Requirement", "parse_requirements", "Finding",
    "check_vague_wording",
    "check_imprecise_quantity",
    "check_imprecise_quantity_phrases",
    "check_performance_criteria",
]
