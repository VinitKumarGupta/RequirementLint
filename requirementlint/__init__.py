"""Tools for analyzing natural-language software requirements."""

from .parser import Requirement, parse_requirements
from .rules import Finding, check_vague_wording

__all__ = ["Requirement", "parse_requirements", "Finding", "check_vague_wording"]
